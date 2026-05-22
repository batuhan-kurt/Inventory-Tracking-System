import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

kategoriler = ["CocaCola_Klasik", "CocaCola_Zero", "Pepsi", "Fanta", "RedBull_Klasik", "RedBull_White", "RedBull_Blue", "RedBull_Lilac", "RedBull_Pembe", "Nescafe_Klasik"]
islem_tipleri = ["Alındı", "Eklendi"]

# Son 7 günün verisini oluştur
bitis_tarihi = datetime.now()
baslangic_tarihi = bitis_tarihi - timedelta(days=7)

veri = []
# Dolap yaklaşık 200 kez açılmış/kapanmış olsun
for _ in range(200):
    # Rastgele bir zaman seç (Daha çok akşam saatlerinde yoğunluk olsun)
    saat = int(np.random.normal(18, 4)) % 24
    dakika = random.randint(0, 59)
    rastgele_gun = random.randint(0, 6)
    
    tarih = bitis_tarihi - timedelta(days=rastgele_gun)
    tarih = tarih.replace(hour=saat, minute=dakika, second=0, microsecond=0)
    
    urun = random.choices(kategoriler, weights=[20, 15, 10, 10, 15, 5, 5, 5, 5, 10])[0]
    
    # %85 ihtimalle ürün alınsın, %15 eklensin
    islem = random.choices(islem_tipleri, weights=[85, 15])[0]
    
    veri.append({
        "Tarih": tarih.strftime("%Y-%m-%d %H:%M:%S"),
        "Urun": urun,
        "Islem": islem,
        "Adet": 1
    })

df = pd.DataFrame(veri)
df = df.sort_values(by="Tarih").reset_index(drop=True)
df.to_csv("satis_gecmisi.csv", index=False)
print("Sahte veri üretildi: satis_gecmisi.csv")
