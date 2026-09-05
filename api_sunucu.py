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
import socket
import threading
import time
from datetime import datetime
import glob

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
# ─────────────────────────────────────────
# ⚠️  BU KOORDINATLARI SEN GÜNCELLEMELİSİN!
# 1) Kamerayı dolabın içine koy, doğru açıya getir
# 2) Python sunucusunu başlat (api_sunucu.py)
# 3) ESP32'yi başlat → dolap_oncesi.jpg çekilir
# 4) Terminal'de:
#      source dolap_venv/bin/activate
#      python3 piksel_bulucu.py
# 5) Açılan görüntüde her ürünün
#    SOL ÜST köşesine sonra SAĞ ALT köşesine tıkla
# 6) Terminalde [y1:y2, x1:x2] çıkar, aşağıya yaz
# ─────────────────────────────────────────
# Şu an TEK RAF var. Her slot = rafta bir ürün pozisyonu.
# ==========================================
RAFLAR = {
    "Raf": {
        "Slot_1": [23, 470, 28, 210],    # Soldaki ürün
        "Slot_2": [18, 467, 213, 394],   # Ortadaki ürün
        "Slot_3": [1, 471, 406, 610],    # Sağdaki ürün
    }
}

app = Flask(__name__)

# ==========================================
# 3. DOSYA YOLLARI
# ==========================================
ONCESI_YOLU     = "dolap_oncesi.jpg"       # Referans fotoğraf (sürekli güncellenir)
SONRASI_YOLU    = "dolap_sonrasi.jpg"       # Yeni gelen fotoğraf
SON_KAMERA_YOLU = "test_resmi.jpeg"         # Dashboard sidebar için
JSON_DOSYASI    = "data/sistem_durumu.json"
CSV_DOSYASI     = "data/satis_gecmisi.csv"

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


def resimleri_hizala(img_once, img_sonra):
    """Kapak sallantısından kaynaklı kaymaları düzeltmek için img_sonra'yı img_once'ye hizalar (ORB kullanarak)."""
    try:
        gray1 = cv2.cvtColor(img_once, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img_sonra, cv2.COLOR_BGR2GRAY)
        
        orb = cv2.ORB_create(500)
        kp1, des1 = orb.detectAndCompute(gray1, None)
        kp2, des2 = orb.detectAndCompute(gray2, None)
        
        if des1 is None or des2 is None: return img_sonra

        matcher = cv2.DescriptorMatcher_create(cv2.DESCRIPTOR_MATCHER_BRUTEFORCE_HAMMING)
        matches = matcher.match(des2, des1, None)
        matches = sorted(matches, key=lambda x: x.distance)
        good_matches = matches[:int(len(matches) * 0.2)]
        
        if len(good_matches) < 10: return img_sonra
            
        pts1 = np.zeros((len(good_matches), 2), dtype=np.float32)
        pts2 = np.zeros((len(good_matches), 2), dtype=np.float32)
        
        for i, match in enumerate(good_matches):
            pts2[i, :] = kp2[match.queryIdx].pt
            pts1[i, :] = kp1[match.trainIdx].pt
            
        h, mask = cv2.findHomography(pts2, pts1, cv2.RANSAC)
        if h is not None:
            height, width = img_once.shape[:2]
            return cv2.warpPerspective(img_sonra, h, (width, height))
    except Exception as e:
        print(f"⚠️ Görüntü hizalama hatası: {e}")
    return img_sonra


