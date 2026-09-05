/*
  ╔══════════════════════════════════════════════════════════════════╗
  ║        AKILLI DOLAP — ESP32-S3 ANA KOD (FINAL)                  ║
  ║  HX711 Ağırlık Sensörü + OV5640 Kamera + WiFi + FastAPI         ║
  ╠══════════════════════════════════════════════════════════════════╣
  ║  Gerekli Kütüphaneler (Arduino IDE > Library Manager'dan kur):  ║
  ║    1. HX711_ADC  (Olav Kallhovd)                                 ║
  ║    2. ESP32 Board Package (Espressif Systems)                    ║
  ╚══════════════════════════════════════════════════════════════════╝
*/

#include "esp_camera.h"
#include <EEPROM.h>
#include <HTTPClient.h>
#include <HX711_ADC.h>
#include <WiFi.h>
#include <WiFiUDP.h>

// ==========================================
// WiFi AYARLARI
// ==========================================
const char *ssid     = "TECNO SPARK Go 2024";     // Hotspot WiFi
const char *password = "11111111";               // Hotspot WiFi şifresi

// ==========================================
// PYTHON SUNUCU — OTOMATİK KEŞFEDILIR
// IP'yi elle yazmana gerek yok!
// api_sunucu.py her 3 saniyede IP'sini yayınlar,
// ESP32 onu dinleyip otomatik bulur.
// ==========================================
const int PYTHON_PORT      = 5001;
const int UDP_DINLE_PORT   = 4210;     // ESP32'nin dinlediği UDP portu
String    PYTHON_IP        = "";       // Otomatik doldurulacak
WiFiUDP   udp;

// ==========================================
// OV5640 KAMERA PIN AYARLARI
// (kamera_v2.txt'den alınan doğru pinler — PCB'ye göre)
// ==========================================
#define PWDN_GPIO_NUM 21
#define RESET_GPIO_NUM 14
#define XCLK_GPIO_NUM 15
#define SIOD_GPIO_NUM 4
#define SIOC_GPIO_NUM 5
#define Y9_GPIO_NUM 16
#define Y8_GPIO_NUM 17
#define Y7_GPIO_NUM 18
#define Y6_GPIO_NUM 12
#define Y5_GPIO_NUM 10
#define Y4_GPIO_NUM 8
#define Y3_GPIO_NUM 9
#define Y2_GPIO_NUM 11
#define VSYNC_GPIO_NUM 6
#define HREF_GPIO_NUM 7
#define PCLK_GPIO_NUM 13

// ==========================================
// HX711 PIN AYARLARI
// (WIFI_Tartı.txt'den alınan doğru pinler)
// ==========================================
const int HX711_DOUT = 40;
const int HX711_SCK = 41;

// ==========================================
// AĞIRLIK SENSÖRÜ AYARLARI
// ==========================================
HX711_ADC LoadCell(HX711_DOUT, HX711_SCK);
const int CALVAL_EEPROM_ADDR = 0;
const float AGIRLIK_ESIK_DEGERI = 85.0; // 85 gram değişimde tetikle
const int ORTALAMA_ORNEK_SAYISI =
    5; // Gürültüyü azaltmak için 5 örnekle ortalama

float onceki_agirlik = 0.0;
float weightBuffer[ORTALAMA_ORNEK_SAYISI];
int sampleIndex = 0;
float avgWeight = 0.0;
bool ortalamaHazir = false;

// ==========================================
// ZAMANLAMA
// ==========================================
unsigned long sonTetikZamani = 0;
const unsigned long DEBOUNCE_MS = 15000; // 15 saniye — hayalet tetiklemeyi önler

// ─────────────────────────────────────────
// YARDIMCI: Python URL oluştur
// ─────────────────────────────────────────
String pythonUrl(const char *endpoint) {
  return String("http://") + PYTHON_IP + ":" + PYTHON_PORT + endpoint;
}

// ─────────────────────────────────────────
// SUNUCU KEŞFI: UDP Yayını Dinle
// Python sunucusu "DOLAP_SERVER:IP" formatında
// UDP yayını yapar. Biz onu yakalayıp IP'yi alırız.
// ─────────────────────────────────────────
bool sunucuBul(int beklemeSaniye = 30) {
  udp.begin(UDP_DINLE_PORT);
  Serial.printf("\n🔍 Python sunucusu aranıyor (%d sn)...", beklemeSaniye);

  unsigned long baslangic = millis();
  char paket[64];

  while (millis() - baslangic < (unsigned long)beklemeSaniye * 1000) {
    int boyut = udp.parsePacket();
    if (boyut > 0) {
      udp.read(paket, sizeof(paket) - 1);
      paket[boyut] = '\0';
      String mesaj = String(paket);

      // Paket formatı: "DOLAP_SERVER:192.168.x.x"
      if (mesaj.startsWith("DOLAP_SERVER:")) {
        PYTHON_IP = mesaj.substring(13); // "DOLAP_SERVER:" → 13 karakter
        PYTHON_IP.trim();
        Serial.printf("\n✅ Sunucu bulundu! IP: %s\n", PYTHON_IP.c_str());
        udp.stop();
        return true;
      }
    }
    delay(200);
    Serial.print(".");
  }

  udp.stop();
  Serial.println("\n❌ Sunucu bulunamadı! api_sunucu.py çalışıyor mu?");
  return false;
}

