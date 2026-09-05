"""
tam_otonom_dolap.py — %100 Akıllı Envanter Sistemi (Sade ve Röntgenli)
===================================================================
Açıklama: Vitrin düzenini öğrenir, satılanı bulur ve nereyi kestiğini 
görmen için kırpılan fotoğrafları (debug) klasörüne kaydeder.
"""

import cv2
import numpy as np
from tensorflow.keras.models import load_model

print("⚙️ [OTONOM SİSTEM] Akıllı dolap mekanizması başlatılıyor...")
model = load_model("akilli_dolap_beyni.keras")

KATEGORILER = [
    "CocaCola_Klasik", "CocaCola_Zero", "Pepsi", "Fanta",
    "RedBull_Klasik", "RedBull_White", "RedBull_Blue",
    "RedBull_Lilac", "RedBull_Pembe", "Nescafe_Klasik", "Bos_Raf"
]

# --- 1. DONANIM KALİBRASYONU (Piksel koordinatların) ---
RAFLAR = {
    "Ust_Raf": {
        "Slot_1": [192, 976, 44, 449],
        "Slot_2": [281, 988, 449, 742],
        "Slot_3": [285, 1000, 781, 1028],
        "Slot_4": [286, 1005, 1126, 1338],
    }
}

# --- 2. YAPAY ZEKA GÖRME FONKSİYONU ---
def urun_nedir(kesilen_resim, kaydet_adi=""):
    """Kareyi kaydeder, RGB'ye çevirip modeli çalıştırır"""
    
    # 📸 RÖNTGEN: Nereyi kestiğini görmek için klasöre kaydediyoruz
    if kaydet_adi != "":
        cv2.imwrite(f"{kaydet_adi}.jpg", kesilen_resim)
        
    # OpenCV'nin BGR formatını modelin anladığı RGB formatına çeviriyoruz
    resim_rgb  = cv2.cvtColor(kesilen_resim, cv2.COLOR_BGR2RGB)
    
    resim_boyutlu = cv2.resize(resim_rgb, (224, 224))  # beyin_egit.py ile aynı boyut
    resim_normalize = np.array(resim_boyutlu, dtype="float32") / 255.0
    resim_batch = np.expand_dims(resim_normalize, axis=0)
    
    tahmin = model.predict(resim_batch, verbose=0)
    return KATEGORILER[np.argmax(tahmin)]

# --- 3. TAM OTONOM ANALİZ MOTORU ---
def tam_otonom_satis_analizi(oncesi_foto_yolu, sonrasi_foto_yolu):
    print("\n🔍 [AŞAMA 1] 'Önceki' fotoğraf inceleniyor, vitrin haritası çıkarılıyor...")
    img_once = cv2.imread(oncesi_foto_yolu)
    img_sonra = cv2.imread(sonrasi_foto_yolu)
    
    if img_once is None or img_sonra is None:
        print("❌ HATA: Fotoğraflar bulunamadı! Klasörü ve isimleri kontrol et.")
        return

    # Kurşun geçirmez zırh: İki fotoğrafın boyutlarını eşitliyoruz
    img_sonra = cv2.resize(img_sonra, (img_once.shape[1], img_once.shape[0]))

    # A) İlk durumdaki ürünleri yapay zekaya sor ve hafızaya kaydet
    anlik_hafiza = {"Ust_Raf": {}}
    for raf_adi, slotlar in RAFLAR.items():
        for slot_adi, kords in slotlar.items():
            y1, y2, x1, x2 = kords
            # Nereyi kestiğini görmek için isimlendirip fonksiyona yolluyoruz
            urun = urun_nedir(img_once[y1:y2, x1:x2], kaydet_adi=f"debug_kesilen_{slot_adi}")
            anlik_hafiza[raf_adi][slot_adi] = urun
            print(f"   [Mevcut Düzen] {slot_adi} Konumunda Tespit Edilen: {urun}")
    
    print("✅ [BAŞARILI] Vitrin haritası yapay zeka tarafından çıkarıldı.")

    # B) İki fotoğraf arasındaki mutlak piksel farkını bul
    print("\n🔍 [AŞAMA 2] 'Sonraki' fotoğraf ile piksel karşılaştırması yapılıyor...")
    fark_resmi = cv2.absdiff(img_once, img_sonra)
    gri_fark = cv2.cvtColor(fark_resmi, cv2.COLOR_BGR2GRAY)
    _, esiklenmis_fark = cv2.threshold(gri_fark, 30, 255, cv2.THRESH_BINARY)
    
    degisim_olan_raf = None
    degisim_olan_slot = None
    max_degisim_orani = 0

    # Hangi slotta en yüksek piksel değişimi (hareket) olduğunu hesapla
    for raf_adi, slotlar in RAFLAR.items():
        for slot_adi, kords in slotlar.items():
            y1, y2, x1, x2 = kords
            maske = esiklenmis_fark[y1:y2, x1:x2]
            oran = (np.sum(maske == 255) / maske.size) * 100
            
            print(f"   -> {slot_adi} Piksel Değişim Oranı: %{oran:.2f}")
            
            if oran > max_degisim_orani:
                max_degisim_orani = oran
                degisim_olan_raf = raf_adi
                degisim_olan_slot = slot_adi

    # C) Sonucu Ekrana Bas (Faturayı Kes)
    if max_degisim_orani > 5.0: # %5 barajı sahte alarmları engeller
        satilan_urun = anlik_hafiza[degisim_olan_raf][degisim_olan_slot]
        
        print("\n" + "★"*50)
        print("🛒 OTONOM SATIŞ RAPORLANDI!")
        print(f"📍 Satış Konumu  : {degisim_olan_raf} -> {degisim_olan_slot}")
        print(f"📦 SATILAN ÜRÜN  : {satilan_urun}")
        print("★"*50 + "\n")
    else:
        print("⚠️ [UYARI] Dolapta anlamlı bir piksel değişimi (ürün eksilmesi) bulunamadı.")

# ─────────────────────────────────────────────
#  ÇALIŞTIRMA ALANI (TEST)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    FOTO_ONCESI = "dolap_oncesi.jpg"
    FOTO_SONRASI = "dolap_sonrasi.jpg"
    
    tam_otonom_satis_analizi(FOTO_ONCESI, FOTO_SONRASI)