def slot_bazli_analiz_multi(img_once, img_sonra, agirlik_degisimi):
    """
    İki görüntüyü slot-bazlı karşılaştırır ve birden fazla olayı tespit edebilir.
    Döndürür: list of dicts -> [{"slot": slot_adi, "islem": "ALINDI" | "EKLENDI", "urun": urun_adi, "eminlik": 95.0, "oran": 15.2}, ...]
    """
    img_sonra = cv2.resize(img_sonra, (img_once.shape[1], img_once.shape[0]))
    
    # ── YENİ: Kapak sallantısını düzeltmek için otomatik hizalama (ORB) ──
    img_sonra = resimleri_hizala(img_once, img_sonra)
    fark_resmi   = cv2.absdiff(img_once, img_sonra)
    gri_fark     = cv2.cvtColor(fark_resmi, cv2.COLOR_BGR2GRAY)
    _, esik_fark = cv2.threshold(gri_fark, 30, 255, cv2.THRESH_BINARY)

    olaylar = []
    
    # Tüm slotlar çok yüksek değişim gösteriyorsa -> bozuk JPEG
    slot_sayisi = sum(len(s) for s in RAFLAR.values())
    yuksek_slot = sum(
        1 for raf in RAFLAR.values()
        for kords in raf.values()
        for _ in [esik_fark[kords[0]:kords[1], kords[2]:kords[3]]]
        if _.size > 0 and (np.sum(_ == 255) / _.size) * 100 > 90
    )
    if yuksek_slot == slot_sayisi and slot_sayisi > 1:
        print("⚠️  BOZUK JPEG tespit edildi — bu kare atlanıyor.")
        return olaylar

    for raf_adi, slotlar in RAFLAR.items():
        for slot_adi, kords in slotlar.items():
            y1, y2, x1, x2 = kords
            maske = esik_fark[y1:y2, x1:x2]
            if maske.size == 0:
                continue
            oran = (np.sum(maske == 255) / maske.size) * 100
            
            if oran > 8.0:
                print(f"   → {slot_adi} Piksel Değişim: %{oran:.2f} -> AI İnceliyor...")
                # Öncesi ve Sonrasını AI'a sor
                urun_once, eminlik_once = urun_nedir_slot(img_once, y1, y2, x1, x2, kaydet_adi=f"{slot_adi}_once")
                urun_sonra, eminlik_sonra = urun_nedir_slot(img_sonra, y1, y2, x1, x2, kaydet_adi=f"{slot_adi}_sonra")
                
                once_dolu = urun_once not in ("Bos_Raf", "Bilinmiyor") and eminlik_once >= 50.0
                sonra_dolu = urun_sonra not in ("Bos_Raf", "Bilinmiyor") and eminlik_sonra >= 50.0
                
                if once_dolu and not sonra_dolu:
                    olaylar.append({"slot": slot_adi, "islem": "ALINDI", "urun": urun_once, "eminlik": eminlik_once, "oran": oran})
                elif not once_dolu and sonra_dolu:
                    olaylar.append({"slot": slot_adi, "islem": "EKLENDI", "urun": urun_sonra, "eminlik": eminlik_sonra, "oran": oran})
                elif once_dolu and sonra_dolu and urun_once != urun_sonra:
                    # SWAP DURUMU
                    olaylar.append({"slot": slot_adi, "islem": "ALINDI", "urun": urun_once, "eminlik": eminlik_once, "oran": oran})
                    olaylar.append({"slot": slot_adi, "islem": "EKLENDI", "urun": urun_sonra, "eminlik": eminlik_sonra, "oran": oran})

    # ── YENİ: Ağırlığa Göre Akıllı Doğrulama (Reconciliation) ──
    # Ortalama bir kutu içecek 230g ile 290g arasıdır (Orta nokta: 260g).
    scale_net = round(agirlik_degisimi / 260.0)
    
    # AI'nin bulduğu olaylardan net değişimi hesapla
    ai_net = sum(1 if o["islem"] == "EKLENDI" else -1 for o in olaylar)
    
    # Eğer AI, terazinin söylediğinden daha fazla ürün EKLENDI sanıyorsa (boş rafı ürün sanma hatası)
    while ai_net > scale_net:
        eklendi_olaylar = [o for o in olaylar if o["islem"] == "EKLENDI"]
        if not eklendi_olaylar:
            break 
        # En düşük eminliğe sahip sahte EKLENDI olayını bul ve sil
        en_zayif = min(eklendi_olaylar, key=lambda x: x["eminlik"])
        olaylar.remove(en_zayif)
        print(f"     ⚖️ Tartı Düzeltmesi: Fazladan algılanan {en_zayif['urun']} (EKLENDI) iptal edildi. (%{en_zayif['eminlik']:.1f})")
        ai_net -= 1
        
    # Eğer AI, terazinin söylediğinden daha fazla ürün ALINDI sanıyorsa
    while ai_net < scale_net:
        alindi_olaylar = [o for o in olaylar if o["islem"] == "ALINDI"]
        if not alindi_olaylar:
            break
        en_zayif = min(alindi_olaylar, key=lambda x: x["eminlik"])
        olaylar.remove(en_zayif)
        print(f"     ⚖️ Tartı Düzeltmesi: Fazladan algılanan {en_zayif['urun']} (ALINDI) iptal edildi. (%{en_zayif['eminlik']:.1f})")
        ai_net += 1

    return olaylar


