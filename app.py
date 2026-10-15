import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Grafika Plus - Kalkulator", layout="centered")

st.title("🖨️ Kalkulator Tiska & Dorade")

# Učitavanje cjenika iz CSV datoteke
@st.cache_data
def ucitaj_cjenik():
    try:
        # Čitanje CSV datoteke
        df = pd.read_csv("cjenik_tiskara.csv", comment="=", skip_blank_lines=True)
        # Čišćenje razmaka u nazivima stupaca
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Greška pri učitavanju cjenik_tiskara.csv datoteke: {e}")
        return None

df_cjenik = ucitaj_cjenik()

if df_cjenik is not None:
    # B2B Rabat opcije u bočnoj traci
    rabat_pct = st.sidebar.number_input("B2B Rabat za klijenta (%)", min_value=0, max_value=50, value=0, step=5)

    tehnologija = st.radio("Odaberite tehnologiju:", ["Aračni tisak (Konica Minolta C4065)", "Veliki format iz role (Epson SC-S40610)"])

    st.divider()

    # --- MODUL 1: ARAČNI TISAK ---
    if "Aračni" in tehnologija:
        st.subheader("📄 Aračni tisak (KM C4065)")
        
        # Filtriranje materijala za arak
        materijali_arak = df_cjenik[df_cjenik['Tip'].astype(str).str.strip() == 'arak']
        odabrani_mat_naziv = st.selectbox("Vrsta papira / materijala:", materijali_arak['Naziv Materijala'].tolist())
        mat_red = materijali_arak[materijali_arak['Naziv Materijala'] == odabrani_mat_naziv].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            sirina_prod = st.number_input("Širina proizvoda (mm):", value=148)
        with col2:
            visina_prod = st.number_input("Visina proizvoda (mm):", value=105)
            
        kolicina = st.number_input("Količina (komada):", value=500, step=50)
        marza = st.slider("Marža (%)", min_value=10, max_value=200, value=60)

        if st.button("🧮 Izračunaj aračni tisak", type="primary"):
            arak_s = float(mat_red['Širina (mm)'])
            arak_v = float(mat_red['Visina (mm)'])
            
            stane1 = (arak_s // sirina_prod) * (arak_v // visina_prod)
            stane2 = (arak_s // visina_prod) * (arak_v // sirina_prod)
            komada_po_arku = max(stane1, stane2)
            
            if komada_po_arku == 0:
                st.error("Dimenzija proizvoda je veća od ulaznog formata arka!")
            else:
                potrebno_araka = math.ceil(kolicina / komada_po_arku) + 3 # +3 makulatura
                nabavna_cijena_arka = float(mat_red['Nabavna Cijena (EUR)'])
                
                # Siguran dohvat podataka za stroj KM C4065 (STR-01)
                stroj_red = df_cjenik[df_cjenik['ID'].astype(str).str.strip() == 'STR-01']
                
                if not stroj_red.empty:
                    setup_stroj = float(stroj_red.iloc[0].iloc[3])  # 4. stupac: Fiksna Priprema
                    klik_cijena = float(stroj_red.iloc[0].iloc[4])  # 5. stupac: Cijena Prolaza/Klika
                else:
                    setup_stroj = 3.00
                    klik_cijena = 0.035
                
                neto_trosak = (potrebno_araka * nabavna_cijena_arka) + (potrebno_araka * klik_cijena) + setup_stroj
                vpc_osnovna = neto_trosak * (1 + marza / 100)
                konacna_cijena = vpc_osnovna * (1 - rabat_pct / 100)
                
                st.success(f"**Ukupna cijena za klijenta:** {konacna_cijena:.2f} EUR + PDV")
                st.info(f"""
                * **Cijena po komadu:** {konacna_cijena/kolicina:.3f} EUR
                * **Potrebno araka s makulaturom:** {potrebno_araka} (Stane na arak: {int(komada_po_arku)} kom)
                * **Čisti trošak proizvodnje:** {neto_trosak:.2f} EUR
                * **Primijenjen B2B rabat:** {rabat_pct}%
                """)

    # --- MODUL 2: TISAK IZ ROLE ---
    else:
        st.subheader("🎞️ Veliki format iz role (Epson SC-S40610)")
        
        materijali_rola = df_cjenik[df_cjenik['Tip'].astype(str).str.strip() == 'rola']
        odabrani_mat_naziv = st.selectbox("Materijal iz role:", materijali_rola['Naziv Materijala'].tolist())
        mat_red = materijali_rola[materijali_rola['Naziv Materijala'] == odabrani_mat_naziv].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            sirina_m = st.number_input("Širina (m):", value=1.0, step=0.1)
        with col2:
            visina_m = st.number_input("Visina / Duljina (m):", value=2.0, step=0.1)
            
        kolicina_rola = st.number_input("Količina (komada):", value=1)
        marza_rola = st.slider("Marža (%)", min_value=10, max_value=200, value=70)

        if st.button("🧮 Izračunaj veliki format", type="primary"):
            kvadratura = sirina_m * visina_m * kolicina_rola
            nabavna_cijena_m2 = float(mat_red['Nabavna Cijena (EUR)'])
            
            # Siguran dohvat podataka za stroj Epson (STR-02)
            stroj_red = df_cjenik[df_cjenik['ID'].astype(str).str.strip() == 'STR-02']
            
            if not stroj_red.empty:
                setup_epson = float(stroj_red.iloc[0].iloc[3])  # 4. stupac: Fiksna Priprema
                boja_m2 = float(stroj_red.iloc[0].iloc[4])      # 5. stupac: Cijena Boje/m2
            else:
                setup_epson = 5.00
                boja_m2 = 1.20
            
            neto_trosak = (kvadratura * nabavna_cijena_m2) + (kvadratura * boja_m2) + setup_epson
            vpc_osnovna = neto_trosak * (1 + marza_rola / 100)
            konacna_cijena = vpc_osnovna * (1 - rabat_pct / 100)
            
            st.success(f"**Ukupno za klijenta:** {konacna_cijena:.2f} EUR + PDV")
            st.info(f"""
            * **Cijena po m² za klijenta:** {konacna_cijena/kvadratura:.2f} EUR/m²
            * **Ukupna kvadratura:** {kvadratura:.2f} m²
            * **Čisti trošak proizvodnje:** {neto_trosak:.2f} EUR
            * **Primijenjen B2B rabat:** {rabat_pct}%
            """)
