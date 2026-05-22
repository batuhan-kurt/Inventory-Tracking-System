"""
api_sunucu.py — Tam Entegre Akıllı Dolap API Sunucusu
=======================================================
ESP32'den gelen fotoğrafları alır, referans yönetimi yapar,
tam_otonom_dolap.py motoru ile slot-bazlı karşılaştırma yapar
ve dashboard'a veri akışı sağlar.
"""

from flask import Flask, request, jsonify
import cv2
import numpy as np
import os
import json
import csv
import shutil
from datetime import datetime

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

# ==========================================
# 1. YAPAY ZEKA BEYNİNİ BELLEĞE YÜKLE
# ==========================================
print("🧠 Yapay Zeka Belleğe Yükleniyor... Lütfen Bekleyin.")
from tensorflow.keras.models import load_model

try:
    beyin = load_model("akilli_dolap_beyni.keras")
    print("✅ Beyin başarıyla yüklendi! Sunucu ultra hızlı çalışacak.")
except Exception as e:
    print("HATA: Beyin dosyası bulunamadı!", e)
    beyin = None

KATEGORILER = [
    "CocaCola_Klasik", "CocaCola_Zero", "Pepsi", "Fanta",
    "RedBull_Klasik", "RedBull_White", "RedBull_Blue",
    "RedBull_Lilac", "RedBull_Pembe", "Nescafe_Klasik", "Bos_Raf"
]

# ==========================================
# 2. RAF / SLOT KALİBRASYONU
# (piksel_bulucu.py ile aldığın koordinatlar)
# ==========================================
RAFLAR = {
    "Ust_Raf": {
        "Slot_1": [192, 976, 44, 449],
        "Slot_2": [281, 988, 449, 742],
        "Slot_3": [285, 1000, 781, 1028],
        "Slot_4": [286, 1005, 1126, 1338],
    }
}

app = Flask(__name__)

# ==========================================
# 3. DOSYA YOLLARI
# ==========================================
ONCESI_YOLU     = "dolap_oncesi.jpg"       # Referans fotoğraf (sürekli güncellenir)
SONRASI_YOLU    = "dolap_sonrasi.jpg"       # Yeni gelen fotoğraf
SON_KAMERA_YOLU = "test_resmi.jpeg"         # Dashboard sidebar için
JSON_DOSYASI    = "sistem_durumu.json"
CSV_DOSYASI     = "satis_gecmisi.csv"

# ==========================================
# 4. YARDIMCI FONKSİYONLAR
# ==========================================

def urun_nedir_slot(img, y1, y2, x1, x2, kaydet_adi=""):
    """Verilen koordinatlardaki slotu kırpıp modele sorar."""
    if beyin is None:
        return "Bilinmiyor", 0.0
    kesit = img[y1:y2, x1:x2]
    if kesit.size == 0:
        return "Bilinmiyor", 0.0
    if kaydet_adi:
        cv2.imwrite(f"debug_kesilen_{kaydet_adi}.jpg", kesit)
    resim_rgb  = cv2.cvtColor(kesit, cv2.COLOR_BGR2RGB)
    resim_224  = cv2.resize(resim_rgb, (224, 224))  # beyin_egit.py ile aynı boyut
    resim_norm = np.array(resim_224, dtype="float32") / 255.0
    resim_bat  = np.expand_dims(resim_norm, axis=0)
    tahmin     = beyin.predict(resim_bat, verbose=0)
    idx        = int(np.argmax(tahmin))
    return KATEGORILER[idx], float(np.max(tahmin) * 100)


def slot_bazli_analiz(img_once, img_sonra):
    """
    İki görüntüyü slot-bazlı karşılaştırır.
    Döndürür: (satilan_urun, slot_adi, eminlik, degisim_orani)
    """
    # Boyut eşitle
    img_sonra = cv2.resize(img_sonra, (img_once.shape[1], img_once.shape[0]))

    # Piksel fark haritası
    fark_resmi   = cv2.absdiff(img_once, img_sonra)
    gri_fark     = cv2.cvtColor(fark_resmi, cv2.COLOR_BGR2GRAY)
    _, esik_fark = cv2.threshold(gri_fark, 30, 255, cv2.THRESH_BINARY)

    max_oran        = 0.0
    degisen_slot    = None
    degisen_raf     = None

    # Her slotta kaç piksel değişti?
    for raf_adi, slotlar in RAFLAR.items():
        for slot_adi, kords in slotlar.items():
            y1, y2, x1, x2 = kords
            maske = esik_fark[y1:y2, x1:x2]
            if maske.size == 0:
                continue
            oran = (np.sum(maske == 255) / maske.size) * 100
            print(f"   → {slot_adi} Piksel Değişim: %{oran:.2f}")
            if oran > max_oran:
                max_oran     = oran
                degisen_slot = slot_adi
                degisen_raf  = raf_adi

    if max_oran < 5.0:
        # Anlamlı bir değişim yok (5% eşik)
        return None, None, 0.0, max_oran

    # Değişen slottaki ürünü tespit et (sonraki fotoğraftan)
    y1, y2, x1, x2 = RAFLAR[degisen_raf][degisen_slot]
    urun, eminlik = urun_nedir_slot(img_sonra, y1, y2, x1, x2, kaydet_adi=degisen_slot)

    return urun, degisen_slot, eminlik, max_oran


