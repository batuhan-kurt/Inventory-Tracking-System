"""
tahmin_yap.py — Manuel Görsel Test Scripti
===========================================
Kullanım:
  python tahmin_yap.py                   → test_resmi.jpeg kullanır
  python tahmin_yap.py benim_fotom.jpg   → istediğiniz görseli test eder
"""

import cv2
import numpy as np
import os
import sys
from tensorflow.keras.models import load_model

# ─────────────────────────────────────────────
#  AYARLAR — veri_hazirla.py ile birebir aynı
# ─────────────────────────────────────────────
MODEL_DOSYASI  = "akilli_dolap_beyni.keras"
RESIM_BOYUTU   = 224
KATEGORILER    = [
    "CocaCola_Klasik",
    "CocaCola_Zero",
    "Pepsi",
    "Fanta",
    "RedBull_Klasik",
    "RedBull_White",
    "RedBull_Blue",
    "RedBull_Lilac",
    "RedBull_Pembe",
    "Nescafe_Klasik",
    "Bos_Raf",
]

# ─────────────────────────────────────────────
print("\n" + "="*50)
print("🤖 AKILLI DOLAP — Görsel Test Modu")
print("="*50 + "\n")

# 1. Modeli yükle
if not os.path.exists(MODEL_DOSYASI):
    print(f"❌ HATA: '{MODEL_DOSYASI}' bulunamadı!")
    print("   Önce: python beyin_egit.py")
    sys.exit(1)

print("📦 Yapay zeka modeli yükleniyor...")
beyin = load_model(MODEL_DOSYASI)
print("✅ Model başarıyla yüklendi!\n")

# 2. Test edilecek resmi belirle
test_resmi_yolu = sys.argv[1] if len(sys.argv) > 1 else "test_resmi.jpeg"

if not os.path.exists(test_resmi_yolu):
    print(f"❌ HATA: '{test_resmi_yolu}' bulunamadı!")
    print("   Bir resim dosyası yolu belirtin veya 'test_resmi.jpeg' adıyla klasöre koyun.")
    sys.exit(1)

print(f"📸 Resim işleniyor: {test_resmi_yolu}")

# 3. Ön işleme (tam pipeline — api_sunucu.py ile aynı)
resim = cv2.imread(test_resmi_yolu)
resim_rgb   = cv2.cvtColor(resim, cv2.COLOR_BGR2RGB)           # BGR → RGB
kucuk_resim = cv2.resize(resim_rgb, (RESIM_BOYUTU, RESIM_BOYUTU))  # 224x224
normalize   = kucuk_resim / 255.0                              # 0-1 aralığı
batch       = np.expand_dims(normalize, axis=0)                # (1, 224, 224, 3)

# 4. Tahmin
tahminler = beyin.predict(batch, verbose=0)[0]  # (11,) olasılık vektörü

# 5. Sonuçları yorumla
sirali_indeksler = np.argsort(tahminler)[::-1]  # Büyükten küçüğe sırala

kazanan_idx  = sirali_indeksler[0]
kazanan_isim = KATEGORILER[kazanan_idx]
eminlik      = tahminler[kazanan_idx] * 100

# 6. Ekrana yazdır
print("\n" + "="*50)
print("🎯 YAPAY ZEKA KARARI:")
print(f"   {kazanan_isim}  →  %{eminlik:.1f} ihtimalle")
print("="*50)

print("\n📊 Tam Olasılık Tablosu (Top 3):")
print("-"*38)
for i, idx in enumerate(sirali_indeksler[:3]):
    yildiz = "★" if i == 0 else " "
    print(f"  {yildiz} {KATEGORILER[idx]:<22}  %{tahminler[idx]*100:5.1f}")
print("-"*38)

# 7. İsteğe bağlı görsel pencere
if len(sys.argv) <= 2 or sys.argv[-1] != "--no-gui":
    try:
        # Orijinal resim üzerine etiketi yaz
        goruntu = cv2.imread(test_resmi_yolu)
        h, w = goruntu.shape[:2]
        cv2.rectangle(goruntu, (0, 0), (w, 70), (0, 0, 0), -1)
        yazi = f"{kazanan_isim}  %{eminlik:.1f}"
        cv2.putText(goruntu, yazi, (12, 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 80), 2, cv2.LINE_AA)
        cv2.rectangle(goruntu, (2, 2), (w-2, h-2), (0, 255, 80), 4)
        cv2.imshow("Akilli Dolap — AI Analiz", goruntu)
        print("\n💡 Pencereyi kapatmak için herhangi bir tuşa basın...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except Exception:
        pass  # Başsız (headless) ortamda GUI açılmazsa sessizce geç

print("\n✅ Test tamamlandı.\n")