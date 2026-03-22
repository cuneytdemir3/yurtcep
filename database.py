import streamlit as st
import pandas as pd
import time

from database import init_data, save_data, archive_data, reset_daily_data, get_archive_df, delete_all_students, SUTUNLAR
from helpers import inject_css, authenticate, kat_bul, wp, sablon_indir
from pdf_engine import pdf_yap

# --- AYARLAR ---
st.set_page_config(page_title="Yurt Mobil", page_icon="📱", layout="centered")
inject_css()
if not authenticate(): st.stop()

# Veritabanını Başlat
init_data()

# --- AKSİYON FONKSİYONLARI ---
def izn(i): st.session_state.df.at[i,"İzin Durumu"] = "İzin Yok" if st.session_state.df.at[i,"İzin Durumu"]=="İzin Var" else "İzin Var"; save_data()
def ey(i,t): st.session_state.df.at[i,t] = {"⚪":"✅ Var","✅ Var":"❌ Yok","❌ Yok":"⚪"}.get(st.session_state.df.at[i,t],"⚪"); save_data()
def msj(i,m): st.session_state.df.at[i,"Mesaj Durumu"] = m; save_data()

def kalanlari_yurtta_yap():
    mask = st.session_state.df["Durum"] == "Belirsiz"
    st.session_state.df.loc[mask, "Durum"] = "Yurtta"
    st.session_state.df.loc[mask, "Mesaj Durumu"] = "-"
    save_data()

# --- KAT RENKLERİ ---
KAT_RENKLERI = {"1. KAT": "#E3F2FD", "2. KAT": "#E8F5E9", "3. KAT": "#FFF3E0", "DİĞER": "#F3E5F5"}

# ==========================================
# YAN MENÜ (SIDEBAR)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>📱 Yurt Mobil</h2>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("MENÜ", ["📋 LİSTE", "🎫 İZİN", "📝 TUTANAK", "➕ EKLE", "🗑️ SİL", "🗄️ GEÇMİŞ", "📄 PDF"], label_visibility="collapsed")
    st.divider()
    st.caption("v2.5 - WhatsApp Okuyucu")

c1, c2 = st.columns([4,1])
with c1: st.title(menu) 
with c2: 
    if st.button("🔄 Yenile", use_container_width=True): st.cache_data.clear(); st.rerun()

f_df = st.session_state.df

