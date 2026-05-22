# 🛒 Sensor & AI Based Inventory Tracking System
### Autonomous Smart Cabinet Inventory Management with ESP32-S3 Camera + HX711 Load Cell + Deep Learning

> 🇹🇷 [Türkçe versiyon → README.md](README.md)

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-orange?logo=tensorflow)](https://tensorflow.org)
[![Flask](https://img.shields.io/badge/Flask-API-green?logo=flask)](https://flask.palletsprojects.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red?logo=streamlit)](https://streamlit.io)
[![ESP32](https://img.shields.io/badge/ESP32--S3-Firmware-lightgrey?logo=espressif)](https://espressif.com)

---

## 📌 Project Overview

A fully autonomous smart inventory tracking system that detects **which product was taken from a shelf — without any human intervention** — tracks stock levels in real time, and displays everything on a live dashboard.

The system is built on three integrated layers:

```
[Hardware Layer]           [Server Layer]              [Visualization]
HX711 Load Cell     →    Flask API Server      →    Streamlit Dashboard
ESP32-S3 Camera     →    CNN Image Analysis    →    Live Stock Tracking
Wi-Fi Communication →    JSON + CSV Database   →    Sales History
```

---

## 🧠 How It Works

### 1️⃣ Weight-Based Triggering
- The **HX711** load cell continuously measures the shelf weight.
- When a change of more than **50 grams** is detected, the ESP32 activates.

### 2️⃣ Image Capture
- The ESP32-S3 camera waits **2 seconds** for stabilization before capturing.
- This prevents motion blur caused by the customer's hand movement.

### 3️⃣ AI Analysis (Slot-Based)
- The shelf is divided into **4 slots** (coordinates calibrated using `piksel_bulucu.py`).
- `tam_otonom_dolap.py` computes the **pixel difference** between two consecutive images.
- The slot with the highest change is identified as the target.
- The product in that slot is queried from the **CNN model** → product name is determined.

### 4️⃣ Reference Update
- After each successful sale, `after.jpg` is saved as the new `before.jpg`.
- Each subsequent customer uses the previous customer's shelf state as the reference image.

### 5️⃣ Data Recording & Dashboard
- `sistem_durumu.json` is updated with the new stock count.
- `satis_gecmisi.csv` receives a new timestamped sales record.
- The Streamlit dashboard refreshes automatically.

---

## 🔧 Hardware Requirements

| Component | Model | Quantity |
|---|---|---|
| Microcontroller + Camera | ESP32-S3 (with camera module) | 1 |
| Load Cell Amplifier | HX711 | 1 |
| Load Cell | 1–5 kg (based on shelf weight) | 1 |

### Pin Configuration (ESP32-S3)

```
HX711 DOUT → GPIO 4
HX711 SCK  → GPIO 5
Camera     → Built-in (ESP32-S3 WROVER)
```

> **Note:** Camera pin definitions in `esp32_hx711_main.cpp` may need to be adjusted depending on your specific ESP32-S3 board model.

---

## 💻 Installation

### 1. Set Up Python Environment

```bash
git clone https://github.com/batuhan-kurt/Inventory-Tracking-System.git
cd Inventory-Tracking-System

python3.11 -m venv ai_ortami
source ai_ortami/bin/activate  # Windows: ai_ortami\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure Wi-Fi Settings

Edit the following lines in `esp32_hx711_main.cpp`:

```cpp
const char* ssid      = "YOUR_WIFI_NAME";
const char* password  = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://YOUR_COMPUTER_IP:5001/tetikle";
```

> To find your computer's IP: `ifconfig` (Mac/Linux) or `ipconfig` (Windows)

### 3. Calibrate Slot Coordinates

```bash
python piksel_bulucu.py
```

Click on the top-left and bottom-right corner of each shelf slot in the image. Paste the resulting coordinates into the `RAFLAR` dictionary inside both `tam_otonom_dolap.py` and `api_sunucu.py`.

### 4. Start the System

```bash
# Terminal 1: API Server
python api_sunucu.py

# Terminal 2: Dashboard
streamlit run dashboard.py
```

### 5. Flash ESP32 Firmware

Upload `esp32_hx711_main.cpp` to the ESP32-S3 using Arduino IDE or PlatformIO.

---

## 🤖 Model Training

### Dataset Preparation

```bash
# Place product photos in separate folders inside dataset/:
# dataset/CocaCola_Klasik/
# dataset/Fanta/
# ...

# Balance the dataset
python veri_denge.py

# Apply advanced data augmentation
python super_augment.py
```

### Train the Model

```bash
python beyin_egit.py
```

### Batch Testing

```bash
python tahmin_yap_toplu.py
```

---

## 📊 Supported Product Categories

| Category | Description |
|---|---|
| `CocaCola_Klasik` | Coca-Cola Classic (can/bottle) |
| `CocaCola_Zero` | Coca-Cola Zero (can/bottle) |
| `Pepsi` | Pepsi (can/bottle) |
| `Fanta` | Fanta (can/bottle) |
| `RedBull_Klasik` | Red Bull Classic |
| `RedBull_White` | Red Bull White Edition |
| `RedBull_Blue` | Red Bull Blue Edition |
| `RedBull_Lilac` | Red Bull Lilac Edition |
| `RedBull_Pembe` | Red Bull Pink Edition |
| `Nescafe_Klasik` | Nescafé Instant Coffee |
| `Bos_Raf` | Empty shelf detection |

> The system can be extended to support any product category by adding training images.

---

## 📁 Project Structure

```
Inventory-Tracking-System/
├── api_sunucu.py          # Flask API — receives and processes ESP32 signals
├── dashboard.py           # Streamlit live monitoring panel
├── tam_otonom_dolap.py    # Slot-based image comparison engine
├── piksel_bulucu.py       # Interactive slot coordinate calibration tool
├── beyin_egit.py          # CNN model training
├── super_augment.py       # Advanced data augmentation pipeline
├── veri_denge.py          # Dataset balancing
├── tahmin_yap.py          # Single image prediction tool
├── tahmin_yap_toplu.py    # Batch image prediction tool
├── esp32_hx711_main.cpp   # ESP32-S3 + HX711 firmware (Arduino/PlatformIO)
├── urun_katalogu.json     # Product metadata and critical stock thresholds
├── sistem_durumu.json     # Live stock status database
├── satis_gecmisi.csv      # Sales history log
└── requirements.txt       # Python dependencies
```

---

## 🚀 System Flow

```
ESP32 Powers On
    │
    ├─→ POST /sifirla  (clears old reference image)
    └─→ POST /tetikle  (captures and sends initial reference photo)
              │
              ▼
        dolap_oncesi.jpg created (reference established)

Customer takes a product
    │
    ├─ HX711: Weight drop > 50g detected
    ├─ Wait 2 seconds (stabilization)
    ├─ Capture photo
    └─→ POST /tetikle  (photo + weight delta in header)
              │
              ▼
        slot_bazli_analiz()
              │
              ├─ Which slot changed? (pixel difference map)
              ├─ What product is in that slot? (CNN inference)
              ├─ Update JSON stock count
              ├─ Append CSV sales record
              └─ after.jpg → before.jpg (reference rotated for next customer)
```

---

## 📸 Dashboard Features

The Streamlit dashboard provides:
- 📦 Real-time stock levels (per product)
- 🚪 Cabinet access count
- 🛒 Items needing reorder (critical stock alerts)
- 🏆 Best-selling product analytics
- 📡 Latest camera capture (sidebar)
- 🔴 Live transaction ticker

Language support: 🇹🇷 Turkish / 🇬🇧 English

---

## 📝 License

**© 2026 Batuhan Kurt — All Rights Reserved.**

This project and its source code are protected under copyright law.
It may be viewed for personal study and educational purposes only.
**Commercial use, copying, redistribution, or modification without explicit permission is strictly prohibited.**
For collaboration or licensing inquiries, please get in touch.

---

## 👤 Developer

**Batuhan Kurt** — Sensor & AI Based Inventory Tracking System  
*ESP32-S3 + Deep Learning + IoT Integration*  
🔗 [github.com/batuhan-kurt](https://github.com/batuhan-kurt)
