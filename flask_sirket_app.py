
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

    # GPT'den Madde 3 alma
    headers = {
        "Authorization": "Bearer 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",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "Sen bir limited şirket ana sözleşmesi hazırlayan uzmansın. MERSİS formatına uygun resmi dil kullan."},
            {"role": "user", "content": f"{faaliyet} alanında faaliyet gösterecek bir limited şirket için Türk Ticaret Kanununa uygun Madde 3 – Amaç ve Konu metni hazırla. En az 5 ana başlık ve her başlıkta 3-5 alt madde olacak şekilde yaz."}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        data = response.json()
        amac_konu = data["choices"][0]["message"]["content"] if "choices" in data else "[GPT yanıtı alınamadı]"
    except Exception as e:
        amac_konu = f"[GPT hatası]: {str(e)}"

    # Belge oluşturma
    doc = Document()
    doc.add_heading('LİMİTED ŞİRKET ANA SÖZLEŞMESİ', 0)

    doc.add_heading('1. KURULUŞ', level=1)
    doc.add_paragraph("Bu sözleşme hükümlerine göre aşağıda bilgileri bulunan kurucu ortaklar arasında bir limited şirket kurulmuştur.")

    doc.add_heading('2. UNVAN', level=1)
    doc.add_paragraph(f"Şirketin unvanı {unvan} LIMITED ŞİRKETİ'dir.")

    doc.add_heading('3. AMAÇ VE KONU', level=1)
    doc.add_paragraph(amac_konu)

    doc.add_heading('4. MERKEZ VE ADRES', level=1)
    doc.add_paragraph(f"Şirketin merkezi {merkez_il} ili {merkez_ilce} ilçesidir.
Adres: {adres}")

    doc.add_heading('5. SÜRE', level=1)
    doc.add_paragraph("Şirketin süresi, kuruluşundan itibaren sınırsızdır. Bu süre şirket sözleşmesini değiştirmek suretiyle uzatılıp kısaltılabilir.")

    doc.add_heading('6. SERMAYE VE PAYLAR', level=1)
    doc.add_paragraph(f"Şirketin toplam sermayesi {toplam_sermaye} TL'dir ve toplam {toplam_pay} paya ayrılmıştır.")
    for ortak in ortaklar:
        doc.add_paragraph(f"{ortak['ad']} - {ortak['sermaye']} TL, {ortak['pay_adedi']} pay, Müdür: {ortak['mudur'].capitalize()}, İmza Yetkisi: {ortak['imza']}")

    doc.add_heading('7. ŞİRKETİN İDARESİ', level=1)
    doc.add_paragraph("Şirketin işleri ve işlemleri genel kurul tarafından seçilecek bir veya birkaç müdür tarafından yürütülür.")
    for ortak in ortaklar:
        if ortak['mudur'] == 'evet':
            doc.add_paragraph(f"{ortak['ad']} müdür olarak atanmıştır.")

    doc.add_heading('8. TEMSİL', level=1)
    doc.add_paragraph("Şirketi müdürler temsil ederler. Müdürlerin temsil şekli aşağıda belirtilmiştir:")
    for ortak in ortaklar:
        if ortak['mudur'] == 'evet':
            doc.add_paragraph(f"{ortak['ad']} - Temsil Yetkisi: {ortak['imza']}")

    doc.add_heading('9. GENEL KURUL', level=1)
    doc.add_paragraph("Genel Kurullar, olağan ve olağanüstü toplanırlar. Toplantılar Türk Ticaret Kanunu hükümlerine tabidir.")

    doc.add_heading('10. İLAN', level=1)
    doc.add_paragraph("Şirkete ait ilanlar Türkiye Ticaret Sicili Gazetesinde yapılır.")

    doc.add_heading('11. HESAP DÖNEMİ', level=1)
    doc.add_paragraph("Şirketin hesap yılı, Ocak ayının 1. günü başlar ve Aralık ayının 31. günü sona erer.")

    doc.add_heading('12. KARIN TESPİTİ VE DAĞITIMI', level=1)
    doc.add_paragraph("Şirketin net dönem karı üzerinden yasal kesintiler yapıldıktan sonra kalan kısım, ortaklara dağıtılır.")

    doc.add_heading('13. YEDEK AKÇE', level=1)
    doc.add_paragraph("Yedek akçelerin ayrılmasında Türk Ticaret Kanununun ilgili hükümleri uygulanır.")

    doc.add_heading('14. KANUNİ HÜKÜMLER', level=1)
    doc.add_paragraph("Bu sözleşmede bulunmayan hususlarda Türk Ticaret Kanunu hükümleri uygulanır.")

    doc.add_heading("ORTAKLAR", level=1)
    for ortak in ortaklar:
        doc.add_paragraph(f"{ortak['ad']} - T.C.: {ortak['tc']} - Uyruk: {ortak['uyruk']}")

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="sirket_ana_sozlesmesi.docx")

if __name__ == '__main__':
    app.run(debug=True)
