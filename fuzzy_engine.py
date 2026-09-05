"""
fuzzy_engine.py — Bulanık Mantık (Fuzzy Rule-Base) Karar Motoru
================================================================
Akıllı Dolap Sistemi için Mamdani-tipi Fuzzy Inference System.

Adımlar:
  1. Fuzzification
  2. Rule Evaluation
  3. Aggregation
  4. Defuzzification
"""

# ══════════════════════════════════════════════════════════════════
#  1. ÜYELIK FONKSİYONLARI (Membership Functions)
# ══════════════════════════════════════════════════════════════════

def trimf(x, a, b, c):
    if b == a:
        left = 1.0 if x >= a else 0.0
    else:
        left = max(0.0, (x - a) / (b - a))
    if c == b:
        right = 1.0 if x <= c else 0.0
    else:
        right = max(0.0, (c - x) / (c - b))
    return min(left, right)

def trapmf(x, a, b, c, d):
    if x <= a or x >= d:
        return 0.0
    if x <= b:
        return (x - a) / (b - a) if b > a else 1.0
    if x <= c:
        return 1.0
    return (d - x) / (d - c) if d > c else 1.0

# ══════════════════════════════════════════════════════════════════
#  2. STOK DÜZEYI & TÜKETİM HIZI
# ══════════════════════════════════════════════════════════════════

def stok_kritik(r):  return trapmf(r, 0.00, 0.00, 0.12, 0.28)
def stok_dusuk(r):   return trimf(r,  0.12, 0.28, 0.50)
def stok_orta(r):    return trimf(r,  0.35, 0.55, 0.75)
def stok_yeterli(r): return trapmf(r, 0.60, 0.80, 1.00, 1.00)

def hiz_yavash(h):  return trapmf(h, 0.0, 0.0, 0.30, 0.90)
def hiz_normal(h):  return trimf(h,  0.5, 1.50, 3.00)
def hiz_hizli(h):   return trapmf(h, 2.0, 3.50, 5.00, 5.00)

# ══════════════════════════════════════════════════════════════════
#  3. KURAL TABANI VE ÇIKARIM
# ══════════════════════════════════════════════════════════════════

CIKTI = {"Dusuk": 12.0, "Orta": 48.0, "Yuksek": 85.0}

SEVIYE_SINIRLAR = {
    "TR": [
        (70, "KRİTİK",  "#dc2626"),
        (50, "YÜKSEK",  "#ea580c"),
        (30, "ORTA",    "#ca8a04"),
        (0,  "DÜŞÜK",   "#16a34a"),
    ],
    "EN": [
        (70, "CRITICAL", "#dc2626"),
        (50, "HIGH",     "#ea580c"),
        (30, "MEDIUM",   "#ca8a04"),
        (0,  "LOW",      "#16a34a"),
    ]
}

KURALLAR = [
    (stok_kritik,  hiz_hizli,   "Yuksek"),   
    (stok_kritik,  hiz_normal,  "Yuksek"),   
    (stok_kritik,  hiz_yavash,  "Orta"),     
    (stok_dusuk,   hiz_hizli,   "Yuksek"),   
    (stok_dusuk,   hiz_normal,  "Orta"),     
    (stok_dusuk,   hiz_yavash,  "Dusuk"),    
    (stok_orta,    hiz_hizli,   "Orta"),     
    (stok_orta,    hiz_normal,  "Dusuk"),    
    (stok_orta,    hiz_yavash,  "Dusuk"),    
    (stok_yeterli, hiz_hizli,   "Dusuk"),    
    (stok_yeterli, hiz_normal,  "Dusuk"),    
    (stok_yeterli, hiz_yavash,  "Dusuk"),    
]

def _defuzz(stok_norm, hiz):
    r = max(0.0, min(1.0, stok_norm))
    h = max(0.0, min(5.0, hiz))

    agirlik_toplam = 0.0
    carpim_toplam  = 0.0

    for stok_fn, hiz_fn, cikti in KURALLAR:
        ates = min(stok_fn(r), hiz_fn(h))
        if ates > 0:
            agirlik_toplam += ates
            carpim_toplam  += ates * CIKTI[cikti]

    if agirlik_toplam == 0:
        return 0.0
    return carpim_toplam / agirlik_toplam

def _seviye(skor, dil="TR"):
    for esik, etiket, renk in SEVIYE_SINIRLAR.get(dil, SEVIYE_SINIRLAR["TR"]):
        if skor >= esik:
            return etiket, renk
    return "DÜŞÜK" if dil=="TR" else "LOW", "#16a34a"