def durumu_guncelle_olaylar(olaylar, agirlik_degisimi):
    """JSON stok ve CSV satış kaydını çoklu olaylara göre günceller."""
    if not olaylar:
        return
    try:
        with open(JSON_DOSYASI, "r", encoding="utf-8") as f:
            durum = json.load(f)

        zaman_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        son_olay_str = ""
        son_kategori = ""
        son_eminlik = 0.0
        son_slot = ""

        for olay in olaylar:
            kategori = olay["urun"]
            islem = olay["islem"]
            slot = olay["slot"]
            eminlik = olay["eminlik"]

            if islem == "ALINDI":
                if kategori in durum["stok"]:
                    durum["stok"][kategori] = max(0, durum["stok"][kategori] - 1)
                islem_str = "Alındı"
            else: # EKLENDI
                if kategori in durum["stok"]:
                    durum["stok"][kategori] += 1
                else:
                    durum["stok"][kategori] = 1
                islem_str = "Eklendi"

            son_olay_str = f"1 Adet {kategori} {islem_str} ({slot})"
            son_kategori = kategori
            son_eminlik = eminlik
            son_slot = slot

            if kategori != "Bos_Raf" and kategori != "Bilinmiyor":
                with open(CSV_DOSYASI, "a", newline="", encoding="utf-8") as csvf:
                    writer = csv.writer(csvf)
                    writer.writerow([zaman_str, kategori, islem_str, 1])

            print(f"✅ Kayıt: 1 Adet {kategori} {islem_str} ({slot}) | Eminlik: %{eminlik:.1f}")

        if len(olaylar) > 1:
            son_olay_str = f"Eş Zamanlı {len(olaylar)} İşlem Gerçekleşti"

        durum["son_olay"] = {
            "zaman"           : zaman_str,
            "agirlik_degisimi": str(agirlik_degisimi),
            "yapilan_islem"   : son_olay_str,
            "kategori"        : son_kategori,
            "slot"            : son_slot,
            "eminlik"         : round(son_eminlik, 1)
        }

        with open(JSON_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(durum, f, ensure_ascii=False, indent=4)

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
        # ── İLK KAYIT: Dolap ilk defa taranıyor ──────────────────
        shutil.copy(gecici_yol, ONCESI_YOLU)
        print("📸 [İLK KAYIT] Referans fotoğraf oluşturuldu → dolap_oncesi.jpg")

        img = cv2.imread(ONCESI_YOLU)
        tespit_edilen = []

        if img is not None:
            print("🔍 OTOMATİK ENVANTER TARAMASI başlıyor — tüm slotlar analiz ediliyor...")
            try:
                with open(JSON_DOSYASI, "r", encoding="utf-8") as jf:
                    durum = json.load(jf)
            except:
                durum = {"stok": {}, "son_olay": {}}

            zaman_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Her slotu tara — mevcut ürünleri stoka ekle
            for raf_adi, slotlar in RAFLAR.items():
                for slot_adi, kords in slotlar.items():
                    y1, y2, x1, x2 = kords
                    # Debug görüntüsü de kaydediliyor (Dashboard Kamera sayfasında görünür)
                    urun, eminlik = urun_nedir_slot(img, y1, y2, x1, x2, kaydet_adi=slot_adi)
                    print(f"   → {slot_adi}: {urun} (%{eminlik:.1f} eminlik)")

                    if urun not in ("Bos_Raf", "Bilinmiyor") and eminlik >= 50.0:
                        # Stoku artır
                        if urun in durum["stok"]:
                            durum["stok"][urun] += 1
                        else:
                            durum["stok"][urun] = 1  # katalogda yoksa sıfırdan başlat
                        tespit_edilen.append((urun, slot_adi, eminlik))
                        # CSV'ye başlangıç stok girişi olarak kaydet
                        with open(CSV_DOSYASI, "a", newline="", encoding="utf-8") as csvf:
                            writer = csv.writer(csvf)
                            writer.writerow([zaman_str, urun, "Eklendi", 1])

            # Özet yazdır
            sep = "★" * 50
            print(f"\n{sep}")
            print(f"✅ BAŞLANGIÇ ENVANTERİ TAMAMLANDI — {len(tespit_edilen)} ÜRÜN TESPİT EDİLDİ")
            for u, s, e in tespit_edilen:
                print(f"   📦 {u} → {s} (%{e:.1f} eminlik)")
            if not tespit_edilen:
                print("   ⚠️  Hiç ürün tespit edilemedi (raf boş veya eminlik düşük).")
            print(f"{sep}\n")

            ozet_str = f"Sistem Başlatıldı — {len(tespit_edilen)} Ürün Envantere Eklendi"
            durum["son_olay"] = {
                "zaman"           : zaman_str,
                "agirlik_degisimi": agirlik_degisimi,
                "yapilan_islem"   : ozet_str,
                "kategori"        : tespit_edilen[0][0] if tespit_edilen else "-",
                "slot"            : "-",
                "eminlik"         : round(tespit_edilen[0][2], 1) if tespit_edilen else 0.0
            }
            with open(JSON_DOSYASI, "w", encoding="utf-8") as jf:
                json.dump(durum, jf, ensure_ascii=False, indent=4)

        return jsonify({
            "durum"  : "referans_alindi",
            "mesaj"  : f"İlk tarama tamamlandı. {len(tespit_edilen)} ürün stoka eklendi."
        }), 200


    else:
        # ── NORMAL ÇALIŞMA: Karşılaştırma yap ───────────────────────
        shutil.copy(gecici_yol, SONRASI_YOLU)
        print(f"📸 Yeni fotoğraf alındı → dolap_sonrasi.jpg | Ağırlık: {agirlik_degisimi}g")

        img_once = cv2.imread(ONCESI_YOLU)
        img_sonra = cv2.imread(SONRASI_YOLU)

        if img_once is None or img_sonra is None:
            return jsonify({"hata": "Fotoğraflar okunamadı!"}), 500

        # Boyut kontrolü — çok küçük fotoğraf bozuk demektir
        if img_sonra.shape[0] < 50 or img_sonra.shape[1] < 50:
            print("⚠️  Fotoğraf çok küçük — bozuk JPEG, atlanıyor.")
            return jsonify({"durum": "bozuk_jpeg", "mesaj": "Bozuk fotoğraf atlandı"}), 200

        print("🔍 Çoklu Slot-bazlı karşılaştırma başlıyor...")
        agirlik_float = float(agirlik_degisimi)
        olaylar = slot_bazli_analiz_multi(img_once, img_sonra, agirlik_float)

        if olaylar:
            sep = "★" * 50
            for olay in olaylar:
                islem_ikonu = "🟥" if olay["islem"] == "ALINDI" else "🟩"
                print(f"\n{sep}")
                print(f"{islem_ikonu} ÜRÜN {olay['islem']}!")
                print(f"📍 Slot      : {olay['slot']}")
                print(f"📦 Ürün      : {olay['urun']}")
                print(f"📊 Eminlik   : %{olay['eminlik']:.1f}")
                print(f"⚖️  Ağırlık   : {agirlik_degisimi}g (Toplam Değişim)")
                print(f"{sep}\n")

            durumu_guncelle_olaylar(olaylar, agirlik_degisimi)

            # ── REFERANSI GÜNCELLE: sonrası → öncesi ─────────────────
            shutil.copy(SONRASI_YOLU, ONCESI_YOLU)
            print("🔄 Referans güncellendi: dolap_sonrasi.jpg → dolap_oncesi.jpg")

            return jsonify({
                "durum"         : "basarili",
                "olay_sayisi"   : len(olaylar),
                "islem"         : "coklu" if len(olaylar) > 1 else olaylar[0]["islem"]
            }), 200
        else:
            print("⚠️  Anlamlı bir ürün değişimi tespit edilemedi (sadece ağırlık değişti).")
            # Yine de referansı güncelleyelim ki sistem kitlenmesin
            shutil.copy(SONRASI_YOLU, ONCESI_YOLU)
            return jsonify({"durum": "degisiklik_yok"}), 200



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


@app.route('/tam_sifirla', methods=['POST'])
def tam_sifirla():
    """
    TAM SİFIRLAMA:
    - Tüm ürün stoklarını 0'a sıfırlar
    - satis_gecmisi.csv geçmişini temizler (sadece başlık kalır)
    - Tüm fotoğrafları siler (referans, debug, geçici)
    - sistem_durumu.json'u başlangıç durumuna getirir
    """
    print("\n🔄 TAM SİFIRLAMA başlatıldı...")

    # 1. sistem_durumu.json → stokları 0'a sıfırla
    try:
        with open(JSON_DOSYASI, "r", encoding="utf-8") as f:
            durum = json.load(f)
        for urun in durum["stok"]:
            durum["stok"][urun] = 0
        durum["son_olay"] = {
            "zaman"           : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "agirlik_degisimi": "0.00",
            "yapilan_islem"   : "Sistem Tamamen Sıfırlandı",
            "kategori"        : "-",
            "slot"            : "-",
            "eminlik"         : 0.0
        }
        with open(JSON_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(durum, f, ensure_ascii=False, indent=4)
        print("   ✅ Stoklar 0'a sıfırlandı.")
    except Exception as e:
        print(f"   ❌ JSON sıfırlama hatası: {e}")

    # 2. satis_gecmisi.csv → başlık satırı hariç temizle
    try:
        with open(CSV_DOSYASI, "w", newline="", encoding="utf-8") as csvf:
            csvf.write("Tarih,Urun,Islem,Adet\n")
        print("   ✅ Satış geçmişi temizlendi.")
    except Exception as e:
        print(f"   ❌ CSV sıfırlama hatası: {e}")

    # 3. Tüm fotoğrafları sil
    dosyalar = [
        ONCESI_YOLU, SONRASI_YOLU, "gecici_esp32.jpg", "test_resmi.jpeg"
    ]
    # Eskiden statik olarak 3 debug fotoğrafını veriyorduk.
    # Şimdi 'once' ve 'sonra' olabildiği için dinamik bulalım:
    debug_fotolar = glob.glob("debug_kesilen_*.jpg")
    dosyalar.extend(debug_fotolar)

    for dosya in dosyalar:
        if os.path.exists(dosya):
            os.remove(dosya)
            print(f"   🗑️  {dosya} silindi.")

    print("✅ TAM SİFIRLAMA tamamlandı! Sistem başlangıç durumunda.\n")
    return jsonify({
        "durum"  : "tamamen_sifirland",
        "mesaj"  : "Stoklar, geçmiş ve fotoğraflar temizlendi."
    }), 200



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


# ==========================================
# UDP YAYIN — ESP32 SUNUCUYU OTOMATIİK BULUR
# ==========================================
def udp_yayin_yap():
    """
    Her 3 saniyede bir ağa UDP yayını gönderir.
    ESP32 bu yayını dinleyerek sunucunun IP'sini öğrenir.
    Format: 'DOLAP_SERVER:192.168.x.x'
    """
    soket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    soket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    soket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Sunucunun kendi IP'sini bul
    gecici = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        gecici.connect(("8.8.8.8", 80))
        kendi_ip = gecici.getsockname()[0]
    except Exception:
        kendi_ip = "127.0.0.1"
    finally:
        gecici.close()
    
    mesaj = f"DOLAP_SERVER:{kendi_ip}".encode()
    print(f"📡 UDP yayını başlatıldı — Sunucu IP: {kendi_ip} (ESP32 otomatik bulacak)")
    
    while True:
        try:
            soket.sendto(mesaj, ("255.255.255.255", 4210))
        except Exception as e:
            print(f"UDP hata: {e}")
        time.sleep(3)


if __name__ == '__main__':
    print("\n🌐 Akıllı Dolap API Sunucusu Başlatılıyor...")
    print("📡 Dinlenen Adres  : http://0.0.0.0:5001")
    print("📌 Endpointler:")
    print("   POST /tetikle  → ESP32'den gelen fotoğraf + ağırlık")
    print("   POST /sifirla  → Referansı sil (dolap yeniden dolduruldu)")
    print("   GET  /durum    → Anlık sistem durumu (debug)\n")
    
    # UDP yayınını arka planda başlat
    udp_thread = threading.Thread(target=udp_yayin_yap, daemon=True)
    udp_thread.start()
    
    app.run(host='0.0.0.0', port=5001, debug=False)
