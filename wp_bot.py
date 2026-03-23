import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import firebase_admin
from firebase_admin import credentials, firestore

# ==========================================
# 1. FİREBASE BAĞLANTISI
# ==========================================
# İNDİRDİĞİN FİREBASE JSON DOSYASININ YOLUNU BURAYA YAZ
# (Streamlit secrets kullanamayız çünkü bu bağımsız bir dosya)
CRED_PATH = "firebase_gizli_anahtar.json" 

if not firebase_admin._apps:
    cred = credentials.Certificate(CRED_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ==========================================
# 2. AYARLAR
# ==========================================
# Okunacak WhatsApp Grubunun Tam Adı
HEDEF_GRUP = "Yurt İzin Grubu" 
SON_OKUNAN_MESAJ = ""

# Türkçe karakterleri temizleme fonksiyonu (Eşleştirme kolaylığı için)
def cevir(t):
    return str(t).replace('İ','i').replace('I','ı').lower().strip()

# ==========================================
# 3. WHATSAPP WEB'İ BAŞLATMA
# ==========================================
print("🚀 WhatsApp Botu Başlatılıyor...")
options = webdriver.ChromeOptions()
# options.add_argument('--headless') # Arka planda gizli çalışması için (Testten sonra açabilirsin)
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

driver.get("https://web.whatsapp.com")
print("📱 Lütfen 30 saniye içinde WhatsApp QR kodunu okutun...")
time.sleep(20) # QR okutman için bekleme süresi

# ==========================================
# 4. GRUBU BUL VE DİNLEMEYE BAŞLA
# ==========================================
try:
    # Arama kutusuna grubun adını yazıp Enter'a bas
    arama_kutusu = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
    arama_kutusu.send_keys(HEDEF_GRUP)
    time.sleep(2)
    arama_kutusu.send_keys(Keys.ENTER)
    print(f"✅ {HEDEF_GRUP} grubuna girildi. Dinleme başlıyor...\n")
    
except Exception as e:
    print("❌ Grup bulunamadı veya sayfa yüklenmedi. Hata:", e)
    driver.quit()
    exit()

# Sonsuz Döngü (7/24 Mesajları Dinler)
while True:
    try:
        # Ekrandaki tüm mesaj kutularını bul (Sınıf adları WhatsApp güncellendikçe değişebilir!)
        mesajlar = driver.find_elements(By.CSS_SELECTOR, "div.message-in span.selectable-text")
        
        if mesajlar:
            en_son_mesaj = mesajlar[-1].text # En alttaki son mesajı al
            
            # Eğer bu mesajı daha önce okumadıysak işle
            if en_son_mesaj != SON_OKUNAN_MESAJ:
                print(f"📩 Yeni Mesaj Yakalandı: {en_son_mesaj}")
                SON_OKUNAN_MESAJ = en_son_mesaj
                
                # --- Firebase'den Güncel Listeyi Çek ---
                doc_ref = db.collection('sistem').document('guncel_liste')
                doc = doc_ref.get()
                
                if doc.exists:
                    liste = doc.to_dict().get('veriler', [])
                    degisiklik_var_mi = False
                    
                    aranan_metin = cevir(en_son_mesaj)
                    
                    # Mesajdaki ismi listedekilerle karşılaştır
                    for ogrenci in liste:
                        ad_kucuk = cevir(ogrenci.get('Ad Soyad', ''))
                        
                        if ad_kucuk and ad_kucuk in aranan_metin:
                            print(f"🎯 Eşleşme Bulundu: {ogrenci['Ad Soyad']} -> İzinli İşaretleniyor...")
                            ogrenci['Durum'] = 'Evde'
                            ogrenci['İzin Durumu'] = 'İzin Var'
                            degisiklik_var_mi = True
                    
                    # Eğer bir öğrenci bulup değiştirdiysek, Firebase'i güncelle
                    if degisiklik_var_mi:
                        doc_ref.set({'veriler': liste})
                        print("☁️ Firebase güncellendi! Ana uygulamaya yansıdı.\n")
                
    except Exception as e:
        pass # Hata olursa (örneğin element bulunamazsa) çökmesin, devam etsin
        
    time.sleep(5) # Her 5 saniyede bir yeni mesaj var mı diye kontrol et