def durumu_guncelle(fark_gr, kategori, slot, eminlik):
    """JSON stok ve CSV satış kaydını günceller."""
    try:
        with open(JSON_DOSYASI, "r", encoding="utf-8") as f:
            durum = json.load(f)

        zaman_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if float(fark_gr) < -20:
            # Ürün alındı
            if kategori in durum["stok"]:
                durum["stok"][kategori] = max(0, durum["stok"][kategori] - 1)
            islem_tipi    = f"1 Adet {kategori} Alındı ({slot})"
            islem_kisa    = "Alındı"
        elif float(fark_gr) > 20:
            # Ürün eklendi
            if kategori in durum["stok"]:
                durum["stok"][kategori] = durum["stok"][kategori] + 1
            islem_tipi = f"1 Adet {kategori} Eklendi ({slot})"
            islem_kisa = "Eklendi"
        else:
            islem_tipi = f"Geçersiz değişim ({fark_gr}g)"
            islem_kisa = None

        durum["son_olay"] = {
            "zaman"           : zaman_str,
            "agirlik_degisimi": fark_gr,
            "yapilan_islem"   : islem_tipi,
            "kategori"        : kategori,
            "slot"            : slot if slot else "-",
            "eminlik"         : round(eminlik, 1)
        }

        with open(JSON_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(durum, f, ensure_ascii=False, indent=4)

        # CSV'ye yaz (sadece gerçek ürünler için)
        if islem_kisa and kategori != "Bos_Raf" and kategori != "Bilinmiyor":
            with open(CSV_DOSYASI, "a", newline="", encoding="utf-8") as csvf:
                writer = csv.writer(csvf)
                writer.writerow([zaman_str, kategori, islem_kisa, 1])

        print(f"✅ Kayıt: {islem_tipi} | Eminlik: %{eminlik:.1f}")

    except Exception as e:
        print("❌ JSON/CSV Güncelleme Hatası:", e)


# ==========================================
# 5. ANA ENDPOINT — ESP32'DEN GELEN SİNYAL
# ==========================================
@app.route('/tetikle', methods=['POST'])
def tetikle():
    zaman = datetime.now().strftime('%H:%M:%S')
    print(f"\n[{zaman}] 🚨 ESP32'DEN SİNYAL GELDİ!")

    agirlik_degisimi = request.headers.get('X-Agirlik-Degisimi', '0')
    resim_verisi     = request.data

    if not resim_verisi:
        return jsonify({"hata": "Fotoğraf alınamadı!"}), 400

    # 1. Gelen fotoğrafı geçici olarak kaydet
    gecici_yol = "gecici_esp32.jpg"
    with open(gecici_yol, "wb") as f:
        f.write(resim_verisi)

    # Dashboard sidebar için her zaman güncelle
    shutil.copy(gecici_yol, SON_KAMERA_YOLU)

    # 2. REFERANS FOTO MANTIĞI
    if not os.path.exists(ONCESI_YOLU):
        # ── İLK KAYIT: Sabah dolap ilk defa doluyor ──────────────────
        shutil.copy(gecici_yol, ONCESI_YOLU)
        print("📸 [İLK KAYIT] Referans fotoğraf oluşturuldu → dolap_oncesi.jpg")

        # Slot haritasını çıkar ve JSON'a işle
        img = cv2.imread(ONCESI_YOLU)
        if img is not None:
            print("🗺️  Vitrin haritası çıkarılıyor...")
            try:
                with open(JSON_DOSYASI, "r", encoding="utf-8") as jf:
                    durum = json.load(jf)
            except:
                durum = {"stok": {}, "son_olay": {}}

            durum["son_olay"] = {
                "zaman"           : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "agirlik_degisimi": agirlik_degisimi,
                "yapilan_islem"   : "Sistem Başlatıldı — Referans Fotoğraf Alındı",
                "kategori"        : "-",
                "slot"            : "-",
                "eminlik"         : 0.0
            }
            with open(JSON_DOSYASI, "w", encoding="utf-8") as jf:
                json.dump(durum, jf, ensure_ascii=False, indent=4)

        return jsonify({
            "durum"  : "referans_alindi",
            "mesaj"  : "İlk referans fotoğraf kaydedildi. Sistem izlemeye geçti."
        }), 200

    else:
        # ── NORMAL ÇALIŞMA: Karşılaştırma yap ───────────────────────
        shutil.copy(gecici_yol, SONRASI_YOLU)
        print(f"📸 Yeni fotoğraf alındı → dolap_sonrasi.jpg | Ağırlık: {agirlik_degisimi}g")

        img_once = cv2.imread(ONCESI_YOLU)
        img_sonra = cv2.imread(SONRASI_YOLU)

        if img_once is None or img_sonra is None:
            return jsonify({"hata": "Fotoğraflar okunamadı!"}), 500

        print("🔍 Slot-bazlı karşılaştırma başlıyor...")
        urun, slot, eminlik, degisim_orani = slot_bazli_analiz(img_once, img_sonra)

        if urun is not None:
            islem = "alindi" if float(agirlik_degisimi) < -20 else "eklendi"
            print(f"\n{'★'*50}")
            print(f"🛒 OTONOM SATIŞ RAPORLANDI!")
            print(f"📍 Slot      : {slot}")
            print(f"📦 Ürün      : {urun}")
            print(f"📊 Eminlik   : %{eminlik:.1f}")
            print(f"🔄 Değişim   : {agirlik_degisimi}g")
            print(f"{'★'*50}\n")

            durumu_guncelle(agirlik_degisimi, urun, slot, eminlik)

            # ── REFERANSI GÜNCELLE: sonrası → öncesi ─────────────────
            shutil.copy(SONRASI_YOLU, ONCESI_YOLU)
            print("🔄 Referans güncellendi: dolap_sonrasi.jpg → dolap_oncesi.jpg")

            return jsonify({
                "durum"         : "basarili",
                "kategori"      : urun,
                "slot"          : slot,
                "eminlik"       : round(eminlik, 1),
                "degisim_orani" : round(degisim_orani, 2),
                "islem"         : islem
            }), 200

        else:
            print(f"⚠️ Anlamlı piksel değişimi yok (max: %{degisim_orani:.2f})")
            # Referansı yine de güncelle (görüntü pozisyon kayması olabilir)
            shutil.copy(SONRASI_YOLU, ONCESI_YOLU)
            return jsonify({
                "durum" : "degisim_yok",
                "mesaj" : f"Piksel değişimi eşik altında (%{degisim_orani:.2f})"
            }), 200


# ==========================================
# 6. MANUEL SIFIRLA ENDPOINT'İ
# (Dolap yeniden doldurulduğunda kullan)
# ==========================================
@app.route('/sifirla', methods=['POST'])
def sifirla():
    """
    Bu endpoint'i çağırdığında:
    - Mevcut 'oncesi' fotoğrafı siler
    - Bir sonraki ESP32 sinyali yeni referans fotoğrafı oluşturur
    """
    if os.path.exists(ONCESI_YOLU):
        os.remove(ONCESI_YOLU)
        print("🔃 Referans fotoğraf silindi. Sistem sıfırlandı.")
        return jsonify({"durum": "sifirland", "mesaj": "Bir sonraki fotoğraf yeni referans olacak."}), 200
    else:
        return jsonify({"durum": "zaten_bos", "mesaj": "Referans fotoğraf zaten yok."}), 200


# ==========================================
# 7. DURUM ENDPOINT'İ (Debug için)
# ==========================================
@app.route('/durum', methods=['GET'])
def durum_goster():
    try:
        with open(JSON_DOSYASI, "r", encoding="utf-8") as f:
            durum = json.load(f)
        durum["referans_foto_var"] = os.path.exists(ONCESI_YOLU)
        return jsonify(durum), 200
    except Exception as e:
        return jsonify({"hata": str(e)}), 500


if __name__ == '__main__':
    print("\n🌐 Akıllı Dolap API Sunucusu Başlatılıyor...")
    print("📡 Dinlenen Adres  : http://0.0.0.0:5001")
    print("📌 Endpointler:")
    print("   POST /tetikle  → ESP32'den gelen fotoğraf + ağırlık")
    print("   POST /sifirla  → Referansı sil (dolap yeniden dolduruldu)")
    print("   GET  /durum    → Anlık sistem durumu (debug)\n")
    app.run(host='0.0.0.0', port=5001, debug=False)
