# helpers.py
import streamlit as st
import urllib.parse
import pandas as pd
from io import BytesIO

def inject_css():
    st.markdown("""
    <style>
        div[data-testid="stButton"] button { width: 100%; border-radius: 12px; border: 1px solid #ddd; padding: 15px 5px; font-size: 16px; font-weight: bold; min-height: 50px; }
        div[data-testid="stButton"] button:hover { background-color: #f0f2f6; border-color: #333; }
        a[kind="primary"] { width: 100%; border-radius: 12px; text-align: center; padding: 15px 5px; font-weight: bold; text-decoration: none; display: inline-block; background-color: #25D366 !important; color: white !important; border: none; margin-bottom: 5px; }
        .streamlit-expanderHeader { font-size: 16px !important; font-weight: 700 !important; background-color: #f8f9fa; border: 1px solid #ddd; border-radius: 10px; margin-bottom: 5px; color: #333 !important; }
        div[role="radiogroup"] { background-color: #f9f9f9; padding: 10px; border-radius: 10px; justify-content: center; }
        .stTextArea textarea { font-size: 16px; border-radius: 10px; }
        .kat-baslik { padding: 10px; border-radius: 8px; margin-bottom: 15px; border-left: 5px solid #666; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

def authenticate():
    try: GERCEK_SIFRE = st.secrets["genel"]["admin_sifresi"]
    except: GERCEK_SIFRE = "1234"

    if "mobil_giris" not in st.session_state: st.session_state.mobil_giris = False
    
    if not st.session_state.mobil_giris:
        st.markdown("<br><h1 style='text-align: center;'>📱 Yurt Mobil Giriş</h1>", unsafe_allow_html=True)
        sifre = st.text_input("Şifre", type="password", label_visibility="collapsed", placeholder="Şifreyi Girin")
        if st.button("Giriş Yap", type="primary"):
            if sifre == GERCEK_SIFRE:
                st.session_state.mobil_giris = True
                st.rerun()
            else: st.error("Hatalı Şifre!")
        return False
    return True

def kat_bul(oda_no):
    try:
        no = int(str(oda_no).strip())
        if 101 <= no <= 115: return "1. KAT"
        elif 201 <= no <= 215: return "2. KAT"
        elif 301 <= no <= 315: return "3. KAT"
        else: return "DİĞER"
    except: return "DİĞER"

def wp(tel, m):
    t = str(tel).replace(' ','').lstrip('0').replace('-','').replace('.','').strip()
    if not t or len(t) < 10: return None
    return f"https://wa.me/90{t}?text={urllib.parse.quote(m)}"

def sablon_indir():
    df_sablon = pd.DataFrame(columns=["Ad Soyad", "Numara", "Oda No", "Baba Adı", "Anne Adı", "Baba Tel", "Anne Tel"])
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer: df_sablon.to_excel(writer, index=False)
    return output.getvalue()
