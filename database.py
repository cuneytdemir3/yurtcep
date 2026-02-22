# database.py
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SHEET_LINKI = "https://docs.google.com/spreadsheets/d/14vue2y63WXYE6-uXqtiEUgGU-yVrBCJy6R6Nj_EdyMI/edit?gid=0#gid=0"
SUTUNLAR = ["Ad Soyad", "Numara", "Oda No", "Durum", "İzin Durumu", "Etüd", "Yat", "Mesaj Durumu", "Baba Adı", "Anne Adı", "Baba Tel", "Anne Tel"]

def get_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error("🚨 Sunucu Bağlantı Hatası!")
        return None

def get_sheet(): 
    c = get_client()
    return c.open_by_url(SHEET_LINKI).sheet1 if c else None

def get_log():
    c = get_client()
    if c:
        s = c.open_by_url(SHEET_LINKI)
        try: return s.worksheet("GECMIS")
        except: 
            ws = s.add_worksheet("GECMIS", 1000, 12)
            ws.append_row(["Tarih"] + SUTUNLAR)
            return ws
    return None

def init_data():
    if "tutanak_1" not in st.session_state: st.session_state.tutanak_1 = "Olumsuz bir durum yoktur."
    if "tutanak_2" not in st.session_state: st.session_state.tutanak_2 = "Olumsuz bir durum yoktur."
    if "tutanak_3" not in st.session_state: st.session_state.tutanak_3 = "Olumsuz bir durum yoktur."

    if "df" not in st.session_state:
        try:
            s = get_sheet()
            if s:
                d = s.get_all_records()
                st.session_state.df = pd.DataFrame(d) if d else pd.DataFrame(columns=SUTUNLAR)
                for c in SUTUNLAR:
                    if c not in st.session_state.df.columns: st.session_state.df[c] = "-"
                st.session_state.df = st.session_state.df.fillna("-").astype(str)
            else:
                st.session_state.df = pd.DataFrame(columns=SUTUNLAR)
        except Exception as e: 
            st.error(f"Veri Hatası: {e}")
            st.stop()

def save_data():
    try: 
        s = get_sheet()
        if s: s.update([st.session_state.df.columns.tolist()] + st.session_state.df.astype(str).values.tolist())
    except: st.warning("⚠️ Kayıt edilemedi (İnternet/API hatası).")

def archive_data():
    try:
        t = datetime.now().strftime("%d.%m.%Y"); d = st.session_state.df.copy(); d.insert(0, "Tarih", t)
        l = get_log()
        if l: l.append_rows(d.astype(str).values.tolist()); st.success(f"✅ {t} Arşivlendi!"); st.balloons()
    except: st.error("Arşiv Hatası")

def reset_daily_data():
    st.session_state.df["Durum"] = "Belirsiz"
    st.session_state.df["Etüd"] = "⚪"
    st.session_state.df["Yat"] = "⚪"
    st.session_state.df["Mesaj Durumu"] = "-"
    save_data()
