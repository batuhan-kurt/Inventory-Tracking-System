"""
veri_hazirla.py — Dataset → NumPy Paketiyle Dönüştürme Robotu
==============================================================
Önce 'dataset_dengeli/' klasörünü arar (veri_denge.py çalıştırıldıysa).
Eğer bulamazsa 'dataset/' orijinal klasörünü kullanır.

Çıktı:
  X_verileri.npy   → (N, 224, 224, 3) piksel matrisi
  Y_etiketler.npy  → (N,) etiket dizisi
"""

import os
import cv2
import numpy as np

print("🤖 Veri İşleme Robotu Çalışıyor...\n")

# ─────────────────────────────────────────────
#  AYARLAR
# ─────────────────────────────────────────────
DENGELI_KLASOR  = "dataset_dengeli"   # veri_denge.py çıktısı (öncelikli)
ORIJINAL_KLASOR = "dataset"           # Yedek
RESIM_BOYUTU    = 224

KATEGORILER = [
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
#  Kullanılacak Klasörü Belirle
# ─────────────────────────────────────────────
if os.path.isdir(DENGELI_KLASOR):
    veri_klasoru = DENGELI_KLASOR
    print(f"✅ Dengeli dataset bulundu: '{DENGELI_KLASOR}/' kullanılıyor.\n")
else:
    veri_klasoru = ORIJINAL_KLASOR
    print(f"⚠️  '{DENGELI_KLASOR}/' bulunamadı. Orijinal '{ORIJINAL_KLASOR}/' kullanılıyor.")
    print("   (Önce 'python veri_denge.py' çalıştırmanız önerilir.)\n")

# ─────────────────────────────────────────────
#  Klasörleri Gez, Resimleri Oku
# ─────────────────────────────────────────────
X_goruntuler = []
Y_etiketler  = []

for etiket_numarasi, kategori in enumerate(KATEGORILER):
    klasor_yolu = os.path.join(veri_klasoru, kategori)

    if not os.path.exists(klasor_yolu):
        print(f"⛔ [{kategori}] klasörü bulunamadı, atlandı.")
        continue

    dosyalar = [
        f for f in os.listdir(klasor_yolu)
        if not f.startswith(".") and f.lower().endswith(
            (".jpg", ".jpeg", ".png", ".bmp", ".webp")
        )
    ]

    print(f"📂 [{kategori}] — {len(dosyalar)} dosya bulundu, işleniyor...")

    basarili_sayi = 0
    for resim_adi in dosyalar:
        resim_tam_yolu = os.path.join(klasor_yolu, resim_adi)
        resim = cv2.imread(resim_tam_yolu)

        if resim is None:
            print(f"   ❌ OKUNAMADI (Bozuk Format): {resim_adi}")
            continue

        # BGR → RGB (OpenCV ters okur; yapay zeka RGB ister)
        resim = cv2.cvtColor(resim, cv2.COLOR_BGR2RGB)
        # 224x224'e yeniden boyutlandır
        resim = cv2.resize(resim, (RESIM_BOYUTU, RESIM_BOYUTU))

        X_goruntuler.append(resim)
        Y_etiketler.append(etiket_numarasi)
        basarili_sayi += 1

    print(f"   ✅ {basarili_sayi} resim başarıyla paketlendi.\n")

# ─────────────────────────────────────────────
#  NumPy Matrisine Çevir ve Kaydet
# ─────────────────────────────────────────────
X_goruntuler = np.array(X_goruntuler, dtype=np.uint8)
Y_etiketler  = np.array(Y_etiketler,  dtype=np.int32)

np.save("X_verileri.npy", X_goruntuler)
np.save("Y_etiketler.npy", Y_etiketler)

print("=" * 45)
print("🎯 İŞLEM TAMAMLANDI!")
print(f"   Toplam Resim  : {len(X_goruntuler)}")
print(f"   Matris Boyutu : {X_goruntuler.shape}")
print(f"   Kaynak Klasör : {veri_klasoru}/")
print("=" * 45)
print("\n🔜 Sonraki adım: python beyin_egit.py\n")