# database.py
import streamlit as st
import pandas as pd
import json
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

SUTUNLAR = ["Ad Soyad", "Numara", "Oda No", "Durum", "İzin Durumu", "Etüd", "Yat", "Mesaj Durumu", "Baba Adı", "Anne Adı", "Baba Tel", "Anne Tel"]

# Firebase Bağlantısını Başlat (Cache ile hızlandırıldı)
@st.cache_resource
def get_db():
    if not firebase_admin._apps:
        # Secrets'tan JSON verisini okuyup Firebase'e yetki veriyoruz
        key_dict = json.loads(st.secrets["firebase_json"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = get_db()

def init_data():
    if "tutanak_1" not in st.session_state: st.session_state.tutanak_1 = "Olumsuz bir durum yoktur."
    if "tutanak_2" not in st.session_state: st.session_state.tutanak_2 = "Olumsuz bir durum yoktur."
    if "tutanak_3" not in st.session_state: st.session_state.tutanak_3 = "Olumsuz bir durum yoktur."

    if "df" not in st.session_state:
        try:
            # Firestore'dan güncel listeyi çek
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
            st.error(f"Veritabanı Hatası: {e}")
            st.session_state.df = pd.DataFrame(columns=SUTUNLAR)

def save_data():
    try: 
        # Verileri saniyeler içinde Firestore'a yaz
        records = st.session_state.df.to_dict(orient='records')
        db.collection('sistem').document('guncel_liste').set({'veriler': records})
    except Exception as e: 
        st.warning(f"⚠️ Kayıt edilemedi: {e}")

def archive_data():
    try:
        t = datetime.now().strftime("%d.%m.%Y")
        records = st.session_state.df.to_dict(orient='records')
        # Geçmiş günleri ayrı bir klasöre (gecmis) kaydet
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

# Geçmiş verileri tablo olarak getiren fonksiyon
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
