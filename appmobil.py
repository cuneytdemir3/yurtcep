import streamlit as st
import pandas as pd
import urllib.parse
import gspread
from google.oauth2.service_account import Credentials
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import simpleSplit
import os
from datetime import datetime
import time

# --- MOBİL AYARLAR ---
st.set_page_config(page_title="Yurt Mobil", page_icon="📱", layout="centered")

# --- LİNK AYARI ---
SHEET_LINKI = "https://docs.google.com/spreadsheets/d/14vue2y63WXYE6-uXqtiEUgGU-yVrBCJy6R6Nj_EdyMI/edit?gid=0#gid=0"

# --- KAT RENKLERİ ---
KAT_RENKLERI = {
    "1. KAT": "#E3F2FD",
    "2. KAT": "#E8F5E9",
    "3. KAT": "#FFF3E0",
    "DİĞER": "#F3E5F5"
}

# --- MOBİL CSS ---
st.markdown("""
<style>
    div[data-testid="stButton"] button {
        width: 100%;
        border-radius: 12px;
        border: 1px solid #ddd;
        padding: 15px 5px; 
        font-size: 16px;
        font-weight: bold;
        min-height: 50px;
    }
    div[data-testid="stButton"] button:hover {
        background-color: #f0f2f6;
        border-color: #333;
    }
    a[kind="primary"] {
        width: 100%;
        border-radius: 12px;
        text-align: center;
        padding: 15px 5px;
        font-weight: bold;
        text-decoration: none;
        display: inline-block;
        background-color: #25D366 !important;
        color: white !important;
        border: none;
        margin-bottom: 5px;
    }
    .streamlit-expanderHeader {
        font-size: 16px !important;
        font-weight: 700 !important;
        background-color: #f8f9fa;
        border: 1px solid #ddd;
        border-radius: 10px;
        margin-bottom: 5px;
        color: #333 !important;
    }
    div[role="radiogroup"] {
        background-color: #f9f9f9;
        padding: 10px;
        border-radius: 10px;
        justify-content: center;
    }
    .stTextArea textarea {
        font-size: 16px;
        border-radius: 10px;
    }
    .kat-baslik {
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 15px;
        border-left: 5px solid #666;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- GİRİŞ SİSTEMİ ---
def giris_kontrol():
    try: GERCEK_SIFRE = st.secrets["genel"]["admin_sifresi"]
    except: GERCEK_SIFRE = "1234"

    if "mobil_giris" not in st.session_state: st.session_state.mobil_giris = False
    
    if not st.session_state.mobil_giris:
        st.markdown("<br><h1 style='text-align: center;'>📱 Mobil Giriş</h1>", unsafe_allow_html=True)
        sifre = st.text_input("Şifre", type="password", label_visibility="collapsed", placeholder="Şifreyi Girin")
        if st.button("Giriş Yap", type="primary"):
            if sifre == GERCEK_SIFRE:
                st.session_state.mobil_giris = True
                st.rerun()
            else: st.error("Hatalı Şifre!")
        return False
    return True

if not giris_kontrol(): st.stop()

# --- BAĞLANTI ---
def get_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error("🚨 Bağlantı Hatası! Secrets ayarlarını yaptın mı?")
        st.stop()

def get_sheet(): return get_client().open_by_url(SHEET_LINKI).sheet1
def get_log():
    c = get_client(); s = c.open_by_url(SHEET_LINKI)
    try: return s.worksheet("GECMIS")
    except: 
        ws = s.add_worksheet("GECMIS", 1000, 12)
        ws.append_row(["Tarih", "Ad Soyad", "Numara", "Oda No", "Durum", "İzin Durumu", "Etüd", "Yat", "Mesaj Durumu", "Baba Adı", "Anne Adı", "Baba Tel", "Anne Tel"])
        return ws

# --- VERİ YÖNETİMİ ---
SUTUNLAR = ["Ad Soyad", "Numara", "Oda No", "Durum", "İzin Durumu", "Etüd", "Yat", "Mesaj Durumu", "Baba Adı", "Anne Adı", "Baba Tel", "Anne Tel"]

if "tutanak_1" not in st.session_state: st.session_state.tutanak_1 = "Olumsuz bir durum yoktur."
if "tutanak_2" not in st.session_state: st.session_state.tutanak_2 = "Olumsuz bir durum yoktur."
if "tutanak_3" not in st.session_state: st.session_state.tutanak_3 = "Olumsuz bir durum yoktur."

# Verileri çek ve Temizle
if "df" not in st.session_state:
    try:
        d = get_sheet().get_all_records()
        st.session_state.df = pd.DataFrame(d) if d else pd.DataFrame(columns=SUTUNLAR)
        for c in SUTUNLAR:
            if c not in st.session_state.df.columns: st.session_state.df[c] = "-"
        
        # HATA DÜZELTME: Tüm verileri string (metin) yapalım ki karışıklık çıkmasın
        st.session_state.df = st.session_state.df.fillna("-").astype(str)
        
    except Exception as e: st.error(f"Veri Hatası: {e}"); st.stop()

def kaydet():
    try: 
        # Kaydederken de hepsini string'e çeviriyoruz
        get_sheet().update([st.session_state.df.columns.tolist()] + st.session_state.df.astype(str).values.tolist())
    except: 
        st.error("Bağlantı Hatası! Kaydedilemedi.")

def arsivle():
    try:
        t = datetime.now().strftime("%d.%m.%Y"); d = st.session_state.df.copy(); d.insert(0, "Tarih", t)
        get_log().append_rows(d.astype(str).values.tolist()); st.success(f"✅ {t} Arşivlendi!"); st.balloons()
    except: st.error("Arşiv Hatası")

def sifirla_yeni_yoklama():
    st.session_state.df["Durum"] = "Belirsiz"
    st.session_state.df["Etüd"] = "⚪"
    st.session_state.df["Yat"] = "⚪"
    st.session_state.df["Mesaj Durumu"] = "-"
    kaydet()
    st.success("Tüm liste sıfırlandı! Yoklamaya başlayabilirsiniz.")
    time.sleep(1)
    st.rerun()

# --- PDF ---
def pdf_yap(df, b1, b2, b3, t1, t2, t3):
    b = BytesIO(); c = canvas.Canvas(b, pagesize=A4); w, h = A4
    try: pdfmetrics.registerFont(TTFont('Arial', 'C:\\Windows\\Fonts\\arial.ttf')); f = 'Arial'
    except: f = 'Helvetica'
    
    c.setFont(f, 16); c.drawString(40, h-50, "YURT YOKLAMA LİSTESİ")
    c.setFont(f, 10); c.drawString(40, h-75, f"Tarih: {datetime.now().strftime('%d.%m.%Y')}")
    c.setFont(f, 9)
    c.drawRightString(w-40, h-50, f"1. Kat: {b1}"); c.drawRightString(w-40, h-62, f"2. Kat: {b2}"); c.drawRightString(w-40, h-74, f"3. Kat: {b3}")
    c.line(40, h-85, w-40, h-85)
    
    data = [["Ad", "No", "Oda", "Drm", "İzin", "Etüd", "Yat", "Msj"]]
    
    # --- HATA DÜZELTME NOKTASI ---
    # Sıralama yapmadan önce Oda No sütununu kesinlikle String yapıyoruz.
    df_pdf = df.copy()
    df_pdf["Oda No"] = df_pdf["Oda No"].astype(str)
    
    for _, r in df_pdf.sort_values("Oda No").iterrows():
        durum_kisa = r['Durum'][0] if r['Durum'] != "Belirsiz" else "?"
        data.append([str(r['Ad Soyad'])[:15], str(r['Numara']), str(r['Oda No']), durum_kisa, "-" if r['Durum']=="Yurtta" else str(r['İzin Durumu'])[0], str(r['Etüd']).replace("✅ Var","+").replace("❌ Yok","-").replace("⚪",""), str(r['Yat']).replace("✅ Var","+").replace("❌ Yok","-").replace("⚪",""), "OK" if "Atıldı" in str(r['Mesaj Durumu']) else ""])
    
    t = Table(data, colWidths=[90,30,30,30,30,30,30,40]); t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black),('FONTNAME',(0,0),(-1,-1),f),('FONTSIZE',(0,0),(-1,-1),8)]))
    t.wrapOn(c, w, h); t.drawOn(c, 40, h-(110+len(data)*20))
    
    c.showPage()
    c.setFont(f, 16); c.drawString(40, h-50, "GÜNLÜK KAT TUTANAKLARI")
    c.line(40, h-60, w-40, h-60)
    
    y_pos = h - 100
    def yazdir_tutanak(baslik, metin, y):
        c.setFont(f, 12); c.setFillColor(colors.darkblue); c.drawString(40, y, baslik)
        y -= 20
        c.setFont(f, 10); c.setFillColor(colors.black)
        lines = simpleSplit(metin, f, 10, w-80)
        for line in lines: c.drawString(40, y, line); y -= 15
        return y - 30

    y_pos = yazdir_tutanak(f"1. KAT TUTANAĞI ({b1})", t1, y_pos)
    y_pos = yazdir_tutanak(f"2. KAT TUTANAĞI ({b2})", t2, y_pos)
    y_pos = yazdir_tutanak(f"3. KAT TUTANAĞI ({b3})", t3, y_pos)
    c.save(); b.seek(0); return b

def wp(tel, m):
    t = str(tel).replace(' ','').lstrip('0').replace('-','').replace('.','').strip()
    if not t or len(t) < 10: return None
    return f"https://wa.me/90{t}?text={urllib.parse.quote(m)}"

def sablon_indir():
    df_sablon = pd.DataFrame(columns=["Ad Soyad", "Numara", "Oda No", "Baba Adı", "Anne Adı", "Baba Tel", "Anne Tel"])
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_sablon.to_excel(writer, index=False)
    return output.getvalue()

def kat_bul(oda_no):
    try:
        no = int(str(oda_no).strip())
        if 101 <= no <= 115: return "1. KAT"
        elif 201 <= no <= 215: return "2. KAT"
        elif 301 <= no <= 315: return "3. KAT"
        else: return "DİĞER"
    except: return "DİĞER"

# --- İŞLEM FONKSİYONLARI ---
def izn(i): 
    st.session_state.df.at[i,"İzin Durumu"]="İzin Yok" if st.session_state.df.at[i,"İzin Durumu"]=="İzin Var" else "İzin Var"
    kaydet()

def ey(i,t): 
    st.session_state.df.at[i,t]={"⚪":"✅ Var","✅ Var":"❌ Yok","❌ Yok":"⚪"}.get(st.session_state.df.at[i,t],"⚪")
    kaydet()

def msj(i,m): 
    st.session_state.df.at[i,"Mesaj Durumu"]=m
    kaydet()

# --- ARAYÜZ ---
c1, c2 = st.columns([3,1])
with c1: st.title("📱 Mobil Takip")
with c2: 
    if st.button("🔄"): st.cache_data.clear(); st.rerun()

menu = st.selectbox("Menü", ["📋 LİSTE", "📝 TUTANAK", "➕ EKLE", "🗑️ SİL", "🗄️ GEÇMİŞ", "📄 PDF"])

if menu == "📋 LİSTE":
    
    st.write("")
    if st.button("⚪ YENİ YOKLAMA BAŞLAT (Herkesi Sıfırla)", use_container_width=True):
        sifirla_yeni_yoklama()
    st.write("")

    c_kaydet, c_arsiv = st.columns(2)
    with c