# ══════════════════════════════════════════════════════════════════
#  4. ANALİZ FONKSİYONLARI (DİL DESTEKLİ)
# ══════════════════════════════════════════════════════════════════

def urun_analiz(urun_adi, stok, baslangic_stok, tuketim_saatlik, dil="TR"):
    r   = stok / max(baslangic_stok, 1)
    h   = min(tuketim_saatlik, 5.0)
    skor = _defuzz(r, h)

    seviye, renk = _seviye(skor, dil)

    sure = None
    if tuketim_saatlik > 0.001 and stok > 0:
        sure = round(stok / tuketim_saatlik, 1)

    return {
        "urun": urun_adi,
        "stok": stok,
        "skor": round(skor, 1),
        "seviye": seviye,
        "renk": renk,
        "tahmini_sure": sure,
        "tuketim_saatlik": round(tuketim_saatlik, 3),
    }

def kapi_analiz(acilma_son1saat, saat, dil="TR"):
    if 7 <= saat < 12: referans = 4
    elif 12 <= saat < 14: referans = 7
    elif 14 <= saat < 18: referans = 5
    elif 18 <= saat < 22: referans = 8
    else: referans = 1

    oran = acilma_son1saat / max(referans, 1)

    if oran >= 1.8:
        seviye, renk = "YOĞUN" if dil=="TR" else "HEAVY", "#dc2626"
        if dil == "TR":
            aciklama = f"Son 1 saatte {acilma_son1saat} açılım tespit edildi — bu saat için normalin <strong>{oran:.1f}x</strong> üzerinde. Stok tüketimi hızlanmış olabilir."
        else:
            aciklama = f"{acilma_son1saat} openings in the last hour — <strong>{oran:.1f}x</strong> above normal for this time. Stock burn rate may have increased."
    elif oran >= 1.2:
        seviye, renk = "NORMAL ÜZERİ" if dil=="TR" else "ABOVE NORMAL", "#ea580c"
        if dil == "TR":
            aciklama = f"Son 1 saatte {acilma_son1saat} açılım — bu saat için ortalamanın hafif üzerinde ({oran:.1f}x). Stok takibi önerilir."
        else:
            aciklama = f"{acilma_son1saat} openings in the last hour — slightly above average ({oran:.1f}x). Stock monitoring advised."
    elif oran >= 0.6:
        seviye, renk = "NORMAL", "#16a34a"
        if dil == "TR":
            aciklama = f"Son 1 saatte {acilma_son1saat} açılım — bu saat için beklenen aralıkta. Sistem dengeli çalışıyor."
        else:
            aciklama = f"{acilma_son1saat} openings in the last hour — within expected range. System is stable."
    else:
        seviye, renk = "DÜŞÜK" if dil=="TR" else "LOW", "#4f46e5"
        if dil == "TR":
            aciklama = f"Son 1 saatte yalnızca {acilma_son1saat} açılım. Bu saat ({saat}:00) için olağandışı düşük kullanım."
        else:
            aciklama = f"Only {acilma_son1saat} openings in the last hour. Unusually low usage for this time ({saat}:00)."

    return {"yogunluk_seviyesi": seviye, "renk": renk, "aciklama": aciklama}

