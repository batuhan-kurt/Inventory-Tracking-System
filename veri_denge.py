"""
veri_denge.py — Akıllı Dataset Dengeleme ve Artırma Robotu
===========================================================
Bu script şunları yapar:
  1. dataset/ klasörünü analiz eder ve her sınıftaki fotoğraf sayısını gösterir.
  2. En kalabalık sınıfı referans alarak az olan sınıfları augment eder.
  3. Augment sırasında sadece klasik dönüşümlere EK OLARAK:
       - Gaussian Noise (kumlanma)  → ESP32 OV5640 sensör gürültüsünü simüle eder
       - Gaussian Blur              → Lens odak sorunlarını simüle eder
     uygular. Böylece model iPhone'dan değil, ESP32 kamerasından geliyormuş gibi
     fotoğraflarla eğitilmiş olur.
  4. Augmented fotoğrafları dataset_dengeli/ klasörüne kaydeder
     (orijinal dataset/ klasörüne DOKUNMAZ).
  5. Bitince hangi sınıfın kaçtan kaça çıktığını özetler.

Kullanım:
  python veri_denge.py
  --> Çıktı: dataset_dengeli/ klasörü
  --> Ardından: python veri_hazirla.py çalıştırın (dataset klasörünü otomatik kullanır)
"""

import os
import cv2
import numpy as np
import shutil
import random
from collections import Counter

# ─────────────────────────────────────────────
#  1. AYARLAR
# ─────────────────────────────────────────────
KAYNAK_KLASOR  = "dataset"          # Orijinal fotoğraflar (dokunulmaz)
HEDEF_KLASOR   = "dataset_dengeli"  # Augmented çıktı buraya
RESIM_BOYUTU   = 224                # Tüm sistemle tutarlı

# Kaç fotoğrafa eşitlensin?
# "max" → en kalabalık sınıfa eşitle (önerilen)
# Sayı girin → örneğin 120 → hepsini 120'ye getir
HEDEF_SAYI = "max"

# ESP32 kamera simülasyonu şiddeti (0.0 = kapalı, 1.0 = maksimum)
GURULTU_SIDDETI = 0.04   # Gaussian noise standart sapması (piksel üzerinden ~10/255)
BLUR_OLASILIGI  = 0.40   # Her augmented fotoğrafın %40'ına blur uygula

# Kategoriler (sırası önemli — beyin_egit.py ile tutarlı olmalı)
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
#  2. YARDIMCI FONKSİYONLAR
# ─────────────────────────────────────────────

def resim_oku(yol: str) -> np.ndarray | None:
    """Dosyayı okur, BGR→RGB, 224x224 resize yapar."""
    img = cv2.imread(yol)
    if img is None:
        return None
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (RESIM_BOYUTU, RESIM_BOYUTU))
    return img


def resim_kaydet(img: np.ndarray, yol: str) -> None:
    """RGB → BGR'ye çevirip diske yazar (OpenCV BGR formatında saklar)."""
    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    cv2.imwrite(yol, bgr)


def gaussian_noise_ekle(img: np.ndarray, siddet: float) -> np.ndarray:
    """
    Gerçek sensör gürültüsünü simüle eder.
    ESP32 OV5640 düşük ışıkta bu kadar kumlanma üretir.
    """
    gurultu = np.random.normal(0, siddet * 255, img.shape).astype(np.float32)
    noisy = img.astype(np.float32) + gurultu
    return np.clip(noisy, 0, 255).astype(np.uint8)


def blur_ekle(img: np.ndarray) -> np.ndarray:
    """
    Hafif Gaussian blur — lens titremesi veya odak sorununu simüle eder.
    Kernel boyutunu 3 veya 5 piksel arasında rastgele seçer.
    """
    kernel = random.choice([3, 5])
    return cv2.GaussianBlur(img, (kernel, kernel), 0)


def augment_et(img: np.ndarray) -> np.ndarray:
    """
    Tek bir fotoğrafa rastgele bir augmentation kombinasyonu uygular.
    Her çağrıda farklı bir sonuç üretir (rastgelelik sayesinde).
    
    Uygulanacak dönüşümler:
      - Yatay çevirme (flip)
      - Döndürme (-25° ile +25° arası)
      - Zoom / kırpma (%10-%20 arası)
      - Parlaklık & kontrast oynaması
      - Gaussian Noise (ESP32 sensör gürültüsü)
      - Gaussian Blur  (ESP32 lens odak sorunu) — %40 ihtimalle
    """
    h, w = img.shape[:2]

    # --- Yatay Çevirme (50% ihtimalle) ---
    if random.random() > 0.5:
        img = cv2.flip(img, 1)

    # --- Döndürme (-25 ile +25 derece) ---
    aci = random.uniform(-25, 25)
    M = cv2.getRotationMatrix2D((w // 2, h // 2), aci, 1.0)
    img = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)

    # --- Zoom / Kırpma ---
    zoom = random.uniform(0.10, 0.20)   # %10-%20 zoom
    x1 = int(w * zoom)
    y1 = int(h * zoom)
    x2 = int(w * (1 - zoom))
    y2 = int(h * (1 - zoom))
    img = img[y1:y2, x1:x2]
    img = cv2.resize(img, (RESIM_BOYUTU, RESIM_BOYUTU))

    # --- Parlaklık ve Kontrast ---
    # alpha: kontrast (0.7 - 1.3), beta: parlaklık eklentisi (-40 - +40)
    alpha = random.uniform(0.7, 1.3)
    beta  = random.uniform(-40, 40)
    img = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)

    # --- ESP32 Sensör Gürültüsü (Gaussian Noise) ---
    img = gaussian_noise_ekle(img, GURULTU_SIDDETI)

    # --- ESP32 Lens Bulanıklığı (Gaussian Blur — %40 ihtimalle) ---
    if random.random() < BLUR_OLASILIGI:
        img = blur_ekle(img)

    return img


