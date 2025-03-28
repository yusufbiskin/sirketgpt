from flask import Flask, render_template, request, send_file
from docx import Document
from io import BytesIO
import requests
import os

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
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
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
        response.raise_for_status()
        amac_konu = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        amac_konu = f"[GPT hatası]: {str(e)}"

    doc = Document()
    doc.add_heading('LİMİTED ŞİRKET ANA SÖZLEŞMESİ', 0)

    doc.add_heading('1. KURULUŞ', level=1)
    doc.add_paragraph("Aşağıdaki kurucular tarafından bir limited şirket kurulmuştur:")
    table = doc.add_table(rows=1, cols=5)
    table.style = 'Table Grid'
    header = table.rows[0].cells
    header[0].text = 'Sıra'
    header[1].text = 'Kurucu'
    header[2].text = 'Adres'
    header[3].text = 'Uyruk'
    header[4].text = 'Kimlik No'
    for idx, o in enumerate(ortaklar, start=1):
        row = table.add_row().cells
        row[0].text = str(idx)
        row[1].text = o['ad']
        row[2].text = f"{merkez_il} / {merkez_ilce}"
        row[3].text = o['uyruk']
        row[4].text = o['tc']

    doc.add_heading('2. ŞİRKETİN UNVANI', level=1)
    doc.add_paragraph(f"Şirketin unvanı {unvan} LİMİTED ŞİRKETİ'dir.")

    doc.add_heading('3. AMAÇ VE KONU', level=1)
    doc.add_paragraph(amac_konu)

    doc.add_heading('4. ŞİRKETİN MERKEZİ', level=1)
    doc.add_paragraph(f"Şirketin merkezi {merkez_il} ili, {merkez_ilce} ilçesidir. Adresi: {adres}.")

    doc.add_heading('5. SÜRE', level=1)
    doc.add_paragraph("Şirketin süresi sınırsızdır. Bu süre, şirket sözleşmesini değiştirmek suretiyle kısaltılabilir veya uzatılabilir.")

    doc.add_heading('6. SERMAYE VE PAY SENETLERİNİN NEV’İ', level=1)
    doc.add_paragraph(f"Şirketin toplam sermayesi {toplam_sermaye:,} TL olup, toplam {toplam_pay} paya ayrılmıştır.")
    for o in ortaklar:
        doc.add_paragraph(f"{o['ad']}, {o['pay_adedi']} adet pay ({o['pay_tutari']} TL/adet) karşılığı {o['sermaye']} TL sermaye taahhüt etmiştir.")
    doc.add_paragraph("Pay senetleri nama yazılıdır. Nakden taahhüt edilen paylar tescilden itibaren 24 ay içinde ödenecektir.")

    doc.add_heading('7. ŞİRKETİN İDARESİ', level=1)
    for o in ortaklar:
        if o['mudur'] == 'evet':
            doc.add_paragraph(f"{o['ad']} müdür olarak atanmıştır. Adresi: {merkez_il}/{merkez_ilce}. Yetki şekli: Münferiden Temsile Yetkilidir.")

    doc.add_heading('8. TEMSİL', level=1)
    for o in ortaklar:
        if o['mudur'] == 'evet':
            doc.add_paragraph(f"{o['ad']} – İmza Yetkisi: {o['imza'].capitalize()}")

    doc.add_heading('9. GENEL KURUL', level=1)
    doc.add_paragraph("Genel kurul olağan ve olağanüstü olarak toplanır. Olağan genel kurul her yıl hesap dönemi sonundan itibaren 3 ay içinde yapılır.")

    doc.add_heading('10. İLAN', level=1)
    doc.add_paragraph("Şirkete ait ilanlar Türkiye Ticaret Sicili Gazetesi'nde yapılır.")

    doc.add_heading('11. HESAP DÖNEMİ', level=1)
    doc.add_paragraph("Şirketin hesap yılı Ocak ayında başlar, Aralık ayında sona erer.")

    doc.add_heading('12. KARIN TESPİTİ VE DAĞITIMI', level=1)
    doc.add_paragraph("Net dönem kârından %5 genel kanuni yedek akçe ayrılır; kalan tutar genel kurul kararıyla dağıtılır.")

    doc.add_heading('13. YEDEK AKÇE', level=1)
    doc.add_paragraph("Yedek akçeler için Türk Ticaret Kanunu hükümleri uygulanır.")

    doc.add_heading('14. KANUNİ HÜKÜMLER', level=1)
    doc.add_paragraph("Bu sözleşmede bulunmayan hususlarda Türk Ticaret Kanunu uygulanır.")

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="sirket_ana_sozlesmesi.docx")

if __name__ == '__main__':
    app.run(debug=True)