// ─────────────────────────────────────────
// KAMERA KURULUMU
// ─────────────────────────────────────────
bool kameraBaslat() {
  // ─── USB Güç Dalgalanması İçin Hard Reset Sekansı ───
  // USB bağlıyken I2C probe timeout hatasını önler.
  // PWDN: HIGH → kamera uyu, LOW → kamera uyan
  // RESET: LOW → zorla sıfırla, HIGH → çalıştır
  Serial.println("   🔄 Kamera donanım sıfırlaması...");
  pinMode(PWDN_GPIO_NUM,  OUTPUT);
  pinMode(RESET_GPIO_NUM, OUTPUT);

  digitalWrite(PWDN_GPIO_NUM,  HIGH); // Kamerayı kapat
  digitalWrite(RESET_GPIO_NUM, LOW);  // Reset'e al
  delay(200);
  digitalWrite(PWDN_GPIO_NUM,  LOW);  // Kamerayı aç
  delay(100);
  digitalWrite(RESET_GPIO_NUM, HIGH); // Reset'i bırak
  delay(300);  // Sensörün I2C'ye hazır olmasını bekle

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;

  // ─── Kararlılık Ayarları (kamera_v2.txt'den alındı) ───
  // 16 MHz: Donma ve kararmayı önler (20 MHz yerine)
  config.xclk_freq_hz = 16000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA; // 640x480
  config.jpeg_quality = 12;
  config.fb_count = 2; // 2 buffer → kararmayı önler
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.grab_mode = CAMERA_GRAB_LATEST; // Her zaman en güncel kareyi al

  // ─── 3 Deneme Hakkı (USB güç dalgalanmasına karşı) ───
  esp_err_t err = ESP_FAIL;
  for (int deneme = 1; deneme <= 3; deneme++) {
    err = esp_camera_init(&config);
    if (err == ESP_OK) break;
    Serial.printf("   ⚠️  Deneme %d/3 başarısız (0x%x), 1sn bekleniyor...\n", deneme, err);
    esp_camera_deinit(); // Temizle, tekrar dene
    delay(1000);
    // Her denemede reset tekrar at
    digitalWrite(PWDN_GPIO_NUM,  HIGH);
    delay(100);
    digitalWrite(PWDN_GPIO_NUM,  LOW);
    delay(300);
  }

  if (err != ESP_OK) {
    Serial.printf("❌ Kamera başlatılamadı! Hata: 0x%x\n", err);
    return false;
  }

  // Görüntü iyileştirme
  sensor_t *s = esp_camera_sensor_get();
  if (s != NULL) {
    s->set_vflip(s, 1);   // Dikey çevirme
    s->set_hmirror(s, 0); // Yatay aynalama (gerekirse 1 yap)
    s->set_brightness(s, 1);
    s->set_saturation(s, 0);
  }

  Serial.println("✅ Kamera Kuruldu!");
  return true;
}

// ─────────────────────────────────────────
// FOTO ÇEK VE PYTHON'A GÖNDER
// ─────────────────────────────────────────
void fotografCekVeGonder(float agirlikFarki) {
  Serial.println("\n📸 Fotoğraf çekiliyor...");

  // Isınma kareleri — kamera sensörünün kararlı hale gelmesini bekle
  // 8 kare + 150ms: bulanıklık ve paraziti önler
  for (int i = 0; i < 8; i++) {
    camera_fb_t *warmup = esp_camera_fb_get();
    if (warmup)
      esp_camera_fb_return(warmup);
    delay(150);
  }
  delay(300); // Son bir bekleme — sensör tam oturuncaya kadar

  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("❌ Fotoğraf çekilemedi!");
    return;
  }

  Serial.printf("✅ Fotoğraf boyutu: %d byte\n", fb->len);
  Serial.println("🌐 Python sunucusuna gönderiliyor...");

  HTTPClient http;
  http.begin(pythonUrl("/tetikle"));
  http.addHeader("Content-Type", "image/jpeg");
  http.addHeader("X-Agirlik-Degisimi", String(agirlikFarki));
  http.setTimeout(15000); // 15 sn timeout

  int httpCode = http.POST(fb->buf, fb->len);

  if (httpCode > 0) {
    Serial.printf("✅ Sunucu yanıtı: %d\n", httpCode);
    Serial.println("Python diyor ki: " + http.getString());
  } else {
    Serial.printf("❌ Bağlantı hatası: %s\n",
                  http.errorToString(httpCode).c_str());
    Serial.println("→ Kontrol et: api_sunucu.py çalışıyor mu? IP doğru mu?");
  }

  http.end();
  esp_camera_fb_return(fb);
}