def stok_tab_analiz(urun_analizler, dil="TR"):
    sirali = sorted(urun_analizler, key=lambda x: x["skor"], reverse=True)
    kritik = [u for u in sirali if u["skor"] >= 70]
    orta   = [u for u in sirali if 30 <= u["skor"] < 70]
    dusuk  = [u for u in sirali if u["skor"] < 30]

    en_kritik = sirali[0] if sirali else None

    parcalar = []
    if dil == "TR":
        if kritik:
            isimler = ", ".join(u["urun"].replace("_", " ") for u in kritik[:3])
            parcalar.append(f"<strong style='color:#f87171;'>✦ KRİTİK ({len(kritik)} ürün):</strong> {isimler}")
        if orta:
            isimler = ", ".join(u["urun"].replace("_", " ") for u in orta[:2])
            parcalar.append(f"<strong style='color:#fb923c;'>⚠ ORTA ({len(orta)} ürün):</strong> {isimler}")
        if dusuk:
            parcalar.append(f"<span style='color:#4ade80;'>✓ DÜŞÜK ÖNCELİK: {len(dusuk)} ürün stok durumu yeterli.</span>")
        aciklama = "<br>".join(parcalar) if parcalar else "Tüm ürünler yeterli stok düzeyinde."
    else:
        if kritik:
            isimler = ", ".join(u["urun"].replace("_", " ") for u in kritik[:3])
            parcalar.append(f"<strong style='color:#f87171;'>✦ CRITICAL ({len(kritik)} items):</strong> {isimler}")
        if orta:
            isimler = ", ".join(u["urun"].replace("_", " ") for u in orta[:2])
            parcalar.append(f"<strong style='color:#fb923c;'>⚠ MEDIUM ({len(orta)} items):</strong> {isimler}")
        if dusuk:
            parcalar.append(f"<span style='color:#4ade80;'>✓ LOW PRIORITY: {len(dusuk)} items have sufficient stock.</span>")
        aciklama = "<br>".join(parcalar) if parcalar else "All items have sufficient stock levels."

    return {
        "en_kritik": en_kritik,
        "kritik_sayisi": len(kritik),
        "orta_sayisi": len(orta),
        "dusuk_sayisi": len(dusuk),
        "aciklama": aciklama,
    }

def siparis_tab_analiz(urun_analizler, dil="TR"):
    kritik = [u for u in urun_analizler if u["skor"] >= 70]
    orta   = [u for u in urun_analizler if 30 <= u["skor"] < 70]

    satirlar = []
    for u in sorted(kritik, key=lambda x: x["skor"], reverse=True):
        if dil == "TR":
            sure_str = f" (~{u['tahmini_sure']}s)" if u["tahmini_sure"] else ""
            satirlar.append(f"<span style='color:#f87171;'>✦ KRİTİK</span> <strong>{u['urun'].replace('_',' ')}</strong>{sure_str} — Skor: {u['skor']}/100")
        else:
            sure_str = f" (~{u['tahmini_sure']}h)" if u["tahmini_sure"] else ""
            satirlar.append(f"<span style='color:#f87171;'>✦ CRITICAL</span> <strong>{u['urun'].replace('_',' ')}</strong>{sure_str} — Score: {u['skor']}/100")
            
    for u in sorted(orta, key=lambda x: x["skor"], reverse=True):
        if dil == "TR":
            satirlar.append(f"<span style='color:#fb923c;'>⚠ ORTA</span> <strong>{u['urun'].replace('_',' ')}</strong> — Skor: {u['skor']}/100")
        else:
            satirlar.append(f"<span style='color:#fb923c;'>⚠ MEDIUM</span> <strong>{u['urun'].replace('_',' ')}</strong> — Score: {u['skor']}/100")

    if not satirlar:
        aciklama = "<span style='color:#4ade80;'>✓ Tüm ürünler yeterli stok düzeyinde. Acil sipariş gerekmez.</span>" if dil == "TR" else "<span style='color:#4ade80;'>✓ All items have sufficient stock. No urgent orders needed.</span>"
    else:
        if dil == "TR":
            ozet = f"<strong>Fuzzy Öncelik Sıralaması ({len(kritik)} KRİTİK, {len(orta)} ORTA):</strong><br>"
        else:
            ozet = f"<strong>Fuzzy Priority Ranking ({len(kritik)} CRITICAL, {len(orta)} MEDIUM):</strong><br>"
        aciklama = ozet + "<br>".join(satirlar)

    return {"aciklama": aciklama, "kritik_sayisi": len(kritik), "orta_sayisi": len(orta)}

