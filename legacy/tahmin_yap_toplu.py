"""
tahmin_yap_toplu.py — Kategorili Toplu Görsel Test & Doğruluk Analizi
======================================================================
Kullanım:
  python tahmin_yap_toplu.py          → 'test_grubu/' klasörünü analiz eder
  python tahmin_yap_toplu.py --csv    → sonuçları CSV'ye de kaydeder

Klasör yapısı:
  test_grubu/
    CocaCola_Klasik/   ← alt klasör adı = gerçek etiket (ground truth)
      foto1.jpg
      foto2.jpeg
    RedBull_Blue/
      foto3.png
      ...

Desteklenen formatlar: .jpg, .jpeg, .png, .bmp, .webp
"""

import cv2
import numpy as np
import os
import sys
import csv
import time
from datetime import datetime
from tensorflow.keras.models import load_model

# ─────────────────────────────────────────────
#  AYARLAR
# ─────────────────────────────────────────────
MODEL_DOSYASI = "akilli_dolap_beyni.keras"
RESIM_BOYUTU  = 224
KATEGORILER   = [
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
DESTEKLENEN_UZANTILAR = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# Test klasörü adı → model kategori adı eşleştirme haritası
# (büyük/küçük harf farkları ve isim farklılıklarını kapsar)
KLASOR_ESLESME = {
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

# Renk kodları
YSL  = "\033[92m"   # yeşil  → doğru
KRM  = "\033[91m"   # kırmızı → yanlış
SAR  = "\033[93m"   # sarı   → uyarı
MAV  = "\033[96m"   # cyan
GRI  = "\033[90m"   # gri
KLN  = "\033[1m"    # kalın
SFR  = "\033[0m"    # sıfırla

# ─────────────────────────────────────────────
#  Yardımcı: terminal tablosu
# ─────────────────────────────────────────────
def tablo_ciz(basliklar, satirlar):
    genislikler = [len(b) for b in basliklar]
    for satir in satirlar:
        for i, hucre in enumerate(satir):
            genislikler[i] = max(genislikler[i], len(str(hucre)))

    ayrac = "+" + "+".join("-" * (g + 2) for g in genislikler) + "+"
    baslik_satiri = "|" + "|".join(
        f" {KLN}{b:<{g}}{SFR} " for b, g in zip(basliklar, genislikler)
    ) + "|"

    print(ayrac)
    print(baslik_satiri)
    print(ayrac.replace("-", "="))

    for satir in satirlar:
        dogru_mu = satir[-1]  # son sütun "✅" veya "❌"
        renk = YSL if "✅" in str(dogru_mu) else KRM
        hucre_str = "|" + "|".join(
            f" {str(h):<{g}} " for h, g in zip(satir, genislikler)
        ) + "|"
        print(renk + hucre_str + SFR)

    print(ayrac)

# ─────────────────────────────────────────────
#  Yardımcı: ön işle ve tahmin et
# ─────────────────────────────────────────────
def resim_tahmin_et(beyin, dosya_yolu):
    try:
        resim = cv2.imread(dosya_yolu)
        if resim is None:
            return None
        resim_rgb   = cv2.cvtColor(resim, cv2.COLOR_BGR2RGB)
        kucuk_resim = cv2.resize(resim_rgb, (RESIM_BOYUTU, RESIM_BOYUTU))
        normalize   = kucuk_resim / 255.0
        batch       = np.expand_dims(normalize, axis=0)
        tahminler   = beyin.predict(batch, verbose=0)[0]
        return tahminler
    except Exception as e:
        print(f"\n  ⚠️  İşlenemedi → {os.path.basename(dosya_yolu)}: {e}")
        return None

# ─────────────────────────────────────────────
#  ANA PROGRAM
# ─────────────────────────────────────────────
print("\n" + "=" * 65)
print(f"{KLN}🤖 AKILLI DOLAP — Kategorili Toplu Test & Doğruluk Analizi{SFR}")
print("=" * 65 + "\n")

kaydet_csv  = "--csv" in sys.argv
test_klasor = "test_grubu"

# --- Model yükle ---
if not os.path.exists(MODEL_DOSYASI):
    print(f"❌ HATA: '{MODEL_DOSYASI}' bulunamadı!")
    print("   Önce: python beyin_egit.py")
    sys.exit(1)

print("📦 Yapay zeka modeli yükleniyor...")
beyin = load_model(MODEL_DOSYASI)
print("✅ Model başarıyla yüklendi!\n")

# --- Klasör kontrolü ---
if not os.path.isdir(test_klasor):
    print(f"❌ HATA: '{test_klasor}' klasörü bulunamadı!")
    sys.exit(1)

# --- Alt kategorileri tara ---
alt_klasorler = sorted([
    d for d in os.listdir(test_klasor)
    if os.path.isdir(os.path.join(test_klasor, d)) and not d.startswith(".")
])

if not alt_klasorler:
    print(f"❌ '{test_klasor}' içinde alt kategori klasörü bulunamadı!")
    sys.exit(1)

# --- Kaç fotoğraf var ---
toplam_dosya = 0
for klasor in alt_klasorler:
    yol = os.path.join(test_klasor, klasor)
    dosyalar = [
        f for f in os.listdir(yol)
        if os.path.splitext(f)[1].lower() in DESTEKLENEN_UZANTILAR
    ]
    toplam_dosya += len(dosyalar)

print(f"📁 Klasör     : {os.path.abspath(test_klasor)}")
print(f"📂 Kategori   : {len(alt_klasorler)} adet → {', '.join(alt_klasorler)}")
print(f"🖼️  Toplam     : {toplam_dosya} görsel\n")
print("🔄 Tahminler hesaplanıyor...\n")

# ─────────────────────────────────────────────
#  Her kategori klasörünü işle
# ─────────────────────────────────────────────
sonuclar   = []
basarisiz  = []
is_sayaci  = 0
baslangic  = time.time()

for klasor_adi in alt_klasorler:
    klasor_yolu = os.path.join(test_klasor, klasor_adi)

    # Gerçek etiketi bul (eşleşme haritasından)
    gercek_etiket = KLASOR_ESLESME.get(klasor_adi.lower())
    if gercek_etiket is None:
        print(f"{SAR}  ⚠️  '{klasor_adi}' tanınmayan kategori — atlanıyor.{SFR}")
        continue

    dosyalar = sorted([
        f for f in os.listdir(klasor_yolu)
        if os.path.splitext(f)[1].lower() in DESTEKLENEN_UZANTILAR
    ])

    for dosya_adi in dosyalar:
        is_sayaci += 1
        tam_yol   = os.path.join(klasor_yolu, dosya_adi)

        # İlerleme
        yuzde = int((is_sayaci / toplam_dosya) * 30)
        bar   = "█" * yuzde + "░" * (30 - yuzde)
        print(f"\r  [{bar}] {is_sayaci}/{toplam_dosya}", end="", flush=True)

        tahminler = resim_tahmin_et(beyin, tam_yol)
        if tahminler is None:
            basarisiz.append(f"{klasor_adi}/{dosya_adi}")
            continue

        sirali       = np.argsort(tahminler)[::-1]
        tahmin_1     = KATEGORILER[sirali[0]]
        dogru_mu     = (tahmin_1 == gercek_etiket)

        sonuclar.append({
            "no"            : is_sayaci,
            "kategori"      : gercek_etiket,
            "dosya"         : dosya_adi,
            "tahmin"        : tahmin_1,
            "guven"         : round(tahminler[sirali[0]] * 100, 1),
            "tahmin_2"      : KATEGORILER[sirali[1]],
            "guven_2"       : round(tahminler[sirali[1]] * 100, 1),
            "dogru_mu"      : dogru_mu,
        })

sure = time.time() - baslangic
print(f"\r  {'✅ Tamamlandı!':<60}")
print(f"  ⏱️  Süre: {sure:.1f} sn  ({sure/max(len(sonuclar),1)*1000:.0f} ms/görsel)\n")

if not sonuclar:
    print("❌ Hiçbir görsel işlenemedi.")
    sys.exit(1)

# ─────────────────────────────────────────────
#  SONUÇ TABLOSU
# ─────────────────────────────────────────────
print("\n" + "=" * 65)
print(f"{KLN}📊 TAHMİN SONUÇLARI — Fotoğraf Bazlı{SFR}")
print("=" * 65 + "\n")

basliklar = [
    "#", "Gerçek Kategori", "Dosya Adı",
    "Tahmin", "Güven %", "2. İhtimal", "2. Güven %", "Sonuç"
]

satirlar = [
    [
        s["no"],
        s["kategori"],
        s["dosya"],
        s["tahmin"],
        f"%{s['guven']:.1f}",
        s["tahmin_2"],
        f"%{s['guven_2']:.1f}",
        "✅ Doğru" if s["dogru_mu"] else "❌ Yanlış",
    ]
    for s in sonuclar
]

tablo_ciz(basliklar, satirlar)

# ─────────────────────────────────────────────
#  KATEGORİ BAZLI DOĞRULUK TABLOSU
# ─────────────────────────────────────────────
print("\n" + "=" * 65)
print(f"{KLN}📈 KATEGORİ BAZLI DOĞRULUK ANALİZİ{SFR}")
print("=" * 65 + "\n")

kategori_istatistik = {}
for s in sonuclar:
    k = s["kategori"]
    if k not in kategori_istatistik:
        kategori_istatistik[k] = {"toplam": 0, "dogru": 0, "guvenler": []}
    kategori_istatistik[k]["toplam"] += 1
    if s["dogru_mu"]:
        kategori_istatistik[k]["dogru"] += 1
    kategori_istatistik[k]["guvenler"].append(s["guven"])

kat_basliklar = ["Kategori", "Test Adedi", "Doğru", "Yanlış", "Doğruluk %", "Ort. Güven %"]
kat_satirlar  = []

for kat, ist in sorted(kategori_istatistik.items()):
    yanlis    = ist["toplam"] - ist["dogru"]
    dogruluk  = ist["dogru"] / ist["toplam"] * 100
    ort_guven = np.mean(ist["guvenler"])
    kat_satirlar.append([
        kat,
        ist["toplam"],
        ist["dogru"],
        yanlis,
        f"%{dogruluk:.1f}",
        f"%{ort_guven:.1f}",
    ])

# Kat tablosunu düz renkle çiz (renklendirme için özel versiyon)
genislikler = [len(b) for b in kat_basliklar]
for satir in kat_satirlar:
    for i, h in enumerate(satir):
        genislikler[i] = max(genislikler[i], len(str(h)))

ayrac = "+" + "+".join("-" * (g + 2) for g in genislikler) + "+"
print(ayrac)
print("|" + "|".join(f" {KLN}{b:<{g}}{SFR} " for b, g in zip(kat_basliklar, genislikler)) + "|")
print(ayrac.replace("-", "="))

for satir in kat_satirlar:
    dogruluk_val = float(str(satir[4]).replace("%", ""))
    renk = YSL if dogruluk_val >= 80 else (SAR if dogruluk_val >= 50 else KRM)
    print(renk + "|" + "|".join(f" {str(h):<{g}} " for h, g in zip(satir, genislikler)) + "|" + SFR)

print(ayrac)

# ─────────────────────────────────────────────
#  GENEL ÖZET
# ─────────────────────────────────────────────
toplam       = len(sonuclar)
dogru_toplam = sum(1 for s in sonuclar if s["dogru_mu"])
yanlis_top   = toplam - dogru_toplam
genel_dogruluk = dogru_toplam / toplam * 100
ort_guven_genel = np.mean([s["guven"] for s in sonuclar])

print(f"\n{'='*65}")
print(f"{KLN}🎯 GENEL SONUÇ{SFR}")
print(f"{'='*65}")
print(f"  Toplam Test      : {toplam} görsel")
print(f"  {YSL}Doğru Tahmin  : {dogru_toplam}{SFR}")
print(f"  {KRM}Yanlış Tahmin : {yanlis_top}{SFR}")
print(f"  Genel Doğruluk   : {KLN}%{genel_dogruluk:.1f}{SFR}")
print(f"  Ortalama Güven   : %{ort_guven_genel:.1f}")

if basarisiz:
    print(f"\n  {SAR}⚠️  İşlenemeyen: {len(basarisiz)} dosya{SFR}")
    for f in basarisiz:
        print(f"     • {f}")

# ─────────────────────────────────────────────
#  CSV KAYDET (isteğe bağlı)
# ─────────────────────────────────────────────
if kaydet_csv:
    zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_dosyasi   = f"toplu_sonuclar_{zaman_damgasi}.csv"
    with open(csv_dosyasi, "w", newline="", encoding="utf-8") as f:
        alanlar = ["no", "kategori", "dosya", "tahmin", "guven",
                   "tahmin_2", "guven_2", "dogru_mu"]
        yazar = csv.DictWriter(f, fieldnames=alanlar)
        yazar.writeheader()
        yazar.writerows(sonuclar)
    print(f"\n  💾 Sonuçlar kaydedildi: {csv_dosyasi}")

print(f"\n{'='*65}")
print("✅ Toplu test tamamlandı.")
print(f"{'='*65}\n")
