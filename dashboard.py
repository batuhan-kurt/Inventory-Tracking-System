import streamlit as st
import pandas as pd
import json
import time
import os
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import fuzzy_engine as fe
import base64

# ==========================================
# AYARLAR VE CSS (Ortak Tasarım)
# ==========================================
st.set_page_config(page_title="AI Smart Fridge Pro", page_icon="✦", layout="wide")

css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* --- 1. GLOBAL & TYPOGRAPHY --- */
* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}

.stApp {
    background: radial-gradient(circle at top center, #111827 0%, #030712 100%) !important;
    color: #f1f5f9;
}

/* Streamlit Header Gizleme ve Sidebar Glassmorphism */
header[data-testid="stHeader"] { background: transparent !important; }

/* Sidebar Ana Kasa */
[data-testid="stSidebar"] {
    background: rgba(17, 24, 39, 0.65) !important;
    backdrop-filter: blur(30px) saturate(150%);
    -webkit-backdrop-filter: blur(30px) saturate(150%);
    border-right: 1px solid rgba(255,255,255,0.05);
}

/* Sidebar İçerisindeki Yazı Tipleri (Premium Font) */
[data-testid="stSidebar"] * {
    font-family: 'Inter', -apple-system, sans-serif !important;
    color: #f8fafc !important; /* PARLAK BEYAZ YAZILAR */
}
[data-testid="stSidebar"] p, [data-testid="stSidebar"] div, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {
    font-weight: 600 !important;
    font-size: 15px !important;
    letter-spacing: 0.5px;
    color: #ffffff !important;
}
/* Özel Başlık Gradientleri */
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    background: linear-gradient(135deg, #ffffff 0%, #9ca3af 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
}

/* Sidebar collapse butonunu ("keyboard / double arrow") tamamen gizle */
[data-testid="stSidebarCollapseButton"] { display: none !important; }
[data-testid="stSidebarNav"] { display: none !important; }
button[title*="sidebar"], button[aria-label*="sidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* --- 2. NATIVE STREAMLIT COMPONENT OVERRIDES (Müthiş Tasarım Entegrasyonu) --- */

/* Dataframe (Tablo) Tasarımları */
[data-testid="stDataFrame"] {
    background: rgba(31, 41, 55, 0.4);
    backdrop-filter: blur(20px);
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.05);
    padding: 10px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}
[data-testid="stDataFrame"] th {
    background-color: rgba(0,0,0,0.3) !important;
    color: #38bdf8 !important;
    font-weight: 700 !important;
    border-bottom: 2px solid rgba(56, 189, 248, 0.3) !important;
}
[data-testid="stDataFrame"] td {
    color: #e2e8f0 !important;
    border-bottom: 1px solid rgba(255,255,255,0.03) !important;
}

/* Streamlit Header'ları (h1, h2, h3, markdown başlıkları) */
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
    font-weight: 800;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, #f8fafc 0%, #94a3b8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

/* Streamlit Butonlar (Sidebar ve Ana Ekran) */
div.stButton > button, div.stDownloadButton > button {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
    color: #f8fafc !important;
    border: 1px solid rgba(56, 189, 248, 0.3) !important;
    border-radius: 12px !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}
div.stButton > button:hover, div.stDownloadButton > button:hover {
    border-color: #38bdf8 !important;
    box-shadow: 0 10px 25px rgba(56,189,248,0.4) !important;
    transform: translateY(-2px) scale(1.02);
}

/* Sidebar Butonları Daha Görünür Olsun (Tamamen Eşit Stil) */
[data-testid="stSidebar"] button[kind="primary"],
[data-testid="stSidebar"] button[kind="secondary"],
[data-testid="stSidebar"] button[data-testid="baseButton-secondary"],
[data-testid="stSidebar"] div.stButton > button, 
[data-testid="stSidebar"] div.stDownloadButton > button {
    background: linear-gradient(135deg, #334155 0%, #1e293b 100%) !important;
    border: 1px solid rgba(56, 189, 248, 0.8) !important;
    box-shadow: 0 4px 20px rgba(56,189,248,0.2) !important;
    color: #ffffff !important;
    border-radius: 12px !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    min-height: 46px !important;
}
[data-testid="stSidebar"] button[kind="primary"]:hover,
[data-testid="stSidebar"] button[kind="secondary"]:hover,
[data-testid="stSidebar"] button[data-testid="baseButton-secondary"]:hover,
[data-testid="stSidebar"] div.stButton > button:hover, 
[data-testid="stSidebar"] div.stDownloadButton > button:hover {
    border-color: #38bdf8 !important;
    box-shadow: 0 10px 25px rgba(56,189,248,0.5) !important;
    transform: translateY(-2px) scale(1.02) !important;
}

/* Sekmeler (Tabs) */
div[data-testid="stTabs"] > div[role="tablist"] {
    gap: 8px;
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(15px);
    padding: 8px;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.05);
    box-shadow: 0 8px 25px rgba(0,0,0,0.3);
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"], [data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] { display: none !important; }
button[role="tab"] {
    background: transparent !important; border: none !important;
    border-radius: 12px !important; padding: 12px 24px !important;
    color: #94a3b8 !important; font-size: 15px !important; font-weight: 600 !important;
    transition: all 0.3s ease;
}
button[role="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%) !important;
    color: #ffffff !important;
    border: 1px solid rgba(56, 189, 248, 0.2) !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}

/* Metric (Sayısal Göstergeler) */
div[data-testid="stMetricValue"] {
    font-size: 46px !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -2px;
}
div[data-testid="stMetricLabel"] {
    font-size: 14px !important; color: #94a3b8 !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 1px;
}

/* Info, Success, Error Box (st.info vb.) */
div[data-testid="stAlert"] {
    background: rgba(30, 41, 59, 0.5) !important;
    backdrop-filter: blur(15px);
    border-radius: 16px !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
}

/* Radio Button Özelleştirmesi */
div.stRadio > div[role="radiogroup"] {
    background: rgba(0,0,0,0.2);
    padding: 12px 16px !important;
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.05);
}
div.stRadio > div[role="radiogroup"] > label {
    color: #ffffff !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    font-family: 'Inter', 'Helvetica Neue', sans-serif !important;
    margin-bottom: 0 !important;
}

/* --- 3. KENDİ HTML KARTLARIMIZ İÇİN (Apple Style Smooth) --- */
@keyframes fadeInUp { 0% { opacity: 0; transform: translateY(20px) scale(0.99); } 100% { opacity: 1; transform: translateY(0) scale(1); } }
.mobile-card { animation: fadeInUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
.mobile-card:nth-child(1) { animation-delay: 0.1s; } .mobile-card:nth-child(2) { animation-delay: 0.2s; } .mobile-card:nth-child(3) { animation-delay: 0.3s; }

.mobile-card {
    background: linear-gradient(145deg, rgba(31, 41, 55, 0.4), rgba(17, 24, 39, 0.7));
    backdrop-filter: blur(30px) saturate(150%);
    -webkit-backdrop-filter: blur(30px) saturate(150%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 28px;
    padding: 30px;
    margin-bottom: 25px;
    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
    position: relative;
    overflow: hidden;
    transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}
.mobile-card::before {
    content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 4px;
    background: linear-gradient(90deg, #38bdf8, #818cf8, #34d399);
    opacity: 0.5; transition: opacity 0.4s;
}
.mobile-card:hover {
    transform: translateY(-8px) scale(1.01);
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
}
.mobile-card:hover::before { opacity: 1; }

.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.icon-box {
    background: rgba(56, 189, 248, 0.1);
    width: 56px; height: 56px; border-radius: 18px;
    display: flex; align-items: center; justify-content: center;
    font-size: 28px; border: 1px solid rgba(56, 189, 248, 0.2);
    box-shadow: inset 0 0 15px rgba(56, 189, 248, 0.05);
}
.detail-btn { background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.3); color: #38bdf8; padding: 6px 14px; border-radius: 20px; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; transition: all 0.3s; }
.detail-btn:hover { background: #38bdf8; color: #020617; }

.card-title { font-size: 13px; color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 6px; }
.card-value { font-size: 46px; font-weight: 800; color: #f8fafc; line-height: 1; margin-bottom: 8px; letter-spacing: -2px; }
.card-subtitle { font-size: 14px; color: #38bdf8; font-weight: 500; }

.list-title { font-size: 12px; color: #64748b; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin: 24px 0 12px 0; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px; }
.list-item { display: flex; align-items: center; gap: 12px; padding: 12px 16px; background: rgba(0,0,0,0.2); border-radius: 16px; margin-bottom: 8px; border: 1px solid rgba(255,255,255,0.03); transition: all 0.3s; }
.list-item:hover { background: rgba(56, 189, 248, 0.08); transform: translateX(5px); border-color: rgba(56, 189, 248, 0.2); }
.item-number { width: 30px; height: 30px; background: rgba(56, 189, 248, 0.15); color: #38bdf8; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; }
.item-text { font-size: 15px; color: #e2e8f0; font-weight: 500; }

.comment-box { background: linear-gradient(135deg, rgba(15, 23, 42, 0.7), rgba(30, 41, 59, 0.8)); backdrop-filter: blur(25px); border-left: 4px solid #38bdf8; border-right: 1px solid rgba(255,255,255,0.05); border-top: 1px solid rgba(255,255,255,0.05); border-bottom: 1px solid rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; margin-top: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
.comment-title { font-size: 12px; color: #38bdf8; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
.comment-text { font-size: 15px; color: #cbd5e1; line-height: 1.6; font-weight: 400; }


.apple-box {
    background: linear-gradient(145deg, rgba(31, 41, 55, 0.5), rgba(17, 24, 39, 0.8));
    backdrop-filter: blur(25px) saturate(180%);
    -webkit-backdrop-filter: blur(25px) saturate(180%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 24px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
    transition: transform 0.4s ease, box-shadow 0.4s ease;
}
.apple-box:hover {
    transform: translateY(-4px);
    box-shadow: 0 20px 45px rgba(0, 0, 0, 0.4);
    border-color: rgba(255, 255, 255, 0.15);
}

/* --- 4. TİCKER (KAYAN YAZI) --- */
.ticker-wrap { width: 100%; overflow: hidden; background: linear-gradient(90deg, rgba(15, 23, 42, 0.2), rgba(56, 189, 248, 0.1), rgba(15, 23, 42, 0.2)); border: 1px solid rgba(56, 189, 248, 0.2); padding: 14px 0; margin-bottom: 30px; border-radius: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }
.ticker-move { display: inline-block; white-space: nowrap; padding-left: 100%; animation: ticker 25s linear infinite; }
.ticker-move:hover { animation-play-state: paused; }
.ticker-item { display: inline-block; padding: 0 30px; color: #cbd5e1; font-weight: 500; font-size: 15px; }
.ticker-item span { color: #38bdf8; font-weight: 700; margin-right: 8px; }
@keyframes ticker { 0% { transform: translateX(0); } 100% { transform: translateX(-100%); } }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

def clean_html(html):
    """Streamlit markdown'ın indented HTML'i kod bloğu olarak yorumlamasını önler."""
    return ''.join(line.strip() for line in html.split('\n') if line.strip())

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
JSON_DURUM  = "sistem_durumu.json"
JSON_KATALOG = "urun_katalogu.json"
CSV_GECMIS  = "satis_gecmisi.csv"
RESIM_YOLU  = "dolap_oncesi.jpg"   # Gerçek dolap kamera görüntüsü

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
    df_gecmis_ham = pd.read_csv(CSV_GECMIS, names=["Tarih", "Urun", "Islem", "Adet"])
    df_gecmis_ham['Tarih'] = pd.to_datetime(df_gecmis_ham['Tarih'], errors='coerce')
    df_gecmis_ham = df_gecmis_ham.dropna(subset=['Tarih'])
except: 
    df_gecmis_ham = pd.DataFrame(columns=["Tarih", "Urun", "Islem", "Adet"])


# ==========================================
# YAN MENÜ (SIDEBAR) & SEÇİMLER
# ==========================================
st.sidebar.markdown("**Dil / Language**")
secilen_dil = st.sidebar.radio("Dil", ["TR", "EN"], horizontal=True, label_visibility="collapsed")
st.sidebar.markdown("---")

st.sidebar.markdown("**Sayfa / Page**" if secilen_dil == "TR" else "**Page**")
secilen_sayfa = st.sidebar.radio("Sayfa", 
                                ["✦ Ana Dashboard", "❖ Akıllı Tahminler", "⚲ Canlı Operasyon", "⌘ Kamera & Görüş"] if secilen_dil == "TR" else ["✦ Main Dashboard", "❖ Smart Predictions", "⚲ Live Operations", "⌘ Camera & Vision"], 
                                label_visibility="collapsed")
st.sidebar.markdown("---")

st.sidebar.markdown("**Arayüz / Interface**")
arayuz_tipi = st.sidebar.radio(
    "Arayüz", 
    ["📱 Mobil Arayüz", "💻 Web Arayüz"] if secilen_dil == "TR" else ["📱 Mobile UI", "💻 Web UI"],
    index=1,
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
yenile_secenekleri = ["⌘ Kapalı", "⚲ Açık"] if secilen_dil == "TR" else ["⌘ Off", "⚲ On"]
otomatik_yenile_secim = st.sidebar.radio("Otomatik Yenile", yenile_secenekleri, label_visibility="collapsed")
otomatik_yenile = "Açık" in otomatik_yenile_secim or "On" in otomatik_yenile_secim

# Kamera görüntüsü sidebar'dan kaldırıldı ve kendi özel sayfasına (Kamera & Görüş) taşındı.

# Sistemi sıfırla butonu aşağıya taşındı
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
# FUZZY ENGINE — VERİ HAZIRLIĞI
# ==========================================
_now = pd.Timestamp.now()
_saat = _now.hour

# Son 1 saatte kapı açılımı (fuzzy kapı analizi için)
_acilma_son1saat = 0
if not df_gecmis_ham.empty:
    _son1saat_df = df_gecmis_ham[df_gecmis_ham['Tarih'] >= (_now - pd.Timedelta(hours=1))]
    _acilma_son1saat = len(_son1saat_df)

# Ürün bazında saatlik tüketim hızı (son 24 saat)
_tuketim_saatlik = {}
if not df_gecmis_ham.empty:
    _son24 = df_gecmis_ham[
        (df_gecmis_ham['Tarih'] >= (_now - pd.Timedelta(hours=24))) &
        (df_gecmis_ham['Islem'].str.contains('Al', na=False))
    ]
    _sayim = _son24.groupby('Urun').size()
    for _u in durum['stok']:
        _tuketim_saatlik[_u] = float(_sayim.get(_u, 0)) / 24.0
else:
    for _u in durum['stok']:
        _tuketim_saatlik[_u] = 0.0

# Tüm ürünler için fuzzy analiz
_fuzzy_urun = []
for _urun, _stok in durum['stok'].items():
    _bas = katalog.get(_urun, {}).get('baslangic_stok', 20)
    _sonuc = fe.urun_analiz(_urun, _stok, _bas, _tuketim_saatlik.get(_urun, 0.0), dil=secilen_dil)
    _fuzzy_urun.append(_sonuc)

# Sekme bazlı fuzzy özetleri
_fz_kapi    = fe.kapi_analiz(_acilma_son1saat, _saat, dil=secilen_dil)
_fz_stok    = fe.stok_tab_analiz(_fuzzy_urun, dil=secilen_dil)
_fz_siparis = fe.siparis_tab_analiz(_fuzzy_urun, dil=secilen_dil)

# Trend analizi için veriler
_satis_7gun = 0
_satis_3gun = 0
if not df_gecmis_ham.empty:
    _s7 = df_gecmis_ham[
        (df_gecmis_ham['Tarih'] >= (_now - pd.Timedelta(days=7))) &
        (df_gecmis_ham['Islem'].str.contains('Al', na=False))
    ]
    _s3 = df_gecmis_ham[
        (df_gecmis_ham['Tarih'] >= (_now - pd.Timedelta(days=3))) &
        (df_gecmis_ham['Islem'].str.contains('Al', na=False))
    ]
    _satis_7gun = len(_s7)
    _satis_3gun = len(_s3)

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
        ikon = "⌘" if row["Islem"] == "Alındı" else "⚲"
        
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
if not df_gecmis.empty:
    df_gecmis['Gun_Index'] = df_gecmis['Tarih'].dt.dayofweek
    gunluk_veri = df_gecmis['Gun_Index'].value_counts().sort_index()
    en_yogun_gun_idx = gunluk_veri.idxmax() if not gunluk_veri.empty else 0
    for idx, count in gunluk_veri.items():
        liste_acilis.append(f"{gun_isimleri[idx]}: {count}")

# Fuzzy kapı yorum kutusu
_kapi_badge = fe.badge_html(_fz_kapi['yogunluk_seviyesi'], _fz_kapi['renk'], dil=secilen_dil)
yorum_acilis = fe.yorum_kutusu(
    f"🧠 {'Bulanık Analiz' if secilen_dil == 'TR' else 'Fuzzy Analytics'} &nbsp; {_kapi_badge}",
    _fz_kapi['aciklama']
)

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
    pie_data.append({"Ürün": isim, "Stok": stok, "Orijinal": urun})

# Fuzzy stok yorum kutusu
_stok_badge = ""
if _fz_stok['en_kritik']:
    _ek = _fz_stok['en_kritik']
    _stok_badge = fe.badge_html(_ek['seviye'], _ek['renk'], _ek['skor'], dil=secilen_dil)
yorum_stok = fe.yorum_kutusu(
    f"🧠 {'Bulanık Analiz' if secilen_dil == 'TR' else 'Fuzzy Analytics'} &nbsp; {_stok_badge}",
    _fz_stok['aciklama']
)

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

# Fuzzy sipariş yorum kutusu
if not liste_siparis:
    liste_siparis = ["Sipariş gereken ürün yok." if secilen_dil == "TR" else "No items need ordering."]
_sp_sev = ("KRİTİK" if secilen_dil == "TR" else "CRITICAL") if _fz_siparis['kritik_sayisi'] > 0 else (("ORTA" if secilen_dil == "TR" else "MEDIUM") if _fz_siparis['orta_sayisi'] > 0 else ("DÜŞÜK" if secilen_dil == "TR" else "LOW"))
_sp_renk = "#dc2626" if _fz_siparis['kritik_sayisi'] > 0 else ("#ca8a04" if _fz_siparis['orta_sayisi'] > 0 else "#16a34a")
_siparis_badge = fe.badge_html(_sp_sev, _sp_renk, dil=secilen_dil)
yorum_siparis = fe.yorum_kutusu(
    f"🧠 {'Bulanık Analiz' if secilen_dil == 'TR' else 'Fuzzy Analytics'} &nbsp; {_siparis_badge}",
    _fz_siparis['aciklama']
)

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
    ]
    baslik_trend = en_cok_satan.replace("_", " ")
    # Fuzzy trend analizi
    _fz_trend = fe.trend_tab_analiz(_satis_7gun, _satis_3gun, en_cok_satan, int(satis_adeti), dil=secilen_dil)
else:
    liste_trend = ["Seçili zaman aralığında veri yok" if secilen_dil == "TR" else "No data for selected time"]
    baslik_trend = "Bilinmiyor" if secilen_dil == "TR" else "Unknown"
    _fz_trend = {"ivme_seviyesi": "VERİ YOK" if secilen_dil=="TR" else "NO DATA", "renk": "#64748b", "aciklama": "Trend analizi için satış verisi gereklidir." if secilen_dil=="TR" else "Sales data required for trend analytics."}

# Fuzzy trend yorum kutusu
_trend_badge = fe.badge_html(_fz_trend['ivme_seviyesi'], _fz_trend['renk'], dil=secilen_dil)
yorum_trend = fe.yorum_kutusu(
    f"🧠 {'Bulanık Analiz' if secilen_dil == 'TR' else 'Fuzzy Analytics'} &nbsp; {_trend_badge}",
    _fz_trend['aciklama']
)

# ==========================================
# DONANIM DURUMU & EXPORT (SIDEBAR)
# ==========================================
st.sidebar.markdown("---")
st.sidebar.markdown("**⚲ Donanım Durumu**" if secilen_dil == "TR" else "**⚲ Hardware Status**")

def check_sensor(filepath, name_tr, name_en):
    if os.path.exists(filepath):
        mtime = os.path.getmtime(filepath)
        age_hours = (time.time() - mtime) / 3600
        if age_hours > (15 / 60):  # 15 dakikadan eskiyse uyku modu/pasif
            status = "Uyku Modu ❖" if secilen_dil == "TR" else "Standby ❖"
            color = "#ca8a04"
        else:
            status = "Aktif ⚲" if secilen_dil == "TR" else "Online ⚲"
            color = "#16a34a"
    else:
        status = "Bağlantı Yok ⌘" if secilen_dil == "TR" else "Offline ⌘"
        color = "#dc2626"
    
    label = name_tr if secilen_dil == "TR" else name_en
    return f"<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:5px; font-size:13px; color:#cbd5e1;'><span>{label}:</span> <strong style='color:{color}; display:flex; align-items:center; gap:4px;'>{status}</strong></div>"

hw_html = "<div style='background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.2); padding: 12px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);'>"
hw_html += check_sensor(RESIM_YOLU, "Kamera (ESP32)", "Camera (ESP32)")
hw_html += check_sensor(JSON_DURUM, "Load Cell (Tartı)", "Load Cell Sensors")
hw_html += check_sensor(CSV_GECMIS, "Veritabanı API", "Database API")
hw_html += "</div>"
st.sidebar.markdown(hw_html, unsafe_allow_html=True)

# ──── SİSTEMİ SIFIRLA VE CSV BUTONLARI (ALT ALTA) ────────────────────────────────────
st.sidebar.markdown("**⌘ Sistem Kontrolü**" if secilen_dil == "TR" else "**⌘ System Control**")
if st.sidebar.button(
    "🗑️ Tüm Veriyi Sıfırla" if secilen_dil == "TR" else "🗑️ Full Reset",
    use_container_width=True,
    help="Stokları 0'a sıfırlar, geçmiş kayıtları temizler ve referans fotoğrafını siler. Test verilerini temizlemek için kullan."
):
    try:
        resp = requests.post("http://localhost:5001/tam_sifirla", timeout=5)
        if resp.status_code == 200:
            st.sidebar.success("✅ Tüm veriler sıfırlandı!" if secilen_dil == "TR" else "✅ All data reset!")
            time.sleep(0.5)
            st.rerun()
        else:
            st.sidebar.error(f"Sunucu hatası: {resp.status_code}")
    except Exception as e:
        st.sidebar.error(f"Sunucu bağlantısı yok\n{e}")

csv_lines = ["Urun_Adi,Mevcut_Stok,Fuzzy_Skoru,Aciliyet_Seviyesi\n"]
for u in _fuzzy_urun:
    csv_lines.append(f"{u['urun']},{u['stok']},{u['skor']},{u['seviye']}\n")
csv_data = "".join(csv_lines)

st.sidebar.download_button(
    label="⬇️ CSV İndir" if secilen_dil == "TR" else "⬇️ Download CSV",
    data=csv_data.encode('utf-8-sig'),
    file_name=f"smart_fridge_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv",
    use_container_width=True
)


# ==========================================
# RENDER FONKSİYONLARI (Kapsülleme)
# ==========================================
def draw_acilis():
    render_mobile_ui("✦", "Açılıp Kapanma Sayısı" if secilen_dil == "TR" else "Door Open Count", f"{dolap_acilma_sayisi} Kez" if secilen_dil == "TR" else f"{dolap_acilma_sayisi} Times", "Filtrelenen zaman aralığındaki açılış sayısı." if secilen_dil == "TR" else "Door accesses in the filtered time frame.", liste_acilis, system_note_text, yorum_acilis, detail_btn_text)
    
    # ------------------ SAATLİK YOĞUNLUK GRAFİĞİ ------------------
    if not df_gecmis.empty:
        baslik_tr = f"Saatlik Aktivite Eğrisi"
        baslik_en = f"Hourly Activity Curve"
        st.markdown(f"<div class='list-title'>{baslik_tr if secilen_dil == 'TR' else baslik_en}</div>", unsafe_allow_html=True)
        
        df_saat = df_gecmis.copy()
        df_saat['Saat'] = df_saat['Tarih'].dt.hour
        saatlik_veri = df_saat.groupby('Saat').size().reset_index(name='Açılım')
        
        tum_saatler = pd.DataFrame({'Saat': range(24)})
        saatlik_veri = pd.merge(tum_saatler, saatlik_veri, on='Saat', how='left').fillna(0)
        
        fig_area = px.area(
            saatlik_veri, x="Saat", y="Açılım",
            labels={"Saat": "Saat (0-23)", "Açılım": "Açılım Sayısı"} if secilen_dil == "TR" else {"Saat": "Time (0-23)", "Açılım": "Openings"}
        )
        
        fig_area.update_traces(
            line=dict(color="#38bdf8", width=3, shape="spline"),
            fillcolor="rgba(56, 189, 248, 0.15)",
            mode="lines+markers",
            marker=dict(color="#818cf8", size=6, symbol="circle")
        )
        
        fig_area.update_layout(
            height=250,
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)', 
            font=dict(family="'Inter', 'Helvetica Neue', sans-serif", size=13, color='#cbd5e1'), 
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis=dict(showgrid=True, gridcolor='rgba(51, 65, 85, 0.4)', gridwidth=1, tickmode='linear', tick0=0, dtick=3),
            yaxis=dict(showgrid=True, gridcolor='rgba(51, 65, 85, 0.4)', gridwidth=1, visible=False),
            showlegend=False
        )
        st.plotly_chart(fig_area, width='stretch')

def get_product_svg(urun_adi):
    import base64
    if "RedBull" in urun_adi:
        if "Lilac" in urun_adi: color = "#c084fc"
        elif "Peach" in urun_adi: color = "#fb923c"
        elif "White" in urun_adi: color = "#f8fafc"
        elif "Blue" in urun_adi: color = "#3b82f6"
        elif "Pembe" in urun_adi or "Pink" in urun_adi: color = "#f472b6"
        else: color = "#dc2626"
        
        isim = urun_adi.replace("RedBull_", "").replace("_", " ")
        if isim == "Klasik": isim = "Classic"
        
        svg = f"""<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <circle cx="50" cy="40" r="24" fill="#facc15" />
          <path fill="{color}" d="M 45 35 Q 35 25 20 30 Q 10 35 20 45 Q 25 60 45 55 Q 35 45 45 35 Z" />
          <path fill="{color}" d="M 55 35 Q 65 25 80 30 Q 90 35 80 45 Q 75 60 55 55 Q 65 45 55 35 Z" />
          <text x="50" y="85" font-family="Arial, sans-serif" font-size="15" font-weight="bold" fill="white" text-anchor="middle">{isim.upper()}</text>
        </svg>"""
    elif "Pepsi" in urun_adi:
        svg = """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <circle cx="50" cy="40" r="28" fill="#1d4ed8" />
          <path fill="#dc2626" d="M 22 40 A 28 28 0 0 1 78 40 Q 50 50 22 40 Z" />
          <path fill="white" d="M 22 40 Q 50 50 78 40 Q 60 55 26 50 Z" />
          <text x="50" y="85" font-family="Arial, sans-serif" font-size="15" font-weight="bold" fill="white" text-anchor="middle">PEPSI</text>
        </svg>"""
    elif "Fanta" in urun_adi:
        svg = """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <circle cx="50" cy="40" r="28" fill="#f97316" />
          <path fill="#22c55e" d="M 65 15 Q 75 5 85 15 Q 75 25 65 15 Z" />
          <text x="50" y="48" font-family="Arial, sans-serif" font-size="22" font-weight="900" fill="white" text-anchor="middle">F</text>
          <text x="50" y="85" font-family="Arial, sans-serif" font-size="15" font-weight="bold" fill="white" text-anchor="middle">FANTA</text>
        </svg>"""
    elif "CocaCola_Zero" in urun_adi or "Zero" in urun_adi:
        svg = """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <circle cx="50" cy="40" r="26" fill="#000000" />
          <path fill="none" stroke="#dc2626" stroke-width="2.5" d="M 30 45 Q 40 30 50 45 T 70 40" />
          <text x="50" y="85" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="white" text-anchor="middle">COCA COLA ZERO</text>
        </svg>"""
    elif "Cola" in urun_adi:
        svg = """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <circle cx="50" cy="40" r="26" fill="#dc2626" />
          <path fill="none" stroke="white" stroke-width="2.5" d="M 30 45 Q 40 30 50 45 T 70 40" />
          <path fill="none" stroke="white" stroke-width="1.5" d="M 35 52 Q 45 42 52 52 T 65 48" />
          <text x="50" y="85" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="white" text-anchor="middle">COCA COLA CLASSIC</text>
        </svg>"""
    elif "Nescafe" in urun_adi:
        svg = """<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <rect x="26" y="16" width="48" height="48" rx="8" fill="#dc2626" />
          <path fill="none" stroke="white" stroke-width="3" stroke-linecap="round" d="M 36 30 C 36 30 42 20 48 30 C 54 40 64 30 64 30" />
          <path fill="white" d="M 35 45 L 65 45 L 60 55 L 40 55 Z" />
          <text x="50" y="85" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="white" text-anchor="middle">NESCAFE</text>
        </svg>"""
    else:
        isim = urun_adi.replace("_", " ")[:10]
        svg = f"""<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <circle cx="50" cy="40" r="28" fill="#64748b" />
          <text x="50" y="85" font-family="Arial, sans-serif" font-size="15" font-weight="bold" fill="white" text-anchor="middle">{isim.upper()}</text>
        </svg>"""
        
    b64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{b64}"

def draw_stok():
    render_mobile_ui("❖", "Stok Durumu" if secilen_dil == "TR" else "Stock Status", f"{toplam_stok} Ürün" if secilen_dil == "TR" else f"{toplam_stok} Items", "Dolapta bulunan toplam ürün miktarı ve stok dağılımı." if secilen_dil == "TR" else "Total items in fridge and stock distribution.", liste_stok, system_note_text, yorum_stok, detail_btn_text)
    if pie_data:
        # Streamlit markdown parser indents as code blocks, so we remove leading spaces
        html = '<div style="display:flex; flex-wrap:wrap; gap:12px; justify-content:center; margin-bottom:20px; margin-top: 10px;">\n'
        for d in pie_data:
            svg_uri = get_product_svg(d["Orijinal"])
            isim = d["Ürün"]
            stok = d["Stok"]
            
            # Stok 0 ise soluk göster
            opacity = "1.0" if stok > 0 else "0.4"
            filter_css = "grayscale(0%)" if stok > 0 else "grayscale(100%)"
            
            html += f'<div style="background: linear-gradient(145deg, rgba(30,41,59,0.6), rgba(15,23,42,0.8)); border: 1px solid rgba(56,189,248,0.2); border-radius:16px; padding:12px; width:115px; display:flex; flex-direction:column; align-items:center; box-shadow: 0 4px 15px rgba(0,0,0,0.3); position:relative; opacity:{opacity}; filter:{filter_css}; transition: all 0.3s ease;">'
            if stok > 0:
                html += f'<div style="position:absolute; top:8px; right:10px; background:#38bdf8; color:#0f172a; font-size:11px; font-weight:800; padding:2px 6px; border-radius:8px;">{stok}</div>'
            else:
                html += f'<div style="position:absolute; top:8px; right:10px; background:#ef4444; color:#fff; font-size:11px; font-weight:800; padding:2px 6px; border-radius:8px;">0</div>'
            html += f'<img src="{svg_uri}" style="width:75px; height:75px; margin-bottom:8px;">'
            html += f'<div style="color:#e2e8f0; font-size:11px; font-weight:600; text-align:center; line-height:1.2; height:28px; overflow:hidden; display:flex; align-items:center;">{isim}</div>'
            html += '</div>\n'
        
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

def draw_siparis():
    render_mobile_ui("⚲", "Sipariş Gerekenler" if secilen_dil == "TR" else "Items Needing Order", f"{len([x for x in liste_siparis if 'yok' not in x and 'No items' not in x])} Ürün" if secilen_dil == "TR" else f"{len([x for x in liste_siparis if 'yok' not in x and 'No items' not in x])} Items", "Stok seviyesine göre sipariş edilmesi gereken ürünler." if secilen_dil == "TR" else "Items to be ordered based on current burn rate.", liste_siparis, system_note_text, yorum_siparis, detail_btn_text)

def draw_trend():
    render_mobile_ui("⌘", "En Çok Satılan Ürün" if secilen_dil == "TR" else "Top Selling Product", baslik_trend, "Seçili zaman aralığında satışı en yüksek ürün." if secilen_dil == "TR" else "Highest performing product in filtered time.", liste_trend, system_note_text, yorum_trend, detail_btn_text)
    
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
if "Tahminler" in secilen_sayfa or "Smart Predictions" in secilen_sayfa:
    st.markdown(f"<h2 style='color:white; margin-bottom: 20px;'>{'❖ Akıllı Tahminler & Bulanık Mantık Merkezi' if secilen_dil == 'TR' else '❖ Smart Predictions & Fuzzy Logic Center'}</h2>", unsafe_allow_html=True)
    
    st.markdown(f"#### {'1. Genel Sistem Davranışı' if secilen_dil == 'TR' else '1. General System Behavior'}")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(yorum_acilis, unsafe_allow_html=True)
    with c2:
        st.markdown(yorum_trend, unsafe_allow_html=True)
        
    st.markdown("---")
    st.markdown(f"#### {'2. Sipariş & Stok Öncelikleri' if secilen_dil == 'TR' else '2. Order & Stock Priorities'}")
    c3, c4 = st.columns(2)
    with c3:
        st.markdown(yorum_siparis, unsafe_allow_html=True)
    with c4:
        st.markdown(yorum_stok, unsafe_allow_html=True)
        
    st.markdown("---")
    st.markdown(f"#### {'3. Dolum & Optimizasyon Tavsiyesi' if secilen_dil == 'TR' else '3. Refill & Optimization Advice'}")
    
    # Çeşitlendirilmiş Akıllı Tahmin - Boşluk Analizi
    toplam_olmasi_gereken = sum([k.get('baslangic_stok', 20) for k in katalog.values()])
    mevcut_stok = sum(durum['stok'].values())
    bosluk_orani = 1 - (mevcut_stok / max(toplam_olmasi_gereken, 1))
    
    if bosluk_orani > 0.6:
        t_renk = "#dc2626"
        t_sev = "ACİL DOLUM" if secilen_dil == "TR" else "URGENT REFILL"
        t_msg = f"Dolap kapasitesinin <strong>%{(bosluk_orani*100):.0f}'i boş</strong>. En kısa sürede genel dolum yapılması gerekiyor." if secilen_dil == "TR" else f"Cabinet is <strong>%{(bosluk_orani*100):.0f} empty</strong>. General refill required ASAP."
    elif bosluk_orani > 0.3:
        t_renk = "#ca8a04"
        t_sev = "KISMEN DOLUM" if secilen_dil == "TR" else "PARTIAL REFILL"
        t_msg = f"Dolapta <strong>%{(bosluk_orani*100):.0f} boşluk</strong> var. Kritik ürünlerin takviyesi yapılabilir." if secilen_dil == "TR" else f"Cabinet is <strong>%{(bosluk_orani*100):.0f} empty</strong>. Critical items can be replenished."
    else:
        t_renk = "#16a34a"
        t_sev = "OPTIMUM" if secilen_dil == "TR" else "OPTIMAL"
        t_msg = "Dolap doluluk oranı optimum seviyede. Şu an için toplu bir dolum operasyonuna gerek yoktur." if secilen_dil == "TR" else "Cabinet capacity is at optimal level. No bulk refill operation needed currently."
    
    _tavsiye_badge = fe.badge_html(t_sev, t_renk, dil=secilen_dil)
    tavsiye_html = fe.yorum_kutusu(f"🤖 {'Yapay Zeka Operasyon Önerisi' if secilen_dil == 'TR' else 'AI Operation Suggestion'} &nbsp; {_tavsiye_badge}", t_msg)
    st.markdown(tavsiye_html, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f"#### {'4. ⏳ Stok Tükenme Tahmin Takvimi' if secilen_dil == 'TR' else '4. ⏳ Stock Depletion Forecast'}")
    if secilen_dil == "TR":
        st.caption("Mevcut tüketim hızı devam ederse her ürünün ne zaman biteceğini ve 24 saatlik tükenme riskini gösterir.")
    else:
        st.caption("Shows when each product will run out based on current consumption rate, plus 24-hour depletion risk.")

    pred_rows = []
    for u in _fuzzy_urun:
        tuk  = u["tuketim_saatlik"]
        stok = u["stok"]
        bitis   = fe.tahmin_bitis_zamani(stok, tuk)
        risk24  = fe.stok_tukenis_olasiligi(stok, tuk, 24)
        risk_str = f"%{risk24}"
        pred_rows.append({
            ("Ürün" if secilen_dil=="TR" else "Product"): u["urun"].replace("_", " "),
            ("Stok" if secilen_dil=="TR" else "Stock"): stok,
            ("Fuzzy Skor" if secilen_dil=="TR" else "Fuzzy Score"): u["skor"],
            ("24s Risk" if secilen_dil=="TR" else "24h Risk"): risk_str,
            ("Tahmini Bitiş" if secilen_dil=="TR" else "Est. Depletion"): bitis.get("tarih") or "—",
        })

    if not pred_rows:
        st.info("Yeterli tüketim verisi yok." if secilen_dil == "TR" else "Not enough consumption data.")
    else:
        # Kod görünümü (st.dataframe) yerine şık bir HTML tablo tasarımı
        table_html = "<div style='overflow-x:auto;'><table style='width:100%; border-collapse: collapse; text-align: left;'>"
        headers = list(pred_rows[0].keys())
        table_html += "<thead><tr style='border-bottom: 2px solid rgba(56,189,248,0.3);'>"
        for h in headers:
            table_html += f"<th style='padding: 14px; color:#94a3b8; font-weight:600; font-size:14px;'>{h}</th>"
        table_html += "</tr></thead><tbody>"
        for i, row in enumerate(pred_rows):
            bg = "background: rgba(15,23,42,0.5);" if i % 2 == 0 else "background: rgba(30,41,59,0.3);"
            table_html += f"<tr style='border-bottom: 1px solid rgba(56,189,248,0.1); {bg}'>"
            for val in row.values():
                table_html += f"<td style='padding: 14px; color:#e2e8f0; font-size:14px; font-weight:500;'>{val}</td>"
            table_html += "</tr>"
        table_html += "</tbody></table></div>"
        
        st.markdown(
            f"<div style='background: linear-gradient(145deg, rgba(15,23,42,0.6), rgba(2,6,23,0.8)); border: 1px solid rgba(56,189,248,0.2); border-radius:18px; padding:20px;'>{table_html}</div>", 
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown(f"#### {'5. 🧬 Fuzzy Kural Motor Analizi (Mamdani)' if secilen_dil == 'TR' else '5. 🧬 Fuzzy Rule Engine Analysis (Mamdani)'}")

    if secilen_dil == "TR":
        st.caption("Sistem hangi bulanık kuralları ateşledi ve aktivasyon gücü ne kadar? En kritik ürün için kural tabanı görselleştirilmiştir.")
    else:
        st.caption("Which fuzzy rules fired and how strongly? Rule-base visualized for the most critical product.")

    en_kritik_urun = max(_fuzzy_urun, key=lambda x: x["skor"], default=None)
    if en_kritik_urun:
        bas_stok = katalog.get(en_kritik_urun["urun"], {}).get("baslangic_stok", 20)
        r_norm   = en_kritik_urun["stok"] / max(bas_stok, 1)
        h_norm   = min(en_kritik_urun["tuketim_saatlik"], 5.0)
        ates_lst = fe.kural_ates_detayi(r_norm, h_norm, dil=secilen_dil)

        urun_adi_goster = en_kritik_urun["urun"].replace("_", " ")
        st.markdown(f"**{('Analiz edilen ürün' if secilen_dil=='TR' else 'Analyzed product')}:** {urun_adi_goster}  "
                    f"| Stok oranı: `{r_norm:.2f}` | Tüketim hızı: `{h_norm:.3f}` birim/saat")

        if ates_lst:
            renk_map = {"Yuksek": "#dc2626", "Orta": "#ca8a04", "Dusuk": "#16a34a"}
            rows_html = ""
            for k in ates_lst:
                bar_c = renk_map.get(k["cikti"], "#64748b")
                rows_html += (f"<div style='margin-bottom:14px;'>"
                    f"<div style='color:#cbd5e1; font-size:13.5px; margin-bottom:5px; font-family:\"Inter\", \"Helvetica Neue\", sans-serif; font-weight:600;'>{k['kural']}</div>"
                    f"<div style='display:flex; align-items:center; gap:12px;'>"
                    f"<div style='flex:1; background:rgba(51,65,85,0.6); border-radius:8px; height:14px; overflow:hidden; border:1px solid rgba(255,255,255,0.05);'>"
                    f"<div style='width:{k['yuzde']}%; height:100%; background:{bar_c}; border-radius:8px;'></div>"
                    f"</div>"
                    f"<div style='color:#e2e8f0; font-size:13px; font-weight:700; min-width:55px; text-align:right;'>%{k['yuzde']}</div>"
                    f"</div></div>")
            st.markdown(
                f"<div style='background:rgba(15,23,42,0.7); border:1px solid rgba(56,189,248,0.25); border-radius:18px; padding:24px; margin-top:8px;'>{rows_html}</div>",
                unsafe_allow_html=True
            )

            # Kural çıktı dağılımı — Pie chart
            cikti_sayim = {"Yuksek": 0, "Orta": 0, "Dusuk": 0}
            for k in ates_lst:
                cikti_sayim[k["cikti"]] += k["ates"]
            if sum(cikti_sayim.values()) > 0:
                cikti_etiket = {
                    "Yuksek": "Yüksek Aciliyet" if secilen_dil=="TR" else "High Urgency",
                    "Orta":   "Orta Aciliyet"   if secilen_dil=="TR" else "Medium Urgency",
                    "Dusuk":  "Düşük Aciliyet"  if secilen_dil=="TR" else "Low Urgency",
                }
                labels = [cikti_etiket[k] for k in cikti_sayim]
                values = list(cikti_sayim.values())
                colors = ["#dc2626", "#ca8a04", "#16a34a"]
                fig_pie = go.Figure(go.Pie(
                    labels=labels, values=values,
                    marker=dict(colors=colors, line=dict(color="#0f172a", width=2)),
                    hole=0.4, textfont_size=13,
                    textfont_family="Inter, Helvetica Neue, sans-serif"
                ))
                fig_pie.update_layout(
                    height=230, paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(t=10, b=10, l=10, r=10), showlegend=True,
                    legend=dict(font=dict(color="#cbd5e1", size=12)),
                    title=dict(
                        text="Kural Çıktı Dağılımı" if secilen_dil=="TR" else "Rule Output Distribution",
                        font=dict(color="#94a3b8", size=13), x=0.5
                    )
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Bu ürün için aktif kural bulunamadı." if secilen_dil=="TR" else "No active rules found for this product.")
elif "Canlı Operasyon" in secilen_sayfa or "Live Operations" in secilen_sayfa:
    st.markdown(f"### {'⚲ Canlı Operasyon Akışı' if secilen_dil == 'TR' else '⚲ Live Operations Feed'}")
    if secilen_dil == "TR":
        st.caption("Fiziksel dolaptaki hareketlerin (Ekleme/Alma) anlık detaylı log kayıtları.")
    else:
        st.caption("Real-time detailed log of physical cabinet actions (Added/Removed).")
    
    # 1. En son olayı çok detaylı (terminaldeki gibi) göster
    if durum.get("son_olay") and durum["son_olay"]["zaman"] != "-":
        son = durum["son_olay"]
        st.markdown(f"#### {'✦ Son Canlı Algılama' if secilen_dil == 'TR' else '✦ Last Live Detection'}")
        
        islem_text = son.get("yapilan_islem", "")
        if "Alındı" in islem_text:
            renk, ikon, baslik = "#ef4444", "⌘", "ÜRÜN ALINDI!" if secilen_dil=="TR" else "PRODUCT REMOVED!"
            bg = "rgba(239,68,68,0.1)"
            brd = "rgba(239,68,68,0.3)"
        elif "Eklendi" in islem_text:
            renk, ikon, baslik = "#22c55e", "⚲", "ÜRÜN EKLENDİ!" if secilen_dil=="TR" else "PRODUCT ADDED!"
            bg = "rgba(34,197,94,0.1)"
            brd = "rgba(34,197,94,0.3)"
        else:
            renk, ikon, baslik = "#38bdf8", "✦", "SİSTEM MESAJI" if secilen_dil=="TR" else "SYSTEM MESSAGE"
            bg = "rgba(56,189,248,0.1)"
            brd = "rgba(56,189,248,0.3)"
            
        urun = son.get("kategori", "").replace("_", " ")
        slot = son.get("slot", "")
        eminlik = son.get("eminlik", 0.0)
        agirlik = son.get("agirlik_degisimi", "0")
        zaman = son.get("zaman", "-")
        
        detay_html = f"""
        <div class='apple-box' style='border-left: 4px solid {renk};'>
            <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;'>
                <div style='font-size:22px; font-weight:800; color:{renk}; letter-spacing:1px;'>{ikon} {baslik}</div>
                <div style='color:#94a3b8; font-size:14px; font-family:monospace;'>✦ {zaman}</div>
            </div>
            <div style='display:grid; grid-template-columns: 1fr 1fr; gap:16px;'>
                <div style='font-size:16px; color:#e2e8f0;'><span style='color:#94a3b8;'>⚲ Slot:</span> &nbsp;&nbsp;&nbsp;<strong>{slot}</strong></div>
                <div style='font-size:16px; color:#e2e8f0;'><span style='color:#94a3b8;'>❖ Ağırlık:</span> <strong>{agirlik}g</strong></div>
                <div style='font-size:16px; color:#e2e8f0;'><span style='color:#94a3b8;'>❖ Ürün:</span> &nbsp;&nbsp;<strong>{urun}</strong></div>
                <div style='font-size:16px; color:#e2e8f0;'><span style='color:#94a3b8;'>✦ Eminlik:</span> <strong>%{eminlik}</strong></div>
            </div>
            <div style='margin-top:16px; padding-top:16px; border-top:1px solid rgba(255,255,255,0.1); color:{renk}; font-weight:600; font-size:15px; text-align:center;'>
                ✦ Kayıt: {islem_text} | Eminlik: %{eminlik}
            </div>
        </div>
        """
        st.markdown(detay_html, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown(f"#### {'📜 Geçmiş Operasyonlar' if secilen_dil == 'TR' else '📜 Historical Operations'}")
    
    if df_gecmis_ham.empty:
        st.info("Henüz kaydedilmiş bir hareket bulunmuyor." if secilen_dil == "TR" else "No actions recorded yet.")
    else:
        # En yeniler en üstte
        df_feed = df_gecmis_ham.copy().sort_values(by="Tarih", ascending=False)
        
        feed_html = "<div style='display:flex; flex-direction:column; gap:12px;'>"
        for _, row in df_feed.iterrows():
            islem = row["Islem"]
            urun = row["Urun"].replace("_", " ")
            tarih = row["Tarih"].strftime('%Y-%m-%d %H:%M:%S')
            
            if "Al" in islem or "Remove" in islem:
                renk = "#ef4444"
                ikon = "⌘"
                baslik = "ALINDI" if secilen_dil == "TR" else "REMOVED"
                bg_grad = "linear-gradient(90deg, rgba(239, 68, 68, 0.1) 0%, rgba(15, 23, 42, 0.4) 100%)"
                border = "border-left: 4px solid #ef4444;"
            else:
                renk = "#22c55e"
                ikon = "⚲"
                baslik = "EKLENDİ" if secilen_dil == "TR" else "ADDED"
                bg_grad = "linear-gradient(90deg, rgba(34, 197, 94, 0.1) 0%, rgba(15, 23, 42, 0.4) 100%)"
                border = "border-left: 4px solid #22c55e;"
                
            feed_html += (f"<div class='apple-box' style='{border} padding: 16px; margin-bottom: 12px; display:flex; justify-content:space-between; align-items:center;'>"
                f"<div style='display:flex; align-items:center; gap:16px;'>"
                f"<div style='font-size:18px;'>{ikon}</div>"
                f"<div><div style='color:#e2e8f0; font-size:15px; font-weight:600;'>{urun}</div>"
                f"<div style='color:{renk}; font-size:13px; font-weight:700;'>{baslik} (1 Adet)</div></div>"
                f"</div>"
                f"<div style='color:#94a3b8; font-size:12px; font-family:monospace; text-align:right;'>✦ {tarih}</div>"
                f"</div>")
        feed_html += "</div>"
        st.markdown(feed_html, unsafe_allow_html=True)

elif "Kamera" in secilen_sayfa or "Camera" in secilen_sayfa:
    st.markdown(f"### {'⌘ Kamera ve Bilgisayarlı Görüş (Computer Vision)' if secilen_dil == 'TR' else '⌘ Camera & Computer Vision'}")
    if secilen_dil == "TR":
        st.caption("Fiziksel dolaptan gelen ham görüntüler ve AI modeline gönderilen kırpılmış slot (raf) kareleri.")
    else:
        st.caption("Raw images from the physical cabinet and cropped slot frames sent to the AI model.")
    
    st.markdown("---")
    
    def render_img_card(path, title, border_color="#38bdf8", height="auto", object_fit="contain"):
        if os.path.exists(path):
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            html = f"<div style='background: rgba(15, 23, 42, 0.6); padding: 12px; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 28px; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4); text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: space-between;'>"
            html += f"<div style='color:#e2e8f0; font-size:15px; font-weight:700; margin-bottom:12px; letter-spacing:1px;'>{title}</div>"
            if height == "auto":
                html += f"<img src='data:image/jpeg;base64,{b64}' style='border-radius: 12px; width: 100%; height: auto; border: 1px solid rgba(56, 189, 248, 0.1); margin: auto 0;'>"
            else:
                html += f"<img src='data:image/jpeg;base64,{b64}' style='border-radius: 12px; width: 100%; height: {height}; object-fit: {object_fit}; border: 1px solid rgba(56, 189, 248, 0.1); margin: auto 0;'>"
            html += "</div>"
            return html
        else:
            html = "<div style='background: rgba(15, 23, 42, 0.4); padding: 30px 12px; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 28px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); text-align: center; color: #64748b; font-weight: 600; height: 100%; display: flex; align-items: center; justify-content: center;'>"
            html += f"<div>⌘ {title} <br><span style='font-size:12px; font-weight:400;'>(Görsel Yok / No Image)</span></div>"
            html += "</div>"
            return html

    st.markdown(f"#### {'⚲ Ana Görüntüler (Öncesi / Sonrası)' if secilen_dil == 'TR' else '⚲ Main Captures (Before / After)'}")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(render_img_card("dolap_oncesi.jpg", "Mevcut Referans (Öncesi)", height="auto"), unsafe_allow_html=True)
    with col2:
        st.markdown(render_img_card("dolap_sonrasi.jpg", "Yeni Algılanan (Sonrası)", border_color="#facc15", height="auto"), unsafe_allow_html=True)
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    st.markdown(f"#### {'❖ AI Tarafından Kırpılan Slotlar' if secilen_dil == 'TR' else '❖ Slots Cropped by AI'}")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(render_img_card("debug_kesilen_Slot_1.jpg", "Slot 1 (Sol)", height="450px", object_fit="contain"), unsafe_allow_html=True)
    with c2:
        st.markdown(render_img_card("debug_kesilen_Slot_2.jpg", "Slot 2 (Orta)", height="450px", object_fit="contain"), unsafe_allow_html=True)
    with c3:
        st.markdown(render_img_card("debug_kesilen_Slot_3.jpg", "Slot 3 (Sağ)", height="450px", object_fit="contain"), unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)

else:
    if "Mobil" in arayuz_tipi or "Mobile" in arayuz_tipi:
        col_left, col_mid, col_right = st.columns([1, 2, 1])
        with col_mid:
            tab_isimleri = ["✦ Kapak", "❖ Stok", "⚲ Sipariş", "⌘ Analiz"] if secilen_dil == "TR" else ["✦ Access", "❖ Stock", "⚲ Orders", "⌘ Analytics"]
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