def trend_tab_analiz(satis_son7gun, satis_son3gun, en_cok_satan, en_cok_satis, dil="TR"):
    if satis_son7gun < 2:
        seviye, renk = "YETERSİZ VERİ" if dil=="TR" else "NOT ENOUGH DATA", "#64748b"
        aciklama = "Trend analizi için daha fazla satış verisi gereklidir." if dil=="TR" else "More sales data is required for trend analytics."
        return {"ivme_seviyesi": seviye, "renk": renk, "aciklama": aciklama}

    onceki4 = satis_son7gun - satis_son3gun
    onceki4_gunluk = onceki4 / 4.0 if onceki4 > 0 else 0.001
    son3_gunluk    = satis_son3gun / 3.0 if satis_son3gun > 0 else 0.0

    ivme = son3_gunluk / onceki4_gunluk if onceki4_gunluk > 0 else 1.0

    if ivme >= 1.5:
        seviye, renk = "HIZLANIYOR" if dil=="TR" else "ACCELERATING", "#dc2626"
        tavsiye_yuzde = int((ivme - 1) * 100)
        if dil == "TR":
            aciklama = f"Son 3 günlük satış hızı önceki 4 güne kıyasla <strong style='color:#f87171;'>%{tavsiye_yuzde} arttı.</strong><br><strong>{en_cok_satan.replace('_',' ')}</strong> en yüksek talebi görüyor ({en_cok_satis} adet). Hafta sonu için <strong>%{min(tavsiye_yuzde+10, 60)} ekstra stok</strong> planlaması önerilir."
        else:
            aciklama = f"Sales speed in the last 3 days <strong style='color:#f87171;'>increased by {tavsiye_yuzde}%</strong> compared to previous 4 days.<br><strong>{en_cok_satan.replace('_',' ')}</strong> has the highest demand ({en_cok_satis} units). We recommend planning for <strong>{min(tavsiye_yuzde+10, 60)}% extra stock</strong> for the weekend."
    elif ivme >= 1.1:
        seviye, renk = "STABİL/ARTAN" if dil=="TR" else "STABLE/RISING", "#ca8a04"
        if dil == "TR":
            aciklama = f"Satış hızı istikrarlı, hafif artış eğiliminde (<strong>{ivme:.1f}x</strong>).<br>Mevcut stok planlaması yeterli, ancak <strong>{en_cok_satan.replace('_',' ')}</strong> takibini sıklaştırın."
        else:
            aciklama = f"Sales speed is stable with a slight rising trend (<strong>{ivme:.1f}x</strong>).<br>Current stock planning is sufficient, but monitor <strong>{en_cok_satan.replace('_',' ')}</strong> closely."
    elif ivme >= 0.7:
        seviye, renk = "STABİL" if dil=="TR" else "STABLE", "#16a34a"
        if dil == "TR":
            aciklama = f"Satış hızı bu hafta dengeli seyrediyor (ivme oranı: {ivme:.2f}x).<br><strong>{en_cok_satan.replace('_',' ')}</strong> ({en_cok_satis} adet) lider ürün. Mevcut stok planlaması yeterli görünüyor."
        else:
            aciklama = f"Sales speed is balanced this week (acceleration: {ivme:.2f}x).<br><strong>{en_cok_satan.replace('_',' ')}</strong> ({en_cok_satis} units) is the leading product. Current stock planning is sufficient."
    else:
        seviye, renk = "YAVAŞLIYOR" if dil=="TR" else "SLOWING DOWN", "#4f46e5"
        if dil == "TR":
            aciklama = f"Satış hızı son 3 günde yavaşlıyor (önceki döneme oran: {ivme:.2f}x).<br>Fazla stok riski oluşabilir. Promosyon veya fiyat düzenlemesi düşünülebilir."
        else:
            aciklama = f"Sales speed has slowed down in the last 3 days (ratio: {ivme:.2f}x).<br>Overstock risk possible. Consider promotions or price adjustments."

    return {"ivme_seviyesi": seviye, "renk": renk, "aciklama": aciklama}

def badge_html(seviye, renk, skor=None, dil="TR"):
    skor_str = f" &nbsp;|&nbsp; {'Skor' if dil=='TR' else 'Score'}: {skor}/100" if skor is not None else ""
    return (
        f'<span style="background:{renk}; color:#fff; padding:3px 11px; '
        f'border-radius:20px; font-size:11px; font-weight:700; '
        f'letter-spacing:0.5px;">{seviye}</span>'
        f'<span style="color:#64748b; font-size:11px; margin-left:6px;">{skor_str}</span>'
    )

def yorum_kutusu(on_html, aciklama_html):
    return (
        f'<div class="apple-box" style="margin-bottom: 20px;">'
        f'<div style="margin-bottom:12px;">{on_html}</div>'
        f'<div style="line-height:1.7; color:#e2e8f0; font-size:15px;">'
        f'{aciklama_html}</div>'
        f'</div>'
    )


# ══════════════════════════════════════════════════════════════════
#  5. GELİŞMİŞ ANALİZ — KURAL MOTORU DETAYI & TAHMİNLER
# ══════════════════════════════════════════════════════════════════