# ─────────────────────────────────────────────
#  3. ANA PROGRAM
# ─────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  📊 Akıllı Dataset Dengeleme Robotu")
    print("=" * 55)

    # ── Adım 1: Orijinal sınıf sayılarını say ──────────────
    print("\n📂 Orijinal Dataset Analizi:")
    print("-" * 40)

    sinif_resimleri: dict[str, list[str]] = {}   # {kategori: [dosya yolları]}
    for kategori in KATEGORILER:
        klasor = os.path.join(KAYNAK_KLASOR, kategori)
        if not os.path.isdir(klasor):
            print(f"  ⚠️  '{kategori}' klasörü bulunamadı, atlandı.")
            sinif_resimleri[kategori] = []
            continue
        dosyalar = [
            os.path.join(klasor, f)
            for f in os.listdir(klasor)
            if not f.startswith(".") and f.lower().endswith(
                (".jpg", ".jpeg", ".png", ".bmp", ".webp")
            )
        ]
        sinif_resimleri[kategori] = dosyalar
        print(f"  {'✅' if dosyalar else '❌'} {kategori:<22} → {len(dosyalar):>3} fotoğraf")

    sayilar = [len(v) for v in sinif_resimleri.values() if v]
    if not sayilar:
        print("\n❌ Hiç fotoğraf bulunamadı. Dataset klasörünü kontrol edin.")
        return

    max_sayi    = max(sayilar)
    min_sayi    = min(sayilar)
    hedef_sayi  = max_sayi if HEDEF_SAYI == "max" else int(HEDEF_SAYI)

    print(f"\n  📈 En kalabalık sınıf : {max_sayi} fotoğraf")
    print(f"  📉 En az fotoğraflı   : {min_sayi} fotoğraf")
    print(f"  🎯 Hedef (eşitleme)   : {hedef_sayi} fotoğraf / sınıf")

    # ── Adım 2: Hedef klasörü hazırla ──────────────────────
    if os.path.exists(HEDEF_KLASOR):
        shutil.rmtree(HEDEF_KLASOR)
        print(f"\n🗑️  Eski '{HEDEF_KLASOR}' klasörü temizlendi.")
    os.makedirs(HEDEF_KLASOR)

    # ── Adım 3: Her sınıfı dengele ve kaydet ───────────────
    print(f"\n🔄 Augmentation & Dengeleme İşlemi Başlıyor...\n")
    print("-" * 55)

    ozet: list[tuple[str, int, int]] = []   # (kategori, önce, sonra)

    for kategori, dosyalar in sinif_resimleri.items():
        hedef_dir = os.path.join(HEDEF_KLASOR, kategori)
        os.makedirs(hedef_dir, exist_ok=True)

        onceki_sayi = len(dosyalar)

        if onceki_sayi == 0:
            print(f"  ⛔ {kategori:<22} → Fotoğraf yok, atlandı.")
            ozet.append((kategori, 0, 0))
            continue

        # Orijinal fotoğrafları kopyala
        for i, dosya_yolu in enumerate(dosyalar):
            hedef_yol = os.path.join(hedef_dir, f"orig_{i:04d}.jpg")
            img = resim_oku(dosya_yolu)
            if img is not None:
                resim_kaydet(img, hedef_yol)

        # Eksik fotoğrafları augmentation ile üret
        eksik_sayi = hedef_sayi - onceki_sayi
        if eksik_sayi <= 0:
            print(f"  ✅ {kategori:<22} → Zaten yeterli ({onceki_sayi}/{hedef_sayi}), kopyalandı.")
            ozet.append((kategori, onceki_sayi, onceki_sayi))
            continue

        print(f"  🔧 {kategori:<22} → {onceki_sayi} → +{eksik_sayi} aug → {hedef_sayi} fotoğraf üretiliyor...")

        aug_sayac = 0
        while aug_sayac < eksik_sayi:
            # Rastgele bir orijinal fotoğraf seç
            kaynak_yolu = random.choice(dosyalar)
            img = resim_oku(kaynak_yolu)
            if img is None:
                continue

            aug_img = augment_et(img)
            hedef_yol = os.path.join(hedef_dir, f"aug_{aug_sayac:05d}.jpg")
            resim_kaydet(aug_img, hedef_yol)
            aug_sayac += 1

        # Son kontrolü yap
        uretilen = len([
            f for f in os.listdir(hedef_dir)
            if not f.startswith(".")
        ])
        ozet.append((kategori, onceki_sayi, uretilen))

    # ── Adım 4: Özet rapor ─────────────────────────────────
    print("\n" + "=" * 55)
    print("  📋 DENGELEME ÖZET RAPORU")
    print("=" * 55)
    print(f"  {'Sınıf':<22}  {'Önce':>6}  {'Sonra':>6}  {'Eklenen':>8}")
    print("-" * 55)

    toplam_once  = 0
    toplam_sonra = 0
    for kategori, once, sonra in ozet:
        eklenen = sonra - once
        toplam_once  += once
        toplam_sonra += sonra
        isaret = "✅" if once > 0 else "⛔"
        print(f"  {isaret} {kategori:<22} {once:>6}  {sonra:>6}  +{eklenen:>6}")

    print("-" * 55)
    print(f"  {'TOPLAM':<22} {toplam_once:>6}  {toplam_sonra:>6}  +{toplam_sonra - toplam_once:>6}")
    print("=" * 55)
    print(f"\n✅ Dengeli dataset '{HEDEF_KLASOR}/' klasörüne kaydedildi!")
    print("🔜 Sonraki adım: python veri_hazirla.py")
    print()


if __name__ == "__main__":
    main()
