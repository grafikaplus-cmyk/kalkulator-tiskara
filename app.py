import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Grafika Plus - Kalkulator", layout="wide")

# CSS stil za oblikovanje kartica naklada kao na slici
st.markdown("""
    <style>
    .stRadio > div {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 18px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🖨️ Grafika Plus - Prodajni Kalkulator")

@st.cache_data
def ucitaj_cjenik():
    try:
        df = pd.read_csv("cjenik_tiskara.csv", comment="=", skip_blank_lines=True)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        return None

df_cjenik = ucitaj_cjenik()

if df_cjenik is not None:
    rabat_pct = st.sidebar.number_input("B2B Rabat klijenta (%)", min_value=0, max_value=50, value=0, step=5)

    st.subheader("1. ODABIR PROIZVODA I SPECIFIKACIJE")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        proizvod = st.selectbox("Proizvod / Format:", [
            "Vizitka Standard (85x55 mm)",
            "Vizitka Euro (90x50 mm)",
            "Vizitka Kvadratna (55x55 mm)",
            "Letak A6 (105x148 mm)",
            "Letak A5 (148x210 mm)",
            "Letak A4 (210x297 mm)"
        ])
    
    with col2:
        materijali_arak = df_cjenik[df_cjenik['Tip'].astype(str).str.strip() == 'arak']
        odabrani_papir = st.selectbox("Vrsta papira / materijala:", materijali_arak['Naziv Materijala'].tolist())
        mat_red = materijali_arak[materijali_arak['Naziv Materijala'] == odabrani_papir].iloc[0]
        
    with col3:
        tisak = st.selectbox("Tisak:", ["4/0 - Kolor jednostrano", "4/4 - Kolor obostrano"])
        plastifikacija = st.selectbox("Zaštita / Plastifikacija:", ["Bez plastifikacije", "Mat plastifikacija 1/0", "Mat plastifikacija 1/1", "Sjaj plastifikacija 1/0"])

    marza = st.slider("Marža (%)", min_value=10, max_value=200, value=80, step=5)

    # Određivanje dimenzija i kapaciteta na SRA3 arku
    if "85x55" in proizvod or "90x50" in proizvod:
        sirina_p, visina_p, kom_po_arku = 85, 55, 24
    elif "55x55" in proizvod:
        sirina_p, visina_p, kom_po_arku = 55, 55, 35
    elif "A6" in proizvod:
        sirina_p, visina_p, kom_po_arku = 105, 148, 8
    elif "A5" in proizvod:
        sirina_p, visina_p, kom_po_arku = 148, 210, 4
    elif "A4" in proizvod:
        sirina_p, visina_p, kom_po_arku = 210, 297, 2
    else:
        sirina_p, visina_p, kom_po_arku = 85, 55, 24

    st.divider()
    st.subheader("2. ODABERITE NAKLADU")

    # Mreža naklada kao sa slike
    naklade = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1500, 2000, 2500, 3000, 4000, 5000]
    
    stroj_red = df_cjenik[df_cjenik['ID'].astype(str).str.strip() == 'STR-01']
    setup_stroj = float(stroj_red.iloc[0].iloc[3]) if not stroj_red.empty else 3.0
    klik_osnovni = float(stroj_red.iloc[0].iloc[4]) if not stroj_red.empty else 0.035
    
    # Množitelj klika za obostrani tisak
    množitelj_tiska = 2 if "4/4" in tisak else 1
    klik_cijena = klik_osnovni * množitelj_tiska
    
    # Dodatak za plastifikaciju po arku
    cijena_plastifikacije = 0.10 if "plastifikacija" in plastifikacija.lower() else 0.0
    if "1/1" in plastifikacija:
        cijena_plastifikacije *= 2

    nabavna_cijena_arka = float(mat_red['Nabavna Cijena (EUR)'])

    # Generiranje opcija naklada s cijenom
    opcije_naklada = []
    cijene_mapa = {}

    for n in naklade:
        araka = math.ceil(n / kom_po_arku)
        trosak = (araka * nabavna_cijena_arka) + (araka * klik_cijena) + (araka * cijena_plastifikacije) + setup_stroj
        prodajna = (trosak * (1 + marza / 100)) * (1 - rabat_pct / 100)
        
        tekst_opcije = f"{n} kom  =  {prodajna:.2f} €"
        opcije_naklada.append(tekst_opcije)
        cijene_mapa[tekst_opcije] = (n, prodajna)

    # Mreža radijskih gumba u 4 stupca
    odabrana_opcija = st.radio("Odaberite željenu količinu:", opcije_naklada, index=0)

    # Prikaz odabrane stavke na dnu
    odabrana_kolicina, odabrana_cijena = cijene_mapa[odabrana_opcija]
    cijena_po_kom = odabrana_cijena / odabrana_kolicina

    st.markdown("---")
    col_out1, col_out2 = st.columns([2, 1])
    with col_out1:
        st.markdown(f"### Odabrali ste količinu: **{odabrana_kolicina} kom = {odabrana_cijena:.2f} € + PDV**")
    with col_out2:
        st.markdown(f"*(Cijena po komadu: **{cijena_po_kom:.3f} €**)*")

    # Slobodni unos količine koja nije na popisu
    with st.expander("Trebate količinu koja nije navedena iznad?"):
        proizvoljna_kol = st.number_input("Unesite željenu količinu (kom):", min_value=1, value=1200, step=50)
        araka_p = math.ceil(proizvoljna_kol / kom_po_arku)
        trosak_p = (araka_p * nabavna_cijena_arka) + (araka_p * klik_cijena) + (araka_p * cijena_plastifikacije) + setup_stroj
        prodajna_p = (trosak_p * (1 + marza / 100)) * (1 - rabat_pct / 100)
        st.write(f"Cijena za **{proizvoljna_kol} kom** iznosi: **{prodajna_p:.2f} € + PDV** ({prodajna_p/proizvoljna_kol:.3f} €/kom)")
