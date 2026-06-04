"""
rapor_olustur.py — Bitirme Projesi Rapor Üretici (Tam Sürüm)
==============================================================
Bu kod terminale yazı yazdırmaz; hocanın istediği tüm metrikleri,
tabloları ve hiperparametre açıklamalarını profesyonel PDF ve PNG
dosyaları olarak klasörüne otomatik kaydeder.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from tensorflow.keras.models import load_model
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd

print("📊 Bitirme Projesi raporları oluşturuluyor, lütfen bekleyin...\n")

# ─────────────────────────────────────────────
#  1. VERİLERİ YÜKLE VE BÖL (Senin Gerçek Verilerin)
# ─────────────────────────────────────────────
X = np.load("X_verileri.npy").astype("float32") / 255.0
Y = np.load("Y_etiketler.npy").astype("int32")

X_train, X_test, Y_train, Y_test = train_test_split(
    X, Y, test_size=0.2, random_state=42, stratify=Y
)

# ─────────────────────────────────────────────
#  2. KATEGORİLER (Senin Gerçek Ürünlerin)
# ─────────────────────────────────────────────
KATEGORILER = [
    "CocaCola_Klasik", "CocaCola_Zero", "Pepsi", "Fanta",
    "RedBull_Klasik", "RedBull_White", "RedBull_Blue",
    "RedBull_Lilac", "RedBull_Pembe", "Nescafe_Klasik", "Bos_Raf"
]

# ─────────────────────────────────────────────
#  3. MODEL TAHMİNLERİ
# ─────────────────────────────────────────────
model = load_model("akilli_dolap_beyni.keras")
tahminler_vektor = model.predict(X_test, verbose=0)
Y_tahmin = np.argmax(tahminler_vektor, axis=1)

# =====================================================================
#  ÇIKTI 1: CONFUSION MATRIX GRAFİĞİ (PNG ve PDF)
# =====================================================================
cm = confusion_matrix(Y_test, Y_tahmin)
plt.figure(figsize=(12, 10))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=KATEGORILER, yticklabels=KATEGORILER)

plt.title('Akıllı Envanter - Sınıflandırma Karmaşıklık Matrisi (Confusion Matrix)', fontsize=14)
plt.ylabel('Gerçek Ürünler', fontsize=12, fontweight='bold')
plt.xlabel('Modelin Tahmin Ettiği Ürünler', fontsize=12, fontweight='bold')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('1_Confusion_Matrix.png', dpi=300)
plt.savefig('1_Confusion_Matrix.pdf')
plt.close()

# =====================================================================
#  ÇIKTI 2: SINIF BAZLI BAŞARI RAPORU (Tablo Görseli)
# =====================================================================
rapor_dict = classification_report(Y_test, Y_tahmin, target_names=KATEGORILER, output_dict=True)
df_rapor = pd.DataFrame(rapor_dict).iloc[:-1, :].T # support sütununu at, transpoze al

fig, ax = plt.subplots(figsize=(10, 6))
ax.axis('tight')
ax.axis('off')
ax.set_title("Sınıf Bazlı ve Toplam Başarı (Accuracy) Tablosu", fontsize=14, fontweight='bold', pad=20)
tablo = ax.table(cellText=np.round(df_rapor.values, 3), colLabels=df_rapor.columns, rowLabels=df_rapor.index, loc='center', cellLoc='center')
tablo.scale(1, 2)
tablo.auto_set_font_size(False)
tablo.set_fontsize(10)
plt.savefig('2_Basari_Oranlari_Tablosu.png', dpi=300, bbox_inches='tight')
plt.close()

# =====================================================================
#  ÇIKTI 3: VERİ SETİ BİLGİSİ VE DATA AUGMENTATION RAPORU (PDF)
# =====================================================================
with PdfPages('3_Veri_Seti_ve_Augmentation_Raporu.pdf') as pdf:
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.axis('off')

    metin = (
        "PROJE VERİ SETİ VE DATA AUGMENTATION (VERİ ARTIRIMI) RAPORU\n"
        "===========================================================\n\n"
        "1. Train / Test Dağılımı\n"
        "------------------------\n"
        f"Toplam Veri Sayısı : {X.shape[0]} adet fotoğraf\n"
        f"Train (Eğitim) Seti: {X_train.shape[0]} adet fotoğraf (%80)\n"
        f"Test (Doğrulama)   : {X_test.shape[0]} adet fotoğraf (%20)\n"
        "Bölme Yöntemi      : Stratified split (her sınıftan eşit oranda)\n\n"
        "2. Super Augmentation Pipeline (super_augment.py)\n"
        "-------------------------------------------------\n"
        "Projedeki ham veri seti sınıf başına dengesiz sayıda görüntü içeriyordu.\n"
        "Tüm sınıfları TAM 400 ADET fotoğrafa eşitlemek için özel bir\n"
        "'Super Augmentation' boru hattı (super_augment.py) geliştirilmiştir.\n"
        "Bu boru hattı 3 seviyeye ayrılmış 16 farklı dönüşüm uygular:\n\n"
        "  [HAFİF DÖNÜŞÜMLER]\n"
        "    - Rotation       : ±35 derece rastgele döndürme\n"
        "    - Zoom + Crop    : %8–25 oranında merkezi kırpma + yeniden boyutlandırma\n"
        "    - Horizontal Flip: Yatay eksende simetrik çevirme\n"
        "    - Contrast       : alpha=0.5–1.8, beta=−50/+50 kontrast ayarı\n"
        "    - Channel Shift  : Her renk kanalına bağımsız x0.65–1.35 sapma\n"
        "    - Sharpening     : Unsharp mask filtresi (mix=0.4–1.0)\n"
        "    - Sensor Noise   : σ = %3–10 Gaussian gürültü (ESP32 kamera simülasyonu)\n\n"
        "  [ORTA DÖNÜŞÜMLER]\n"
        "    - Perspective    : ±%18 perspektif bozulması (farklı açı simülasyonu)\n"
        "    - Focus Blur     : 5–13 piksel Gaussian blur (odak kaybı)\n"
        "    - Motion Blur    : 7–19 piksel yatay/dikey/köşegen hareket bulanıklığı\n"
        "    - Shadow Strip   : Yatay veya dikey gölge şeridi (x0.2–0.55 koyultma)\n"
        "    - Vignette       : Kenar kararması (Gaussian maske, f=0.35–0.70)\n"
        "    - JPEG Artifact  : 15–55 kalite JPEG sıkıştırma (düşük kalite kamera)\n"
        "    - HSV Color Shift: Hue ±25°, Saturation x0.4–1.6, Value x0.5–1.5\n\n"
        "  [AĞIR DÖNÜŞÜMLER] — %45 ihtimalle uygulanır\n"
        "    - Dark Room      : x0.15–0.55 karanlık ortam simülasyonu\n"
        "    - Overexposure   : x1.50–2.20 aşırı parlak ortam simülasyonu\n\n"
        "3. Online Augmentation (beyin_egit.py — Eğitim Sırasında)\n"
        "----------------------------------------------------------\n"
        "Model eğitimi sırasında her epoch'ta ek hafif dönüşümler uygulanmıştır:\n"
        "  - Horizontal Flip : %50 ihtimalle yatay çevirme\n"
        "  - Rotation        : ±15 derece döndürme\n"
        "  - Brightness      : x0.70–1.30 parlaklık değişimi\n"
        "  - Gaussian Noise  : σ = 0.02 (normalize uzayda)\n"
        "Bu sayede model her epoch'ta görüntülerin farklı varyantlarını görmüştür.\n"
    )

    ax.text(0.04, 0.97, metin, transform=ax.transAxes, fontsize=9.8,
            verticalalignment='top', family='monospace', linespacing=1.4)
    pdf.savefig(fig)
    plt.close()

# =====================================================================
#  ÇIKTI 4: HİPERPARAMETRE AÇIKLAMA RAPORU (PDF)
# =====================================================================
with PdfPages('4_Hiperparametre_ve_Mimari_Raporu.pdf') as pdf:
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.axis('off')

    metin = (
        "CNN MİMARİSİ VE HİPERPARAMETRE TERCİHLERİ\n"
        "===========================================================\n\n"
        "1. Model Mimarisi — 5 Katmanlı Özel CNN\n"
        "----------------------------------------\n"
        "  Giriş        : 224 x 224 x 3 (RGB görüntü)\n"
        "  Blok 1       : Conv2D(32,  3×3, ReLU) → BatchNorm → MaxPool(2×2)\n"
        "  Blok 2       : Conv2D(64,  3×3, ReLU) → BatchNorm → MaxPool(2×2)\n"
        "  Blok 3       : Conv2D(128, 3×3, ReLU) → BatchNorm → MaxPool(2×2)\n"
        "  Blok 4       : Conv2D(256, 3×3, ReLU) → BatchNorm → MaxPool(2×2)\n"
        "  Blok 5       : Conv2D(256, 3×3, ReLU) → BatchNorm  (pooling yok)\n"
        "  Karar Bölümü : GlobalAveragePooling2D → Dense(256) → Dropout(0.5)\n"
        "                 → Dense(128) → Dropout(0.3) → Dense(11, Softmax)\n\n"
        "2. GlobalAveragePooling2D\n"
        "Flatten() yerine tercih edildi. Flatten, 25+ milyon parametre üreterek\n"
        "overfitting'e yol açıyordu. GlobalAveragePooling2D özellik haritasını\n"
        "tek bir değere indirger; parametre sayısını dramatik biçimde düşürür\n"
        "ve modelin genelleme kapasitesini artırır.\n\n"
        "3. L2 Regularization (kernel_regularizer=l2(1e-4))\n"
        "Tüm Conv2D ve Dense(256) katmanlarına uygulandı. Ağırlıkların\n"
        "büyümesini cezalandırarak modelin gereksiz karmaşıklık öğrenmesini önler.\n\n"
        "4. Dropout Oranları\n"
        "  - Dense(256) sonrası Dropout(0.5) : Nöronların %50'si rastgele kapatılır;\n"
        "    büyük boyutlu katmanda güçlü regularization etkisi sağlar.\n"
        "  - Dense(128) sonrası Dropout(0.3) : Daha dar katmanda daha hafif baskı,\n"
        "    son sınıflandırma kararı için yeterli bilgi akışı korunur.\n\n"
        "5. batch_size = 32\n"
        "32'lik mini-batch, gradient güncellemelerini dengeleyerek hem hız hem\n"
        "genelleme açısından optimum noktadır. 8 → çok yavaş; 128 → genelleme kaybı.\n\n"
        "6. EarlyStopping (monitor='val_accuracy', patience=15)\n"
        "Val_accuracy 15 epoch boyunca iyileşmezse eğitim durur ve en iyi\n"
        "ağırlıklar geri yüklenir (restore_best_weights=True).\n\n"
        "7. ReduceLROnPlateau (monitor='val_loss', factor=0.5, patience=5)\n"
        "Val_loss 5 epoch plato yaptığında öğrenme hızı yarıya düşürülür.\n"
        "Minimum öğrenme hızı: 1e-6. Bu mekanizma modelin ince ayar yapmasını sağlar.\n\n"
        "8. Optimizer & Loss\n"
        "  Optimizer : Adam (adaptif öğrenme hızı, varsayılan lr=1e-3)\n"
        "  Loss      : Sparse Categorical Cross-Entropy (integer etiketler için)\n"
        "  Metric    : Accuracy\n"
    )

    ax.text(0.04, 0.97, metin, transform=ax.transAxes, fontsize=9.8,
            verticalalignment='top', family='monospace', linespacing=1.4)
    pdf.savefig(fig)
    plt.close()

print("✅ BÜTÜN RAPORLAR BAŞARIYLA OLUŞTURULDU!")
print("Klasörünüzdeki '1_', '2_', '3_' ve '4_' ile başlayan yeni dosyalara göz atabilirsiniz.")