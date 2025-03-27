
from flask import Flask, render_template, request, send_file
from docx import Document
from io import BytesIO
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/olustur', methods=['POST'])
def olustur():
    try:
        ortak_sayisi = int(request.form.get('ortak_sayisi'))
        ortaklar = []
        toplam_sermaye = 0
        toplam_pay = 0

        for i in range(ortak_sayisi):
            ad = request.form.get(f'ortak_ad_{i}')
            sermaye = int(request.form.get(f'ortak_sermaye_{i}') or 0)
            pay_adedi = int(request.form.get(f'ortak_pay_{i}') or 1)
            tc = request.form.get(f'ortak_tc_{i}')
            uyruk = request.form.get(f'ortak_uyruk_{i}')
            mudur = 'evet' if request.form.get(f'ortak_mudur_{i}') else 'hayir'
            imza = request.form.get(f'ortak_imza_{i}') or 'belirtilmedi'
            pay_tutari = round(sermaye / pay_adedi)

            toplam_sermaye += sermaye
            toplam_pay += pay_adedi

            ortaklar.append({
                'ad': ad,
                'sermaye': sermaye,
                'pay_adedi': pay_adedi,
                'pay_tutari': pay_tutari,
                'tc': tc,
                'uyruk': uyruk,
                'mudur': mudur,
                'imza': imza
            })

        unvan = request.form.get('unvan')
        merkez_il = request.form.get('merkez_il')
        merkez_ilce = request.form.get('merkez_ilce')
        adres = request.form.get('adres')
        faaliyet = request.form.get('faaliyet')

        headers = {
            "Authorization": "Bearer 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",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "Sen bir limited şirket ana sözleşmesi hazırlayan uzmansın. MERSİS formatına uygun resmi dil kullan."
                },
                {
                    "role": "user",
                    "content": f"{faaliyet} alanında faaliyet gösterecek bir limited şirket için Türk Ticaret Kanununa uygun Madde 3 – Amaç ve Konu metni hazırla. En az 5 ana başlık ve her başlıkta 3-5 alt madde olacak şekilde yaz."
                }
            ]
        }

        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            amac_konu = response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            amac_konu = f"[GPT hatası]: {str(e)}"

        doc = Document()
        doc.add_heading('LİMİTED ŞİRKET ANA SÖZLEŞMESİ', 0)
        doc.add_heading('3. AMAÇ VE KONU', level=1)
        doc.add_paragraph(amac_konu)

        doc.add_heading('6. SERMAYE VE ORTAKLAR', level=1)
        for ortak in ortaklar:
            doc.add_paragraph(f"{ortak['ad']} - {ortak['sermaye']} TL sermaye, {ortak['pay_adedi']} pay, Müdür: {ortak['mudur'].capitalize()}, İmza Yetkisi: {ortak['imza']}")

        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name="sirket_ana_sozlesmesi.docx")

    except Exception as e:
        return f"HATA OLUŞTU: {e}"

if __name__ == '__main__':
    app.run(debug=True)