// ─────────────────────────────────────────
// REFERANS FOTOĞRAFI (Sistem İlk Açıldığında)
// ─────────────────────────────────────────
void referansFotoGonder() {
  Serial.println("\n📸 Referans fotoğrafı gönderiliyor...");

  // Önce Python'a "sıfırla" sinyali gönder (eski referansı temizle)
  HTTPClient http_reset;
  http_reset.begin(pythonUrl("/sifirla"));
  http_reset.POST("");
  http_reset.end();
  delay(500);

  // Sonra referans fotoğrafını gönder
  fotografCekVeGonder(0.0);
  Serial.println("✅ Referans fotoğraf gönderildi.");
}

// ─────────────────────────────────────────
// SETUP
// ─────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n\n╔═══════════════════════════════════════╗");
  Serial.println("║  AKILLI DOLAP SİSTEMİ BAŞLATILIYOR   ║");
  Serial.println("╚═══════════════════════════════════════╝");

  // 1. HX711 Başlat
  Serial.println("\n[1/4] Ağırlık Sensörü Başlatılıyor...");
  EEPROM.begin(512);
  LoadCell.begin();

  float calibrationValue = 696.0; // Varsayılan kalibrasyon
  EEPROM.get(CALVAL_EEPROM_ADDR, calibrationValue);

  LoadCell.start(2000, true); // 2 sn stabilizasyon + tare
  if (LoadCell.getTareTimeoutFlag()) {
    Serial.println("❌ HX711 bağlantı hatası! Pin 40 (DOUT) ve 41 (SCK) "
                   "bağlantılarını kontrol et.");
    while (1)
      delay(1000);
  }
  LoadCell.setCalFactor(calibrationValue);
  Serial.printf("✅ HX711 Hazır! Kalibrasyon: %.1f\n", calibrationValue);

  // 2. Kamera Başlat
  Serial.println("\n[2/4] Kamera Başlatılıyor...");
  if (!kameraBaslat()) {
    Serial.println("❌ Kamera başlatılamadı! Pin bağlantılarını kontrol et.");
    while (1)
      delay(1000);
  }

  // 3. WiFi Bağlantısı
  Serial.printf("\n[3/4] WiFi: %s\n", ssid);
  WiFi.mode(WIFI_STA);      // Sadece client modu
  WiFi.disconnect(true);    // Eski bağlantıları temizle
  delay(1000);
  WiFi.begin(ssid, password);
  int deneme = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    deneme++;
    if (deneme % 20 == 0) { // Her 10 saniyede durum yaz
      Serial.printf("\n   [%ds] WiFi durumu: %d\n", (deneme / 2), WiFi.status());
    }
    if (deneme > 120) {     // 60 saniye sonra restart
      Serial.println("\n❌ WiFi bağlanamadı! Yeniden başlatılıyor...");
      ESP.restart();
    }
  }
  Serial.printf("\n✅ WiFi Bağlandı! ESP32 IP: %s\n",
                WiFi.localIP().toString().c_str());

  // 4. Python Sunucusunu Bul (UDP ile otomatik keşif)
  Serial.println("\n[4/5] Python sunucusu aranıyor...");
  if (!sunucuBul(30)) {
    Serial.println("❌ Sunucu bulunamadı! api_sunucu.py çalışıyor mu?");
    Serial.println("   30 saniye sonra yeniden denenecek...");
    delay(30000);
    ESP.restart();
  }

  // 5. Başlangıç Ağırlığı
  Serial.println("\n[5/5] Başlangıç ağırlığı ölçülüyor...");
  delay(500);
  float toplam = 0;
  int okunanSayi = 0;
  for (int i = 0; i < 10; i++) {
    if (LoadCell.update()) {
      toplam += LoadCell.getData();
      okunanSayi++;
    }
    delay(100);
  }
  onceki_agirlik = (okunanSayi > 0) ? (toplam / okunanSayi) : 0.0;
  Serial.printf("✅ Başlangıç ağırlığı: %.2f gram\n", onceki_agirlik);

  // 6. Referans Fotoğraf
  Serial.println("\n⏳ Referans fotoğraf için 3 saniye bekleniyor...");
  delay(3000);
  referansFotoGonder();

  Serial.println("\n╔═══════════════════════════════════════╗");
  Serial.printf("║  SİSTEM HAZIR — Eşik: %.0fg           ║\n",
                AGIRLIK_ESIK_DEGERI);
  Serial.println("╚═══════════════════════════════════════╝\n");
}

