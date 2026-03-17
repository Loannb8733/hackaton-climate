"""
Données géographiques pour la carte choroplèthe de France.

Anomalies de température par région, calibrées sur les données du HCC 2025
et DRIAS (projections climatiques régionales).

L'amplification du réchauffement varie selon les régions :
- Régions méditerranéennes : réchauffement plus marqué (+20% vs moyenne)
- Régions atlantiques : réchauffement atténué (-10% vs moyenne)
- Régions continentales : proche de la moyenne
"""

import json

# Facteurs d'amplification régionale du réchauffement
# Source : DRIAS / Météo France (tendances observées et projetées)
REGIONS_AMPLIFICATION = {
    "Île-de-France": 1.05,
    "Centre-Val de Loire": 1.00,
    "Bourgogne-Franche-Comté": 1.05,
    "Normandie": 0.90,
    "Hauts-de-France": 0.92,
    "Grand Est": 1.08,
    "Pays de la Loire": 0.92,
    "Bretagne": 0.85,
    "Nouvelle-Aquitaine": 1.00,
    "Occitanie": 1.15,
    "Auvergne-Rhône-Alpes": 1.10,
    "Provence-Alpes-Côte d'Azur": 1.20,
    "Corse": 1.18,
}

# Températures de base régionales (approx. moyennes annuelles actuelles)
REGIONS_TEMP_BASE = {
    "Île-de-France": 12.5,
    "Centre-Val de Loire": 12.0,
    "Bourgogne-Franche-Comté": 11.5,
    "Normandie": 11.0,
    "Hauts-de-France": 10.8,
    "Grand Est": 10.8,
    "Pays de la Loire": 12.2,
    "Bretagne": 11.8,
    "Nouvelle-Aquitaine": 13.0,
    "Occitanie": 14.0,
    "Auvergne-Rhône-Alpes": 11.5,
    "Provence-Alpes-Côte d'Azur": 14.5,
    "Corse": 15.0,
}

# Codes INSEE des régions (pour le GeoJSON)
REGIONS_CODES = {
    "Île-de-France": "11",
    "Centre-Val de Loire": "24",
    "Bourgogne-Franche-Comté": "27",
    "Normandie": "28",
    "Hauts-de-France": "32",
    "Grand Est": "44",
    "Pays de la Loire": "52",
    "Bretagne": "53",
    "Nouvelle-Aquitaine": "75",
    "Occitanie": "76",
    "Auvergne-Rhône-Alpes": "84",
    "Provence-Alpes-Côte d'Azur": "93",
    "Corse": "94",
}


def compute_regional_anomalies(
    national_anomaly: float,
    target_year: int = 2050,
) -> dict:
    """
    Calcule les anomalies de température par région pour une année cible.

    Args:
        national_anomaly: anomalie nationale moyenne (°C vs préindustriel)
        target_year: année de la projection

    Returns:
        Dict {region_name: {temp_projected, anomaly, amplification}}
    """
    results = {}
    for region, factor in REGIONS_AMPLIFICATION.items():
        regional_anomaly = round(national_anomaly * factor, 2)
        base_temp = REGIONS_TEMP_BASE[region]
        projected_temp = round(base_temp + regional_anomaly - 1.5, 2)  # -1.5 car base_temp inclut déjà un réchauffement

        results[region] = {
            "code": REGIONS_CODES[region],
            "temp_base": base_temp,
            "temp_projected": projected_temp,
            "anomaly": regional_anomaly,
            "amplification": factor,
            "year": target_year,
        }
    return results


def get_geojson_url() -> str:
    """URL du GeoJSON des régions françaises (source officielle)."""
    return "https://france-geojson.gregoiredavid.fr/repo/regions.geojson"
