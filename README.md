# 🛒 Sensor & AI Based Inventory Tracking System
### ESP32-S3 Kamera + HX711 Yük Hücresi + Derin Öğrenme ile Akıllı Dolap Envanter Takibi

> 🇬🇧 [English version → README_EN.md](README_EN.md)

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-orange?logo=tensorflow)](https://tensorflow.org)
[![Flask](https://img.shields.io/badge/Flask-API-green?logo=flask)](https://flask.palletsprojects.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red?logo=streamlit)](https://streamlit.io)
[![ESP32](https://img.shields.io/badge/ESP32--S3-Firmware-lightgrey?logo=espressif)](https://espressif.com)

---

## 📌 Proje Özeti

Bu proje; bir raf/dolap sisteminde **kimse müdahale etmeden** hangi ürünün alındığını otomatik olarak tespit eden, stok takibi yapan ve canlı dashboard üzerinden izlenen tam entegre bir akıllı envanter sistemidir.

Sistem üç katmandan oluşur:

```
[Donanım Katmanı]         [Sunucu Katmanı]         [Görselleştirme]
HX711 Yük Hücresi   →    Flask API Sunucusu   →    Streamlit Dashboard
ESP32-S3 Kamera     →    CNN Görüntü Analizi  →    Canlı Stok Takibi
Wi-Fi İletişimi     →    JSON + CSV Veritabanı →   Satış Geçmişi
```

---

## 🧠 Nasıl Çalışır?

### 1️⃣ Ağırlık Tabanlı Tetikleme
- **HX711** yük hücresi, rafın ağırlığını sürekli ölçer.
- **50 gramdan** fazla değişim tespit edildiğinde ESP32 harekete geçer.

### 2️⃣ Görüntü Yakalama
- ESP32-S3 kamerası **2 saniye stabilizasyon** sonrası fotoğraf çeker.
- (Hareket bulanıklığını önlemek için müşteri elini çektikten sonra)

### 3️⃣ Yapay Zeka Analizi (Slot-Bazlı)
- Raf **4 slota** bölünmüştür (koordinatlar `piksel_bulucu.py` ile kalibrate edilir).
- `tam_otonom_dolap.py` iki fotoğraf arasındaki **piksel farkını** hesaplar.
- En fazla değişim gösteren slot tespit edilir.
- O slottaki ürün **CNN modeline** sorulur → Ürün adı belirlenir.

### 4️⃣ Referans Güncelleme
- Her başarılı satış sonrası `sonrasi.jpg` → `oncesi.jpg` olarak kaydedilir.
- Böylece her yeni müşteri, bir öncekinin bıraktığı görüntüyü referans alır.

### 5️⃣ Veri Kaydı ve Dashboard
- `sistem_durumu.json` stok güncellenir.
- `satis_gecmisi.csv` satış kaydı eklenir.
- Streamlit dashboard canlı olarak yenilenir.

---

## 🔧 Donanım Gereksinimleri

| Bileşen | Model | Adet |
|---|---|---|
| Mikrodenetleyici + Kamera | ESP32-S3 (kameralı) | 1 |
| Yük Hücresi Amplifikatörü | HX711 | 1 |
| Yük Hücresi | 1-5 kg (raf ağırlığına göre) | 1 |

### Pin Bağlantısı (ESP32-S3)

```
HX711 DOUT → GPIO 4
HX711 SCK  → GPIO 5
Kamera     → Dahili (ESP32-S3 WROVER)
```

> **Not:** `esp32_hx711_main.cpp` içindeki kamera pin ayarlarını kendi ESP32-S3 modeline göre güncellemen gerekebilir.

---

## 💻 Kurulum

### 1. Python Ortamını Kur

```bash
git clone https://github.com/batuhan-kurt/Inventory-Tracking-System.git
cd Inventory-Tracking-System

python3.11 -m venv ai_ortami
source ai_ortami/bin/activate  # Windows: ai_ortami\Scripts\activate

pip install -r requirements.txt
```

### 2. Wi-Fi Ayarlarını Güncelle

`esp32_hx711_main.cpp` içindeki şu satırları düzenle:

```cpp
const char* ssid     = "WIFI_ADINIZ";
const char* password = "WIFI_SIFRENIZ";
const char* serverUrl = "http://BILGISAYAR_IP:5001/tetikle";
```

> Bilgisayar IP'ni öğrenmek için: `ifconfig` (Mac/Linux) veya `ipconfig` (Windows)

### 3. Slot Koordinatlarını Kalibre Et

```bash
python piksel_bulucu.py
```

Fotoğraf üzerinde her slotun sol-üst ve sağ-alt köşesine tıkla. Çıkan koordinatları `tam_otonom_dolap.py` ve `api_sunucu.py` içindeki `RAFLAR` sözlüğüne yapıştır.

### 4. Sistemi Başlat

```bash
# Terminal 1: API Sunucusu
python api_sunucu.py

# Terminal 2: Dashboard
streamlit run dashboard.py
```

### 5. ESP32 Firmware'ini Yükle

Arduino IDE veya PlatformIO ile `esp32_hx711_main.cpp` dosyasını ESP32-S3'e yükle.

---

## 🤖 Model Eğitimi

### Veri Seti Hazırlama

```bash
# Fotoğrafları dataset/ klasörüne her ürün için ayrı klasörlere koy:
# dataset/CocaCola_Klasik/
# dataset/Fanta/
# ...

# Veriyi dengele
python veri_denge.py

# Gelişmiş veri artırımı (süper augmentasyon)
python super_augment.py
```

### Modeli Eğit

```bash
python beyin_egit.py
```

### Toplu Test

```bash
python tahmin_yap_toplu.py
```

---

## 📊 Desteklenen Ürün Kategorileri

| Kategori | Açıklama |
|---|---|
| `CocaCola_Klasik` | Coca-Cola klasik kutu/şişe |
| `CocaCola_Zero` | Coca-Cola Zero kutu/şişe |
| `Pepsi` | Pepsi kutu/şişe |
| `Fanta` | Fanta kutu/şişe |
| `RedBull_Klasik` | Red Bull klasik |
| `RedBull_White` | Red Bull White Edition |
| `RedBull_Blue` | Red Bull Blue Edition |
| `RedBull_Lilac` | Red Bull Lilac Edition |
| `RedBull_Pembe` | Red Bull Pink Edition |
| `Nescafe_Klasik` | Nescafé hazır kahve |
| `Bos_Raf` | Boş raf tespiti |

---

## 📁 Proje Yapısı

```
Inventory-Tracking-System/
├── api_sunucu.py          # Flask API — ESP32'den gelen sinyalleri işler
├── dashboard.py           # Streamlit canlı izleme paneli
├── tam_otonom_dolap.py    # Slot-bazlı görüntü karşılaştırma motoru
├── piksel_bulucu.py       # Interaktif slot koordinat kalibrasyon aracı
├── beyin_egit.py          # CNN model eğitimi
├── super_augment.py       # Gelişmiş veri artırımı pipeline'ı
├── veri_denge.py          # Dataset dengeleme
├── tahmin_yap.py          # Tekil görüntü tahmin aracı
├── tahmin_yap_toplu.py    # Toplu görüntü tahmin aracı
├── esp32_hx711_main.cpp   # ESP32-S3 + HX711 firmware (Arduino/PlatformIO)
├── urun_katalogu.json     # Ürün metadata ve kritik stok eşikleri
├── sistem_durumu.json     # Canlı stok durumu
├── satis_gecmisi.csv      # Satış geçmişi veritabanı
└── requirements.txt       # Python bağımlılıkları
```

---

## 🚀 Sistem Akışı

```
ESP32 Açılır
    │
    ├─→ /sifirla (Eski referans temizlenir)
    └─→ /tetikle (Başlangıç referans fotoğrafı)
              │
              ▼
        dolap_oncesi.jpg oluşur
        
Müşteri ürün alır
    │
    ├─ HX711: Ağırlık düşüşü > 50g
    ├─ 2 sn bekle (stabilizasyon)
    ├─ Fotoğraf çek
    └─→ /tetikle (fotoğraf + ağırlık değişimi)
              │
              ▼
        slot_bazli_analiz()
              │
              ├─ Hangi slotta değişim? (piksel farkı)
              ├─ O slottaki ürün ne? (CNN)
              ├─ JSON stok güncelle
              ├─ CSV satış kaydı
              └─ dolap_sonrasi → dolap_oncesi (döngü)
```

---

## 📸 Dashboard

Streamlit dashboard şunları gösterir:
- 📦 Anlık stok durumu (ürün bazında)
- 🚪 Dolap açılma sayısı
- 🛒 Sipariş gereken ürünler (kritik stok uyarısı)  
- 🏆 En çok satılan ürün analizi
- 📡 Son kamera görüntüsü (sidebar)
- 🔴 Canlı işlem akışı (ticker)

Dil seçeneği: 🇹🇷 Türkçe / 🇬🇧 English

---

## 📝 Lisans

**© 2026 Batuhan Kurt — Tüm Haklar Saklıdır.**

Bu proje ve içindeki kaynak kodlar, telif hakkı yasaları kapsamında korunmaktadır.  
Kişisel inceleme ve eğitim amaçlı görüntülenebilir; ancak **izin alınmadan ticari amaçla kullanılamaz, kopyalanamaz, dağıtılamaz veya değiştirilemez.**  
İşbirliği ve lisanslama talepleri için iletişime geçin.

---

## 👤 Geliştirici

**Batuhan Kurt** — Akıllı Envanter Takip Sistemi  
*ESP32-S3 + Derin Öğrenme + IoT Entegrasyonu*  
🔗 [github.com/batuhan-kurt](https://github.com/batuhan-kurt)
