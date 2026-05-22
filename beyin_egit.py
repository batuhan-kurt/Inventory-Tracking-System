"""
beyin_egit.py — Geliştirilmiş CNN Eğitim Scripti
=================================================
İYİLEŞTİRMELER:
  - Online augmentation: her epoch'ta model fotoğrafları farklı görür (ezberleme önlenir)
  - 5. Conv2D bloğu eklendi (daha derin özellik çıkarımı)
  - L2 regularization eklendi
  - Daha geniş Dense katmanı (256)
"""

import numpy as np
import cv2
import random
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    Dense, Conv2D, MaxPooling2D, Dropout,
    BatchNormalization, Input, GlobalAveragePooling2D
)
from tensorflow.keras.regularizers import l2
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.utils import Sequence

print("🧠 Stabil ve Hafifletilmiş CNN Eğitimi Başlıyor...\n")

# ─────────────────────────────────────────────
#  1. VERİLERİ YÜKLE
# ─────────────────────────────────────────────
try:
    X = np.load("X_verileri.npy").astype("float32") / 255.0
    Y = np.load("Y_etiketler.npy").astype("int32")
except FileNotFoundError:
    print("HATA: X_verileri.npy veya Y_etiketler.npy bulunamadı!")
    print("Önce: python3 veri_hazirla.py")
    exit(1)

print(f"✅ Veri yüklendi: {X.shape} | Etiket: {Y.shape}")
print(f"   Sınıf dağılımı (0-10): {np.bincount(Y)}\n")

# Eğitim/Validasyon ayrımı (stratified — her sınıftan eşit oranda al)
X_train, X_val, Y_train, Y_val = train_test_split(
    X, Y, test_size=0.2, random_state=42, stratify=Y
)
print(f"   Eğitim seti  : {X_train.shape[0]} resim")
print(f"   Validasyon   : {X_val.shape[0]} resim\n")

# ─────────────────────────────────────────────
#  2. ONLİNE AUGMENTATION (eğitim sırasında)
# ─────────────────────────────────────────────
def online_augment(img):
    """Eğitim sırasında her görüntüye hafif rastgele dönüşüm uygular."""
    # Yatay flip
    if random.random() > 0.5:
        img = cv2.flip(img, 1)
    # Hafif döndürme
    if random.random() > 0.5:
        aci = random.uniform(-15, 15)
        h, w = img.shape[:2]
        M = cv2.getRotationMatrix2D((w//2, h//2), aci, 1.0)
        img = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)
    # Parlaklık
    if random.random() > 0.5:
        f = random.uniform(0.7, 1.3)
        img = np.clip(img * f, 0, 1).astype(np.float32)
    # Hafif noise
    if random.random() > 0.6:
        noise = np.random.normal(0, 0.02, img.shape).astype(np.float32)
        img = np.clip(img + noise, 0, 1).astype(np.float32)
    return img

class AugmentedGenerator(Sequence):
    """Her epoch'ta online augmentation uygulayan veri üretici."""
    def __init__(self, X, Y, batch_size=32, augment=True):
        self.X = X
        self.Y = Y
        self.batch_size = batch_size
        self.augment = augment
        self.indices = np.arange(len(X))

    def __len__(self):
        return int(np.ceil(len(self.X) / self.batch_size))

    def __getitem__(self, idx):
        batch_idx = self.indices[idx * self.batch_size:(idx + 1) * self.batch_size]
        X_batch = self.X[batch_idx].copy()
        Y_batch = self.Y[batch_idx]
        if self.augment:
            for i in range(len(X_batch)):
                X_batch[i] = online_augment(X_batch[i])
        return X_batch, Y_batch

    def on_epoch_end(self):
        np.random.shuffle(self.indices)

# ─────────────────────────────────────────────
#  3. GELİŞTİRİLMİŞ CNN MİMARİSİ
# ─────────────────────────────────────────────
N_SINIF = 11
REG = l2(1e-4)  # L2 regularization — overfitting'i azaltır

beyin = Sequential([
    Input(shape=(224, 224, 3)),

    # --- 1. BLOK ---
    Conv2D(32, (3, 3), padding='same', activation='relu', kernel_regularizer=REG),
    BatchNormalization(),
    MaxPooling2D((2, 2)),

    # --- 2. BLOK ---
    Conv2D(64, (3, 3), padding='same', activation='relu', kernel_regularizer=REG),
    BatchNormalization(),
    MaxPooling2D((2, 2)),

    # --- 3. BLOK ---
    Conv2D(128, (3, 3), padding='same', activation='relu', kernel_regularizer=REG),
    BatchNormalization(),
    MaxPooling2D((2, 2)),

    # --- 4. BLOK ---
    Conv2D(256, (3, 3), padding='same', activation='relu', kernel_regularizer=REG),
    BatchNormalization(),
    MaxPooling2D((2, 2)),

    # --- 5. BLOK (Logo/doku detayları için) ---
    Conv2D(256, (3, 3), padding='same', activation='relu', kernel_regularizer=REG),
    BatchNormalization(),

    # --- KARAR KATMANLARI ---
    GlobalAveragePooling2D(),
    Dense(256, activation='relu', kernel_regularizer=REG),
    Dropout(0.5),
    Dense(128, activation='relu'),
    Dropout(0.3),
    Dense(N_SINIF, activation='softmax'),
])

beyin.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

beyin.summary()

# ─────────────────────────────────────────────
#  3. CALLBACKS
# ─────────────────────────────────────────────
erken_durdurma = EarlyStopping(
    monitor='val_accuracy',
    patience=15,
    restore_best_weights=True,
    verbose=1
)
hiz_dusurucu = ReduceLROnPlateau(
    monitor='val_loss',
    factor=0.5,
    patience=5,
    min_lr=1e-6,
    verbose=1
)

# ─────────────────────────────────────────────
#  4. EĞİT
# ─────────────────────────────────────────────
# Online augmentation generator'larını oluştur
train_gen = AugmentedGenerator(X_train, Y_train, batch_size=32, augment=True)
val_gen   = AugmentedGenerator(X_val,   Y_val,   batch_size=32, augment=False)

print("\n🚀 Eğitim başlıyor (online augmentation aktif)...\n")
tarih = beyin.fit(
    train_gen,
    epochs=50,
    validation_data=val_gen,
    callbacks=[erken_durdurma, hiz_dusurucu],
    verbose=1
)

# ─────────────────────────────────────────────
#  5. SONUÇ VE KAYDET
# ─────────────────────────────────────────────
son_val_acc  = max(tarih.history['val_accuracy'])
son_egit_acc = max(tarih.history['accuracy'])

print("\n" + "=" * 50)
print("🎯 EĞİTİM TAMAMLANDI!")
print(f"   En iyi Train Accuracy : %{son_egit_acc*100:.1f}")
print(f"   En iyi Val Accuracy   : %{son_val_acc*100:.1f}")
print("=" * 50)

beyin.save("akilli_dolap_beyni.keras")
print("\n✅ Model 'akilli_dolap_beyni.keras' olarak kaydedildi.")
print("🔜 Sonraki adım: python3 tahmin_yap.py\n")