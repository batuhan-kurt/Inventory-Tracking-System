"""
report_generator.py — Graduation Project Report Generator (Full Version)
==============================================================
This code saves professional PDF and PNG metric reports to your folder.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from tensorflow.keras.models import load_model
import pandas as pd
import matplotlib.gridspec as gridspec

# Set professional academic fonts (LaTeX style Computer Modern / Serif)
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Computer Modern Roman', 'Times New Roman', 'DejaVu Serif', 'serif']
plt.rcParams['mathtext.fontset'] = 'cm'

BG   = "#ffffff"
TEXT_MAIN = "#000000"

print("📊 Generating Graduation Project reports, please wait...\n")

# ─────────────────────────────────────────────
#  1. LOAD AND SPLIT DATA
# ─────────────────────────────────────────────
X = np.load("X_verileri.npy").astype("float32") / 255.0
Y = np.load("Y_etiketler.npy").astype("int32")

X_train, X_test, Y_train, Y_test = train_test_split(
    X, Y, test_size=0.2, random_state=42, stratify=Y
)

# ─────────────────────────────────────────────
#  2. CATEGORIES
# ─────────────────────────────────────────────
KATEGORILER = [
    "CocaCola_Classic", "CocaCola_Zero", "Pepsi", "Fanta",
    "RedBull_Classic", "RedBull_White", "RedBull_Blue",
    "RedBull_Lilac", "RedBull_Pink", "Nescafe_Classic", "Empty_Shelf"
]
SHORT_NAMES = [
    "CC Classic", "CC Zero", "Pepsi", "Fanta",
    "RB Classic", "RB White", "RB Blue",
    "RB Lilac", "RB Pink", "Nescafe", "Empty Shelf"
]

# ─────────────────────────────────────────────
#  3. MODEL PREDICTIONS
# ─────────────────────────────────────────────
model = load_model("akilli_dolap_beyni.keras")
tahminler_vektor = model.predict(X_test, verbose=0)
Y_tahmin = np.argmax(tahminler_vektor, axis=1)

# =====================================================================
#  OUTPUT 1: CONFUSION MATRIX (PNG)
# =====================================================================
cm = confusion_matrix(Y_test, Y_tahmin)
plt.figure(figsize=(14, 12))
plt.gcf().patch.set_facecolor(BG)
ax = plt.gca()
ax.set_facecolor(BG)

sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=SHORT_NAMES, yticklabels=SHORT_NAMES,
            linewidths=1.0, linecolor=TEXT_MAIN,
            annot_kws={"size": 13, "color": "black", "weight": "bold"})

plt.title('Smart Inventory - Classification Confusion Matrix', fontsize=18, fontweight='black', pad=20)
plt.ylabel('True Products', fontsize=15, fontweight='bold')
plt.xlabel('Predicted Products', fontsize=15, fontweight='bold')
plt.xticks(rotation=45, ha='right', fontsize=12, fontweight='bold')
plt.yticks(fontsize=12, fontweight='bold')

for spine in ax.spines.values():
    spine.set_edgecolor(TEXT_MAIN)
    spine.set_linewidth(2.0)
    spine.set_visible(True)

plt.tight_layout(pad=2.0)
plt.savefig('1_Confusion_Matrix.png', dpi=300, bbox_inches='tight', facecolor=BG)
plt.close()

# =====================================================================
#  OUTPUT 2: PER-CLASS ACCURACY REPORT (PNG)
# =====================================================================
rapor_dict = classification_report(Y_test, Y_tahmin, target_names=SHORT_NAMES, output_dict=True)
df_rapor = pd.DataFrame(rapor_dict).iloc[:-1, :].T 

fig, ax = plt.subplots(figsize=(14, 8))
fig.patch.set_facecolor(BG)
ax.axis('tight')
ax.axis('off')
ax.set_title("Per-Class and Overall Performance Table", fontsize=18, fontweight='black', pad=20)

tablo = ax.table(cellText=np.round(df_rapor.values, 4), colLabels=df_rapor.columns, rowLabels=df_rapor.index, loc='center', cellLoc='center')
tablo.scale(1, 2.5)
tablo.auto_set_font_size(False)
tablo.set_fontsize(13)

for (r, c), cell in tablo.get_celld().items():
    if r == 0 or c == -1:
        cell.set_facecolor("#e0e0e0")
        cell.set_text_props(color=TEXT_MAIN, fontweight="black")
    else:
        cell.set_facecolor("#ffffff" if r % 2 == 0 else "#f9f9f9")
        cell.set_text_props(color=TEXT_MAIN, fontweight="bold")
    cell.set_edgecolor(TEXT_MAIN)
    cell.set_linewidth(1.5)

plt.savefig('2_Performance_Rates_Table.png', dpi=300, bbox_inches='tight', facecolor=BG)
plt.close()

# =====================================================================
#  OUTPUT 3: DATASET AND AUGMENTATION REPORT (PNG)
# =====================================================================
fig = plt.figure(figsize=(18, 22))
fig.patch.set_facecolor(BG)

gs = gridspec.GridSpec(5, 1, figure=fig, height_ratios=[1, 0.4, 2, 0.3, 1])

# --- TABLE 1: Distribution ---
ax1 = fig.add_subplot(gs[0])
ax1.axis('off')
ax1.set_title("1. Train / Test Distribution", fontsize=18, fontweight='black', pad=15)
data1 = [
    ["Total Samples", f"{X.shape[0]} images"],
    ["Train Set", f"{X_train.shape[0]} images (80%)"],
    ["Test Set", f"{X_test.shape[0]} images (20%)"],
    ["Splitting Method", "Stratified split (equal ratio per class)"]
]
tbl1 = ax1.table(cellText=data1, colLabels=["Metric", "Value"], loc='center', cellLoc='center')
tbl1.auto_set_font_size(False); tbl1.set_fontsize(14); tbl1.scale(1, 2.8)
for (r, c), cell in tbl1.get_celld().items():
    if r == 0:
        cell.set_facecolor("#e0e0e0")
        cell.set_text_props(color=TEXT_MAIN, fontweight="black", ha="center")
    else:
        cell.set_facecolor("#ffffff" if r % 2 == 0 else "#f9f9f9")
        cell.set_text_props(color=TEXT_MAIN, fontweight="bold")
    cell.set_edgecolor(TEXT_MAIN); cell.set_linewidth(1.5)

# --- TEXT 2: Super Augmentation ---
ax2_txt = fig.add_subplot(gs[1])
ax2_txt.axis('off')
ax2_txt.set_title("2. Super Augmentation Pipeline (super_augment.py)", fontsize=18, fontweight='black', pad=15)
txt2 = "The raw dataset contained an imbalanced number of images per class. A custom 'Super Augmentation'\npipeline was developed to equalize all classes to EXACTLY 400 IMAGES. It applies 16 distinct transformations:"
ax2_txt.text(0.5, 0.5, txt2, ha='center', va='center', fontsize=15, fontweight='bold', color=TEXT_MAIN, linespacing=1.6)

# --- TABLE 2: Super Augmentation ---
ax2 = fig.add_subplot(gs[2])
ax2.axis('off')
details_txt = (
    "   [LIGHT TRANSFORMATIONS]\n"
    "     $\\bullet$ Rotation : $\\pm$35 degrees random rotation\n"
    "     $\\bullet$ Zoom + Crop : 8-25% central crop + resize\n"
    "     $\\bullet$ Horizontal Flip: Symmetric horizontal flip\n"
    "     $\\bullet$ Contrast : alpha=0.5-1.8, beta=-50/+50\n"
    "     $\\bullet$ Channel Shift : Independent x0.65-1.35 color shift\n"
    "     $\\bullet$ Sharpening : Unsharp mask filter (mix=0.4-1.0)\n"
    "     $\\bullet$ Sensor Noise : std = 3-10% Gaussian noise (ESP32 sim)\n\n"
    "   [MEDIUM TRANSFORMATIONS]\n"
    "     $\\bullet$ Perspective : $\\pm$18% perspective distortion\n"
    "     $\\bullet$ Focus Blur : 5-13 pixels Gaussian blur\n"
    "     $\\bullet$ Motion Blur : 7-19 pixels motion blur\n"
    "     $\\bullet$ Shadow Strip : Horizontal/vertical shadow (x0.2-0.55)\n"
    "     $\\bullet$ Vignette : Edge darkening (f=0.35-0.70)\n"
    "     $\\bullet$ JPEG Artifact : 15-55 quality JPEG compression\n"
    "     $\\bullet$ HSV Color Shift: Hue $\\pm$25 degrees, Sat x0.4-1.6, Val x0.5-1.5\n\n"
    "   [HEAVY TRANSFORMATIONS] (45% chance)\n"
    "     $\\bullet$ Dark Room : x0.15-0.55 low light environment\n"
    "     $\\bullet$ Overexposure : x1.50-2.20 bright light environment"
)
ax2.text(0.18, 0.95, details_txt, ha='left', va='top', fontsize=15, fontweight='bold', color=TEXT_MAIN, linespacing=1.6)

# --- TEXT 3: Online Augmentation ---
ax3_txt = fig.add_subplot(gs[3])
ax3_txt.axis('off')
ax3_txt.set_title("3. Online Augmentation (During Training)", fontsize=18, fontweight='black', pad=15)
txt3 = "Additional light transformations applied during model training to improve robustness:"
ax3_txt.text(0.5, 0.5, txt3, ha='center', va='center', fontsize=15, fontweight='bold', color=TEXT_MAIN)

# --- TABLE 3: Online Augmentation ---
ax3 = fig.add_subplot(gs[4])
ax3.axis('off')
data3 = [
    ["Horizontal Flip", "50% chance"],
    ["Rotation", "$\\pm$15 degrees"],
    ["Brightness", "x0.70-1.30 variance"],
    ["Gaussian Noise", "std = 0.02 (in normalized space)"]
]
tbl3 = ax3.table(cellText=data3, colLabels=["Transformation", "Parameter"], loc='center', cellLoc='center')
tbl3.auto_set_font_size(False); tbl3.set_fontsize(14); tbl3.scale(1, 2.5)
for (r, c), cell in tbl3.get_celld().items():
    if r == 0:
        cell.set_facecolor("#e0e0e0")
        cell.set_text_props(color=TEXT_MAIN, fontweight="black", ha="center")
    else:
        cell.set_facecolor("#ffffff" if r % 2 == 0 else "#f9f9f9")
        cell.set_text_props(color=TEXT_MAIN, fontweight="bold")
    cell.set_edgecolor(TEXT_MAIN); cell.set_linewidth(1.5)

fig.suptitle("PROJECT DATASET AND DATA AUGMENTATION REPORT", fontsize=24, fontweight='black', y=0.97)
plt.tight_layout(pad=3.0, rect=[0, 0, 1, 0.94])
plt.savefig('3_Data_Set_and_Augmentation_Report.png', dpi=300, bbox_inches='tight', facecolor=BG)
plt.close()

# =====================================================================
#  OUTPUT 4: HYPERPARAMETER REPORT (PNG)
# =====================================================================
fig = plt.figure(figsize=(18, 24))
fig.patch.set_facecolor(BG)

gs = gridspec.GridSpec(3, 1, figure=fig, height_ratios=[1.2, 1.2, 1.3])

# --- TABLE 1: Model Architecture ---
ax1 = fig.add_subplot(gs[0])
ax1.axis('off')
ax1.set_title("1. Model Architecture — Custom 5-Layer CNN", fontsize=18, fontweight='black', pad=15)
data1 = [
    ["Input Layer", "224 x 224 x 3 (RGB image)"],
    ["Block 1", "Conv2D(32, 3x3, ReLU) $\\rightarrow$ BatchNorm $\\rightarrow$ MaxPool(2x2)"],
    ["Block 2", "Conv2D(64, 3x3, ReLU) $\\rightarrow$ BatchNorm $\\rightarrow$ MaxPool(2x2)"],
    ["Block 3", "Conv2D(128, 3x3, ReLU) $\\rightarrow$ BatchNorm $\\rightarrow$ MaxPool(2x2)"],
    ["Block 4", "Conv2D(256, 3x3, ReLU) $\\rightarrow$ BatchNorm $\\rightarrow$ MaxPool(2x2)"],
    ["Block 5", "Conv2D(256, 3x3, ReLU) $\\rightarrow$ BatchNorm (no pooling)"],
    ["Decision Head", "GlobalAveragePooling2D $\\rightarrow$ Dense(256) $\\rightarrow$ Dropout(0.5)\n$\\rightarrow$ Dense(128) $\\rightarrow$ Dropout(0.3) $\\rightarrow$ Dense(11, Softmax)"]
]
tbl1 = ax1.table(cellText=data1, colLabels=["Layer", "Structure"], loc='center', cellLoc='center')
tbl1.auto_set_font_size(False); tbl1.set_fontsize(14); tbl1.scale(1, 2.5)
for (r, c), cell in tbl1.get_celld().items():
    if c == 0: cell.set_width(0.2)
    elif c == 1: cell.set_width(0.8)
    
    if r == 0:
        cell.set_facecolor("#e0e0e0")
        cell.set_text_props(color=TEXT_MAIN, fontweight="black", ha="center")
    else:
        cell.set_facecolor("#ffffff" if r % 2 == 0 else "#f9f9f9")
        cell.set_text_props(color=TEXT_MAIN, fontweight="bold")
    cell.set_edgecolor(TEXT_MAIN); cell.set_linewidth(1.5)

# --- TABLE 2: Hyperparameter Choices ---
ax2 = fig.add_subplot(gs[1])
ax2.axis('off')
ax2.set_title("Hyperparameter Configuration Summary", fontsize=18, fontweight='black', pad=15)
data2 = [
    ["Batch Size", "32"],
    ["Optimizer", "Adam (lr=1e-3)"],
    ["Loss Function", "Sparse Categorical Cross-Entropy"],
    ["Metric", "Accuracy"],
    ["L2 Regularization", "kernel_regularizer=l2(1e-4)"],
    ["Dropout Rates", "Dense 256: 0.5 | Dense 128: 0.3"],
    ["EarlyStopping", "monitor='val_accuracy', patience=15"],
    ["ReduceLROnPlateau", "monitor='val_loss', factor=0.5, patience=5"]
]
tbl2 = ax2.table(cellText=data2, colLabels=["Hyperparameter", "Configuration"], loc='center', cellLoc='center')
tbl2.auto_set_font_size(False); tbl2.set_fontsize(14); tbl2.scale(1, 2.2)
for (r, c), cell in tbl2.get_celld().items():
    if r == 0:
        cell.set_facecolor("#e0e0e0")
        cell.set_text_props(color=TEXT_MAIN, fontweight="black", ha="center")
    else:
        cell.set_facecolor("#ffffff" if r % 2 == 0 else "#f9f9f9")
        cell.set_text_props(color=TEXT_MAIN, fontweight="bold")
    cell.set_edgecolor(TEXT_MAIN); cell.set_linewidth(1.5)

# --- TEXT: Detailed Explanations ---
ax3 = fig.add_subplot(gs[2])
ax3.axis('off')
ax3.set_title("Detailed Technical Explanations", fontsize=18, fontweight='black', pad=10)
explanations = (
    "$\\bullet$ GlobalAveragePooling2D: Preferred over Flatten(). Flatten generates 25+ million parameters leading\n"
    "  to severe overfitting. GlobalAveragePooling2D reduces the feature map to a single value, dramatically reducing parameter count.\n\n"
    "$\\bullet$ L2 Regularization: Applied to all Conv2D and Dense(256) layers. Penalizes large weights to prevent the model\n"
    "  from learning unnecessary complexities.\n\n"
    "$\\bullet$ Dropout Rates: Post Dense(256) $\\rightarrow$ Dropout(0.5): 50% neurons randomly deactivated; provides strong regularization in the\n"
    "  large layer. Post Dense(128) $\\rightarrow$ Dropout(0.3): Lighter pressure on narrow layer, preserving info for final classification.\n\n"
    "$\\bullet$ Batch Size = 32: Provides an optimal balance between training speed and generalization. (8 $\\rightarrow$ too slow; 128 $\\rightarrow$ generalization loss).\n\n"
    "$\\bullet$ EarlyStopping: Training stops if val_accuracy does not improve for 15 epochs, and the best weights are restored.\n\n"
    "$\\bullet$ ReduceLROnPlateau: Learning rate is halved when val_loss plateaus for 5 epochs. Minimum learning rate: 1e-6.\n"
    "  Allows the model to fine-tune."
)
ax3.text(0.05, 0.9, explanations, ha='left', va='top', fontsize=15, fontweight='bold', color=TEXT_MAIN, linespacing=1.8)

fig.suptitle("CNN ARCHITECTURE AND HYPERPARAMETER CHOICES", fontsize=24, fontweight='black', y=0.98)
plt.tight_layout(pad=3.0, rect=[0, 0, 1, 0.95])
plt.savefig('4_Hyperparameter_and_Architecture_Report.png', dpi=300, bbox_inches='tight', facecolor=BG)
plt.close()

print("✅ ALL REPORTS GENERATED SUCCESSFULLY!")
print("You can check the new files starting with '1_', '2_', '3_' and '4_' in your directory.")