# ==========================================
# İÇERİK EKRANLARI
# ==========================================
if menu == "📋 LİSTE":
    
    if not f_df.empty:
        toplam = len(f_df)
        yurtta = len(f_df[f_df['Durum'] == 'Yurtta'])
        izinli = len(f_df[f_df['Durum'].isin(['İzinli', 'Evde'])])
        belirsiz = len(f_df[f_df['Durum'] == 'Belirsiz'])
        
        islem_gorenler = toplam - belirsiz
        yuzde = int((islem_gorenler / toplam) * 100) if toplam > 0 else 0
        st.progress(yuzde / 100.0, text=f"📊 Günlük Yoklama İlerlemesi: %{yuzde} Tamamlandı")

        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f"""<div style="background-color: #E3F2FD; padding: 15px 5px; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #BBDEFB;"><p style="margin: 0; font-size: 13px; color: #1565C0; font-weight: bold;">Toplam</p><h2 style="margin: 0; color: #0D47A1; font-size: 26px;">{toplam}</h2></div>""", unsafe_allow_html=True)
        k2.markdown(f"""<div style="background-color: #E8F5E9; padding: 15px 5px; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #C8E6C9;"><p style="margin: 0; font-size: 13px; color: #2E7D32; font-weight: bold;">🟢 Yurtta</p><h2 style="margin: 0; color: #1B5E20; font-size: 26px;">{yurtta}</h2></div>""", unsafe_allow_html=True)
        k3.markdown(f"""<div style="background-color: #FFF3E0; padding: 15px 5px; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #FFE0B2;"><p style="margin: 0; font-size: 13px; color: #E65100; font-weight: bold;">🟡 İzinli</p><h2 style="margin: 0; color: #BF360C; font-size: 26px;">{izinli}</h2></div>""", unsafe_allow_html=True)
        k4.markdown(f"""<div style="background-color: #F5F5F5; padding: 15px 5px; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #E0E0E0;"><p style="margin: 0; font-size: 13px; color: #616161; font-weight: bold;">⚪ Belirsiz</p><h2 style="margin: 0; color: #212121; font-size: 26px;">{belirsiz}</h2></div>""", unsafe_allow_html=True)
        st.write("")
        
        grafik_verisi = pd.DataFrame({"Durum": ["Yurtta", "İzinli", "Belirsiz"], "Kişi Sayısı": [yurtta, izinli, belirsiz]}).set_index("Durum")
        st.bar_chart(grafik_verisi, height=150, color="#1565C0")
        st.divider()

    c_sifirla, c_toplu = st.columns(2)
    with c_sifirla:
        with st.expander("⚠️ YENİ GÜN BAŞLAT"):
            st.warning("Tüm liste sıfırlanır.")
            if st.button("🔴 SIFIRLA", type="primary", use_container_width=True): 
                reset_daily_data(); st.success("Sıfırlandı!"); time.sleep(1); st.rerun()
    with c_toplu:
        with st.expander("✨ HIZLI YOKLAMA"):
            st.info("Kalanları 'Yurtta' işaretler.")
            if st.button("✅ KALANLARI YURTTA SAY", type="primary", use_container_width=True):
                kalanlari_yurtta_yap(); st.success("Kalan herkes Yurtta olarak işaretlendi!"); time.sleep(1.5); st.rerun()
            
    c_kaydet, c_arsiv = st.columns(2)
    with c_kaydet: 
        if st.button("☁️ KAYDET", type="primary"): save_data(); st.toast("Kaydedildi!")
    with c_arsiv:
        if st.button("🌙 GÜNÜ BİTİR"): archive_data()
        
    ara = st.text_input("🔍 Ara", placeholder="Öğrenci Adı veya Oda No...")
    if ara: f_df = f_df[f_df.astype(str).apply(lambda x: x.str.contains(ara, case=False)).any(axis=1)]

    f_df["_Kat_Grubu"] = f_df["Oda No"].apply(kat_bul)
    kat_sirasi = ["1. KAT", "2. KAT", "3. KAT", "DİĞER"]

    for kat in kat_sirasi:
        kat_df = f_df[f_df["_Kat_Grubu"] == kat]
        if not kat_df.empty:
            with st.expander(f"🏢 {kat} ({len(kat_df)} Öğrenci)", expanded=False):
                renk = KAT_RENKLERI.get(kat, "#eee")
                st.markdown(f"""<div class="kat-baslik" style="background-color: {renk}; font-weight:bold;">{kat} LİSTESİ</div>""", unsafe_allow_html=True)
                odalar = sorted(kat_df["Oda No"].unique().tolist(), key=str)
                for oda in odalar:
                    st.markdown(f"##### 🛏️ Oda {oda}")
                    for i in kat_df[kat_df["Oda No"] == oda].index:
                        r = f_df.loc[i]
                        ikon = {"Yurtta": "🟢", "İzinli": "🟡", "Evde": "🔵", "Belirsiz": "⚪"}.get(r['Durum'], "⚪")
                        
                        tikler = ""
                        if "Var" in str(r['Etüd']): tikler += " [E✅]"
                        elif "Yok" in str(r['Etüd']): tikler += " [E❌]"
                        if "Var" in str(r['Yat']): tikler += " [Y✅]"
                        elif "Yok" in str(r['Yat']): tikler += " [Y❌]"
                        
                        with st.expander(f"{ikon} {r['Ad Soyad']} {tikler}"):
                            st.caption("Durum Seçiniz:")
                            secenekler = ["Yurtta", "İzinli", "Evde"]; 
                            if r['Durum'] == "Belirsiz": secenekler.insert(0, "Belirsiz")
                            try: m_idx = secenekler.index(r['Durum'])
                            except: m_idx = 0
                            yeni = st.radio("D", secenekler, index=m_idx, key=f"rd{i}", horizontal=True, label_visibility="collapsed")
                            if yeni != r['Durum']: st.session_state.df.at[i, "Durum"] = yeni; st.session_state.df.at[i, "Mesaj Durumu"] = "-"; save_data(); st.rerun()
                            
                            if r['Durum'] == "Belirsiz": st.warning("⚠️ Seçiniz.")
                            elif r['Durum'] == "Yurtta":
                                st.divider(); c3, c4 = st.columns(2)
                                with c3:
                                    s = "primary" if "Yok" in str(r['Etüd']) else "secondary"
                                    if st.button(f"Etüd: {r['Etüd']}", key=f"e{i}", type=s, use_container_width=True): ey(i,"Etüd"); st.rerun()
                                with c4:
                                    s = "primary" if "Yok" in str(r['Yat']) else "secondary"
                                    if st.button(f"Yat: {r['Yat']}", key=f"y{i}", type=s, use_container_width=True): ey(i,"Yat"); st.rerun()
                                if "Yok" in str(r['Etüd']) or "Yok" in str(r['Yat']):
                                    st.warning("⚠️ Yoklamada Yok!"); msj_txt = f"Öğrenciniz {r['Ad Soyad']} etüd yoklamasına katılmamıştır." if "Yok" in str(r['Etüd']) else f"Öğrenciniz {r['Ad Soyad']} Yat yoklamasında yurtta bulunmamıştır."
                                    lb = wp(r['Baba Tel'], msj_txt); la = wp(r['Anne Tel'], msj_txt)
                                    if lb: st.link_button(f"👨 Baba", lb, use_container_width=True, type="primary")
                                    if la: st.link_button(f"👩 Anne", la, use_container_width=True, type="primary")
                                    if st.button("✅ Mesaj Atıldı", key=f"m{i}", use_container_width=True): msj(i, "Msj Atıldı"); st.rerun()
                            elif r['Durum'] == "Evde":
                                st.write(""); btn = "primary" if r['İzin Durumu']=="İzin Yok" else "secondary"; lbl = "✅ İzinli" if r['İzin Durumu']=="İzin Var" else "⛔ İzinsiz"
                                if st.button(lbl, key=f"i{i}", type=btn, use_container_width=True): izn(i); st.rerun()
                                if r['İzin Durumu'] == "İzin Var": st.success("Evci İzinli.")
                                else:
                                     st.error("🚨 KAÇAK!"); msj_txt = f"Öğrenciniz {r['Ad Soyad']} izinsiz olarak yurtta bulunmamaktadır."; lb = wp(r['Baba Tel'], msj_txt); la = wp(r['Anne Tel'], msj_txt)
                                     if lb: st.link_button("👨 Baba", lb, use_container_width=True, type="primary")
                                     if la: st.link_button("👩 Anne", la, use_container_width=True, type="primary")
                                     if st.button("✅ Ok", key=f"m{i}", use_container_width=True): msj(i, "Msj Atıldı"); st.rerun()
                            else: 
                                st.info("Çarşı İzinli"); s_yat = "primary" if "Yok" in str(r['Yat']) else "secondary"
                                if st.button(f"🛏️ Yat: {r['Yat']}", key=f"iy{i}", type=s_yat, use_container_width=True): ey(i,"Yat"); st.rerun()
                                if "Yok" in str(r['Yat']):
                                    st.warning("⚠️ Dönmedi!"); msj_txt = f"Öğrenciniz {r['Ad Soyad']} izinli olmasına rağmen Yat yoklamasında yurda giriş yapmamıştır."; lb = wp(r['Baba Tel'], msj_txt); la = wp(r['Anne Tel'], msj_txt)
                                    if lb: st.link_button("👨 Baba", lb, use_container_width=True, type="primary")
                                    if la: st.link_button("👩 Anne", la, use_container_width=True, type="primary")
                                    if st.button("✅ Ok", key=f"m{i}", use_container_width=True): msj(i, "Msj Atıldı"); st.rerun()

