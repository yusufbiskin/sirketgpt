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
    ortak_sayisi = int(request.form.get('ortak_sayisi'))
    ortaklar = []
    toplam_sermaye = 0
    toplam_pay = 0

    for i in range(ortak_sayisi):
        ad = request.form.get(f'ortak_ad_{i}')
        sermaye = int(request.form.get(f'ortak_sermaye_{i}', 0))
        pay_adedi = int(request.form.get(f'ortak_pay_{i}', 1))
        tc = request.form.get(f'ortak_tc_{i}')
        uyruk = request.form.get(f'ortak_uyruk_{i}', 'TÜRKİYE CUMHURİYETİ')
        mudur = 'evet' if request.form.get(f'ortak_mudur_{i}') else 'hayir'
        imza = request.form.get(f'ortak_imza_{i}', 'belirtilmedi')
        pay_tutari = round(sermaye / pay_adedi)

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

        toplam_sermaye += sermaye
        toplam_pay += pay_adedi

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
        data = response.json()
        amac_konu = data["choices"][0]["message"]["content"]
    except Exception as e:
        amac_konu = f"[GPT hatası]: {e}"

    doc = Document()
    doc.add_heading("LİMİTED ŞİRKET ANA SÖZLEŞMESİ", 0)
    
    sabit_maddeler = [
        ("1. KURULUŞ", "Aşağıdaki kurucular tarafından limited şirket kurulmuştur."),
        ("2. UNVAN", f"Şirketin unvanı {unvan} LİMİTED ŞİRKETİ'dir."),
        ("3. AMAÇ VE KONU", amac_konu),
        ("4. MERKEZ", f"{merkez_il}/{merkez_ilce}, {adres}"),
        ("5. SÜRE", "Şirketin süresi sınırsızdır."),
        ("6. SERMAYE", f"Şirket sermayesi {toplam_sermaye} TL, toplam pay {toplam_pay}."),
        ("7. ŞİRKETİN İDARESİ", "Müdürler genel kurul tarafından seçilir."),
        ("8. TEMSİL", "Şirketi temsil edecek imzalar genel kurulca belirlenir."),
        ("9. GENEL KURUL", "Genel kurullar olağan ve olağanüstü olarak toplanır."),
        ("10. İLAN", "İlanlar Türkiye Ticaret Sicili Gazetesi'nde yayımlanır."),
        ("11. HESAP DÖNEMİ", "Hesap yılı 1 Ocak - 31 Aralıktır."),
        ("12. KARIN TESPİTİ VE DAĞITIMI", "Kârın tespiti ve dağıtımı genel kurul kararına bağlıdır."),
        ("13. YEDEK AKÇE", "Yedek akçeler TTK hükümlerine göre ayrılır."),
        ("14. KANUNİ HÜKÜMLER", "Bu sözleşmede olmayan durumlarda TTK geçerlidir.")
    ]

    for baslik, icerik in sabit_maddeler:
        doc.add_heading(baslik, level=1)
        doc.add_paragraph(icerik)

    doc.add_heading("Ortaklar", level=1)
    for ortak in ortaklar:
        doc.add_paragraph(f"{ortak['ad']}, Sermaye: {ortak['sermaye']} TL, Pay: {ortak['pay_adedi']}, Müdür: {ortak['mudur']}, İmza: {ortak['imza']}")

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="sirket_ana_sozlesmesi.docx")

if __name__ == '__main__':
    app.run(debug=True)