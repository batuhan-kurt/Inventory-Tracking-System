#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include "esp_camera.h"
#include "HX711.h"

// ==========================================
// AĞ (Wi-Fi) ve SUNUCU AYARLARI
// ==========================================
const char* ssid = "WIFI_ADINIZ";
const char* password = "WIFI_SIFRENIZ";
// Bilgisayarınızın yerel IP adresi (Python sunucusu burada çalışacak)
const char* serverUrl = "http://192.168.1.50:5001/tetikle"; 

// ==========================================
// HX711 (Yük Hücresi) PIN AYARLARI
// ==========================================
const int LOADCELL_DOUT_PIN = 4;
const int LOADCELL_SCK_PIN = 5;
HX711 scale;
float onceki_agirlik = 0.0;
const float AGIRLIK_ESIK_DEGERI = 50.0; // 50 gram değişim
bool ilk_calisma = true;         // Sabah başlangıç fotoğrafı için bayrak

// ==========================================
// OV5640 KAMERA PIN AYARLARI (ESP32-S3 WROVER İÇİN ÖRNEK)
// ==========================================
#define PWDN_GPIO_NUM  -1
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM  21
#define SIOD_GPIO_NUM  26
#define SIOC_GPIO_NUM  27
#define Y9_GPIO_NUM    35
#define Y8_GPIO_NUM    34
#define Y7_GPIO_NUM    39
#define Y6_GPIO_NUM    36
#define Y5_GPIO_NUM    19
#define Y4_GPIO_NUM    18
#define Y3_GPIO_NUM    5
#define Y2_GPIO_NUM    4
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM  23
#define PCLK_GPIO_NUM  22

// Fonksiyon prototipleri
void fotografCekVeGonder(float degisim);
void referansFotoCek();

void setup() {
  Serial.begin(115200);
  Serial.println("\n--- Akıllı Dolap Sistemi Başlatılıyor ---");

  // 1. Wi-Fi Bağlantısı
  WiFi.begin(ssid, password);
  Serial.print("Wi-Fi ağına bağlanılıyor");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ Wi-Fi Bağlandı!");
  Serial.print("ESP32 IP Adresi: ");
  Serial.println(WiFi.localIP());

  // 2. Kamera Kurulumu
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
  config.xclk_freq_hz = 20000000;
  config.frame_size = FRAMESIZE_VGA; // 640x480 Çözünürlük
  config.pixel_format = PIXFORMAT_JPEG; // Python'a doğrudan JPEG yollayacağız
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  // Kamerayı başlat
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("❌ Kamera başlatılamadı! Hata Kodu: 0x%x\n", err);
  } else {
    Serial.println("✅ Kamera Başarıyla Kuruldu!");
  }

  // 3. HX711 Kurulumu
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale(2280.f); 
  scale.tare(); 
  onceki_agirlik = scale.get_units(10); // Başlangıç ağırlığını kaydet
  Serial.println("✅ HX711 Darası Alındı. Sistem İzlemeye Hazır.");

  // SABAH KALİBRASYONU: Sistem açıldığında referans fotoğraf çek
  Serial.println("📸 Başlangıç referans fotoğrafı çekiliyor...");
  delay(3000); // Dolap kapağının kapanması için bekle
  referansFotoCek();
  ilk_calisma = false;
  Serial.println("\n✅ Sistem Hazır — Ürün İzleme Aktif\n");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ Wi-Fi koptu! Yeniden bağlanılmaya çalışılıyor...");
    WiFi.begin(ssid, password);
    delay(3000);
    return;
  }

  if (scale.is_ready()) {
    float mevcut_agirlik = scale.get_units(10);
    float fark = mevcut_agirlik - onceki_agirlik;
    
    // Mutlak değer değişimi eşikten büyükse
    if (abs(fark) > AGIRLIK_ESIK_DEGERI) {
      Serial.println("-----------------------------------");
      Serial.printf("🚨 AĞIRLIK DEĞİŞİMİ: %.2f gram\n", fark);
      
      // Ürün tam yerine oturana kadar 2 saniye bekle (bulanık fotoğraf önleme)
      delay(2000);
      fotografCekVeGonder(fark);
      
      onceki_agirlik = mevcut_agirlik;
      // Çift tetiklemeyi önlemek için uzun debounce
      delay(7000); 
    }
  }
  delay(500); 
}

void fotografCekVeGonder(float degisim) {
  Serial.println("📸 Fotoğraf çekiliyor...");
  
  // Kameradan resmi al (Frame Buffer)
  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("❌ Fotoğraf çekilemedi!");
    return;
  }

  Serial.println("🌐 Python Sunucusuna Yollanıyor...");
  HTTPClient http;
  
  // Python sunucusundaki Flask endpointi
  http.begin(serverUrl);
  
  // İstek başlığı
  http.addHeader("Content-Type", "image/jpeg");
  
  // Özel bir HTTP başlığı olarak değişimi de gönderebiliriz
  String farkStr = String(degisim);
  http.addHeader("X-Agirlik-Degisimi", farkStr);

  // Buffer'daki resmi doğrudan POST isteği gövdesi (body) olarak gönderiyoruz
  int httpResponseCode = http.POST(fb->buf, fb->len);

  if (httpResponseCode > 0) {
    Serial.printf("✅ Başarılı! Sunucu Cevabı: %d\n", httpResponseCode);
    String response = http.getString();
    Serial.println("Python Diyor ki: " + response);
  } else {
    Serial.printf("❌ Hata! HTTP POST Kod: %d\n", httpResponseCode);
    Serial.println("Python sunucusu (api_sunucu.py) çalışıyor mu? IP adresini kontrol edin.");
  }

  http.end();
  
  // Belleği temizle (Çok Önemli!)
  esp_camera_fb_return(fb);
}

// ==========================================
// SABAH REFERANS FOTOĞRAFI
// ==========================================
void referansFotoCek() {
  Serial.println("📸 Referans fotoğraf çekiliyor (/sifirla çağrısı gönderiliyor)...");
  
  // Önce sunucuya sıfırlama sinyali gönder
  // (Eski referans varsa temizlenir, yeni fotoğraf referans olur)
  HTTPClient http_reset;
  String resetUrl = String(serverUrl);
  resetUrl.replace("/tetikle", "/sifirla");
  http_reset.begin(resetUrl);
  http_reset.POST("");
  http_reset.end();
  delay(500);
  
  // Şimdi normal fotoğraf çek ve gönder (API bunu referans yapacak)
  fotografCekVeGonder(0.0);
  Serial.println("✅ Referans fotoğraf gönderildi.");
}