# ==========================================
# 🎫 İZİN İŞLEMLERİ (MANUEL & WHATSAPP)
# ==========================================
elif menu == "🎫 İZİN":
    
    tab_manuel, tab_wp = st.tabs(["✍️ Tek Tek İzin Ver", "💬 WhatsApp Metninden Oku"])
    
    # --- 1. SEKMESİ: MANUEL İZİN ---
    with tab_manuel:
        ara_izin = st.text_input("Öğrenci Ara (Ad veya Oda No)", placeholder="İzne çıkacak öğrenciyi arayın...")
        if ara_izin:
            bulunanlar = f_df[f_df.astype(str).apply(lambda x: x.str.contains(ara_izin, case=False)).any(axis=1)]
            if not bulunanlar.empty:
                for i in bulunanlar.index:
                    r = bulunanlar.loc[i]
                    st.markdown(f"**👤 {r['Ad Soyad']}** (Oda: {r['Oda No']})")
                    c1, c2 = st.columns([2, 1])
                    izin_turu = c1.selectbox("İzin Türü", ["Evci İzni (Haftasonu/Evde)", "Çarşı İzni (Günlük)", "Raporlu/Hastane"], key=f"tur_{i}", label_visibility="collapsed")
                    if c2.button("✅ İzne Çıkar", key=f"btn_izin_{i}", type="primary", use_container_width=True):
                        if "Evci" in izin_turu or "Raporlu" in izin_turu:
                            st.session_state.df.at[i, "Durum"] = "Evde"
                        else:
                            st.session_state.df.at[i, "Durum"] = "İzinli"
                        st.session_state.df.at[i, "İzin Durumu"] = "İzin Var"
                        st.session_state.df.at[i, "Mesaj Durumu"] = "-"
                        save_data()
                        st.success(f"{r['Ad Soyad']} izne çıkarıldı!")
                        time.sleep(1); st.rerun()
                    st.divider()

    # --- 2. SEKMESİ: YENİ WHATSAPP METİN OKUYUCU ---
    with tab_wp:
        st.info("💡 WhatsApp grubundaki izin mesajlarını kopyalayıp aşağıdaki kutuya yapıştırın. Sistem metindeki isimleri listeden otomatik tespit edecektir.")
        
        wp_metin = st.text_area("WhatsApp Mesajları", height=200, placeholder="Örn:\n101 nolu odadan Ahmet Yılmaz evci iznine çıkmıştır.\n105 Ali Demir raporlu olduğu için yurda gelmeyecek...")
        
        if wp_metin:
            # Türkçe karakter sorunlarını çözmek için ufak bir temizleme aracı
            def cevir(t):
                return str(t).replace('İ','i').replace('I','ı').lower().strip()
                
            aranan_metin = cevir(wp_metin)
            eslesenler = []
            eslesen_idx = []
            
            # Tüm öğrenci listesini tara ve isim metnin içinde geçiyor mu kontrol et
            for idx, r in f_df.iterrows():
                ad_orj = str(r['Ad Soyad']).strip()
                if not ad_orj or ad_orj == "-": continue
                
                ad_kucuk = cevir(ad_orj)
                oda = str(r['Oda No']).strip()
                
                # Eğer öğrencinin Adı ve Soyadı metnin içinde birebir geçiyorsa
                if ad_kucuk in aranan_metin:
                    eslesenler.append(f"👤 **{ad_orj}** (Oda: {oda})")
                    eslesen_idx.append(idx)
                    
            if eslesenler:
                st.success(f"✅ Sistem metnin içinde {len(eslesenler)} öğrenci tespit etti:")
                for e in eslesenler:
                    st.markdown(f"- {e}")
                    
                st.warning("Eğer liste doğruysa aşağıdaki butona basarak hepsini tek seferde izne (Evci) çıkarabilirsiniz.")
                if st.button("🚀 Tespit Edilenleri İzne Çıkar (Evci)", type="primary"):
                    for i in eslesen_idx:
                        st.session_state.df.at[i, "Durum"] = "Evde"  # WhatsApp izinleri varsayılan olarak Evci sayılır
                        st.session_state.df.at[i, "İzin Durumu"] = "İzin Var"
                        st.session_state.df.at[i, "Mesaj Durumu"] = "-"
                    save_data()
                    st.balloons()
                    st.success("Harika! Tüm tespit edilen öğrenciler izne çıkarıldı.")
                    time.sleep(2)
                    st.rerun()
            else:
                st.warning("Metinde kayıtlı öğrencilerinizden hiçbiriyle eşleşen bir isim bulunamadı. Lütfen isimlerin listedekiyle aynı yazıldığından emin olun.")

    st.write("---")
    
    # --- 3. BÖLÜM: Şu An İzinde Olanlar ---
    st.markdown("##### 🟡 Şu An İzinde Olan Öğrenciler")
    izinliler = f_df[f_df['Durum'].isin(["İzinli", "Evde"])]
    
    if not izinliler.empty:
        for i in izinliler.index:
            r = izinliler.loc[i]
            ikon = '🔵 Evde/Raporlu' if r['Durum'] == 'Evde' else '🟡 Çarşıda'
            with st.container():
                c_isim, c_islem = st.columns([2, 1])
                c_isim.write(f"{ikon} \n\n **{r['Ad Soyad']}** (Oda: {r['Oda No']})")
                if c_islem.button("↩️ Yurda Döndü", key=f"dondu_{i}", use_container_width=True):
                    st.session_state.df.at[i, "Durum"] = "Yurtta"
                    save_data()
                    st.toast(f"✅ {r['Ad Soyad']} yurda giriş yaptı!")
                    time.sleep(1); st.rerun()
                st.divider()
    else:
        st.info("Şu an izinde olan öğrenci bulunmuyor.")

