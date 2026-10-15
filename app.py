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
        
        # Dohvat proizvoda iz CSV-a
        proizvodi_df = df_cjenik[df_cjenik['ID'].astype(str).str.startswith('PRZ')]
        
        if not proizvodi_df.empty:
            kategorija = st.selectbox("Kategorija proizvoda:", proizvodi_df['Kategorija'].unique())
            filtrirani_proizvodi = proizvodi_df[proizvodi_df['Kategorija'] == kategorija]
            
            odabrani_proizvod = st.selectbox("Proizvod / Format:", filtrirani_proizvodi['Naziv Proizvoda'].tolist())
            prz_red = filtrirani_proizvodi[filtrirani_proizvodi['Naziv Proizvoda'] == odabrani_proizvod].iloc[0]
            
            sirina_p = float(prz_red['Širina (mm)'])
            visina_p = float(prz_red['Visina (mm)'])
            marza_p = float(prz_red['Preporučena Marža (%)'])
            
            # Odabir papira
            materijali_arak = df_cjenik[df_cjenik['Tip'].astype(str).str.strip() == 'arak']
            odabrani_papir = st.selectbox("Odaberite papir:", materijali_arak['Naziv Materijala'].tolist())
            mat_red = materijali_arak[materijali_arak['Naziv Materijala'] == odabrani_papir].iloc[0]
            
            st.divider()
            st.write("### Cjenik po nakladama (EUR + PDV)")
            
            # Zadane naklade poput onih sa slike
            naklade = [100, 200, 300, 400, 500, 1000]
            
            # Izračun iskorištenja arka (SRA3 450x320)
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
        st.write("Dizajnirano za po mjeri dimenzije (proizvoljna širina/visina).")
        # (Ovdje ide dosadašnji kod za aračni tisak)

    # --- TAB 3: VELIKI FORMAT ---
    with tab3:
        st.write("Dizajnirano za tisak iz role.")
        # (Ovdje ide dosadašnji kod za rolu)
