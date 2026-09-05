<div align="center">

![Hero Banner](docs/hero_banner.jpg)

# 🧠 Sensor & AI Based Smart Inventory Tracking System

### Autonomous Shelf Tracking — ESP32-S3 + OV5640 Camera + HX711 Load Cell + Deep Learning + Fuzzy Logic

> 🇹🇷 [Türkçe versiyon → README.md](README.md)

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)](https://python.org)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.16+-orange?logo=tensorflow&logoColor=white)](https://tensorflow.org)
[![Flask](https://img.shields.io/badge/Flask-REST_API-black?logo=flask)](https://flask.palletsprojects.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-green?logo=opencv)](https://opencv.org)
[![ESP32](https://img.shields.io/badge/ESP32--S3-Firmware-E7352C?logo=espressif)](https://espressif.com)
[![License](https://img.shields.io/badge/License-All_Rights_Reserved-red)](LICENSE)

</div>

---

## 🎯 Project Overview

A fully autonomous smart inventory tracking system that detects **which product was taken from a shelf — with zero human intervention** — tracks stock levels in real time, and delivers AI-powered reorder predictions through a premium live dashboard.

> 💡 **Current Prototype:** Proof-of-concept running on a mini smart fridge. The same system scales directly to supermarket cold drink aisles, shelf-based retail environments, and vending machines — no software or hardware changes required.

**Three integrated layers:**

```
[Hardware Layer]           [Server Layer]                 [Visualization]
ESP32-S3 + OV5640    →    Flask REST API          →    Streamlit Dashboard
HX711 Load Cell      →    CNN Image Analysis      →    Real-Time Stock View
Wi-Fi UDP Discovery  →    Fuzzy Logic Engine      →    AI Prediction Center
ORB Feature Matching →    OpenCV Slot Analysis    →    Live Operations Feed
```

---

## 🏪 Vision: From Prototype to Industrial Product

![Architecture Diagram](docs/architecture_diagram.jpg)

**This system is currently a mini fridge prototype.** But its architecture was intentionally designed to scale:

| Application | Required Change | Example |
|---|---|---|
| 🧊 Market Cold Drink Cabinet | Wider slot coordinates + multi-camera | Migros, Carrefour cold aisle |
| 🛒 Supermarket Shelf | Increase slot count (4 → 12+) | Dry goods, snack aisles |
| 🤖 Vending Machine | Optimize camera angle | AI-powered vending |
| 🏥 Hospital Kiosk | Change product catalog | Medical supply tracking |

> **The core advantage:** No human is needed to count shelves. The system operates 24/7 autonomously.

---

## 🧠 How It Works — Step by Step

### 1️⃣ Weight-Based Hardware Trigger
- The **HX711** load cell continuously measures shelf weight (5-sample moving average for noise reduction).
- A change of more than **85 grams** triggers the ESP32.
- Since a typical beverage can weighs **230–290 grams**, this threshold filters out small vibrations.

### 2️⃣ Smart Image Capture
- The ESP32-S3 captures using the **OV5640 camera** after **8 warm-up frames + 150ms delay** (VGA 640×480).
- This eliminates both hand-in-frame blur and sensor instability from the first frames.
- The image is sent via **HTTP POST over Wi-Fi** to the Python server.

### 3️⃣ Image Alignment (ORB Feature Matching)
- Pixel shift caused by cabinet door vibration is corrected using the **ORB algorithm**.
- A **homography matrix** is computed using the best 20% of feature matches.
- Without this step, slot detection would produce errors — the system handles this automatically.

### 4️⃣ Slot-Based Pixel Difference Analysis (OpenCV)
- The shelf is divided into **slots using calibrated pixel coordinates** (set via `piksel_bulucu.py`).
- Absolute pixel difference (`cv2.absdiff`) is computed between both frames.
- Any slot with more than **8% pixel change** is sent to AI analysis.

### 5️⃣ CNN Image Classification (The AI Brain)
- The changed slot is cropped from both before and after frames.
- Each crop is resized to **224×224 pixels** and fed into the CNN.
- The model classifies the product and returns a **confidence score (%)**.
- `Before FULL → After EMPTY`: Product **removed**
- `Before EMPTY → After FULL`: Product **added**

### 6️⃣ Scale-Based Cross Validation
- The number of events detected by AI is compared against the **product count inferred from HX711 weight change**.
- If inconsistent (e.g., AI says 2 items but scale says 1), the **lowest-confidence detection is discarded**.
- This sensor fusion mechanism dramatically reduces false positive rates.

### 7️⃣ Fuzzy Logic Decision System
- Stock level and consumption rate are evaluated using a **Mamdani-type fuzzy inference system**.
- A **12-rule base** generates a reorder urgency score (0–100).
- Expected usage intensity by time of day is factored in.

### 8️⃣ Reference Rotation & Data Logging
- After each successful detection, `after.jpg` is saved as the new `before.jpg`.
- Each new customer uses the previous customer's shelf state as the reference image.
- `sistem_durumu.json` is updated, and a timestamped record is appended to `satis_gecmisi.csv`.

---

## 🤖 AI Model — Technical Details

### CNN Architecture (5 Blocks)

```
Input: 224×224×3 (RGB image)
│
├── Block 1: Conv2D(32) → BatchNorm → MaxPool(2×2)
├── Block 2: Conv2D(64) → BatchNorm → MaxPool(2×2)
├── Block 3: Conv2D(128) → BatchNorm → MaxPool(2×2)
├── Block 4: Conv2D(256) → BatchNorm → MaxPool(2×2)
├── Block 5: Conv2D(256) → BatchNorm  ← Logo / texture detail extraction
│
├── GlobalAveragePooling2D
├── Dense(256) + L2 Regularization + Dropout(0.5)
├── Dense(128) + Dropout(0.3)
└── Dense(11) → Softmax  ← 11-class output
```

### Overfitting Prevention Strategy

| Technique | Application |
|---|---|
| **L2 Regularization** | All Conv2D and Dense layers (λ=1e-4) |
| **Dropout** | Rates of 0.5 and 0.3 across two layers |
| **BatchNormalization** | After every convolutional block |
| **Online Augmentation** | Each epoch, images appear differently |
| **EarlyStopping** | Monitoring val_accuracy, patience=15 |
| **ReduceLROnPlateau** | Adaptive learning rate reduction (factor=0.5) |
| **Stratified Split** | Equal proportion from each class (20% validation) |

### Dataset & Super Augmentation Pipeline

Original dataset: **Hand-captured product photos**
Total training set: **~4,400 images (11 categories × ~400 images)**

The `super_augment.py` pipeline generates **16 distinct realistic variants** per original photo:

| # | Technique | Purpose |
|---|---|---|
| 1 | Dark environment (f: 0.15–0.55) | Night / low-light conditions |
| 2 | Overexposed (f: 1.5–2.2) | Sunlight / overexposure |
| 3 | HSV hue & saturation shift | Different camera color profiles |
| 4 | Perspective distortion | Off-angle camera view |
| 5 | Motion blur (7–19px kernel) | Camera vibration |
| 6 | Gaussian blur (focus loss) | Depth of field variation |
| 7 | Sensor noise (ESP32 noise) | Low-quality CMOS sensor |
| 8 | Vignette (edge darkening) | Lens distortion |
| 9 | JPEG artifact (quality: 15–55) | Low-quality Wi-Fi transfer |
| 10 | Sharpening | Camera sharpness variation |
| 11 | Shadow stripe | Shelf shadow / lighting |
| 12 | Channel-based drift | RGB sensor drift |
| 13 | Rotation (-35° / +35°) | Camera angle deviation |
| 14 | Zoom + crop (8–25%) | Distance variation |
| 15 | Horizontal flip | Product orientation |
| 16 | Contrast extremes | HDR/SDR difference |

---

## 🧮 Fuzzy Logic Engine

`fuzzy_engine.py` — A **Mamdani-type FIS written from scratch**, no scikit-fuzzy dependency.

### Membership Functions

**Stock Level (Input 1):**
```
stock_critical  → trapmf(0.00, 0.00, 0.12, 0.28)
stock_low       → trimf (0.12, 0.28, 0.50)
stock_medium    → trimf (0.35, 0.55, 0.75)
stock_sufficient→ trapmf(0.60, 0.80, 1.00, 1.00)
```

**Consumption Rate (Input 2):**
```
rate_slow   → trapmf(0.0, 0.0, 0.30, 0.90)
rate_normal → trimf (0.5, 1.50, 3.00)
rate_fast   → trapmf(2.0, 3.50, 5.00, 5.00)
```

### 12-Rule Decision Table

| Stock \ Rate | SLOW | NORMAL | FAST |
|---|---|---|---|
| **CRITICAL** | MEDIUM ⚠️ | HIGH 🔴 | HIGH 🔴 |
| **LOW** | LOW ✅ | MEDIUM ⚠️ | HIGH 🔴 |
| **MEDIUM** | LOW ✅ | LOW ✅ | MEDIUM ⚠️ |
| **SUFFICIENT** | LOW ✅ | LOW ✅ | LOW ✅ |

**Output:** Reorder urgency score (0–100) via centroid defuzzification

### Additional Fuzzy Analyses

- **Door Intensity:** Compares real-time cabinet openings against expected hourly baseline
- **Sales Trend:** Calculates sales acceleration by comparing last 3 days vs. previous 4 days
- **Depletion Forecast:** Estimates product run-out date via `stock / hourly_consumption`
- **24-Hour Risk:** Calculates probability (0–100%) of depletion within 24 hours

---

## 📡 UDP Auto-Discovery — No Manual IP Required!

Traditional IoT systems require the device IP to be entered manually. Not here:

```
Python Server Side (every 3 seconds):
  "DOLAP_SERVER:192.168.x.x" → UDP Broadcast → 255.255.255.255:4210

ESP32 Side (continuously listening):
  Listens on UDP port 4210
  Receives "DOLAP_SERVER:..." packet
  Stores IP in memory
  Establishes HTTP connection to that IP
```

**Result:** Power on the ESP32, start the Python server — the system finds itself automatically.

---

## 📊 Streamlit Dashboard — Features

The dashboard has four pages and two UI modes (📱 Mobile / 💻 Web):

### ✦ Main Dashboard
- **Door Access Counter** — Hourly intensity area chart
- **Live Stock Grid** — Per-product SVG icons, grayscale if stock is zero
- **Reorder List** — Prioritized by fuzzy urgency score
- **Top Seller** — Horizontal Plotly bar chart

### ❖ Smart Predictions (Fuzzy Logic Center)
- Door intensity fuzzy analysis with explanation
- Sales trend fuzzy analysis with acceleration metric
- Fuzzy reorder priorities and stock summaries
- **Refill recommendation** — URGENT / PARTIAL / OPTIMAL based on capacity gap
- **Stock depletion forecast table** — Estimated run-out date + 24h risk per product
- **Mamdani Rule Engine Visualization** — Which rules fired and at what strength (bar chart + pie)

### ⚲ Live Operations
- Detailed card of the latest detection (product, slot, weight, confidence, timestamp)
- Full historical operations feed (color-coded: red=removed, green=added)

### ⌘ Camera & Vision
- Before/after camera images side by side
- Each AI-cropped slot (Slot 1, 2, 3) rendered as individual cards

### Sidebar Features
- 🇹🇷 / 🇬🇧 Language toggle (all text updates instantly)
- Time filter: All Time / Last 7 Days / Today
- Auto-refresh toggle (2-second interval)
- **Hardware Status:** Camera (ESP32), Load Cell, Database API live indicator
- **Full Reset button** — Clears all data via API call
- **CSV Download** — Export fuzzy score report

---

## 🔧 Hardware Requirements

| Component | Model | Qty | Notes |
|---|---|---|---|
| Microcontroller | ESP32-S3 | 1 | Built-in Wi-Fi + Bluetooth |
| Camera | OV5640 (5MP, VGA 640×480) | 1 | Custom PCB pinout |
| Load Cell Amplifier | HX711 | 1 | 24-bit ADC, 10 Hz sampling |
| Load Cell | 1–5 kg | 1 | Based on shelf capacity |
| Voltage Regulator | AMS1117 3.3V | 1 | ESP32-S3 power supply |
| PCB | Custom / Ready-made | 1 | Camera + ESP32 integration |
| Jumper Wire Set | — | — | Sensor connections |

### ESP32-S3 PCB Pin Map (OV5640)

```
OV5640 Camera Pins:
PWDN  → GPIO 21    RESET → GPIO 18    XCLK → GPIO 10
SIOD  → GPIO 40    SIOC  → GPIO 39    VSYNC → GPIO 6
HREF  → GPIO 7     PCLK  → GPIO 13

D0 → GPIO 11   D1 → GPIO 9    D2 → GPIO 8    D3 → GPIO 12
D4 → GPIO 17   D5 → GPIO 16   D6 → GPIO 15   D7 → GPIO 14

HX711 DOUT → GPIO 40    HX711 SCK → GPIO 41
AMS1117 3.3V → ESP32-S3 3.3V power rail
```

---

## 💻 Installation

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/batuhan-kurt/Inventory-Tracking-System.git
cd Inventory-Tracking-System

python3.11 -m venv ai_ortami
source ai_ortami/bin/activate  # Windows: ai_ortami\Scripts\activate

pip install -r requirements.txt
```

### 2. Flash ESP32 Firmware

Open `ESP32_Akilli_Dolap_FINAL/ESP32_Akilli_Dolap_FINAL.ino` in Arduino IDE.

Required libraries (Arduino Library Manager):
- `HX711_ADC` (Olav Kallhovd)
- `ESP32 Board Package` (Espressif Systems)

Update Wi-Fi credentials:
```cpp
const char *ssid     = "YOUR_WIFI_NAME";
const char *password = "YOUR_WIFI_PASSWORD";
// No need to enter IP — UDP Auto-Discovery handles it automatically.
```

### 3. Calibrate Slot Coordinates

```bash
python piksel_bulucu.py
```

Click on the top-left and bottom-right corners of each product slot in the image. Paste the resulting coordinates into the `RAFLAR` dictionary in `api_sunucu.py`.

### 4. Start the System

```bash
# Terminal 1: API Server (ESP32 connects here)
python api_sunucu.py

# Terminal 2: Dashboard
streamlit run dashboard.py
```

### 5. Power On ESP32

It connects to Wi-Fi → discovers Python server via UDP → captures first reference frame → system is ready.

---

## 🤖 Model Training

### Full Pipeline

```bash
# 1. Place product photos in dataset/ with one folder per product:
#    dataset/CocaCola_Klasik/   dataset/Fanta/  ... 

# 2. Super augmentation — generate 16 variants per photo
python super_augment.py   # → creates dataset_dengeli/

# 3. Convert to NumPy arrays
python veri_hazirla.py    # → X_verileri.npy, Y_etiketler.npy

# 4. Train CNN (50 epochs max, early stopping at ~20-30)
python beyin_egit.py      # → akilli_dolap_beyni.keras

# 5. Batch accuracy test
python tahmin_yap_toplu.py
```

---

## 📊 Supported Product Categories

| Category | Product |
|---|---|
| `CocaCola_Klasik` | Coca-Cola Classic |
| `CocaCola_Zero` | Coca-Cola Zero |
| `Pepsi` | Pepsi |
| `Fanta` | Fanta |
| `RedBull_Klasik` | Red Bull Classic |
| `RedBull_White` | Red Bull White Edition |
| `RedBull_Blue` | Red Bull Blue Edition |
| `RedBull_Lilac` | Red Bull Lilac Edition |
| `RedBull_Pembe` | Red Bull Pink/Summer Edition |
| `Nescafe_Klasik` | Nescafé Cold Coffee |
| `Bos_Raf` | Empty shelf detection |

> To add a new product: place photos in `dataset/NEW_PRODUCT/` and re-run the pipeline.

---

## 📁 Project Structure

```
Inventory-Tracking-System/
│
├── 📡 FIRMWARE
│   ├── ESP32_Akilli_Dolap_FINAL.ino   # Main firmware (OV5640 + HX711 + UDP Auto-Discovery)
│   └── legacy/
│       ├── esp32_hx711_main.cpp       # Old ESP32 firmware (archived)
│       ├── veri_denge.py              # Old basic augmentation (replaced by super_augment.py)
│       ├── tam_otonom_dolap.py        # Standalone engine (integrated into api_sunucu.py)
│       ├── tahmin_yap.py              # Single image test tool (archived)
│       └── tahmin_yap_toplu.py        # Batch test tool (archived)
│
├── 🧠 AI & MODEL
│   ├── beyin_egit.py          # 5-block CNN training (online augmentation)
│   ├── super_augment.py       # 16-technique data augmentation pipeline
│   └── veri_hazirla.py        # Dataset → NumPy converter
│
├── 🖥️ BACKEND
│   ├── api_sunucu.py          # Flask API (UDP broadcast + slot analysis + ORB alignment)
│   ├── fuzzy_engine.py        # Mamdani FIS (written from scratch, 12 rules)
│   └── piksel_bulucu.py       # Interactive slot calibration tool
│
├── 📊 DASHBOARD
│   └── dashboard.py           # 1118-line Streamlit premium UI
│
├── 📂 DATA
│   ├── data/urun_katalogu.json     # Product metadata + price + reorder threshold
│   ├── data/sistem_durumu.json     # Live stock status
│   └── data/satis_gecmisi.csv      # Timestamped sales history
│
├── 📚 DOCS
│   ├── docs/BOM.xlsx          # Bill of Materials
│   ├── docs/hero_banner.jpg   # Vision image
│   └── docs/architecture_diagram.jpg  # System architecture
│
└── requirements.txt           # Python dependencies (Python 3.11)
```

---

## 🚀 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/tetikle` | Receive photo + weight from ESP32, run analysis |
| `POST` | `/sifirla` | Delete reference photo (cabinet refilled) |
| `POST` | `/tam_sifirla` | Full reset: stock, CSV, all photos |
| `GET` | `/durum` | Current system status JSON |

---

## 🛠️ Tech Stack

**Hardware:**
`ESP32-S3` · `OV5640 5MP Camera` · `HX711 24-bit ADC` · `Load Cell 1-5kg` · `Wi-Fi 802.11 b/g/n`

**AI / ML:**
`TensorFlow 2.16+` · `Keras` · `Custom CNN (5-block)` · `OpenCV 4.8+` · `NumPy` · `scikit-learn`

**Backend:**
`Flask` · `UDP Broadcast` · `ORB Feature Matching` · `Mamdani FIS (custom)`

**Dashboard:**
`Streamlit` · `Plotly` · `Pandas` · `SVG Icons (custom)` · `Glassmorphism UI`

**Data:**
`JSON` · `CSV` · `NumPy .npy`

---

## 📝 License

**© 2026 Batuhan Kurt — All Rights Reserved.**

This project and its source code are protected under copyright law.  
It may be viewed for personal study and educational purposes only.  
**Commercial use, copying, redistribution, or modification without explicit permission is strictly prohibited.**  
For collaboration or licensing inquiries, please get in touch.

---

<div align="center">

**Batuhan Kurt** — Sensor & AI Based Smart Inventory Tracking System  
*ESP32-S3 + Deep Learning + Fuzzy Logic + IoT*  
🔗 [github.com/batuhan-kurt](https://github.com/batuhan-kurt)

</div>