elif menu == "📝 TUTANAK":
    st.session_state.tutanak_1 = st.text_area("1. Kat Tutanağı", st.session_state.tutanak_1, height=100)
    st.session_state.tutanak_2 = st.text_area("2. Kat Tutanağı", st.session_state.tutanak_2, height=100)
    st.session_state.tutanak_3 = st.text_area("3. Kat Tutanağı", st.session_state.tutanak_3, height=100)
    if st.button("💾 Tutanakları Kaydet", type="primary"): st.success("Kaydedildi")

elif menu == "➕ EKLE":
    tab1, tab2 = st.tabs(["✍️ Tek Tek Ekle", "📂 Excel Yükle"])
    with tab1:
        with st.form("ekle_manuel"):
            ad=st.text_input("Öğrenci Adı Soyadı"); c1, c2 = st.columns(2); no=c1.text_input("Okul No"); oda=c2.text_input("Oda No")
            st.divider(); st.caption("Aile Bilgileri"); b_ad = st.text_input("Baba Adı"); b_tel = st.text_input("Baba Tel"); a_ad = st.text_input("Anne Adı"); a_tel = st.text_input("Anne Tel")
            if st.form_submit_button("Kaydet", type="primary"):
                y = pd.DataFrame([{"Ad Soyad":ad, "Numara":no, "Oda No":oda, "Durum":"Belirsiz", "İzin Durumu":"İzin Var", "Etüd":"⚪", "Yat":"⚪", "Mesaj Durumu":"-", "Baba Adı":b_ad, "Anne Adı":a_ad, "Baba Tel":b_tel, "Anne Tel":a_tel}])
                st.session_state.df = pd.concat([st.session_state.df, y], ignore_index=True); save_data(); st.success("Eklendi")
    with tab2:
        st.info("Gerekli: Ad Soyad, Numara, Oda No, Baba Adı, Anne Adı, Baba Tel, Anne Tel"); st.download_button("📥 Şablon", sablon_indir(), "sablon.xlsx")
        f = st.file_uploader("Excel Seç", type=["xlsx"])
        if f:
            try:
                ndf = pd.read_excel(f)
                ndf.columns = [str(c).strip() for c in ndf.columns] 
                ndf = ndf.astype(str)
                for c in SUTUNLAR: 
                    if c not in ndf.columns: ndf[c] = "-"
                ndf["Durum"]="Belirsiz"; ndf["İzin Durumu"]="İzin Var"; ndf["Etüd"]="⚪"; ndf["Yat"]="⚪"; ndf["Mesaj Durumu"]="-"
                ndf = ndf.replace("nan", "-")
                if st.button("✅ Yükle", type="primary"):
                    st.session_state.df = pd.concat([st.session_state.df, ndf], ignore_index=True); save_data(); st.success("Yüklendi!"); time.sleep(2); st.rerun()
            except Exception as e: st.error(f"Hata: {e}")

