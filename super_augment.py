"""
super_augment.py — Süper Güçlü Dataset Augmentation
=====================================================
Her orijinal fotoğrafa 15+ farklı, gerçekçi varyant üretir:
  - Karanlık / aşırı parlak ortam simülasyonu
  - Renk kayması, doygunluk değişimi (HSV)
  - Perspektif bozulması (farklı açıdan bakış)
  - Motion blur (kamera titremesi)
  - Odak kaybı blur
  - Sensör gürültüsü (ESP32 noise)
  - Vignette (kenar kararması)
  - JPEG artifact (düşük kalite kamera)
  - Keskinleştirme
  - Gölge şeridi
  - Kanal bazlı renk sapması
  - Döndürme + zoom

Çalıştırma sırası:
  1. python super_augment.py       ← bu script (dataset_dengeli/ yeniden oluşturur)
  2. python veri_hazirla.py        ← NumPy'ı güncelle
  3. python beyin_egit.py          ← modeli eğit
"""

import os
import cv2
import numpy as np
import random
import shutil

# ─────────────────────────────────────────────
#  AYARLAR
# ─────────────────────────────────────────────
KAYNAK_KLASOR  = "dataset"       # Orijinal eğitim fotoğrafları
TEST_KLASOR    = "test_grubu"    # Test fotoğrafları (ek orijinal kaynak)
HEDEF_KLASOR   = "dataset_dengeli"
RESIM_BOYUTU   = 224
HEDEF_SAYI     = 400   # Kategori başına hedef fotoğraf sayısı

# test_grubu klasör adı → dataset kategori adı eşleştirmesi
TEST_ESLESME = {
    "cocacola_klasik" : "CocaCola_Klasik",
    "cocacola_zero"   : "CocaCola_Zero",
    "pepsi"           : "Pepsi",
    "fanta"           : "Fanta",
    "redbull_klasik"  : "RedBull_Klasik",
    "redbull_white"   : "RedBull_White",
    "redbull_blue"    : "RedBull_Blue",
    "redbull_lilac"   : "RedBull_Lilac",
    "redbull_pembe"   : "RedBull_Pembe",
    "nescafe"         : "Nescafe_Klasik",
    "nescafe_klasik"  : "Nescafe_Klasik",
    "bos_raf"         : "Bos_Raf",
}

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

# Renk kodları
YSL = "\033[92m"; KRM = "\033[91m"; SAR = "\033[93m"
KLN = "\033[1m";  SFR = "\033[0m"

# ─────────────────────────────────────────────
#  AUGMENTATION FONKSİYONLARI
# ─────────────────────────────────────────────

def hazirla(img):
    """224x224 resize + RGB dönüşümü."""
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return cv2.resize(img, (RESIM_BOYUTU, RESIM_BOYUTU))

def kaydet(img, yol):
    """RGB → BGR çevirerek diske yaz."""
    cv2.imwrite(yol, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))

# --- 1. Karanlık ortam ---
def karanlik_yap(img):
    f = random.uniform(0.15, 0.55)
    return np.clip(img.astype(np.float32) * f, 0, 255).astype(np.uint8)

# --- 2. Aşırı parlak / overexposed ---
def parlak_yap(img):
    f = random.uniform(1.5, 2.2)
    return np.clip(img.astype(np.float32) * f, 0, 255).astype(np.uint8)

# --- 3. HSV renk & doygunluk kayması ---
def renk_kaydir(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[:, :, 0] = (hsv[:, :, 0] + random.uniform(-25, 25)) % 180  # hue
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * random.uniform(0.4, 1.6), 0, 255)  # saturation
    hsv[:, :, 2] = np.clip(hsv[:, :, 2] * random.uniform(0.5, 1.5), 0, 255)  # value
    return cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2RGB)

# --- 4. Perspektif bozulması ---
def perspektif_boz(img):
    h, w = img.shape[:2]
    ms = int(w * 0.18)
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([
        [random.randint(0, ms), random.randint(0, ms)],
        [w - random.randint(0, ms), random.randint(0, ms)],
        [w - random.randint(0, ms), h - random.randint(0, ms)],
        [random.randint(0, ms), h - random.randint(0, ms)],
    ])
    M = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)

