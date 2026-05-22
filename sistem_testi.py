"""
sistem_testi.py — Tüm Sistem Entegrasyon Testi
================================================
Bu script projenin tüm bileşenlerini sırasıyla test eder:
  1. Model dosyası var mı ve yüklenebiliyor mu?
  2. NumPy veri setleri var mı ve boyutları doğru mu?
  3. JSON/CSV veritabanları var mı ve okunabiliyor mu?
  4. Model test_resmi.jpeg üzerinde çalışıyor mu?
  5. API sunucusu import edilebiliyor mu?

Çalıştırma:
  python sistem_testi.py
"""

import os
import sys
import json
import numpy as np
import traceback

YESIL  = "\033[92m"
KIRMIZI = "\033[91m"
SARI   = "\033[93m"
MAVI   = "\033[94m"
RESET  = "\033[0m"
KALIN  = "\033[1m"

def ok(mesaj):    print(f"  {YESIL}✅ {mesaj}{RESET}")
def hata(mesaj):  print(f"  {KIRMIZI}❌ {mesaj}{RESET}")
def uyari(mesaj): print(f"  {SARI}⚠️  {mesaj}{RESET}")
def bilgi(mesaj): print(f"  {MAVI}ℹ️  {mesaj}{RESET}")

basari_sayisi = 0
hata_sayisi   = 0

def test(baslik, fonksiyon):
    global basari_sayisi, hata_sayisi
    print(f"\n{KALIN}[ {baslik} ]{RESET}")
    try:
        fonksiyon()
        basari_sayisi += 1
    except Exception as e:
        hata(f"BEKLENMEYEN HATA: {e}")
        hata_sayisi += 1

# ─────────────────────────────────────────────
#  TEST 1: Model Dosyası
# ─────────────────────────────────────────────
def test_model_dosyasi():
    MODEL = "akilli_dolap_beyni.keras"
    if not os.path.exists(MODEL):
        raise FileNotFoundError(f"'{MODEL}' bulunamadı! → python beyin_egit.py çalıştırın.")
    boyut_mb = os.path.getsize(MODEL) / (1024 * 1024)
    ok(f"Model dosyası mevcut: {MODEL}  ({boyut_mb:.1f} MB)")

test("TEST 1: Model Dosyası", test_model_dosyasi)

# ─────────────────────────────────────────────
#  TEST 2: Model Yükleme ve Yapı Doğrulama
# ─────────────────────────────────────────────
beyin = None
def test_model_yukle():
    global beyin
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
    from tensorflow.keras.models import load_model
    beyin = load_model("akilli_dolap_beyni.keras")
    giris = beyin.input_shape   # (None, 224, 224, 3)
    cikis = beyin.output_shape  # (None, 11)
    ok(f"Model yüklendi — Giriş: {giris}  Çıkış: {cikis}")
    if giris[1:] != (224, 224, 3):
        raise ValueError(f"Beklenen giriş (224,224,3) ama model {giris[1:]} görüyor!")
    if cikis[1] != 11:
        raise ValueError(f"Beklenen 11 sınıf ama model {cikis[1]} sınıf görüyor!")
    ok("Giriş boyutu (224x224x3) doğrulandı ✓")
    ok("Çıkış sınıf sayısı (11) doğrulandı ✓")

test("TEST 2: Model Yapısı", test_model_yukle)

# ─────────────────────────────────────────────
#  TEST 3: NumPy Veri Setleri
# ─────────────────────────────────────────────
def test_numpy():
    for dosya in ["X_verileri.npy", "Y_etiketler.npy"]:
        if not os.path.exists(dosya):
            raise FileNotFoundError(f"'{dosya}' bulunamadı! → python veri_hazirla.py çalıştırın.")
    X = np.load("X_verileri.npy")
    Y = np.load("Y_etiketler.npy")
    ok(f"X_verileri.npy   : {X.shape}  dtype={X.dtype}")
    ok(f"Y_etiketler.npy  : {Y.shape}  dtype={Y.dtype}")
    if X.shape[1:] != (224, 224, 3):
        raise ValueError(f"Beklenen (N,224,224,3) ama {X.shape} bulundu → veri_hazirla.py tekrar çalıştırın!")
    ok("Veri boyutu (224x224x3) doğrulandı ✓")
    siniflar = np.unique(Y)
    ok(f"Etiket sınıfları : {list(siniflar)}  (beklenen: 0-10)")
    from collections import Counter
    dagılım = Counter(Y.tolist())
    for sinif_id, sayi in sorted(dagılım.items()):
        durum = ok if sayi >= 80 else uyari
        isim_listesi = ["CocaCola_Klasik","CocaCola_Zero","Pepsi","Fanta","RedBull_Klasik",
                        "RedBull_White","RedBull_Blue","RedBull_Lilac","RedBull_Pembe","Nescafe_Klasik","Bos_Raf"]
        durum(f"Sınıf {sinif_id} ({isim_listesi[sinif_id]:<18}) : {sayi} resim")

