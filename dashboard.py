import streamlit as st
import pandas as pd
import json
import time
import os
import plotly.express as px
from datetime import datetime

# ==========================================
# AYARLAR VE CSS (Ortak Tasarım)
# ==========================================
st.set_page_config(page_title="AI Smart Fridge Pro", page_icon="⚡", layout="wide")

css = """
<style>
/* Özgün ve Lüks Koyu Tema (Neon & Glassmorphism) */
.stApp {
    background: radial-gradient(circle at top right, #0a1128 0%, #040710 100%);
    color: #e2e8f0;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(10, 17, 40, 0.95) 0%, rgba(4, 7, 16, 0.95) 100%) !important;
    border-right: 1px solid rgba(56, 189, 248, 0.2);
}
[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* Kayan Yazı (Live Ticker) Tasarımı */
.ticker-wrap {
    width: 100%;
    overflow: hidden;
    background: linear-gradient(90deg, rgba(15, 23, 42, 0.1), rgba(56, 189, 248, 0.15), rgba(15, 23, 42, 0.1));
    border: 1px solid rgba(56, 189, 248, 0.3);
    padding: 10px 0;
    margin-bottom: 25px;
    border-radius: 12px;
    box-shadow: 0 0 15px rgba(56, 189, 248, 0.1);
}
.ticker-move {
    display: inline-block;
    white-space: nowrap;
    padding-left: 100%;
    animation: ticker 30s linear infinite;
}
.ticker-move:hover {
    animation-play-state: paused;
}
.ticker-item {
    display: inline-block;
    padding: 0 25px;
    color: #cbd5e1;
    font-weight: 500;
    font-size: 14px;
    letter-spacing: 0.5px;
}
.ticker-item span {
    color: #38bdf8;
    font-weight: bold;
    margin-right: 5px;
}
@keyframes ticker {
    0% { transform: translateX(0); }
    100% { transform: translateX(-100%); }
}

div[data-testid="stTabs"] > div[role="tablist"] {
    gap: 12px;
    background-color: transparent;
    padding-bottom: 15px;
    border-bottom: 0;
}
/* Sekme altındaki kırmızı/pembe hareketli çizgiyi kesin olarak gizle */
[data-testid="stTabs"] [data-baseweb="tab-highlight"],
[data-baseweb="tab-highlight"],
div[data-baseweb="tab-border"] {
    display: none !important;
    background-color: transparent !important;
    border-bottom: none !important;
}
button[role="tab"] {
    background-color: rgba(15, 23, 42, 0.6) !important;
    backdrop-filter: blur(8px);
    border: 1px solid rgba(56, 189, 248, 0.2) !important;
    border-radius: 14px !important;
    padding: 12px 24px !important;
    color: #94a3b8 !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px;
    transition: all 0.3s ease;
}
button[role="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%) !important;
    color: #ffffff !important;
    border-color: #38bdf8 !important;
    box-shadow: 0 0 15px rgba(56, 189, 248, 0.3);
}

/* Glassmorphism Kart Tasarımı */
.mobile-card {
    background: linear-gradient(145deg, rgba(15, 23, 42, 0.8), rgba(2, 6, 23, 0.9));
    backdrop-filter: blur(12px);
    border: 1px solid rgba(56, 189, 248, 0.15);
    border-radius: 24px;
    padding: 28px;
    margin-bottom: 25px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    position: relative;
    overflow: hidden;
}
.mobile-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; width: 100%; height: 4px;
    background: linear-gradient(90deg, #38bdf8, #818cf8);
}
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 18px;
}
.icon-box {
    background: rgba(56, 189, 248, 0.1);
    width: 48px;
    height: 48px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    border: 1px solid rgba(56, 189, 248, 0.2);
}
.detail-btn {
    background: rgba(56, 189, 248, 0.05);
    border: 1px solid rgba(56, 189, 248, 0.3);
    color: #38bdf8;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.card-title {
    color: #94a3b8;
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 8px;
    letter-spacing: 0.5px;
}
.card-value {
    color: #ffffff;
    font-size: 36px;
    font-weight: 800;
    margin-bottom: 12px;
    background: -webkit-linear-gradient(#ffffff, #94a3b8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.card-subtitle {
    color: #64748b;
    font-size: 13px;
    line-height: 1.5;
}

.list-title {
    color: #f8fafc;
    font-size: 18px;
    font-weight: 700;
    margin-top: 15px;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.list-title::before {
    content: '';
    display: block;
    width: 4px;
    height: 18px;
    background-color: #38bdf8;
    border-radius: 4px;
}

.list-item {
    background: rgba(15, 23, 42, 0.5);
    border: 1px solid rgba(51, 65, 85, 0.5);
    border-radius: 16px;
    padding: 16px 20px;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.list-item:hover {
    transform: translateX(5px);
    border-color: rgba(56, 189, 248, 0.4);
}
.item-number {
    background: linear-gradient(135deg, #38bdf8 0%, #3b82f6 100%);
    color: #ffffff;
    width: 32px;
    height: 32px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 14px;
    margin-right: 18px;
    flex-shrink: 0;
    box-shadow: 0 2px 10px rgba(56, 189, 248, 0.3);
}
.item-text {
    color: #e2e8f0;
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 0.3px;
}

.comment-box {
    background: linear-gradient(145deg, rgba(30, 58, 138, 0.15), rgba(15, 23, 42, 0.6));
    border: 1px dashed rgba(56, 189, 248, 0.3);
    border-radius: 16px;
    padding: 22px;
    margin-top: 25px;
    margin-bottom: 30px;
    position: relative;
}
.comment-title {
    color: #38bdf8;
    font-weight: 700;
    font-size: 13px;
    margin-bottom: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.comment-title::before {
    content: '💡';
    font-size: 16px;
}
.comment-text {
    color: #94a3b8;
    font-size: 14px;
    line-height: 1.6;
}

/* Sidebar Radio Butonlarını Şık Sekmelere (Pill/Tab) Çevirme */
div.stRadio > div[role="radiogroup"] {
    gap: 8px;
    flex-direction: column;
}
/* Sadece yatay (horizontal) radio'ları yan yana dizmek için */
div.stRadio[data-testid="stRadio"] > div[role="radiogroup"][aria-orientation="horizontal"] {
    flex-direction: row;
}
div.stRadio > div[role="radiogroup"] > label {
    background: rgba(15, 23, 42, 0.5) !important;
    border: 1px solid rgba(56, 189, 248, 0.2) !important;
    border-radius: 12px !important;
    padding: 10px 15px !important;
    transition: all 0.3s ease;
    cursor: pointer;
    flex: 1;
    display: flex;
    align-items: center;
}
div.stRadio > div[role="radiogroup"] > label:hover {
    border-color: rgba(56, 189, 248, 0.5) !important;
    background: rgba(30, 58, 138, 0.4) !important;
}
div.stRadio > div[role="radiogroup"] > label[data-checked="true"] {
    background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%) !important;
    border-color: #38bdf8 !important;
    box-shadow: 0 0 12px rgba(56, 189, 248, 0.3);
}
/* Radio içindeki yazıların tasarımı */
div.stRadio > div[role="radiogroup"] > label p {
    font-weight: 600 !important;
    color: #e2e8f0 !important;
    font-size: 14px !important;
    font-family: 'Inter', 'Helvetica Neue', sans-serif !important;
    margin-bottom: 0 !important;
}
/* Orijinal yuvarlak seçim ikonunu hafif küçültme (silmeden) */
div.stRadio > div[role="radiogroup"] > label div:first-child {
    transform: scale(0.85);
    margin-right: 8px;
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

def render_mobile_ui(icon, title, value, subtitle, list_data, comment_title, comment_text, detail_btn_text):
    html = f'<div class="mobile-card">'
    html += f'<div class="card-header">'
    html += f'<div class="icon-box">{icon}</div>'
    html += f'<div class="detail-btn">{detail_btn_text}</div>'
    html += f'</div>'
    html += f'<div class="card-title">{title}</div>'
    html += f'<div class="card-value">{value}</div>'
    html += f'<div class="card-subtitle">{subtitle}</div>'
    html += f'</div>'
    html += f'<div class="list-title">{"Veri Listesi" if detail_btn_text == "Durum Özeti" else "Data List"}</div>'
    
    for idx, item in enumerate(list_data):
        html += f'<div class="list-item">'
        html += f'<div class="item-number">{idx+1}</div>'
        html += f'<div class="item-text">{item}</div>'
        html += f'</div>'
        
    html += f'<div class="comment-box">'
    html += f'<div class="comment-title">{comment_title}</div>'
    html += f'<div class="comment-text">{comment_text}</div>'
    html += f'</div>'
    
    st.markdown(html, unsafe_allow_html=True)

# ==========================================
# VERİ OKUMA VE HESAPLAMA
# ==========================================
JSON_DURUM = "sistem_durumu.json"
JSON_KATALOG = "urun_katalogu.json"
CSV_GECMIS = "satis_gecmisi.csv"
RESIM_YOLU = "test_resmi.jpeg"

try:
    with open(JSON_KATALOG, "r", encoding="utf-8") as f:
        katalog = json.load(f)
except:
    katalog = {}
try:
    with open(JSON_DURUM, "r", encoding="utf-8") as f:
        durum = json.load(f)
except:
    durum = {"stok": {}}
try:
    df_gecmis_ham = pd.read_csv(CSV_GECMIS)
    df_gecmis_ham['Tarih'] = pd.to_datetime(df_gecmis_ham['Tarih'])
except:
    df_gecmis_ham = pd.DataFrame(columns=["Tarih", "Urun", "Islem", "Adet"])


# ==========================================
# YAN MENÜ (SIDEBAR) & SEÇİMLER
# ==========================================
st.sidebar.markdown("**Dil / Language**")
secilen_dil = st.sidebar.radio("Dil", ["TR", "EN"], horizontal=True, label_visibility="collapsed")
st.sidebar.markdown("---")

st.sidebar.markdown("**Arayüz / Interface**")
arayuz_tipi = st.sidebar.radio(
    "Arayüz", 
    ["📱 Mobil Arayüz", "💻 Web Arayüz"] if secilen_dil == "TR" else ["📱 Mobile UI", "💻 Web UI"],
    label_visibility="collapsed"
)
st.sidebar.markdown("---")

# ZAMAN FİLTRESİ (YENİ ÖZELLİK)
st.sidebar.markdown("**Zaman Filtresi / Time Filter**")
zaman_secenekleri = ["Tüm Zamanlar", "Son 7 Gün", "Bugün"] if secilen_dil == "TR" else ["All Time", "Last 7 Days", "Today"]
secilen_zaman = st.sidebar.radio("Zaman Filtresi", zaman_secenekleri, label_visibility="collapsed")

st.sidebar.markdown("---")

# OTOMATİK YENİLE BUTONU (Yeni Tasarım ve Konum)
st.sidebar.markdown("**Otomatik Yenile / Auto Refresh**")
yenile_secenekleri = ["🔴 Kapalı", "🟢 Açık"] if secilen_dil == "TR" else ["🔴 Off", "🟢 On"]
otomatik_yenile_secim = st.sidebar.radio("Otomatik Yenile", yenile_secenekleri, label_visibility="collapsed")
otomatik_yenile = "Açık" in otomatik_yenile_secim or "On" in otomatik_yenile_secim

st.sidebar.markdown("---")
import base64
st.sidebar.markdown("**Son Kamera Görüntüsü**" if secilen_dil == "TR" else "**Last Camera Capture**")
if os.path.exists(RESIM_YOLU):
    with open(RESIM_YOLU, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    img_html = f"""
    <div style="background: linear-gradient(145deg, rgba(15, 23, 42, 0.4), rgba(2, 6, 23, 0.6));
                padding: 12px; border-radius: 18px; border: 1px dashed rgba(56, 189, 248, 0.3);
                box-shadow: 0 4px 15px rgba(0,0,0,0.3); text-align: center; margin-bottom: 20px;">
        <img src="data:image/jpeg;base64,{encoded_string}" style="border-radius: 12px; width: 75%; height: auto; border: 1px solid rgba(56, 189, 248, 0.2);">
    </div>
    """
    st.sidebar.markdown(img_html, unsafe_allow_html=True)
else:
    st.sidebar.warning("Görsel yok" if secilen_dil == "TR" else "No image")

detail_btn_text = "Durum Özeti" if secilen_dil == "TR" else "Status Summary"
system_note_text = "Sistem Notu" if secilen_dil == "TR" else "System Note"

# ==========================================
# VERİ FİLTRELEME
# ==========================================
df_gecmis = df_gecmis_ham.copy()

if not df_gecmis.empty:
    if "Bugün" in secilen_zaman or "Today" in secilen_zaman:
        df_gecmis = df_gecmis[df_gecmis['Tarih'] >= pd.Timestamp.now().normalize()]
    elif "Son 7" in secilen_zaman or "Last 7" in secilen_zaman:
        df_gecmis = df_gecmis[df_gecmis['Tarih'] >= (pd.Timestamp.now() - pd.Timedelta(days=7))]

df_satis = df_gecmis[df_gecmis['Islem'] == "Alındı"].copy()
dolap_acilma_sayisi = len(df_gecmis)

# ==========================================
# CANLI BİLDİRİM AKIŞI (TİCKER)
# ==========================================
if not df_gecmis_ham.empty:
    son_olaylar_df = df_gecmis_ham.sort_values(by="Tarih", ascending=False).head(5)
    ticker_html = "<div class='ticker-wrap'><div class='ticker-move'>"
    for _, row in son_olaylar_df.iterrows():
        saat_str = row["Tarih"].strftime("%H:%M")
        urun_adi = row["Urun"].replace("_", " ")
        islem_tr = row["Islem"]
        islem_en = "Taken" if row["Islem"] == "Alındı" else "Added"
        islem_metni = islem_tr if secilen_dil == "TR" else islem_en
        ikon = "🔴" if row["Islem"] == "Alındı" else "🟢"
        
        ticker_html += f"<div class='ticker-item'><span>[{saat_str}]</span> {urun_adi} {islem_metni} {ikon}</div>"
    ticker_html += "</div></div>"
    st.markdown(ticker_html, unsafe_allow_html=True)


# ==========================================
# ORTAK VERİ HESAPLAMA (TÜM MODÜLLER İÇİN)
# ==========================================
# 1. Açılış Modülü
gunler_tr = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
gunler_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
gun_isimleri = gunler_tr if secilen_dil == "TR" else gunler_en

liste_acilis = []
yorum_acilis = "-"
if not df_gecmis.empty:
    df_gecmis['Gun_Index'] = df_gecmis['Tarih'].dt.dayofweek
    gunluk_veri = df_gecmis['Gun_Index'].value_counts().sort_index()
    en_yogun_gun_idx = gunluk_veri.idxmax() if not gunluk_veri.empty else 0
    for idx, count in gunluk_veri.items():
        liste_acilis.append(f"{gun_isimleri[idx]}: {count}")
    yorum_acilis = f"{gun_isimleri[en_yogun_gun_idx]} günü kullanım zirve yaptığı için satış yoğunluğu ile ilişkilendirilebilir." if secilen_dil == "TR" else f"Peak usage on {gun_isimleri[en_yogun_gun_idx]} correlates directly with sales volume."

# 2. Stok Modülü
toplam_stok = sum(durum['stok'].values())
liste_stok = []
kritik_var = False
pie_data = []
for urun, stok in durum['stok'].items():
    isim = urun.replace("_", " ")
    if urun in katalog and stok <= katalog[urun]['kritik_esik']:
        kritik_var = True
    liste_stok.append(f"{isim}: {stok} adet" if secilen_dil == "TR" else f"{isim}: {stok} units")
    pie_data.append({"Ürün": isim, "Stok": stok})

yorum_stok = "Stok seviyesi genel olarak yeterli, ancak bazı ürünler kritik seviyeye yaklaşıyor." if secilen_dil == "TR" else "Stock levels are generally sufficient, but some items are approaching critical levels."
if not kritik_var:
    yorum_stok = "Tüm ürünlerin stok durumu ideal seviyede." if secilen_dil == "TR" else "All products are at ideal stock levels."

# 3. Sipariş Modülü
liste_siparis = []
for urun, detay in katalog.items():
    mevcut = durum['stok'].get(urun, 0)
    isim = urun.replace("_", " ")
    if mevcut == 0:
        liste_siparis.append(f"{isim}: Tamamen tükendi!" if secilen_dil == "TR" else f"{isim}: Out of stock!")
    elif mevcut <= detay['kritik_esik']:
        liste_siparis.append(f"{isim}: Kritik stok" if secilen_dil == "TR" else f"{isim}: Critical stock")
    elif mevcut <= detay['kritik_esik'] + 3:
        liste_siparis.append(f"{isim}: Hafta sonuna bitebilir" if secilen_dil == "TR" else f"{isim}: May run out soon")

yorum_siparis = "Sipariş verilmezse hafta sonuna doğru bazı raflarda boşluk oluşabilir." if secilen_dil == "TR" else "Empty shelves are likely by weekend if restocking is not planned."
if not liste_siparis:
    liste_siparis = ["Sipariş gereken ürün yok." if secilen_dil == "TR" else "No items need ordering."]
    yorum_siparis = "Şu anda herhangi bir siparişe gerek duyulmuyor." if secilen_dil == "TR" else "No immediate restocking required."

# 4. Trend Modülü
if not df_satis.empty:
    en_cok_satan = df_satis['Urun'].value_counts().idxmax()
    satis_adeti = df_satis['Urun'].value_counts().max()
    df_en_cok = df_satis[df_satis['Urun'] == en_cok_satan].copy()
    df_en_cok['Gun'] = df_en_cok['Tarih'].dt.dayofweek
    en_yogun_gun = df_en_cok['Gun'].mode()[0]
    gun_adi = gun_isimleri[en_yogun_gun]
    df_en_cok['Saat'] = df_en_cok['Tarih'].dt.hour
    en_yogun_saat = df_en_cok['Saat'].mode()[0]
    
    liste_trend = [
        f"Toplam satış: {satis_adeti} adet" if secilen_dil == "TR" else f"Total sales: {satis_adeti} units",
        f"En yoğun gün: {gun_adi}" if secilen_dil == "TR" else f"Peak day: {gun_adi}",
        f"En yoğun saat: {en_yogun_saat}:00 - {en_yogun_saat+2}:00" if secilen_dil == "TR" else f"Peak hours: {en_yogun_saat}:00 - {en_yogun_saat+2}:00",
        f"Tüketim Hızı: Yüksek" if secilen_dil == "TR" else "Burn Rate: High"
    ]
    yorum_trend = "Bu ürün için ekstra stok planlaması yapılması önerilir." if secilen_dil == "TR" else "Extra stock planning is highly recommended for this product."
    baslik_trend = en_cok_satan.replace("_", " ")
else:
    liste_trend = ["Seçili zaman aralığında veri yok" if secilen_dil == "TR" else "No data for selected time"]
    yorum_trend = "-"
    baslik_trend = "Bilinmiyor" if secilen_dil == "TR" else "Unknown"


# ==========================================
# RENDER FONKSİYONLARI (Kapsülleme)
# ==========================================
def draw_acilis():
    render_mobile_ui("🚪", "Açılıp Kapanma Sayısı" if secilen_dil == "TR" else "Door Open Count", f"{dolap_acilma_sayisi} Kez" if secilen_dil == "TR" else f"{dolap_acilma_sayisi} Times", "Filtrelenen zaman aralığındaki açılış sayısı." if secilen_dil == "TR" else "Door accesses in the filtered time frame.", liste_acilis, system_note_text, yorum_acilis, detail_btn_text)

def draw_stok():
    render_mobile_ui("📦", "Stok Durumu" if secilen_dil == "TR" else "Stock Status", f"{toplam_stok} Ürün" if secilen_dil == "TR" else f"{toplam_stok} Items", "Dolapta bulunan toplam ürün miktarı ve stok dağılımı." if secilen_dil == "TR" else "Total items in fridge and stock distribution.", liste_stok, system_note_text, yorum_stok, detail_btn_text)
    if pie_data:
        df_pie = pd.DataFrame(pie_data)
        fig = px.pie(df_pie, values='Stok', names='Ürün', hole=0.4, color_discrete_sequence=px.colors.sequential.Blues_r)
        fig.update_layout(
            height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            font=dict(family="'Inter', 'Helvetica Neue', sans-serif", size=14, color='#cbd5e1'), 
            margin=dict(t=0, b=0, l=0, r=0)
        )
        fig.update_traces(textposition='inside', textinfo='percent+label', textfont_size=15, textfont_color="#ffffff", textfont_family="'Inter', 'Helvetica Neue', sans-serif")
        st.plotly_chart(fig, width='stretch')

def draw_siparis():
    render_mobile_ui("🛒", "Sipariş Gerekenler" if secilen_dil == "TR" else "Items Needing Order", f"{len([x for x in liste_siparis if 'yok' not in x and 'No items' not in x])} Ürün" if secilen_dil == "TR" else f"{len([x for x in liste_siparis if 'yok' not in x and 'No items' not in x])} Items", "Stok seviyesine göre sipariş edilmesi gereken ürünler." if secilen_dil == "TR" else "Items to be ordered based on current burn rate.", liste_siparis, system_note_text, yorum_siparis, detail_btn_text)

def draw_trend():
    render_mobile_ui("🏆", "En Çok Satılan Ürün" if secilen_dil == "TR" else "Top Selling Product", baslik_trend, "Seçili zaman aralığında satışı en yüksek ürün." if secilen_dil == "TR" else "Highest performing product in filtered time.", liste_trend, system_note_text, yorum_trend, detail_btn_text)
    
    # ------------------ EN ÇOK SATANLAR GRAFİĞİ ------------------
    if not df_satis.empty:
        baslik_tr = f"En Çok Satılanlar ({secilen_zaman})"
        baslik_en = f"Top Sellers ({secilen_zaman})"
        st.markdown(f"<div class='list-title'>{baslik_tr if secilen_dil == 'TR' else baslik_en}</div>", unsafe_allow_html=True)
        
        # Veriyi hazırla: Ürün bazında toplam satış (Büyükten küçüğe sıralı)
        top_sellers = df_satis['Urun'].value_counts().reset_index()
        top_sellers.columns = ['Urun', 'Satis']
        top_sellers['Urun'] = top_sellers['Urun'].str.replace('_', ' ') # Alt tireleri temizle
        
        fig_bar = px.bar(
            top_sellers, x="Satis", y="Urun", orientation='h', text="Satis",
            color="Satis", color_continuous_scale="Blues",
            labels={"Satis": "Satış Adedi", "Urun": ""} if secilen_dil == "TR" else {"Satis": "Sales Count", "Urun": ""}
        )
        # Grafiği koyu temaya uydur ve fontları estetikleştir
        fig_bar.update_layout(
            height=250,
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)', 
            font=dict(family="'Inter', 'Helvetica Neue', sans-serif", size=13, color='#cbd5e1'), 
            margin=dict(t=10, b=10, l=10, r=10),
            yaxis={'categoryorder': 'total ascending', 'tickfont': dict(size=14, family="'Inter', 'Helvetica Neue', sans-serif")},
            xaxis={'visible': False}, # Alt ekseni gizle, zaten barların üstünde sayı yazıyor
            showlegend=False,
            coloraxis_showscale=False
        )
        fig_bar.update_traces(textfont_size=16, textfont_family="'Inter', 'Helvetica Neue', sans-serif", textangle=0, textposition="outside", cliponaxis=False)
        st.plotly_chart(fig_bar, width='stretch')


# ==========================================
# ANA EKRAN YERLEŞİMİ (LAYOUT)
# ==========================================
if "Mobil" in arayuz_tipi or "Mobile" in arayuz_tipi:
    col_left, col_mid, col_right = st.columns([1, 2, 1])
    with col_mid:
        tab_isimleri = ["🚪 Kapak", "📦 Stok", "🛒 Sipariş", "🏆 Analiz"] if secilen_dil == "TR" else ["🚪 Access", "📦 Stock", "🛒 Orders", "🏆 Analytics"]
        t1, t2, t3, t4 = st.tabs(tab_isimleri)
        with t1: draw_acilis()
        with t2: draw_stok()
        with t3: draw_siparis()
        with t4: draw_trend()
else:
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1: draw_acilis()
    with row1_col2: draw_stok()
    
    st.markdown("<br>", unsafe_allow_html=True)
    row2_col1, row2_col2 = st.columns(2)
    with row2_col1: draw_siparis()
    with row2_col2: draw_trend()

if otomatik_yenile:
    time.sleep(2)
    st.rerun()