# --- 5. Motion blur (kamera titremesi) ---
def motion_blur(img):
    sid = random.randint(7, 19)
    kernel = np.zeros((sid, sid))
    yon = random.randint(0, 2)
    if yon == 0:
        kernel[sid // 2, :] = 1.0
    elif yon == 1:
        kernel[:, sid // 2] = 1.0
    else:
        np.fill_diagonal(kernel, 1.0)
    kernel /= kernel.sum()
    return cv2.filter2D(img, -1, kernel)

# --- 6. Odak kaybı / Gaussian blur ---
def odak_kaybi(img):
    k = random.choice([5, 7, 9, 11, 13])
    return cv2.GaussianBlur(img, (k, k), 0)

# --- 7. Sensör gürültüsü ---
def sensor_gurultu(img):
    siddet = random.uniform(0.03, 0.10)
    gurultu = np.random.normal(0, siddet * 255, img.shape).astype(np.float32)
    return np.clip(img.astype(np.float32) + gurultu, 0, 255).astype(np.uint8)

# --- 8. Vignette (kenar kararması) ---
def vignet(img):
    h, w = img.shape[:2]
    X = cv2.getGaussianKernel(w, w * 0.55)
    Y = cv2.getGaussianKernel(h, h * 0.55)
    mask = (Y @ X.T)
    mask = mask / mask.max()
    f = random.uniform(0.35, 0.70)
    mask = mask * (1 - f) + f
    res = img.astype(np.float32)
    for i in range(3):
        res[:, :, i] *= mask
    return np.clip(res, 0, 255).astype(np.uint8)

# --- 9. JPEG artifact (düşük kalite kamera) ---
def jpeg_artifact(img):
    kalite = random.randint(15, 55)
    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    _, enc = cv2.imencode('.jpg', bgr, [cv2.IMWRITE_JPEG_QUALITY, kalite])
    dec = cv2.imdecode(enc, cv2.IMREAD_COLOR)
    return cv2.cvtColor(dec, cv2.COLOR_BGR2RGB)

# --- 10. Keskinleştirme ---
def keskinlestir(img):
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    sharp = cv2.filter2D(img, -1, kernel)
    mix = random.uniform(0.4, 1.0)
    return np.clip(
        img.astype(np.float32) * (1 - mix) + sharp.astype(np.float32) * mix,
        0, 255
    ).astype(np.uint8)

# --- 11. Gölge şeridi ---
def golge_serit(img):
    h, w = img.shape[:2]
    res = img.copy().astype(np.float32)
    faktor = random.uniform(0.2, 0.55)
    if random.random() > 0.5:
        y1 = random.randint(0, h // 2)
        y2 = random.randint(h // 2, h)
        res[y1:y2, :] *= faktor
    else:
        x1 = random.randint(0, w // 2)
        x2 = random.randint(w // 2, w)
        res[:, x1:x2] *= faktor
    return np.clip(res, 0, 255).astype(np.uint8)

# --- 12. Kanal bazlı sapma ---
def kanal_sapma(img):
    res = img.astype(np.float32)
    for i in range(3):
        res[:, :, i] = np.clip(res[:, :, i] * random.uniform(0.65, 1.35), 0, 255)
    return res.astype(np.uint8)

# --- 13. Döndürme ---
def dondur(img):
    h, w = img.shape[:2]
    aci = random.uniform(-35, 35)
    M = cv2.getRotationMatrix2D((w // 2, h // 2), aci, 1.0)
    return cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)

# --- 14. Zoom + kırpma ---
def zoom_kirp(img):
    h, w = img.shape[:2]
    z = random.uniform(0.08, 0.25)
    x1, y1 = int(w * z), int(h * z)
    x2, y2 = int(w * (1 - z)), int(h * (1 - z))
    cropped = img[y1:y2, x1:x2]
    return cv2.resize(cropped, (RESIM_BOYUTU, RESIM_BOYUTU))

# --- 15. Yatay flip ---
def flip(img):
    return cv2.flip(img, 1)

# --- 16. Kontrast extremi ---
def kontrast(img):
    alpha = random.uniform(0.5, 1.8)
    beta  = random.uniform(-50, 50)
    return cv2.convertScaleAbs(img, alpha=alpha, beta=beta)

# ─────────────────────────────────────────────
#  AUGMENTATION PIPELINE
# ─────────────────────────────────────────────

HAFIF = [dondur, zoom_kirp, flip, kontrast, kanal_sapma, keskinlestir, sensor_gurultu]
ORTA  = [perspektif_boz, odak_kaybi, motion_blur, golge_serit, vignet, jpeg_artifact, renk_kaydir]
AGIR  = [karanlik_yap, parlak_yap]

def guclu_augment(img):
    """
    Her çağrıda FARKLI bir kombinasyon üretir.
    Ortalama 2-4 dönüşüm uygulanır, model hem hafif hem aşırı koşulları öğrenir.
    """
    # Temel geometri (her zaman uygulanır)
    if random.random() > 0.4:
        img = dondur(img)
    if random.random() > 0.5:
        img = zoom_kirp(img)
    if random.random() > 0.5:
        img = flip(img)

    # Hafif (her zaman 1 adet)
    img = random.choice(HAFIF)(img)

    # Orta (%75 ihtimalle 1-2 adet)
    if random.random() < 0.75:
        img = random.choice(ORTA)(img)
    if random.random() < 0.40:
        img = random.choice(ORTA)(img)

    # Ağır (%45 ihtimalle 1 adet — karanlık/parlak)
    if random.random() < 0.45:
        img = random.choice(AGIR)(img)

    # Boyut garantisi
    if img.shape[:2] != (RESIM_BOYUTU, RESIM_BOYUTU):
        img = cv2.resize(img, (RESIM_BOYUTU, RESIM_BOYUTU))

    return img

# ─────────────────────────────────────────────
#  ANA PROGRAM
# ─────────────────────────────────────────────
def main():
    print("\n" + "=" * 60)
    print(f"{KLN}🚀 SÜPER AUGMENTATION ROBOTU{SFR}")
    print(f"   Hedef: kategori başına {HEDEF_SAYI} fotoğraf")
    print("=" * 60 + "\n")

    if not os.path.isdir(KAYNAK_KLASOR):
        print(f"{KRM}❌ '{KAYNAK_KLASOR}' klasörü bulunamadı!{SFR}")
        return

    # Eski dataset_dengeli'yi temizle
    if os.path.exists(HEDEF_KLASOR):
        shutil.rmtree(HEDEF_KLASOR)
        print(f"{SAR}🗑️  Eski '{HEDEF_KLASOR}' temizlendi.{SFR}\n")
    os.makedirs(HEDEF_KLASOR)

    ozet = []

    for kategori in KATEGORILER:
        kaynak_dir = os.path.join(KAYNAK_KLASOR, kategori)
        hedef_dir  = os.path.join(HEDEF_KLASOR, kategori)
        os.makedirs(hedef_dir, exist_ok=True)

        if not os.path.isdir(kaynak_dir):
            print(f"{KRM}  ⛔ {kategori:<22} → klasör yok, atlandı.{SFR}")
            ozet.append((kategori, 0, 0))
            continue

        uzantilar = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

        # Ana dataset klasöründen fotoğrafları al
        dosyalar = [
            os.path.join(kaynak_dir, f)
            for f in os.listdir(kaynak_dir)
            if not f.startswith(".") and
            os.path.splitext(f)[1].lower() in uzantilar
        ]

        # test_grubu klasöründen ek orijinal fotoğraflar ekle
        if os.path.isdir(TEST_KLASOR):
            for test_alt in os.listdir(TEST_KLASOR):
                eslesen = TEST_ESLESME.get(test_alt.lower())
                if eslesen != kategori:
                    continue
                test_dir = os.path.join(TEST_KLASOR, test_alt)
                if not os.path.isdir(test_dir):
                    continue
                ek = [
                    os.path.join(test_dir, f)
                    for f in os.listdir(test_dir)
                    if not f.startswith(".") and
                    os.path.splitext(f)[1].lower() in uzantilar
                ]
                dosyalar.extend(ek)
                if ek:
                    print(f"     {SAR}+{len(ek)} test fotoğrafı eklendi ({test_alt}/){SFR}")

        if not dosyalar:
            print(f"{KRM}  ⛔ {kategori:<22} → fotoğraf yok, atlandı.{SFR}")
            ozet.append((kategori, 0, 0))
            continue

        orijinal_sayi = len(dosyalar)
        print(f"  {KLN}📂 {kategori:<22}{SFR} → {orijinal_sayi} orijinal fotoğraf")

        # 1) Orijinal fotoğrafları kopyala (resize ederek)
        for i, yol in enumerate(dosyalar):
            img = cv2.imread(yol)
            if img is None:
                continue
            img = hazirla(img)
            kaydet(img, os.path.join(hedef_dir, f"orig_{i:04d}.jpg"))

        # 2) Augmented varyantlar üret
        aug_sayac = 0
        eksik     = HEDEF_SAYI - orijinal_sayi
        if eksik <= 0:
            print(f"     {YSL}✅ Yeterli orijinal var ({orijinal_sayi}), sadece kopyalandı.{SFR}")
            ozet.append((kategori, orijinal_sayi, orijinal_sayi))
            continue

        print(f"     ⚙️  {eksik} varyant üretiliyor", end="", flush=True)

        while aug_sayac < eksik:
            src_yol = random.choice(dosyalar)
            img = cv2.imread(src_yol)
            if img is None:
                continue
            img = hazirla(img)
            img = guclu_augment(img)
            kaydet(img, os.path.join(hedef_dir, f"aug_{aug_sayac:05d}.jpg"))
            aug_sayac += 1

            if aug_sayac % 50 == 0:
                print(".", end="", flush=True)

        toplam = orijinal_sayi + aug_sayac
        print(f"\n     {YSL}✅ Toplam: {toplam} fotoğraf ({orijinal_sayi} orijinal + {aug_sayac} augmented){SFR}\n")
        ozet.append((kategori, orijinal_sayi, toplam))

    # ─── ÖZET ───────────────────────────────────
    print("=" * 60)
    print(f"{KLN}📊 ÖZET RAPORU{SFR}")
    print("=" * 60)
    print(f"  {'Kategori':<22}  {'Orijinal':>8}  {'Toplam':>7}  {'Augmented':>10}")
    print("-" * 60)
    for kat, once, sonra in ozet:
        aug = sonra - once
        isaret = YSL + "✅" + SFR if sonra > 0 else KRM + "⛔" + SFR
        print(f"  {isaret} {kat:<22} {once:>8}  {sonra:>7}  +{aug:>8}")
    print("=" * 60)
    print(f"\n{YSL}{KLN}✅ Dataset hazır! Sıradaki adımlar:{SFR}")
    print(f"   1. python veri_hazirla.py   ← NumPy array'lerini güncelle")
    print(f"   2. python beyin_egit.py     ← modeli eğit\n")

if __name__ == "__main__":
    main()