// ─────────────────────────────────────────
// LOOP
// ─────────────────────────────────────────
void loop() {
  // WiFi kontrol
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi koptu! Yeniden bağlanılıyor...");
    WiFi.begin(ssid, password);
    delay(3000);
    return;
  }

  // HX711'den oku ve 5 örnekle ortalama al
  if (LoadCell.update()) {
    weightBuffer[sampleIndex] = LoadCell.getData();
    sampleIndex++;

    if (sampleIndex >= ORTALAMA_ORNEK_SAYISI) {
      float toplam = 0;
      for (int k = 0; k < ORTALAMA_ORNEK_SAYISI; k++)
        toplam += weightBuffer[k];
      avgWeight = toplam / ORTALAMA_ORNEK_SAYISI;
      sampleIndex = 0;
      ortalamaHazir = true;
    }
  }

  // Ortalama hazırsa değişim kontrol et
  if (ortalamaHazir) {
    float fark = avgWeight - onceki_agirlik;

    if (abs(fark) > AGIRLIK_ESIK_DEGERI) {
      if (millis() - sonTetikZamani > DEBOUNCE_MS) {
        Serial.println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
        Serial.printf("⚡ Değişim tespit edildi: %.2f gram\n", fark);
        Serial.println("⏳ Sallantı kontrolü (2 sn bekleniyor)...");

        // ─── AŞAMA 1: Sallantı filtresi ─────────────────────────
        // Kapı sallantısı genellikle <1 sn sürer.
        // 2 sn bekleyip tekrar ölçüyoruz — hâlâ fark var mı?
        delay(2000);
        float dogrulamaToplam = 0;
        int   dogrulamaSayisi = 0;
        for (int d = 0; d < 10; d++) {
          if (LoadCell.update()) {
            dogrulamaToplam += LoadCell.getData();
            dogrulamaSayisi++;
          }
          delay(100);
        }

        if (dogrulamaSayisi == 0) {
          Serial.println("⚠️  Doğrulama ölçümü alınamadı — atlandı.");

        } else {
          float dogrulamaAgirlik = dogrulamaToplam / dogrulamaSayisi;
          float dogrulamaFarki   = dogrulamaAgirlik - onceki_agirlik;

          if (abs(dogrulamaFarki) < AGIRLIK_ESIK_DEGERI) {
            // Sallantı kaynaklı geçici değişim — yoksay
            Serial.printf("🔕 SALLANTI YOKSAYILDI — geçici değişim: %.2f g\n",
                          dogrulamaFarki);

          } else {
            // ─── AŞAMA 2: Gerçek değişim onaylandı ─────────────
            Serial.printf("✅ Doğrulandı! %.2f gram gerçek değişim\n",
                          dogrulamaFarki);
            Serial.printf("   Önceki: %.2f g → Şimdiki: %.2f g\n",
                          onceki_agirlik, dogrulamaAgirlik);
            Serial.println("📸 Fotoğraf için 5 sn bekleniyor (kapı kapansın)...");

            delay(5000); // Kapı kapansın, el çekilsin, ürün yerine otursun
            fotografCekVeGonder(dogrulamaFarki);

            // Tartıyı stabilize et — yeni referans ağırlığı belirle
            ortalamaHazir = false;
            sampleIndex   = 0;
            float stabilToplam = 0;
            int   stabilSayi   = 0;
            for (int s = 0; s < 10; s++) {
              if (LoadCell.update()) {
                stabilToplam += LoadCell.getData();
                stabilSayi++;
              }
              delay(200); // 10 örnek × 200ms = 2 sn stabilizasyon
            }
            onceki_agirlik = (stabilSayi > 0) ? (stabilToplam / stabilSayi)
                                               : dogrulamaAgirlik;
            Serial.printf("📊 Yeni referans ağırlık: %.2f gram\n", onceki_agirlik);
            sonTetikZamani = millis();
          }
        }
      }
    }


    // Serial'dan 't' gelirse tare al
    if (Serial.available() > 0) {
      char inByte = Serial.read();
      if (inByte == 't') {
        LoadCell.tareNoDelay();
        Serial.println("🔧 Tare alındı!");
      }
    }
  }
}