elif menu == "🗑️ SİL":
    with st.expander("⚠️ TÜM ÖĞRENCİLERİ SİL (Dönem Sonu vs.)"):
        st.error("DİKKAT: Bu işlem listedeki BÜTÜN öğrencileri kalıcı olarak siler! Geri dönüşü yoktur.")
        sil_onay = st.checkbox("Evet, tüm öğrencileri kalıcı olarak silmek istiyorum.")
        if sil_onay:
            if st.button("🚨 TÜMÜNÜ SİL", type="primary", use_container_width=True):
                delete_all_students()
                st.success("Tüm liste başarıyla silindi!")
                time.sleep(1.5)
                st.rerun()

    st.write("---")
    st.caption("Tekli Öğrenci Silme")
    ara_sil = st.text_input("Silinecek Öğrenciyi Ara (Ad veya Oda No)")
    if ara_sil:
        silinecekler = f_df[f_df.astype(str).apply(lambda x: x.str.contains(ara_sil, case=False)).any(axis=1)]
        if not silinecekler.empty:
            for i in silinecekler.index:
                r = silinecekler.loc[i]
                with st.expander(f"❌ {r['Ad Soyad']} - {r['Oda No']}"):
                    if st.button("🗑️ BU ÖĞRENCİYİ SİL", key=f"sil_btn_{i}", type="primary"):
                        st.session_state.df = st.session_state.df.drop(i).reset_index(drop=True); save_data(); st.success("Silindi!"); time.sleep(1); st.rerun()

elif menu == "🗄️ GEÇMİŞ":
    d = get_archive_df()
    if not d.empty:
        secili_tarih = st.selectbox("Tarih Seç", d["Tarih"].unique())
        st.dataframe(d[d["Tarih"] == secili_tarih], use_container_width=True)
    else:
        st.info("Henüz arşivlenmiş kayıt bulunmamaktadır.")

elif menu == "📄 PDF":
    c1, c2, c3 = st.columns(3)
    b1 = c1.text_input("1. Kat Belletmen")
    b2 = c2.text_input("2. Kat Belletmen")
    b3 = c3.text_input("3. Kat Belletmen")
    if st.button("PDF Oluştur", type="primary"):
        st.download_button("⬇️ İndir", pdf_yap(st.session_state.df, b1, b2, b3, st.session_state.tutanak_1, st.session_state.tutanak_2, st.session_state.tutanak_3), "yoklama.pdf", "application/pdf")
