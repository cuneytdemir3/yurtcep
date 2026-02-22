# pdf_engine.py
import streamlit as st
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import simpleSplit
import os
import requests
from datetime import datetime
import warnings
from helpers import kat_bul

warnings.filterwarnings("ignore")

@st.cache_resource
def font_yukle():
    font_yolu = "/tmp/Roboto-Regular.ttf"
    font_adi = "Roboto"
    linkler = [
        "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf",
        "https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Regular.ttf"
    ]
    if not os.path.exists(font_yolu) or os.path.getsize(font_yolu) < 10000:
        for url in linkler:
            try:
                r = requests.get(url, timeout=10, verify=False)
                if r.status_code == 200:
                    with open(font_yolu, "wb") as f: f.write(r.content)
                    break
            except: pass
    try:
        pdfmetrics.registerFont(TTFont(font_adi, font_yolu))
        return font_adi
    except: return "Helvetica"

def tr_upper(text, font_adi):
    if not text: return ""
    if font_adi == "Helvetica":
        return text.replace("İ", "I").replace("ı", "i").replace("Ğ", "G").replace("ğ", "g").replace("Ş", "S").replace("ş", "s").upper()
    return text.replace("i", "İ").replace("ı", "I").upper()

def pdf_yap(df, b1, b2, b3, t1, t2, t3):
    b = BytesIO(); c = canvas.Canvas(b, pagesize=A4); w, h = A4
    font = font_yukle()
    
    secili_katlar = []
    if b1: secili_katlar.append("1. KAT")
    if b2: secili_katlar.append("2. KAT")
    if b3: secili_katlar.append("3. KAT")
    if not secili_katlar: secili_katlar = ["1. KAT", "2. KAT", "3. KAT", "DİĞER"]

    df_pdf = df.copy(); df_pdf["Oda No"] = df_pdf["Oda No"].astype(str)
    df_pdf["_KAT"] = df_pdf["Oda No"].apply(kat_bul)
    df_pdf = df_pdf[df_pdf["_KAT"].isin(secili_katlar)]

    baslik = "YURT YOKLAMA LİSTESİ" if font != "Helvetica" else "YURT YOKLAMA LISTESI"
    c.setFont(font, 16); c.drawString(40, h-50, baslik)
    c.setFont(font, 10); c.drawString(40, h-75, f"Tarih: {datetime.now().strftime('%d.%m.%Y')}")
    c.setFont(font, 9); y_h = 50
    if b1: c.drawRightString(w-40, h-y_h, f"1. Kat: {tr_upper(b1, font)}"); y_h+=12
    if b2: c.drawRightString(w-40, h-y_h, f"2. Kat: {tr_upper(b2, font)}"); y_h+=12
    if b3: c.drawRightString(w-40, h-y_h, f"3. Kat: {tr_upper(b3, font)}")
    c.line(40, h-90, w-40, h-90)
    
    data = [["Ad Soyad", "Oda", "Drm", "İzin", "Etüd", "Yat", "Msj"]]
    for _, r in df_pdf.sort_values("Oda No").iterrows():
        ad = str(r['Ad Soyad'])[:22]
        if font == "Helvetica": ad = ad.replace("İ", "I").replace("ı", "i").replace("Ğ", "G").replace("ğ", "g").replace("Ş", "S").replace("ş", "s")
        drm_str = str(r['Durum']); d_kisa = "?" if (drm_str=="Belirsiz" or not drm_str) else drm_str[0]
        izn_str = str(r['İzin Durumu']); i_kisa="-" if (r['Durum']=="Yurtta" or not izn_str) else izn_str[0]
        data.append([ad, str(r['Oda No']), d_kisa, i_kisa, str(r['Etüd']).replace("✅ Var","+").replace("❌ Yok","-").replace("⚪",""), str(r['Yat']).replace("✅ Var","+").replace("❌ Yok","-").replace("⚪",""), "OK" if "Atıldı" in str(r['Mesaj Durumu']) else ""])
    
    t = Table(data, colWidths=[120, 30, 30, 30, 30, 30, 40]); 
    t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black),('FONTNAME',(0,0),(-1,-1),font),('FONTSIZE',(0,0),(-1,-1),8)]))
    t.wrapOn(c, w, h); t.drawOn(c, 40, h-(110+len(data)*20))
    
    c.showPage(); c.setFont(font, 16)
    tutanak_baslik = "GÜNLÜK KAT TUTANAKLARI" if font != "Helvetica" else "GUNLUK KAT TUTANAKLARI"
    c.drawString(40, h-50, tutanak_baslik); c.line(40, h-60, w-40, h-60); y_pos = h-100
    
    def yazdir_tutanak(baslik, metin, y):
        c.setFont(font, 12); c.setFillColor(colors.darkblue); c.drawString(40, y, baslik); y-=20
        c.setFont(font, 10); c.setFillColor(colors.black)
        for line in simpleSplit(metin, font, 10, w-80): c.drawString(40, y, line); y -= 15
        return y-30
    
    if b1: y_pos = yazdir_tutanak(f"1. KAT TUTANAĞI ({tr_upper(b1, font)})", t1, y_pos)
    if b2: y_pos = yazdir_tutanak(f"2. KAT TUTANAĞI ({tr_upper(b2, font)})", t2, y_pos)
    if b3: y_pos = yazdir_tutanak(f"3. KAT TUTANAĞI ({tr_upper(b3, font)})", t3, y_pos)
    c.save(); b.seek(0); return b