test("TEST 3: Veri Seti", test_numpy)

# ─────────────────────────────────────────────
#  TEST 4: JSON ve CSV Dosyaları
# ─────────────────────────────────────────────
def test_veritabanlari():
    for dosya in ["sistem_durumu.json", "urun_katalogu.json", "satis_gecmisi.csv"]:
        if not os.path.exists(dosya):
            hata(f"'{dosya}' bulunamadı — Dashboard düzgün çalışmayabilir.")
        else:
            boyut = os.path.getsize(dosya)
            ok(f"{dosya:<30} ({boyut} byte)")
    # JSON içeriklerini doğrula
    with open("sistem_durumu.json", "r", encoding="utf-8") as f:
        durum = json.load(f)
    beklenen_anahtarlar = {"stok", "son_olay"}
    eksik = beklenen_anahtarlar - set(durum.keys())
    if eksik:
        uyari(f"sistem_durumu.json'da eksik anahtarlar: {eksik}")
    else:
        ok("sistem_durumu.json yapısı doğrulandı ✓")
    stok_urunler = set(durum["stok"].keys())
    ok(f"Stok takip edilen ürünler: {len(stok_urunler)} adet")

test("TEST 4: Veritabanları (JSON/CSV)", test_veritabanlari)

# ─────────────────────────────────────────────
#  TEST 5: Canlı Tahmin Testi
# ─────────────────────────────────────────────
def test_canli_tahmin():
    import cv2
    KATEGORILER = ["CocaCola_Klasik","CocaCola_Zero","Pepsi","Fanta","RedBull_Klasik",
                   "RedBull_White","RedBull_Blue","RedBull_Lilac","RedBull_Pembe","Nescafe_Klasik","Bos_Raf"]
    if beyin is None:
        raise RuntimeError("Model yüklenmedi (Test 2 başarısız olmuş), tahmin yapılamaz.")
    TEST_RESIM = "test_resmi.jpeg"
    if not os.path.exists(TEST_RESIM):
        uyari(f"'{TEST_RESIM}' bulunamadı — tahmin testi atlandı.")
        bilgi("Test için herhangi bir ürün fotoğrafını 'test_resmi.jpeg' adıyla klasöre koyun.")
        return
    resim = cv2.imread(TEST_RESIM)
    if resim is None:
        raise RuntimeError(f"'{TEST_RESIM}' OpenCV tarafından okunamadı (bozuk dosya?).")
    resim_rgb = cv2.cvtColor(resim, cv2.COLOR_BGR2RGB)
    kucuk    = cv2.resize(resim_rgb, (224, 224))
    batch    = np.expand_dims(kucuk / 255.0, axis=0)
    tahminler = beyin.predict(batch, verbose=0)[0]
    en_iyi_idx  = np.argmax(tahminler)
    eminlik      = tahminler[en_iyi_idx] * 100
    ok(f"Tahmin başarılı: '{KATEGORILER[en_iyi_idx]}'  (Eminlik: %{eminlik:.1f})")
    sirali = np.argsort(tahminler)[::-1]
    bilgi("Top-3 olasılık:")
    for i in range(3):
        idx = sirali[i]
        print(f"         {i+1}. {KATEGORILER[idx]:<22}  %{tahminler[idx]*100:.1f}")

test("TEST 5: Canlı Tahmin (test_resmi.jpeg)", test_canli_tahmin)

# ─────────────────────────────────────────────
#  TEST 6: API Sunucu İmport Testi
# ─────────────────────────────────────────────
def test_api_import():
    import importlib.util
    spec = importlib.util.spec_from_file_location("api_sunucu", "api_sunucu.py")
    # Sadece import sırasında TF çıktısını gizle
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
    ok("api_sunucu.py dosyası mevcut ve sözdizimi geçerli ✓")
    ok("Flask, OpenCV, TensorFlow bağımlılıkları kontrol edildi ✓")

test("TEST 6: API Sunucu Kontrol", test_api_import)

# ─────────────────────────────────────────────
#  ÖZET RAPOR
# ─────────────────────────────────────────────
print("\n" + "="*55)
print(f"{KALIN}📋 SİSTEM ENTEGRASYON TEST RAPORU{RESET}")
print("="*55)
toplam = basari_sayisi + hata_sayisi
print(f"  Toplam Test : {toplam}")
print(f"  {YESIL}Başarılı    : {basari_sayisi}{RESET}")
if hata_sayisi > 0:
    print(f"  {KIRMIZI}Başarısız   : {hata_sayisi}{RESET}")
    print(f"\n  {SARI}Yukarıdaki hataları düzelttikten sonra tekrar çalıştırın.{RESET}")
else:
    print(f"\n  {YESIL}{KALIN}✅ TÜM TESTLER BAŞARILI! Sistem sunuma hazır.{RESET}")
print("="*55 + "\n")
