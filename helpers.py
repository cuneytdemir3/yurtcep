import streamlit as st
import urllib.parse
import pandas as pd
from io import BytesIO

def inject_css():
    st.markdown("""
    <style>
        /* --- GENEL BUTON TASARIMI --- */
        div[data-testid="stButton"] button { 
            width: 100%; 
            border-radius: 12px; 
            border: none; 
            padding: 10px 5px; 
            font-size: 16px; 
            font-weight: 600; 
            min-height: 45px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 5px rgba(0,0,0,0.08);
        }
        div[data-testid="stButton"] button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }
        
        /* --- WP ve DİĞER LİNK BUTONLARI --- */
        a[kind="primary"] { 
            width: 100%; 
            border-radius: 12px; 
            text-align: center; 
            padding: 12px 5px; 
            font-weight: bold; 
            text-decoration: none; 
            display: inline-block; 
            background-color: #25D366 !important; 
            color: white !important; 
            border: none; 
            margin-bottom: 5px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 5px rgba(37,211,102,0.3);
        }
        a[kind="primary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(37,211,102,0.5);
        }

        /* --- AÇILIR KUTULAR (EXPANDER) --- */
        .streamlit-expanderHeader { 
            font-size: 16px !important; 
            font-weight: 600 !important; 
            background-color: white !important; 
            border: 1px solid #f0f2f6 !important; 
            border-radius: 12px !important; 
            margin-bottom: 8px; 
            color: #31333F !important;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04) !important;
        }
        .streamlit-expanderHeader:hover {
            box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important;
            border-color: #e0e2e6 !important;
        }

        /* --- İSTATİSTİK KARTLARI (METRICS) --- */
        div[data-testid="stMetric"] {
            background-color: white;
            padding: 15px 10px;
            border-radius: 15px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            border: 1px solid #f8f9fa;
            text-align: center;
            transition: transform 0.2s ease;
        }
        div[data-testid="stMetric"]:hover {
            transform: scale(1.02);
        }
        div[data-testid="stMetricValue"] {
            font-size: 24px !important;
        }

        /* --- RADİO BUTONLARI --- */
        div[role="radiogroup"] { 
            background-color: #f8f9fa; 
            padding: 10px; 
            border-radius: 12px; 
            justify-content: center;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.03);
        }

        /* --- KAT BAŞLIKLARI --- */
        .kat-baslik { 
            padding: 12px; 
            border-radius: 12px; 
            margin-bottom: 15px; 
            margin-top: 10px;
            border-left: 6px solid #555; 
            text-align: center;
            box-shadow: 0 3px 6px rgba(0,0,0,0.06);
            letter-spacing: 0.5px;
        }
        
        /* --- METİN KUTULARI --- */
        .stTextArea textarea { 
            font-size: 16px; 
            border-radius: 12px; 
            border: 1px solid #ddd;
            padding: 10px;
        }
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
        no = int(float(str(oda_no).strip()))
        if 101 <= no <= 115: return "1. KAT"
        elif 201 <= no <= 215: return "2. KAT"
        elif 301 <= no <= 315: return "3. KAT"
        else: return "DİĞER"
    except: return "DİĞER"

# helpers.py dosyasının içindeki wp fonksiyonunu bununla değiştir:

def wp(tel, m):
    t = str(tel).strip()
    # Excel sonuna .0 eklediyse onu temizle
    if t.endswith('.0'): 
        t = t[:-2]
    # Kalan boşluk, nokta, tire ve baştaki sıfırları temizle
    t = t.replace(' ','').replace('.','').lstrip('0').replace('-','')
    
    # Numara 10 haneden kısaysa hatalı kabul et ve butonu gösterme
    if not t or len(t) < 10: return None
    
    return f"https://wa.me/90{t}?text={urllib.parse.quote(m)}"

def sablon_indir():
    df_sablon = pd.DataFrame(columns=["Ad Soyad", "Numara", "Oda No", "Baba Adı", "Anne Adı", "Baba Tel", "Anne Tel"])
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer: df_sablon.to_excel(writer, index=False)
    return output.getvalue()
