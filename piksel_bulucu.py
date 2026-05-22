import cv2

# Tıklanan noktaları hafızada tutacağımız liste
noktalar = []

def piksel_al(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        noktalar.append((x, y))
        print(f"📍 Tıklandı: X={x}, Y={y}")
        
        # İki kere tıklandığında (Sol üst ve Sağ alt) formatı yazdır
        if len(noktalar) == 2:
            x1, y1 = noktalar[0]
            x2, y2 = noktalar[1]
            
            print("\n✅ KODA YAPIŞTIRILACAK FORMAT: [y1:y2, x1:x2]")
            print(f"[{y1}:{y2}, {x1}:{x2}]\n")
            print("-" * 30)
            
            # Diğer slot için listeyi sıfırla
            noktalar.clear() 

# Kendi fotoğrafının adını buraya yaz
FOTO_ADI = "dolap_oncesi.jpg"

img = cv2.imread(FOTO_ADI)

if img is None:
    print("❌ HATA: Fotoğraf bulunamadı!")
else:
    print("🎯 PİKSEL BULUCU BAŞLADI!")
    print("Kural: Önce ürünün SOL ÜST köşesine, sonra SAĞ ALT köşesine tıkla.")
    print("Çıkmak için fotoğraf üzerindeyken 'q' tuşuna bas.\n")
    
    cv2.imshow("Piksel Bulucu", img)
    cv2.setMouseCallback("Piksel Bulucu", piksel_al)
    
    # 'q' tuşuna basılana kadar bekle
    while True:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()