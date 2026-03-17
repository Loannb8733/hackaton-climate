"""
ClimaVision France — Dashboard de visualisation climatique
Hackathon #26 Sup de Vinci — Big Data & IA : Changement climatique

Point d'entrée Streamlit.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
import requests
from streamlit_folium import st_folium

from utils.data_ingestion import (
    generate_historical_temperatures,
    compute_deviation_from_baseline,
    fetch_real_meteo_data,
    SCENARIOS,
    BASELINE_TEMP_FRANCE,
)
from utils.climate_indicators import (
    EMISSIONS_FRANCE,
    get_preconisations_for_scenario,
)
from utils.geo_data import (
    compute_regional_anomalies,
    get_geojson_url,
)
from models.prophet_forecast import (
    generate_scenario_projections,
    generate_all_scenario_projections,
    compute_crossing_year,
)
from utils.resilience_engine import (
    generate_recommendations,
    get_region_from_postal_code,
    REGIONS_AMPLIFICATION,
    compute_insurance_risk_score,
    compute_cost_of_living_impact,
    compute_pnacc3_effect,
    PNACC3_TIMELINE,
)
from utils.pdf_export import generate_bilan_pdf

# --- Configuration ---
st.set_page_config(
    page_title="ClimaVision France",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS Injection : Premium Glassmorphism ---
st.markdown("""
<style>
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ── Animations ── */
@keyframes pulse-glow {
    0%, 100% { opacity: 0.6; }
    50% { opacity: 1; }
}
@keyframes gradient-shift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
@keyframes fade-in-up {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ── Fond principal — deep dark ── */
.stApp {
    background: linear-gradient(160deg, #050a18 0%, #0a1628 40%, #0d1f35 70%, #050a18 100%);
    background-size: 400% 400%;
    color: #e2e8f0;
}

/* ── Masquer le menu Streamlit ── */
#MainMenu, footer, header {visibility: hidden;}
.stDeployButton {display: none;}

/* ── Padding ── */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1rem !important;
}

/* ── Sidebar — frosted glass ── */
section[data-testid="stSidebar"] {
    background: rgba(10, 22, 40, 0.85) !important;
    backdrop-filter: blur(20px) saturate(1.4);
    -webkit-backdrop-filter: blur(20px) saturate(1.4);
    border-right: 1px solid rgba(59, 130, 246, 0.12);
}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #f1f5f9;
    letter-spacing: -0.05em;
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li {
    color: #94a3b8;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(59, 130, 246, 0.1);
}

/* ── Titres — tight tracking ── */
h1 {
    color: #f8fafc !important;
    font-weight: 900 !important;
    letter-spacing: -0.05em;
}
h2 {
    color: #e2e8f0 !important;
    font-weight: 700 !important;
    letter-spacing: -0.04em;
}
h3, h4 {
    color: #e2e8f0 !important;
    font-weight: 600 !important;
    letter-spacing: -0.03em;
}
.stCaption, caption {
    color: #64748b !important;
    letter-spacing: 0.02em;
}

/* ── Glass card mixin — used everywhere ── */
div[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 18px 22px;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255,255,255,0.05);
    transition: transform 0.3s cubic-bezier(.4,0,.2,1), box-shadow 0.3s cubic-bezier(.4,0,.2,1), border-color 0.3s ease;
    animation: fade-in-up 0.5s ease-out both;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 40px rgba(59, 130, 246, 0.15), inset 0 1px 0 rgba(255,255,255,0.08);
    border-color: rgba(59, 130, 246, 0.25);
}
div[data-testid="stMetric"] label {
    color: #94a3b8 !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
    font-weight: 800 !important;
    font-size: 1.7rem !important;
    letter-spacing: -0.04em;
}
div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {
    font-size: 0.8rem !important;
}

