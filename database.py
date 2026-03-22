import streamlit as st
import pandas as pd
import json
import firebase_admin
from firebase_admin import credentials, firestore

# YENİ EKLENDİ: Saat ve zaman hesaplamaları için
from datetime import datetime, timedelta, timezone 

SUTUNLAR = ["Ad Soyad", "Numara", "Oda No", "Durum", "İzin Durumu", "Etüd", "Yat", "Mesaj Durumu", "Baba Adı", "Anne Adı", "Baba Tel", "Anne Tel"]

# --- AKILLI FİREBASE BAĞLANTISI ---
@st.cache_resource
def get_db():
    if not firebase_admin._apps:
        try:
            if "firebase_json" in st.secrets:
                raw_json = st.secrets["firebase_json"]
            elif "firebase" in st.secrets and "firebase_json" in st.secrets["firebase"]:
                raw_json = st.secrets["firebase"]["firebase_json"]
            else:
                st.error("🚨 KRİTİK HATA: Streamlit Secrets içinde 'firebase_json' anahtarı bulunamadı!")
                st.stop()
                
            key_dict = json.loads(raw_json)
            cred = credentials.Certificate(key_dict)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"🚨 Firebase Kurulum Hatası: JSON içeriği bozuk. Detay: {e}")
            st.stop()
            
    return firestore.client()

db = get_db()

# ==========================================
# YENİ: GECE 02:30 OTOMASYONU
# ==========================================
def otomatik_gece_islemi():
    if "df" not in st.session_state or st.session_state.df.empty:
        return
        
    # Türkiye saati (UTC+3) ayarı
    tz_tr = timezone(timedelta(hours=3))
    suan = datetime.now(tz_tr)
    bugun_str = suan.strftime("%d.%m.%Y")
    
    # Eğer saat gece 02:30'u geçmişse
    if suan.hour > 2 or (suan.hour == 2 and suan.minute >= 30):
        try:
            doc_ref = db.collection('sistem').document('otomasyon')
            doc = doc_ref.get()
            son_islem = doc.to_dict().get('son_arsiv_tarihi', '') if doc.exists else ''
            
            # Eğer bugün henüz otomatik sıfırlama yapılmamışsa
            if son_islem != bugun_str:
                
                # 1. ESKİ LİSTEYİ ARŞİVLE (Dünün tarihi ile kaydeder)
                dun_str = (suan - timedelta(days=1)).strftime("%d.%m.%Y")
                records = st.session_state.df.to_dict(orient='records')
                db.collection('gecmis').document(dun_str).set({'tarih': dun_str, 'veriler': records})
                
                # 2. YENİ GÜNÜ SIFIRLA VE BAŞLAT
                st.session_state.df["Durum"] = "Belirsiz"
                st.session_state.df["Etüd"] = "⚪"
                st.session_state.df["Yat"] = "⚪"
                st.session_state.df["Mesaj Durumu"] = "-"
                
                # 3. TEMİZ LİSTEYİ FİREBASE'E YAZ
                records_yeni = st.session_state.df.to_dict(orient='records')
                db.collection('sistem').document('guncel_liste').set({'veriler': records_yeni})
                
                # 4. BUGÜNÜN İŞLEMİ YAPILDI DİYE SİSTEMİ İŞARETLE
                doc_ref.set({'son_arsiv_tarihi': bugun_str})
                
        except Exception as e:
            pass # Hata olursa sessizce geç, uygulamayı çökertme

# ==========================================

def init_data():
    if "tutanak_1" not in st.session_state: st.session_state.tutanak_1 = "Olumsuz bir durum yoktur."
    if "tutanak_2" not in st.session_state: st.session_state.tutanak_2 = "Olumsuz bir durum yoktur."
    if "tutanak_3" not in st.session_state: st.session_state.tutanak_3 = "Olumsuz bir durum yoktur."

    if "df" not in st.session_state:
        try:
            doc = db.collection('sistem').document('guncel_liste').get()
            if doc.exists:
                data = doc.to_dict().get('veriler', [])
                df = pd.DataFrame(data)
                for c in SUTUNLAR:
                    if c not in df.columns: df[c] = "-"
                st.session_state.df = df.fillna("-").astype(str)
            else:
                st.session_state.df = pd.DataFrame(columns=SUTUNLAR)
        except Exception as e: 
            st.error(f"Veritabanı Okuma Hatası: {e}")
            st.session_state.df = pd.DataFrame(columns=SUTUNLAR)
            
    # HER AÇILIŞTA SESSİZCE GECE 2:30 KONTROLÜNÜ YAP
    otomatik_gece_islemi()

def save_data():
    try: 
        records = st.session_state.df.to_dict(orient='records')
        db.collection('sistem').document('guncel_liste').set({'veriler': records})
    except Exception as e: 
        st.warning(f"⚠️ Kayıt edilemedi: {e}")

def archive_data():
    try:
        t = datetime.now().strftime("%d.%m.%Y")
        records = st.session_state.df.to_dict(orient='records')
        db.collection('gecmis').document(t).set({'tarih': t, 'veriler': records})
        st.success(f"✅ {t} Başarıyla Arşivlendi!"); st.balloons()
    except Exception as e: 
        st.error(f"Arşiv Hatası: {e}")

def reset_daily_data():
    st.session_state.df["Durum"] = "Belirsiz"
    st.session_state.df["Etüd"] = "⚪"
    st.session_state.df["Yat"] = "⚪"
    st.session_state.df["Mesaj Durumu"] = "-"
    save_data()

def delete_all_students():
    st.session_state.df = pd.DataFrame(columns=SUTUNLAR)
    save_data()

def get_archive_df():
    try:
        docs = db.collection('gecmis').stream()
        all_records = []
        for doc in docs:
            data = doc.to_dict()
            tarih = data.get('tarih', '')
            veriler = data.get('veriler', [])
            for v in veriler:
                v['Tarih'] = tarih
                all_records.append(v)
        if all_records:
            return pd.DataFrame(all_records)
        return pd.DataFrame()
    except:
        return pd.DataFrame()
