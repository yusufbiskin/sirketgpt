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

    # GPT'den Madde 3 almak için OpenRouter API kullanımı
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

    # Word dosyası oluştur
    doc = Document()
    doc.add_heading('LİMİTED ŞİRKET ANA SÖZLEŞMESİ', 0)

    # 1. Kuruluş
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

    # 2. Unvan
    doc.add_heading('2. ŞİRKETİN UNVANI', level=1)
    doc.add_paragraph(f"Şirketin unvanı {unvan} LİMİTED ŞİRKETİ'dir.")

    # 3. Amaç ve Konu
    doc.add_heading('3. AMAÇ VE KONU', level=1)
    doc.add_paragraph(amac_konu)

    # 4. Merkez
    doc.add_heading('4. ŞİRKETİN MERKEZİ', level=1)
    doc.add_paragraph(f"Şirketin merkezi {merkez_il} ili, {merkez_ilce} ilçesidir. Adresi: {adres}.")

    # 5. Süre
    doc.add_heading('5. SÜRE', level=1)
    doc.add_paragraph("Şirketin süresi sınırsızdır. Bu süre, şirket sözleşmesini değiştirerek kısaltılabilir veya uzatılabilir.")

    # 6. Sermaye
    doc.add_heading('6. SERMAYE VE PAY SENETLERİNİN NEV’İ', level=1)
    doc.add_paragraph(f"Şirketin toplam sermayesi {toplam_sermaye:,} TL olup, toplam {toplam_pay} paya ayrılmıştır.")
    for o in ortaklar:
        doc.add_paragraph(f"{o['ad']}, {o['pay_adedi']} adet pay ({o['pay_tutari']} TL/adet) karşılığı {o['sermaye']} TL sermaye taahhüt etmiştir.")
    doc.add_paragraph("Pay senetleri nama yazılıdır. Nakden taahhüt edilen paylar tescilden itibaren 24 ay içinde ödenecektir.")

    # 7. İdare
    doc.add_heading('7. ŞİRKETİN İDARESİ', level=1)
    for o in ortaklar:
        if o['mudur'] == 'evet':
            doc.add_paragraph(f"{o['ad']} müdür olarak atanmıştır. Adresi: {merkez_il}/{merkez_ilce}. Yetki şekli: Münferiden Temsile Yetkilidir.")

    # 8. Temsil
    doc.add_heading('8. TEMSİL', level=1)
    doc.add_paragraph("Şirketi müdürler temsil eder. Temsil şekli aşağıda belirtilmiştir:")
    for o in ortaklar:
        if o['mudur'] == 'evet':
            doc.add_paragraph(f"{o['ad']} – İmza Yetkisi: {o['imza'].capitalize()}")

    # 9–14 Sabit Maddeler
    doc.add_heading('9. GENEL KURUL', level=1)
    doc.add_paragraph("Genel kurullar olağan ve olağanüstü olarak toplanır. Olağan genel kurul her yıl hesap dönemi sonunda 3 ay içinde yapılır.")

    doc.add_heading('10. İLAN', level=1)
    doc.add_paragraph("Şirkete ait ilanlar Türkiye Ticaret Sicili Gazetesi'nde yayımlanır.")

    doc.add_heading('11. HESAP DÖNEMİ', level=1)
    doc.add_paragraph("Hesap yılı 1 Ocak’ta başlar, 31 Aralık’ta sona erer.")

    doc.add_heading('12. KARIN TESPİTİ VE DAĞITIMI', level=1)
    doc.add_paragraph("Net kar üzerinden %5 yasal yedek akçe ayrılır, kalanı genel kurul kararı ile dağıtılır.")

    doc.add_heading('13. YEDEK AKÇE', level=1)
    doc.add_paragraph("Yedek akçelere ilişkin olarak TTK’nın 519–523. maddeleri uygulanır.")

    doc.add_heading('14. KANUNİ HÜKÜMLER', level=1)
    doc.add_paragraph("Bu sözleşmede hüküm bulunmayan hallerde Türk Ticaret Kanunu uygulanır.")

    # Kurucular alt tablosu
    doc.add_paragraph("\nKURUCULAR")
    table2 = doc.add_table(rows=1, cols=3)
    table2.style = 'Table Grid'
    footer = table2.rows[0].cells
    footer[0].text = 'Kurucu'
    footer[1].text = 'Uyruk'
    footer[2].text = 'İmza'
    for o in ortaklar:
        row = table2.add_row().cells
        row[0].text = o['ad']
        row[1].text = o['uyruk']
        row[2].text = "________"

    # Word dosyasını oluşturup kullanıcıya gönder
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="sirket_ana_sozlesmesi.docx")

if __name__ == '__main__':
    app.run(debug=True)
