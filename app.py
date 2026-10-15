import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Grafika Plus - Kalkulator", layout="wide")

st.title("🖨️ Grafika Plus - Prodajni Kalkulator")

# Učitavanje cjenika
@st.cache_data
def ucitaj_cjenik():
    try:
        df = pd.read_csv("cjenik_tiskara.csv", comment="=", skip_blank_lines=True)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Greška pri učitavanju cjenika: {e}")
        return None

df_cjenik = ucitaj_cjenik()

if df_cjenik is not None:
    # Sidebar B2B Rabat
    rabat_pct = st.sidebar.number_input("B2B Rabat klijenta (%)", min_value=0, max_value=50, value=0, step=5)

    tab1, tab2, tab3 = st.tabs(["🏷️ Gotovi Proizvodi (Matrica)", "📄 Slobodni Aračni Tisak", "🎞️ Veliki Format (Rola)"])

    # --- TAB 1: GOTOVI PROIZVODI PO NAKLADAMA ---
    with tab1:
        st.subheader("Odaberite gotov proizvod i nakladu")
        
        proizvodi_df = df_cjenik[df_cjenik['ID'].astype(str).str.strip().str.startswith('PRZ')]
        
        if not proizvodi_df.empty:
            kategorija = st.selectbox("Kategorija proizvoda:", proizvodi_df['Kategorija'].unique())
            filtrirani_proizvodi = proizvodi_df[proizvodi_df['Kategorija'] == kategorija]
            
            odabrani_proizvod = st.selectbox("Proizvod / Format:", filtrirani_proizvodi['Naziv Proizvoda'].tolist())
            prz_red = filtrirani_proizvodi[filtrirani_proizvodi['Naziv Proizvoda'] == odabrani_proizvod].iloc[0]
            
            sirina_p = float(prz_red['Širina (mm)'])
            visina_p = float(prz_red['Visina (mm)'])
            marza_p = float(prz_red['Preporučena Marža (%)'])
            
            materijali_arak = df_cjenik[df_cjenik['Tip'].astype(str).str.strip() == 'arak']
            odabrani_papir = st.selectbox("Odaberite papir:", materijali_arak['Naziv Materijala'].tolist())
            mat_red = materijali_arak[materijali_arak['Naziv Materijala'] == odabrani_papir].iloc[0]
            
            st.divider()
            st.write("### Cjenik po nakladama (EUR + PDV)")
            
            naklade = [100, 200, 300, 400, 500, 1000]
            
            arak_s, arak_v = float(mat_red['Širina (mm)']), float(mat_red['Visina (mm)'])
            stane1 = (arak_s // sirina_p) * (arak_v // visina_p)
            stane2 = (arak_s // visina_p) * (arak_v // sirina_p)
            kom_po_arku = max(stane1, stane2)
            
            if kom_po_arku > 0:
                cols = st.columns(len(naklade))
                stroj_red = df_cjenik[df_cjenik['ID'].astype(str).str.strip() == 'STR-01']
                setup_stroj = float(stroj_red.iloc[0].iloc[3]) if not stroj_red.empty else 3.0
                klik = float(stroj_red.iloc[0].iloc[4]) if not stroj_red.empty else 0.035
                
                for idx, naklada in enumerate(naklade):
                    araka = math.ceil(naklada / kom_po_arku) + 3
                    trosak = (araka * float(mat_red['Nabavna Cijena (EUR)'])) + (araka * klik) + setup_stroj
                    prodajna = (trosak * (1 + marza_p / 100)) * (1 - rabat_pct / 100)
                    cijena_kom = prodajna / naklada
                    
                    with cols[idx]:
                        st.metric(
                            label=f"📦 {naklada} kom",
                            value=f"{prodajna:.2f} €",
                            delta=f"{cijena_kom:.3f} €/kom",
                            delta_color="off"
                        )
            else:
                st.error("Proizvod je prevelik za standardni arak!")
        else:
            st.info("Dodajte gotove proizvode u CSV datoteku pod sekciju '=== GOTOVI PROIZVODI ==='")

    # --- TAB 2: SLOBODNI ARAČNI TISAK ---
    with tab2:
        st.subheader("📄 Aračni tisak (Konica Minolta C4065)")
        materijali_arak = df_cjenik[df_cjenik['Tip'].astype(str).str.strip() == 'arak']
        odabrani_mat_naziv = st.selectbox("Vrsta papira / materijala (slobodni unos):", materijali_arak['Naziv Materijala'].tolist())
        mat_red = materijali_arak[materijali_arak['Naziv Materijala'] == odabrani_mat_naziv].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            sirina_prod = st.number_input("Širina proizvoda (mm):", value=148, key="s_arak")
        with col2:
            visina_prod = st.number_input("Visina proizvoda (mm):", value=105, key="v_arak")
            
        kolicina = st.number_input("Količina (komada):", value=500, step=50, key="k_arak")
        marza = st.slider("Marža (%)", min_value=10, max_value=200, value=60, key="m_arak")

        if st.button("🧮 Izračunaj aračni tisak", type="primary"):
            arak_s = float(mat_red['Širina (mm)'])
            arak_v = float(mat_red['Visina (mm)'])
            stane1 = (arak_s // sirina_prod) * (arak_v // visina_prod)
            stane2 = (arak_s // visina_prod) * (arak_v // sirina_prod)
            komada_po_arku = max(stane1, stane2)
            
            if komada_po_arku == 0:
                st.error("Dimenzija je veća od ulaznog formata arka!")
            else:
                potrebno_araka = math.ceil(kolicina / komada_po_arku) + 3
                nabavna_cijena_arka = float(mat_red['Nabavna Cijena (EUR)'])
                stroj_red = df_cjenik[df_cjenik['ID'].astype(str).str.strip() == 'STR-01']
                setup_stroj = float(stroj_red.iloc[0].iloc[3]) if not stroj_red.empty else 3.0
                klik_cijena = float(stroj_red.iloc[0].iloc[4]) if not stroj_red.empty else 0.035
                
                neto_trosak = (potrebno_araka * nabavna_cijena_arka) + (potrebno_araka * klik_cijena) + setup_stroj
                vpc_osnovna = neto_trosak * (1 + marza / 100)
                konacna_cijena = vpc_osnovna * (1 - rabat_pct / 100)
                
                st.success(f"**Ukupna cijena za klijenta:** {konacna_cijena:.2f} EUR + PDV")
                st.info(f"* Cijena po komadu: {konacna_cijena/kolicina:.3f} EUR | Araka s makulaturom: {potrebno_araka}")

    # --- TAB 3: VELIKI FORMAT ---
    with tab3:
        st.subheader("🎞️ Veliki format iz role (Epson SC-S40610)")
        materijali_rola = df_cjenik[df_cjenik['Tip'].astype(str).str.strip() == 'rola']
        odabrani_mat_naziv = st.selectbox("Materijal iz role:", materijali_rola['Naziv Materijala'].tolist(), key="m_rola")
        mat_red = materijali_rola[materijali_rola['Naziv Materijala'] == odabrani_mat_naziv].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            sirina_m = st.number_input("Širina (m):", value=1.0, step=0.1, key="s_m")
        with col2:
            visina_m = st.number_input("Visina / Duljina (m):", value=2.0, step=0.1, key="v_m")
            
        kolicina_rola = st.number_input("Količina (komada):", value=1, key="k_rola")
        marza_rola = st.slider("Marža (%)", min_value=10, max_value=200, value=70, key="m_marza")

        if st.button("🧮 Izračunaj veliki format", type="primary"):
            kvadratura = sirina_m * visina_m * kolicina_rola
            nabavna_cijena_m2 = float(mat_red['Nabavna Cijena (EUR)'])
            stroj_red = df_cjenik[df_cjenik['ID'].astype(str).str.strip() == 'STR-02']
            setup_epson = float(stroj_red.iloc[0].iloc[3]) if not stroj_red.empty else 5.0
            boja_m2 = float(stroj_red.iloc[0].iloc[4]) if not stroj_red.empty else 1.20
            
            neto_trosak = (kvadratura * nabavna_cijena_m2) + (kvadratura * boja_m2) + setup_epson
            vpc_osnovna = neto_trosak * (1 + marza_rola / 100)
            konacna_cijena = vpc_osnovna * (1 - rabat_pct / 100)
            
            st.success(f"**Ukupno za klijenta:** {konacna_cijena:.2f} EUR + PDV")
            st.info(f"* Cijena po m²: {konacna_cijena/kvadratura:.2f} EUR/m² | Ukupno: {kvadratura:.2f} m²")