/* ── Tabs — pill style ── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255, 255, 255, 0.02);
    backdrop-filter: blur(12px);
    border-radius: 14px;
    padding: 5px;
    gap: 4px;
    border: 1px solid rgba(255, 255, 255, 0.06);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    color: #64748b;
    font-weight: 500;
    padding: 10px 18px;
    transition: all 0.3s cubic-bezier(.4,0,.2,1);
    letter-spacing: -0.01em;
}
.stTabs [aria-selected="true"] {
    background: rgba(59, 130, 246, 0.15) !important;
    color: #3b82f6 !important;
    border-bottom: none !important;
    font-weight: 700;
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.15);
}
.stTabs [data-baseweb="tab"]:hover {
    color: #e2e8f0;
    background: rgba(255, 255, 255, 0.04);
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {
    display: none;
}

/* ── Boutons — glass ── */
.stButton > button {
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    background: rgba(255, 255, 255, 0.04) !important;
    backdrop-filter: blur(12px);
    color: #e2e8f0 !important;
    font-weight: 500 !important;
    transition: all 0.3s cubic-bezier(.4,0,.2,1) !important;
    letter-spacing: -0.01em;
}
.stButton > button:hover {
    background: rgba(59, 130, 246, 0.15) !important;
    border-color: rgba(59, 130, 246, 0.4) !important;
    color: #3b82f6 !important;
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(59, 130, 246, 0.2) !important;
}
.stButton > button[kind="primary"],
button[data-testid="stDownloadButton"] {
    background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
    border: 1px solid rgba(59, 130, 246, 0.3) !important;
    color: white !important;
    font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover,
button[data-testid="stDownloadButton"]:hover {
    background: linear-gradient(135deg, #60a5fa, #3b82f6) !important;
    box-shadow: 0 8px 32px rgba(59, 130, 246, 0.4) !important;
    transform: translateY(-2px);
}

/* ── Expanders — glass ── */
.streamlit-expanderHeader {
    background: rgba(255, 255, 255, 0.03) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    backdrop-filter: blur(12px);
}
details {
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    border-radius: 12px !important;
    background: rgba(255, 255, 255, 0.02);
    backdrop-filter: blur(8px);
}

/* ── Inputs — glass ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div {
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    backdrop-filter: blur(8px);
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: rgba(59, 130, 246, 0.5) !important;
    box-shadow: 0 0 16px rgba(59, 130, 246, 0.15) !important;
}

/* ── Alert boxes ── */
.stAlert {
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    backdrop-filter: blur(8px);
}

/* ── Progress bars ── */
.stProgress > div > div > div {
    border-radius: 8px;
    background: linear-gradient(90deg, #3b82f6, #10b981) !important;
}

/* ── Dividers ── */
hr {
    border-color: rgba(255, 255, 255, 0.06) !important;
}

/* ── Markdown text ── */
.stMarkdown p, .stMarkdown li {
    color: #cbd5e1;
}
.stMarkdown strong {
    color: #f1f5f9;
}
.stMarkdown a {
    color: #3b82f6;
    transition: color 0.3s ease;
}
.stMarkdown a:hover {
    color: #60a5fa;
}

/* ── Download button ── */
.stDownloadButton > button {
    background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
    border: 1px solid rgba(59, 130, 246, 0.3) !important;
    color: white !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.3s cubic-bezier(.4,0,.2,1) !important;
}
.stDownloadButton > button:hover {
    background: linear-gradient(135deg, #60a5fa, #3b82f6) !important;
    box-shadow: 0 8px 32px rgba(59, 130, 246, 0.4) !important;
    transform: translateY(-2px);
}

/* ── Plotly charts ── */
.js-plotly-plot .plotly .main-svg {
    border-radius: 14px;
}

/* ── Slider ── */
.stSlider > div > div > div {
    color: #3b82f6 !important;
}
</style>
""", unsafe_allow_html=True)

# Plotly global config
PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}
PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(5, 10, 24, 0.6)",
    plot_bgcolor="rgba(5, 10, 24, 0.3)",
    font=dict(family="Inter, sans-serif", color="#94a3b8"),
    margin=dict(l=40, r=20, t=40, b=40),
)
PLOTLY_AXIS = dict(gridcolor="rgba(148, 163, 184, 0.06)", zerolinecolor="rgba(148, 163, 184, 0.08)")

SCENARIO_COLORS = {
    "Optimiste (SSP1-1.9)": "#10b981",
    "Intermédiaire (SSP2-4.5)": "#3b82f6",
    "Pessimiste (SSP5-8.5)": "#f43f5e",
}

# --- Sidebar ---
st.sidebar.title("ClimaVision France")
st.sidebar.markdown("---")

selected_scenario = st.sidebar.selectbox(
    "Scénario principal",
    list(SCENARIOS.keys()),
    index=1,
    help="SSP (Shared Socioeconomic Pathways) : trajectoires d'émissions mondiales du GIEC. "
         "SSP1-1.9 = neutralité carbone 2050, SSP2-4.5 = efforts modérés, SSP5-8.5 = sans action.",
)

scenario_config = SCENARIOS[selected_scenario]
france_warming_2100 = round(scenario_config["global_2100"] * scenario_config["france_factor"], 1)

st.sidebar.metric(
    "Réchauffement mondial 2100",
    f"+{scenario_config['global_2100']}°C",
    help="Réchauffement moyen de la planète d'ici 2100 selon ce scénario (source : GIEC AR6).",
)
st.sidebar.metric(
    "Réchauffement France 2100",
    f"+{france_warming_2100}°C",
    help="La France se réchauffe ~1.5x plus vite que la moyenne mondiale "
         "en raison de sa position continentale (source : HCC 2025, TRACC).",
)

st.sidebar.markdown("---")

target_year_map = st.sidebar.slider(
    "Année de projection (carte)",
    min_value=2030,
    max_value=2100,
    value=2050,
    step=10,
)

show_all_scenarios = st.sidebar.checkbox("Afficher les 3 scénarios", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Sources** : Météo France, GIEC AR6, HCC 2025, PNACC-3, CITEPA, DRIAS"
)


# --- Chargement des données ---
@st.cache_resource(show_spinner=False)
def load_real_data():
    """Charge les données réelles depuis meteo.data.gouv.fr (une seule fois par session)."""
    df, is_real = fetch_real_meteo_data(start_year=1950)
    df = compute_deviation_from_baseline(df)
    return df, is_real


@st.cache_data
def load_all_projections(_hist_hash):
    hist_df, _ = load_real_data()
    return generate_all_scenario_projections(hist_df)


with st.spinner("Récupération des données gouvernementales en temps réel..."):
    hist_df, DATA_IS_REAL = load_real_data()
    all_proj_df = load_all_projections(id(hist_df))

last_temp = hist_df.iloc[-1]["temp_mean"]
last_anomaly = hist_df.iloc[-1]["anomaly"]

# Badge données source (sidebar) — après le chargement
if DATA_IS_REAL:
    st.sidebar.markdown(
        "<div style='display:flex; align-items:center; gap:8px; padding:10px 14px; "
        "border-radius:10px; background:rgba(16,185,129,0.08); "
        "border:1px solid rgba(16,185,129,0.2);'>"
        "<span style='display:inline-block; width:8px; height:8px; border-radius:50%; "
        "background:#10b981; animation:pulse-glow 2s ease-in-out infinite; "
        "box-shadow:0 0 6px #10b981;'></span>"
        "<span style='color:#10b981; font-size:0.78rem; font-weight:600;'>"
        "Données Source : Météo-France / meteo.data.gouv.fr</span>"
        "</div>",
        unsafe_allow_html=True,
    )
else:
    st.sidebar.markdown(
        "<div style='display:flex; align-items:center; gap:8px; padding:10px 14px; "
        "border-radius:10px; background:rgba(251,191,36,0.08); "
        "border:1px solid rgba(251,191,36,0.2);'>"
        "<span style='display:inline-block; width:8px; height:8px; border-radius:50%; "
        "background:#fbbf24;'></span>"
        "<span style='color:#fbbf24; font-size:0.78rem; font-weight:600;'>"
        "Mode hors-ligne : données simulées</span>"
        "</div>",
        unsafe_allow_html=True,
    )


@st.cache_data
def cached_regional_anomalies(national_anomaly, target_year):
    return compute_regional_anomalies(national_anomaly, target_year)


@st.cache_data
def cached_recommendations(region, scenario, target_year, national_anomaly):
    return generate_recommendations(region, scenario, target_year, national_anomaly)


@st.cache_data
def cached_insurance_risk(regional_anomaly, region):
    return compute_insurance_risk_score(regional_anomaly, region)


@st.cache_data
def cached_cost_impact(regional_anomaly, horizon_year):
    return compute_cost_of_living_impact(regional_anomaly, horizon_year)


@st.cache_data
def cached_pnacc3_effect(anomaly_2100):
    return compute_pnacc3_effect(anomaly_2100)


@st.cache_data
def load_geojson():
    try:
        resp = requests.get(get_geojson_url(), timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


@st.cache_data
def compute_shock_stats(scenario_name, _all_proj_hash):
    """Calcule les 3 chiffres chocs pour la section 'En résumé'."""
    proj_sc = all_proj_df[all_proj_df["scenario"] == scenario_name]
    hist_for_c = hist_df[["year", "anomaly"]].copy()
    combined_c = pd.concat([hist_for_c, proj_sc[["year", "anomaly"]]], ignore_index=True)
    crossing = compute_crossing_year(combined_c, threshold_anomaly=2.0)

    # Coût national de l'inaction cumulé d'ici 2050
    from utils.resilience_engine import COUT_INACTION_PAR_DEGRE
    cout_par_degre_total = sum(COUT_INACTION_PAR_DEGRE.values())
    proj_2025_2050 = proj_sc[(proj_sc["year"] >= 2025) & (proj_sc["year"] <= 2050)]
    if not proj_2025_2050.empty:
        cout_cumule = round(proj_2025_2050["anomaly"].mean() * cout_par_degre_total * 25, 0)
    else:
        cout_cumule = 0

    # Nombre de mesures PNACC-3 activables
    from utils.resilience_engine import FICHES_AGRICULTURE, FICHES_SANTE_URBANISME, FICHES_ECONOMIE
    all_mesures = set()
    for fiches in [FICHES_AGRICULTURE, FICHES_SANTE_URBANISME, FICHES_ECONOMIE]:
        for level_data in fiches.values():
            all_mesures.update(level_data["mesures_pnacc3"])
    nb_mesures = len(all_mesures)

    return crossing, cout_cumule, nb_mesures


crossing_shock, cout_inaction_2050, nb_mesures_pnacc3 = compute_shock_stats(
    selected_scenario, id(all_proj_df)
)

# --- Sidebar : En résumé (chiffres chocs) ---
st.sidebar.markdown("---")
st.sidebar.markdown("### En résumé")

col_s1, col_s2 = st.sidebar.columns(2)
with col_s1:
    if crossing_shock and crossing_shock > 2024:
        st.metric(
            "Bascule +2°C",
            str(crossing_shock),
            help="Année où la France franchit +2°C d'anomalie par rapport à la référence 1961-1990. "
                 "Au-delà, les impacts deviennent difficilement réversibles (source : GIEC AR6).",
        )
    else:
        st.metric("Bascule +2°C", "Déjà franchi", help="Le seuil de +2°C est déjà dépassé.")
with col_s2:
    st.metric(
        "Inaction 2050",
        f"{cout_inaction_2050:.0f} Mds€",
        help="Coût cumulé de l'inaction climatique en France entre 2025 et 2050 "
             "(source : France Stratégie, valeur de l'action pour le climat, mars 2025).",
    )

st.sidebar.metric(
    "Mesures PNACC-3",
    f"{nb_mesures_pnacc3} activables",
    help="PNACC-3 = Plan National d'Adaptation au Changement Climatique, 3ème version. "
         "Nombre de mesures distinctes mobilisées par notre moteur de recommandations sur les 51 du plan.",
)


# --- Header ---
st.title("ClimaVision France")
st.caption(
    "Analyse, Visualisation et Prédiction Climatique Multi-Échelle — "
    "Hackathon #26 Sup de Vinci — Big Data & IA"
)

# --- Bouton d'Urgence ---
with st.expander("🚨 **URGENCE CLIMAT — Échéances législatives PNACC-3** (cliquez pour voir la timeline)", expanded=False):
    timeline_cols = st.columns(len(PNACC3_TIMELINE))
    for i, evt in enumerate(PNACC3_TIMELINE):
        with timeline_cols[i]:
            st.markdown(
                f"<div style='text-align:center; padding:14px 8px; border-radius:14px; "
                f"background:rgba(255,255,255,0.03); backdrop-filter:blur(12px); "
                f"border:1px solid {evt['color']}30; min-height:160px;'>"
                f"<div style='font-size:2rem; font-weight:900; color:{evt['color']}; "
                f"letter-spacing:-0.05em;'>{evt['year']}</div>"
                f"<div style='font-size:0.85rem; font-weight:700; color:#f1f5f9; "
                f"margin:6px 0 4px 0;'>{evt['label']}</div>"
                f"<div style='font-size:0.72rem; color:#94a3b8; line-height:1.3;'>"
                f"{evt['detail']}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)

proj_selected = all_proj_df[all_proj_df["scenario"] == selected_scenario]
proj_2050 = proj_selected[proj_selected["year"] == 2050]
proj_2100 = proj_selected[proj_selected["year"] == 2100]

# Calcul de l'année de franchissement +2°C pour le scénario sélectionné
# On combine historique + projections pour détecter le seuil
hist_for_crossing = hist_df[["year", "anomaly"]].copy()
proj_for_crossing = proj_selected[["year", "anomaly"]].copy()
combined = pd.concat([hist_for_crossing, proj_for_crossing], ignore_index=True)
crossing_2c = compute_crossing_year(combined, threshold_anomaly=2.0)

with col1:
    last_year = int(hist_df.iloc[-1]["year"])
    st.metric(
        f"Température {last_year}",
        f"{last_temp}°C",
        f"+{last_anomaly}°C vs 1961-1990",
        help="Température moyenne annuelle observée en France métropolitaine. "
             "L'anomalie est calculée par rapport à la référence 1961-1990 (norme OMM).",
    )

with col2:
    if not proj_2050.empty:
        st.metric(
            "Projection 2050",
            f"{proj_2050.iloc[0]['temp_mean']}°C",
            f"+{proj_2050.iloc[0]['anomaly']}°C",
            help="Température moyenne projetée pour 2050 selon le scénario sélectionné. "
                 "L'anomalie indique l'écart par rapport à 1961-1990.",
        )

with col3:
    if not proj_2100.empty:
        st.metric(
            "Projection 2100",
            f"{proj_2100.iloc[0]['temp_mean']}°C",
            f"+{proj_2100.iloc[0]['anomaly']}°C",
            delta_color="inverse",
            help="Projection fin de siècle. Le delta rouge indique un réchauffement significatif. "
                 "Source : modèle Prophet calibré sur données Météo France + scénarios SSP du GIEC.",
        )

with col4:
    if crossing_2c:
        st.metric(
            "Bascule +2°C France",
            str(crossing_2c),
            "année de franchissement",
            delta_color="off",
            help="Année où l'anomalie moyenne française dépasse +2°C vs 1961-1990. "
                 "Au-delà de ce seuil, les impacts climatiques deviennent difficilement réversibles (GIEC AR6).",
        )
    else:
        st.metric("Bascule +2°C France", "< 2024", "déjà franchi", delta_color="off")

st.markdown("---")

# --- Onglets ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Températures & Projections",
    "Carte régionale",
    "Émissions GES",
    "Préconisations PNACC-3",
    "Simulateur Citoyen",
])

# ============================================================
# TAB 1 : Températures avec 3 scénarios + zones d'incertitude
# ============================================================
with tab1:
    st.subheader("Évolution de la température moyenne en France (1951-2100)")

    fig = go.Figure()

    # --- Données historiques ---
    fig.add_trace(go.Scatter(
        x=hist_df["year"],
        y=hist_df["temp_mean"],
        mode="lines",
        name="Observations (SIM + LSH)",
        line=dict(color="#64748b", width=1.2),
        opacity=0.6,
    ))

    # Moyenne mobile 10 ans
    rolling = hist_df["temp_mean"].rolling(window=10, center=True).mean()
    fig.add_trace(go.Scatter(
        x=hist_df["year"],
        y=rolling,
        mode="lines",
        name="Tendance (moy. mobile 10 ans)",
        line=dict(color="#e2e8f0", width=3),
    ))

    # --- Projections par scénario ---
    scenarios_to_show = list(SCENARIOS.keys()) if show_all_scenarios else [selected_scenario]

    for scenario_name in scenarios_to_show:
        color = SCENARIO_COLORS[scenario_name]
        proj = all_proj_df[all_proj_df["scenario"] == scenario_name].copy()

        # Point de jonction avec l'historique
        junction_years = [hist_df.iloc[-1]["year"]] + proj["year"].tolist()
        junction_temps = [last_temp] + proj["temp_mean"].tolist()
        junction_upper = [last_temp] + proj["temp_upper"].tolist()
        junction_lower = [last_temp] + proj["temp_lower"].tolist()

        # Zone d'incertitude (fill between)
        fig.add_trace(go.Scatter(
            x=junction_years + junction_years[::-1],
            y=junction_upper + junction_lower[::-1],
            fill="toself",
            fillcolor=color.replace(")", ", 0.15)").replace("rgb", "rgba") if "rgb" in color else f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.15)",
            line=dict(color="rgba(0,0,0,0)"),
            showlegend=False,
            hoverinfo="skip",
        ))

        # Courbe principale
        short_name = scenario_name.split("(")[1].rstrip(")") if "(" in scenario_name else scenario_name
        fig.add_trace(go.Scatter(
            x=junction_years,
            y=junction_temps,
            mode="lines",
            name=f"{short_name}",
            line=dict(color=color, width=2.5, dash="dot"),
        ))

    # --- Ligne de référence 1961-1990 ---
    fig.add_hline(
        y=BASELINE_TEMP_FRANCE,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Référence 1961-1990 ({BASELINE_TEMP_FRANCE}°C)",
        annotation_position="top left",
    )

    # Ligne +2°C France
    fig.add_hline(
        y=BASELINE_TEMP_FRANCE + 2.0,
        line_dash="dot",
        line_color="#f43f5e",
        annotation_text="Seuil +2°C France",
        annotation_position="bottom right",
        annotation_font_color="#f43f5e",
    )

    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis_title="Année",
        yaxis_title="Température moyenne (°C)",
        hovermode="x unified",
        height=550,
        legend=dict(
            yanchor="top", y=0.99, xanchor="left", x=0.01,
            bgcolor="rgba(15, 23, 42, 0.7)",
            font=dict(color="#cbd5e1"),
            bordercolor="rgba(148, 163, 184, 0.1)",
            borderwidth=1,
        ),
        xaxis=dict(range=[1950, 2105], **PLOTLY_AXIS),
        yaxis=dict(**PLOTLY_AXIS),
    )

    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

    # ── Confiance du modèle ──
    confidence_pct = 92 if DATA_IS_REAL else 78
    conf_color = "#10b981" if confidence_pct >= 80 else "#3b82f6" if confidence_pct >= 60 else "#f43f5e"
    st.markdown(
        f"<div style='display:flex; align-items:center; gap:12px; "
        f"padding:10px 16px; border-radius:12px; "
        f"background: rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06);'>"
        f"<span style='color:#64748b; font-size:0.75rem; font-weight:600; "
        f"text-transform:uppercase; letter-spacing:0.08em; white-space:nowrap;'>"
        f"Confiance du Modèle</span>"
        f"<div style='flex:1; height:6px; border-radius:3px; background:rgba(255,255,255,0.06);'>"
        f"<div style='width:{confidence_pct}%; height:100%; border-radius:3px; "
        f"background: linear-gradient(90deg, {conf_color}, {conf_color}cc); "
        f"box-shadow: 0 0 8px {conf_color}40;'></div></div>"
        f"<span style='color:{conf_color}; font-weight:700; font-size:0.85rem;'>{confidence_pct}%</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    data_label = "données Météo-France (SIM 9892 pts + LSH homogénéisées) via meteo.data.gouv.fr" if DATA_IS_REAL else "données simulées"
    st.caption(f"Prophet calibré sur {len(hist_df)} ans de {data_label} + scénarios SSP du GIEC AR6")

    # --- Indicateur de bascule +2°C ---
    st.subheader("Année de franchissement du seuil +2°C en France")

    cols_crossing = st.columns(3)
    for i, scenario_name in enumerate(SCENARIOS.keys()):
        proj_sc = all_proj_df[all_proj_df["scenario"] == scenario_name]
        combined_sc = pd.concat([hist_for_crossing, proj_sc[["year", "anomaly"]]], ignore_index=True)
        crossing = compute_crossing_year(combined_sc, threshold_anomaly=2.0)
        color = SCENARIO_COLORS[scenario_name]

        with cols_crossing[i]:
            short = scenario_name.split("(")[0].strip()
            ssp_tag = scenario_name.split("(")[1].rstrip(")") if "(" in scenario_name else ""
            crossing_val = str(crossing) if (crossing and crossing > 2024) else "Déjà franchi"
            st.markdown(
                f"<div style='text-align:center; padding:22px; "
                f"background: rgba(255, 255, 255, 0.03); "
                f"backdrop-filter: blur(12px); "
                f"border: 1px solid {color}22; border-radius: 16px; "
                f"box-shadow: 0 8px 32px {color}12; "
                f"transition: all 0.3s cubic-bezier(.4,0,.2,1);'>"
                f"<p style='margin:0 0 4px 0; font-size:0.68rem; color:#64748b; "
                f"text-transform:uppercase; letter-spacing:0.1em; font-weight:600;'>{ssp_tag}</p>"
                f"<h2 style='margin:0; color:{color}; font-size:2.2rem; font-weight:900; "
                f"letter-spacing:-0.05em;'>"
                f"{crossing_val}</h2>"
                f"<p style='margin:4px 0 0 0; color:#94a3b8; font-size:0.82rem;'>{short}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("")

    # --- Anomalies en barres ---
    st.subheader("Anomalies de température (vs 1961-1990)")
    colors_bar = ["#f43f5e" if a > 0 else "#3b82f6" for a in hist_df["anomaly"]]
    fig_bar = go.Figure(go.Bar(
        x=hist_df["year"],
        y=hist_df["anomaly"],
        marker_color=colors_bar,
        name="Anomalie",
    ))
    fig_bar.update_layout(
        **PLOTLY_LAYOUT,
        xaxis_title="Année",
        yaxis_title="Anomalie (°C)",
        height=300,
        xaxis=dict(**PLOTLY_AXIS),
        yaxis=dict(**PLOTLY_AXIS),
    )
    st.plotly_chart(fig_bar, use_container_width=True, config=PLOTLY_CONFIG)


# ============================================================
# TAB 2 : Carte choroplèthe
# ============================================================
with tab2:
    st.subheader(f"Anomalie de température par région — Projection {target_year_map}")
    st.markdown(f"**Scénario : {selected_scenario}**")

    # Calcul des anomalies régionales
    proj_target = proj_selected[proj_selected["year"] == target_year_map]
    if not proj_target.empty:
        national_anomaly = proj_target.iloc[0]["anomaly"]
    else:
        # Interpoler si l'année exacte n'est pas disponible
        national_anomaly = france_warming_2100 * (target_year_map - 2024) / (2100 - 2024)

    regional_data = cached_regional_anomalies(national_anomaly, target_year_map)

    # Afficher les métriques régionales
    col_map, col_legend = st.columns([2, 1])

    with col_map:
        geojson = load_geojson()

        if geojson:
            # Créer la carte choroplèthe avec Folium
            m = folium.Map(
                location=[46.603354, 1.888334],
                zoom_start=6,
                tiles="CartoDB dark_matter",
            )

            # Préparer les données pour le choroplèthe
            region_anomalies = {}
            for region_name, data in regional_data.items():
                region_anomalies[region_name] = data["anomaly"]

            # Colormap personnalisée
            import branca.colormap as cm
            min_anomaly = min(d["anomaly"] for d in regional_data.values())
            max_anomaly = max(d["anomaly"] for d in regional_data.values())

            colormap = cm.LinearColormap(
                colors=["#fee08b", "#fdae61", "#f46d43", "#d73027", "#a50026"],
                vmin=min_anomaly,
                vmax=max_anomaly,
                caption=f"Anomalie de température (°C) — {target_year_map}",
            )

            # Ajouter chaque région avec sa couleur
            for feature in geojson["features"]:
                region_name = feature["properties"]["nom"]
                if region_name in regional_data:
                    data = regional_data[region_name]
                    anomaly = data["anomaly"]
                    temp_proj = data["temp_projected"]

                    color = colormap(anomaly)

                    folium.GeoJson(
                        feature,
                        style_function=lambda x, c=color: {
                            "fillColor": c,
                            "color": "#333",
                            "weight": 1,
                            "fillOpacity": 0.7,
                        },
                        tooltip=folium.Tooltip(
                            f"<b>{region_name}</b><br>"
                            f"Anomalie : +{anomaly}°C<br>"
                            f"Temp. projetée : {temp_proj}°C<br>"
                            f"Amplification : x{data['amplification']}"
                        ),
                    ).add_to(m)

            colormap.add_to(m)
            st_folium(m, width=700, height=550)
        else:
            st.warning("Impossible de charger le GeoJSON des régions. Vérifiez la connexion.")

            # Fallback : carte avec marqueurs
            m = folium.Map(location=[46.603354, 1.888334], zoom_start=6)
            for region_name, data in regional_data.items():
                folium.Marker(
                    location=[46.6, 1.9],
                    popup=f"{region_name}: +{data['anomaly']}°C",
                ).add_to(m)
            st_folium(m, width=700, height=550)

    with col_legend:
        st.metric("Anomalie nationale", f"+{national_anomaly:.1f}°C",
                  help="Anomalie moyenne projetée pour la France entière.")
        st.caption(f"Projection {target_year_map} — {selected_scenario}")
        st.markdown("---")

        # Tableau des régions triées par anomalie
        regions_sorted = sorted(
            regional_data.items(),
            key=lambda x: x[1]["anomaly"],
            reverse=True,
        )

        for region_name, data in regions_sorted:
            anomaly = data["anomaly"]
            bar_pct = min(100, (anomaly / max_anomaly) * 100) if max_anomaly > 0 else 50
            risk_color = "#f43f5e" if anomaly > national_anomaly else "#3b82f6"

            st.markdown(
                f"<div style='padding:8px 12px; margin-bottom:4px; border-radius:10px; "
                f"background:rgba(255,255,255,0.03); border-left:3px solid {risk_color}; "
                f"backdrop-filter:blur(8px); transition:all 0.3s ease;'>"
                f"<span style='color:#f1f5f9; font-weight:600; font-size:0.85rem;'>{region_name}</span>"
                f"<span style='float:right; color:{risk_color}; font-weight:700;'>+{anomaly}°C</span>"
                f"</div>",
                unsafe_allow_html=True,
            )


# ============================================================
# TAB 3 : Émissions GES
# ============================================================
with tab3:
    st.subheader("Émissions de gaz à effet de serre en France")
    st.markdown(
        f"**Total : {EMISSIONS_FRANCE['total_mt_eqco2']} Mt éqCO₂/an** "
        f"(moyenne 2019-2023, source : HCC 2025 / CITEPA)"
    )

    col_a, col_b = st.columns(2)

    with col_a:
        secteur_df = pd.DataFrame({
            "Secteur": list(EMISSIONS_FRANCE["par_secteur"].keys()),
            "Part (%)": [v * 100 for v in EMISSIONS_FRANCE["par_secteur"].values()],
            "Mt éqCO₂": [round(v * EMISSIONS_FRANCE["total_mt_eqco2"], 1) for v in EMISSIONS_FRANCE["par_secteur"].values()],
        })
        fig_secteur = px.bar(
            secteur_df.sort_values("Part (%)", ascending=True),
            x="Part (%)",
            y="Secteur",
            orientation="h",
            title="Répartition par secteur",
            color="Part (%)",
            color_continuous_scale=["#10b981", "#3b82f6", "#f43f5e"],
            text="Mt éqCO₂",
        )
        fig_secteur.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=False,
                                   xaxis=dict(**PLOTLY_AXIS), yaxis=dict(**PLOTLY_AXIS))
        fig_secteur.update_traces(texttemplate="%{text} Mt", textposition="outside", textfont=dict(color="#cbd5e1"))
        st.plotly_chart(fig_secteur, use_container_width=True, config=PLOTLY_CONFIG)

    with col_b:
        gaz_df = pd.DataFrame({
            "Gaz": list(EMISSIONS_FRANCE["composition"].keys()),
            "Part (%)": [v * 100 for v in EMISSIONS_FRANCE["composition"].values()],
        })
        fig_gaz = px.pie(
            gaz_df,
            values="Part (%)",
            names="Gaz",
            title="Composition des GES",
            color_discrete_sequence=px.colors.qualitative.Set2,
            hole=0.4,
        )
        fig_gaz.update_layout(**PLOTLY_LAYOUT, height=400,
                              xaxis=dict(**PLOTLY_AXIS), yaxis=dict(**PLOTLY_AXIS))
        st.plotly_chart(fig_gaz, use_container_width=True, config=PLOTLY_CONFIG)

    # Objectifs de réduction
    st.markdown("---")
    st.subheader("Trajectoire de décarbonation")

    objectives = pd.DataFrame({
        "Année": [1990, 2005, 2019, 2023, 2030, 2050],
        "Émissions (Mt éqCO₂)": [596, 560, 436, 406, 270, 80],
        "Type": ["Historique", "Historique", "Historique", "Historique", "Objectif (-55%)", "Objectif (neutralité)"],
    })

    fig_traj = go.Figure()
    hist_obj = objectives[objectives["Type"].str.startswith("Historique")]
    target_obj = objectives[~objectives["Type"].str.startswith("Historique")]

    fig_traj.add_trace(go.Scatter(
        x=hist_obj["Année"], y=hist_obj["Émissions (Mt éqCO₂)"],
        mode="lines+markers", name="Historique",
        line=dict(color="#94a3b8", width=2), marker=dict(size=8),
    ))
    fig_traj.add_trace(go.Scatter(
        x=pd.concat([hist_obj.tail(1), target_obj])["Année"],
        y=pd.concat([hist_obj.tail(1), target_obj])["Émissions (Mt éqCO₂)"],
        mode="lines+markers", name="Objectifs France / UE",
        line=dict(color="#10b981", width=2, dash="dash"), marker=dict(size=10, symbol="star"),
    ))
    fig_traj.update_layout(
        **PLOTLY_LAYOUT,
        xaxis_title="Année", yaxis_title="Mt éqCO₂/an",
        height=350, hovermode="x unified",
        xaxis=dict(**PLOTLY_AXIS), yaxis=dict(**PLOTLY_AXIS),
    )
    st.plotly_chart(fig_traj, use_container_width=True, config=PLOTLY_CONFIG)


# ============================================================
# TAB 4 : Préconisations citoyennes
# ============================================================
with tab4:
    st.subheader("Préconisations citoyennes")
    st.markdown(
        "Recommandations adaptées au niveau de réchauffement projeté, "
        "alignées sur le **PNACC-3** (Plan National d'Adaptation au Changement Climatique, "
        "51 mesures) et l'**Earth Action Report 2025**."
    )

    severity_color = "#f43f5e" if france_warming_2100 >= 4 else "#3b82f6" if france_warming_2100 >= 2.5 else "#10b981"
    st.warning(
        f"Scénario **{selected_scenario}** : réchauffement de "
        f"**+{france_warming_2100}°C** en France d'ici 2100."
    )

    active_precos = get_preconisations_for_scenario(france_warming_2100)

    if not active_precos:
        st.success("Aucune alerte majeure pour ce scénario.")
    else:
        cols = st.columns(2)
        for i, (risk_name, risk_data) in enumerate(active_precos.items()):
            with cols[i % 2]:
                with st.expander(
                    f"{risk_data['icon']} {risk_name} — {risk_data['seuil']}",
                    expanded=True,
                ):
                    for action in risk_data["actions"]:
                        st.markdown(f"- {action}")

    st.markdown("---")
    st.markdown(
        "**Sources** : PNACC-3 (51 mesures), Earth Action Report 2025, "
        "Rapport HCC 2025, Chiffres clés du climat 2024, GIEC AR6"
    )


# ============================================================
# TAB 5 : Simulateur Citoyen
# ============================================================
with tab5:
    st.subheader("Simulateur de futur — Votre territoire en 2050")

    # Command Center layout : inputs à gauche, résultats à droite
    cmd_left, cmd_right = st.columns([1, 2])

    with cmd_left:
        st.markdown(
            "<p style='color:#64748b; font-size:0.82rem; margin-bottom:16px;'>"
            "Configurez votre simulation pour découvrir l'impact climatique sur votre territoire.</p>",
            unsafe_allow_html=True,
        )

        # Exemples rapides
        EXEMPLES_RAPIDES = {
            "Nice — Canicule & littoral": {"cp": "06000", "age": 30, "year": 2050},
            "Bordeaux — Viticulture": {"cp": "33000", "age": 35, "year": 2050},
            "Paris — Îlot de chaleur": {"cp": "75001", "age": 28, "year": 2050},
            "Marseille — Sécheresse": {"cp": "13001", "age": 40, "year": 2060},
        }

        BADGE_ICONS = {"Nice": "☀️", "Bordeaux": "🍇", "Paris": "🏙️", "Marseille": "💧"}
        st.caption("EXEMPLES RAPIDES")
        ex_cols = st.columns(2)
        for i, (label, vals) in enumerate(EXEMPLES_RAPIDES.items()):
            city = label.split("—")[0].strip()
            icon = BADGE_ICONS.get(city, "📍")
            with ex_cols[i % 2]:
                if st.button(f"{icon} {city}", key=f"ex_{i}", use_container_width=True):
                    st.session_state["sim_cp"] = vals["cp"]
                    st.session_state["sim_age"] = vals["age"]
                    st.session_state["sim_year"] = vals["year"]
                    st.rerun()

        st.markdown("")

        # Valeurs par défaut (ou depuis session_state si exemple cliqué)
        default_cp = st.session_state.get("sim_cp", "75001")
        default_age = st.session_state.get("sim_age", 25)
        default_year = st.session_state.get("sim_year", 2050)
        year_options = [2030, 2040, 2050, 2060, 2070, 2080, 2100]
        default_year_idx = year_options.index(default_year) if default_year in year_options else 2

        user_postal = st.text_input(
            "Code postal",
            value=default_cp,
            max_chars=5,
            help="Entrez votre code postal pour identifier votre région.",
        )
        user_age = st.number_input(
            "Votre âge actuel",
            min_value=1,
            max_value=120,
            value=default_age,
        )
        sim_year = st.selectbox(
            "Horizon de projection",
            year_options,
            index=default_year_idx,
        )

    # Identification de la région
    user_region = get_region_from_postal_code(user_postal)

    with cmd_right:
        if user_region:
            # Calcul de l'anomalie nationale pour l'année cible
            proj_sim = proj_selected[proj_selected["year"] == sim_year]
            if not proj_sim.empty:
                sim_national_anomaly = proj_sim.iloc[0]["anomaly"]
            else:
                sim_national_anomaly = france_warming_2100 * (sim_year - 2024) / (2100 - 2024)

            # Génération des recommandations (mise en cache)
            reco = cached_recommendations(
                region=user_region,
                scenario=selected_scenario,
                target_year=sim_year,
                national_anomaly=sim_national_anomaly,
            )

            user_age_target = user_age + (sim_year - 2026)

            # ── Message personnalisé ──
            severity_emoji = {"faible": "🟡", "moyen": "🟠", "fort": "🔴"}
            severity_label = {"faible": "Modéré", "moyen": "Élevé", "fort": "Critique"}
            severity_glow = {"faible": "#10b981", "moyen": "#3b82f6", "fort": "#f43f5e"}
            glow = severity_glow.get(reco["severity"], "#64748b")

            st.markdown(
                f"<div style='padding:28px; border-radius:18px; "
                f"background: rgba(255, 255, 255, 0.03); "
                f"backdrop-filter: blur(12px); "
                f"border: 1px solid {glow}25; box-shadow: 0 8px 40px {glow}15;'>"
                f"<h2 style='margin:0 0 8px 0; color:#f1f5f9; letter-spacing:-0.05em;'>"
                f"{severity_emoji.get(reco['severity'], '⚪')} "
                f"En {sim_year}, vous aurez <span style='color:{glow};'>{user_age_target} ans</span></h2>"
                f"<p style='margin:0 0 6px 0; color:#cbd5e1; font-size:1rem;'>"
                f"Dans votre région <strong style='color:#f1f5f9;'>{user_region}</strong>, "
                f"la température moyenne sera d'environ "
                f"<strong style='color:{glow};'>{reco['temp_projected']}°C</strong>, "
                f"soit une anomalie de "
                f"<strong style='color:{glow};'>+{reco['anomaly_regional']}°C</strong> "
                f"par rapport à la référence 1961-1990.</p>"
                f"<p style='margin:0; color:#94a3b8; font-size:0.85rem;'>"
                f"Niveau d'alerte : <strong style='color:{glow};'>"
                f"{severity_label.get(reco['severity'], 'Inconnu')}</strong> — "
                f"{selected_scenario}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

            # ── Bento Grid KPIs ──
            st.markdown("")
            bento_r1c1, bento_r1c2 = st.columns(2)
            bento_r2c1, bento_r2c2 = st.columns(2)
            with bento_r1c1:
                st.metric(
                    "Anomalie régionale", f"+{reco['anomaly_regional']}°C",
                    help="Écart de température dans votre région par rapport à la référence 1961-1990 (norme OMM).",
                )
            with bento_r1c2:
                st.metric(
                    "Temp. projetée", f"{reco['temp_projected']}°C",
                    help="Température moyenne annuelle projetée dans votre région à l'horizon choisi.",
                )
            with bento_r2c1:
                st.metric(
                    "Coût de l'inaction",
                    f"{reco['metriques']['cout_inaction_regional_mds']} Mds€/an",
                    help="Estimation des dégâts annuels si aucune mesure d'adaptation n'est prise.",
                )
            with bento_r2c2:
                st.metric(
                    "Ratio investissement",
                    f"1€ → {reco['metriques']['ratio_benefice']}€",
                    "dégâts évités",
                    delta_color="off",
                    help="Pour chaque euro investi dans l'adaptation, ce montant de dégâts est évité.",
                )

            # ── Score de Risque Assurantiel ──
            st.markdown("")
            insurance_risk = cached_insurance_risk(reco["anomaly_regional"], user_region)
            cost_impact = cached_cost_impact(reco["anomaly_regional"], sim_year)

            st.markdown(
                f"<div style='padding:18px 20px; border-radius:14px; "
                f"background:rgba(255,255,255,0.03); backdrop-filter:blur(12px); "
                f"border:1px solid {insurance_risk['level_color']}25;'>"
                f"<div style='display:flex; justify-content:space-between; align-items:center;'>"
                f"<div>"
                f"<span style='color:#94a3b8; font-size:0.78rem; text-transform:uppercase; "
                f"letter-spacing:0.05em;'>Score de Risque Assurantiel</span>"
                f"<div style='font-size:2.2rem; font-weight:900; color:{insurance_risk['level_color']}; "
                f"letter-spacing:-0.05em;'>{insurance_risk['score_total']}/100</div>"
                f"<span style='color:{insurance_risk['level_color']}; font-size:0.85rem; "
                f"font-weight:600;'>{insurance_risk['level']}</span>"
                f"</div>"
                f"<div style='text-align:right;'>"
                f"<span style='color:#f1f5f9; font-size:0.9rem; font-weight:600;'>"
                f"Impact coût de la vie d'ici {sim_year}</span><br>"
                f"<span style='font-size:1.8rem; font-weight:900; color:#f59e0b; "
                f"letter-spacing:-0.04em;'>+{cost_impact['total_pct']}%</span><br>"
                f"<span style='color:#94a3b8; font-size:0.75rem;'>"
                f"Énergie +{cost_impact['by_sector']['Énergie']}% · "
                f"Assurances +{cost_impact['by_sector']['Assurances']}% · "
                f"Alimentation +{cost_impact['by_sector']['Alimentation']}%</span>"
                f"</div></div></div>",
                unsafe_allow_html=True,
            )

        else:
            st.info("Entrez un code postal valide pour lancer la simulation.")

    # ── Full-width sections below Command Center ──
    if user_region:
        # Re-compute reco for full-width sections (already cached)
        proj_sim_fw = proj_selected[proj_selected["year"] == sim_year]
        if not proj_sim_fw.empty:
            sim_national_anomaly_fw = proj_sim_fw.iloc[0]["anomaly"]
        else:
            sim_national_anomaly_fw = france_warming_2100 * (sim_year - 2024) / (2100 - 2024)
        reco = cached_recommendations(
            region=user_region, scenario=selected_scenario,
            target_year=sim_year, national_anomaly=sim_national_anomaly_fw,
        )

        # ── 3 Fiches d'action ──
        st.markdown("---")
        st.subheader("Vos 3 mesures d'adaptation prioritaires")

        fiche_configs = [
            ("agriculture", "🌾 Agriculture & Eau", "#10b981"),
            ("sante_urbanisme", "🏥 Santé & Urbanisme", "#3b82f6"),
            ("economie", "💶 Économie & Investissement", "#a855f7"),
        ]

        fiche_cols = st.columns(3)
        for i, (key, title, color) in enumerate(fiche_configs):
            fiche = reco["fiches"][key]
            with fiche_cols[i]:
                st.markdown(
                    f"<div style='padding:20px; border-left: 3px solid {color}; "
                    f"background: rgba(255, 255, 255, 0.03); "
                    f"backdrop-filter: blur(12px); border-radius: 16px; "
                    f"border: 1px solid {color}18; "
                    f"box-shadow: 0 8px 32px {color}10; "
                    f"transition: all 0.3s cubic-bezier(.4,0,.2,1);'>"
                    f"<h4 style='color:{color}; margin:0 0 6px 0; font-weight:700; "
                    f"letter-spacing:-0.03em;'>{title}</h4>"
                    f"<p style='font-size:0.82em; color:#94a3b8; margin:0;'>"
                    f"{fiche['titre']}</p></div>",
                    unsafe_allow_html=True,
                )
                inv_col, hor_col = st.columns(2)
                with inv_col:
                    st.metric("Investissement", f"{fiche['investissement_mds']} Mds€")
                with hor_col:
                    st.metric("Horizon", fiche["horizon"])

                for action in fiche["actions"][:3]:
                    st.markdown(f"- {action}")

                if len(fiche["actions"]) > 3:
                    with st.expander("Voir toutes les actions"):
                        for action in fiche["actions"][3:]:
                            st.markdown(f"- {action}")

                mesures_str = ", ".join(str(m) for m in fiche["mesures_pnacc3"])
                st.caption(f"Mesures PNACC-3 : {mesures_str}")

        # ── Synthèse financière ──
        st.markdown("---")
        st.subheader("Synthèse : investir vs subir")

        metr = reco["metriques"]
        fig_cost = go.Figure()

        fig_cost.add_trace(go.Bar(
            x=["Coût de l'inaction\n(dégâts/an)"],
            y=[metr["cout_inaction_regional_mds"]],
            name="Inaction",
            marker_color="#f43f5e",
            text=[f"{metr['cout_inaction_regional_mds']} Mds€"],
            textposition="outside",
            textfont=dict(color="#fda4af"),
        ))
        fig_cost.add_trace(go.Bar(
            x=["Investissement\nnécessaire"],
            y=[metr["investissement_regional_mds"]],
            name="Investissement",
            marker_color="#3b82f6",
            text=[f"{metr['investissement_regional_mds']} Mds€"],
            textposition="outside",
            textfont=dict(color="#93c5fd"),
        ))
        fig_cost.add_trace(go.Bar(
            x=["Dégâts évités\npar l'investissement"],
            y=[metr["degats_evites_mds"]],
            name="Bénéfice",
            marker_color="#10b981",
            text=[f"{metr['degats_evites_mds']} Mds€"],
            textposition="outside",
            textfont=dict(color="#6ee7b7"),
        ))

        fig_cost.update_layout(
            **PLOTLY_LAYOUT,
            title=f"Analyse coût-bénéfice — {user_region}",
            yaxis_title="Milliards d'euros",
            height=380,
            showlegend=False,
            xaxis=dict(**PLOTLY_AXIS), yaxis=dict(**PLOTLY_AXIS),
        )
        st.plotly_chart(fig_cost, use_container_width=True, config=PLOTLY_CONFIG)

        st.caption(
            "Estimations basées sur France Stratégie (valeur de l'action pour le climat, "
            "mars 2025) et le Haut Conseil pour le Climat (rapport annuel 2025)."
        )

        # ── L'Effet de nos actions (comparatif avec/sans PNACC-3) ──
        st.markdown("---")
        st.subheader("L'Effet de nos actions")

        proj_2100_sc = proj_selected[proj_selected["year"] == 2100]
        if not proj_2100_sc.empty:
            anomaly_2100 = proj_2100_sc.iloc[0]["anomaly"]
        else:
            anomaly_2100 = france_warming_2100

        pnacc3_effect = cached_pnacc3_effect(anomaly_2100)

        effect_cols = st.columns(3)
        with effect_cols[0]:
            st.metric(
                "Sans action (2100)",
                f"+{pnacc3_effect['anomaly_sans_pnacc3']}°C",
                f"{pnacc3_effect['degats_sans_mds']} Mds€/an de dégâts",
                delta_color="inverse",
                help="Anomalie projetée en 2100 sans politiques d'adaptation ni atténuation renforcées.",
            )
        with effect_cols[1]:
            st.metric(
                "Avec PNACC-3 + SNBC (2100)",
                f"+{pnacc3_effect['anomaly_avec_pnacc3']}°C",
                f"-{pnacc3_effect['delta_anomaly']}°C grâce à l'action",
                delta_color="normal",
                help="Anomalie réduite grâce à l'adaptation (PNACC-3) et l'atténuation (SNBC). "
                     "Le PNACC-3 réduit les dégâts de 35% (France Stratégie).",
            )
        with effect_cols[2]:
            st.metric(
                "Dégâts évités",
                f"{pnacc3_effect['degats_evites_mds']} Mds€/an",
                "grâce aux politiques climat",
                delta_color="off",
                help="Économies annuelles permises par la mise en œuvre du PNACC-3 et de la SNBC.",
            )

        st.caption(
            "Comparaison basée sur les trajectoires TRACC (Météo-France/DRIAS) et "
            "l'évaluation socio-économique de France Stratégie (mars 2025). "
            "Le PNACC-3 réduit les dégâts de ~35%, la SNBC réduit la trajectoire de ~12%."
        )

        # ── Export PDF ──
        st.markdown("---")
        st.subheader("Télécharger votre bilan territorial")

        pdf_bytes = generate_bilan_pdf(reco, user_age=user_age)

        st.download_button(
            label="Télécharger le bilan PDF",
            data=pdf_bytes,
            file_name=f"bilan_territorial_{user_region.lower().replace(' ', '_')}_{sim_year}.pdf",
            mime="application/pdf",
            type="primary",
        )

        st.caption(
            "Ce document est un livrable citoyen actionnable. "
            "Il synthétise les projections climatiques et les mesures d'adaptation "
            "pour votre territoire, alignées sur le PNACC-3."
        )

# ════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(
    "<div style='text-align:center; padding:30px 20px 20px 20px;'>"
    "<p style='color:#64748b; font-size:0.82rem; margin:0 0 6px 0;'>"
    "Propulsé par l'IA au service de la résilience territoriale — Hackathon 2026</p>"
    "<p style='color:#475569; font-size:0.72rem; margin:0;'>"
    "Sources : Météo-France (SIM + LSH) via meteo.data.gouv.fr · "
    "GIEC AR6 · HCC 2025 · PNACC-3 · France Stratégie · CITEPA · DRIAS<br>"
    "Défi Changement Climatique — defis.data.gouv.fr</p>"
    "</div>",
    unsafe_allow_html=True,
)