_KURAL_ACIKLAMALARI = {
    "TR": [
        "KRİTİK stok ∧ HIZLI tüketim  →  YÜKSEK aciliyet",
        "KRİTİK stok ∧ NORMAL tüketim →  YÜKSEK aciliyet",
        "KRİTİK stok ∧ YAVAŞ tüketim  →  ORTA aciliyet",
        "DÜŞÜK stok  ∧ HIZLI tüketim  →  YÜKSEK aciliyet",
        "DÜŞÜK stok  ∧ NORMAL tüketim →  ORTA aciliyet",
        "DÜŞÜK stok  ∧ YAVAŞ tüketim  →  DÜŞÜK aciliyet",
        "ORTA stok   ∧ HIZLI tüketim  →  ORTA aciliyet",
        "ORTA stok   ∧ NORMAL tüketim →  DÜŞÜK aciliyet",
        "ORTA stok   ∧ YAVAŞ tüketim  →  DÜŞÜK aciliyet",
        "YETERLİ stok ∧ HIZLI tüketim →  DÜŞÜK aciliyet",
        "YETERLİ stok ∧ NORMAL tüketim → DÜŞÜK aciliyet",
        "YETERLİ stok ∧ YAVAŞ tüketim  → DÜŞÜK aciliyet",
    ],
    "EN": [
        "CRITICAL stock ∧ FAST consumption  →  HIGH urgency",
        "CRITICAL stock ∧ NORMAL consumption →  HIGH urgency",
        "CRITICAL stock ∧ SLOW consumption  →  MEDIUM urgency",
        "LOW stock      ∧ FAST consumption  →  HIGH urgency",
        "LOW stock      ∧ NORMAL consumption →  MEDIUM urgency",
        "LOW stock      ∧ SLOW consumption  →  LOW urgency",
        "MEDIUM stock   ∧ FAST consumption  →  MEDIUM urgency",
        "MEDIUM stock   ∧ NORMAL consumption →  LOW urgency",
        "MEDIUM stock   ∧ SLOW consumption  →  LOW urgency",
        "SUFFICIENT stock ∧ FAST consumption →  LOW urgency",
        "SUFFICIENT stock ∧ NORMAL consumption → LOW urgency",
        "SUFFICIENT stock ∧ SLOW consumption  → LOW urgency",
    ]
}


def kural_ates_detayi(stok_norm, hiz, dil="TR"):
    """
    Verilen stok oranı ve tüketim hızı için hangi Mamdani kurallarının
    ateşlendiğini ve aktivasyon güçlerini döndürür.
    Döndürür: list of dicts — {'kural', 'ates', 'yuzde', 'cikti'}
    """
    r = max(0.0, min(1.0, stok_norm))
    h = max(0.0, min(5.0, hiz))

    aciklamalar = _KURAL_ACIKLAMALARI.get(dil, _KURAL_ACIKLAMALARI["TR"])
    sonuclar = []
    for i, (stok_fn, hiz_fn, cikti) in enumerate(KURALLAR):
        ates = min(stok_fn(r), hiz_fn(h))
        if ates > 0.01:
            sonuclar.append({
                "kural":  aciklamalar[i],
                "ates":   round(ates, 3),
                "yuzde":  round(ates * 100, 1),
                "cikti":  cikti,
            })
    sonuclar.sort(key=lambda x: x["ates"], reverse=True)
    return sonuclar


def tahmin_bitis_zamani(stok, tuketim_saatlik):
    """
    Mevcut tüketim hızına göre stoğun biteceği tarihi tahmin eder.
    Döndürür: dict — {'saat', 'tarih', 'aciklama'}
    """
    from datetime import datetime, timedelta

    if tuketim_saatlik <= 0.001 or stok <= 0:
        return {"saat": None, "tarih": None, "aciklama": "—"}

    kalan_saat = stok / tuketim_saatlik
    bitis      = datetime.now() + timedelta(hours=kalan_saat)
    return {
        "saat":      round(kalan_saat, 1),
        "tarih":     bitis.strftime("%d.%m.%Y %H:%M"),
        "aciklama":  f"{round(kalan_saat, 1)} saat sonra",
    }


def stok_tukenis_olasiligi(stok, tuketim_saatlik, sure_saat=24):
    """
    Gelecek N saatte stok tükenme olasılığını hesaplar (0-100).
    """
    if stok <= 0:
        return 100.0
    if tuketim_saatlik <= 0.001:
        return 0.0
    tahmini = tuketim_saatlik * sure_saat
    return round(min(100.0, (tahmini / stok) * 100), 1)

