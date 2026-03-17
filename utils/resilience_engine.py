"""
Moteur de recommandations prédictives territoriales.

Génère des fiches d'action prioritaires par région, scénario et horizon temporel,
alignées sur :
- PNACC-3 (51 mesures d'adaptation, Annexe 5)
- France Stratégie — Valeur de l'action pour le climat (Annexe 1)
- HCC 2025 — Rapport annuel (Annexe 6)
- Earth Action Report 2025 (Annexe 3)
"""

from utils.geo_data import REGIONS_AMPLIFICATION, REGIONS_TEMP_BASE

# ────────────────────────────────────────────────────────────
# Coût de l'inaction par degré de réchauffement
# Source : France Stratégie (Annexe 1), HCC 2025 (Annexe 6)
# Inondations 2023-2024 : 520-615 M€ (HCC 2025)
# Valeur tutélaire du carbone : 250 €/tCO2 en 2030 (France Stratégie)
# ────────────────────────────────────────────────────────────
COUT_INACTION_PAR_DEGRE = {
    "Agriculture": 2.5,       # Mds €/°C/an — pertes récoltes, irrigation
    "Santé": 1.8,             # Mds €/°C/an — surmortalité canicule, dengue
    "Infrastructure": 3.2,    # Mds €/°C/an — inondations, retrait-gonflement argiles
    "Tourisme": 0.8,          # Mds €/°C/an — baisse attractivité
    "Énergie": 1.2,           # Mds €/°C/an — climatisation, réseau
}

# ────────────────────────────────────────────────────────────
# Fiches d'action par domaine, alignées PNACC-3
# Chaque fiche : mesure PNACC-3, description, investissement estimé
# ────────────────────────────────────────────────────────────
FICHES_AGRICULTURE = {
    "faible": {  # anomalie < 2.5°C
        "titre": "Adaptation agricole — Niveau modéré",
        "mesures_pnacc3": [21, 20],
        "actions": [
            "Diversifier les cultures vers des variétés résistantes à la chaleur",
            "Optimiser l'irrigation : goutte-à-goutte, récupération d'eau pluviale",
            "Renforcer le Plan Eau pour préserver la ressource (PNACC-3, mesure 21)",
        ],
        "investissement_mds": 1.5,
        "horizon": "2025-2035",
    },
    "moyen": {  # 2.5 ≤ anomalie < 4.0
        "titre": "Transformation agricole — Niveau élevé",
        "mesures_pnacc3": [21, 20, 33],
        "actions": [
            "Transition vers des cultures méditerranéennes (olivier, vigne tardive)",
            "Déployer des solutions fondées sur la nature : haies, agroforesterie (PNACC-3, mesure 20)",
            "Préserver la ressource en eau : renforcer le Plan Eau (PNACC-3, mesure 21)",
            "Intégrer l'adaptation dans les stratégies des exploitations (PNACC-3, mesure 33)",
            "Créer des réserves d'eau collinaires pour l'irrigation de secours",
        ],
        "investissement_mds": 4.0,
        "horizon": "2025-2050",
    },
    "fort": {  # anomalie ≥ 4.0
        "titre": "Refonte du modèle agricole — Niveau critique",
        "mesures_pnacc3": [21, 20, 33, 35],
        "actions": [
            "Repenser intégralement les filières : abandon de cultures inadaptées",
            "Agriculture de précision : IA et capteurs pour optimiser chaque goutte d'eau",
            "Protéger les sols : couverture permanente, semis direct",
            "Développer l'aquaponie et cultures hors-sol en zone critique",
            "Solutions fondées sur la nature à grande échelle (PNACC-3, mesure 20)",
            "Accompagner l'adaptation du tourisme rural (PNACC-3, mesure 35)",
        ],
        "investissement_mds": 8.5,
        "horizon": "2025-2070",
    },
}

FICHES_SANTE_URBANISME = {
    "faible": {
        "titre": "Adaptation urbaine — Niveau modéré",
        "mesures_pnacc3": [9, 13],
        "actions": [
            "Adapter les logements au risque chaleur : isolation, ventilation (PNACC-3, mesure 9)",
            "Végétaliser les espaces urbains : îlots de fraîcheur (PNACC-3, mesure 13)",
            "Installer des fontaines et brumisateurs en espace public",
        ],
        "investissement_mds": 2.0,
        "horizon": "2025-2035",
    },
    "moyen": {
        "titre": "Résilience urbaine — Niveau élevé",
        "mesures_pnacc3": [9, 10, 13, 14, 16],
        "actions": [
            "Rénover massivement les logements : confort d'été obligatoire (PNACC-3, mesure 9)",
            "Déployer le froid renouvelable : géothermie, réseaux de froid (PNACC-3, mesure 10)",
            "Renaturer les villes : corridors de biodiversité (PNACC-3, mesure 13)",
            "Protéger les populations précaires des fortes chaleurs (PNACC-3, mesure 14)",
            "Approche 'Une seule santé' pour les risques sanitaires (PNACC-3, mesure 16)",
        ],
        "investissement_mds": 6.0,
        "horizon": "2025-2050",
    },
    "fort": {
        "titre": "Transformation urbaine — Niveau critique",
        "mesures_pnacc3": [9, 10, 13, 14, 15, 16, 17, 18],
        "actions": [
            "Repenser l'urbanisme : matériaux réfléchissants, toits végétalisés obligatoires",
            "Plan canicule renforcé : abris climatisés, horaires décalés (PNACC-3, mesure 14)",
            "Protection des détenus et personnels pénitentiaires (PNACC-3, mesure 15)",
            "Surveillance renforcée des impacts sanitaires (PNACC-3, mesure 17)",
            "Maintien qualité de l'air lors des vagues de chaleur (PNACC-3, mesure 18)",
            "Architecture bioclimatique obligatoire pour tout nouveau bâtiment",
            "Créer des 'quartiers résilients' pilotes dans chaque métropole",
        ],
        "investissement_mds": 15.0,
        "horizon": "2025-2070",
    },
}

FICHES_ECONOMIE = {
    "faible": {
        "titre": "Adaptation économique — Niveau modéré",
        "mesures_pnacc3": [27, 33],
        "actions": [
            "Intégrer le risque climatique dans les financements publics (PNACC-3, mesure 27)",
            "Mobiliser les entreprises sur l'adaptation (PNACC-3, mesure 33)",
            "Valeur carbone : intégrer 250 €/tCO₂ dans les décisions d'investissement (France Stratégie)",
        ],
        "investissement_mds": 3.0,
        "horizon": "2025-2035",
        "ratio_benefice": 3.5,  # 1€ investi = 3.5€ de dégâts évités
    },
    "moyen": {
        "titre": "Transition économique — Niveau élevé",
        "mesures_pnacc3": [27, 30, 31, 33, 34],
        "actions": [
            "Résilience des transports et mobilités (PNACC-3, mesure 30)",
            "Résilience du système énergétique (PNACC-3, mesure 31)",
            "Intégrer l'adaptation dans les aides aux entreprises (PNACC-3, mesure 34)",
            "Développer l'économie circulaire et les circuits courts",
            "Valeur carbone : 500 €/tCO₂ en 2040 pour guider les investissements (France Stratégie)",
        ],
        "investissement_mds": 8.0,
        "horizon": "2025-2050",
        "ratio_benefice": 4.0,
    },
    "fort": {
        "titre": "Refonte économique — Niveau critique",
        "mesures_pnacc3": [1, 2, 27, 30, 31, 32, 33, 34],
        "actions": [
            "Renforcer le fonds Barnier : prévention des territoires (PNACC-3, mesure 1)",
            "Moderniser le système assurantiel face aux risques naturels (PNACC-3, mesure 2)",
            "Résilience des télécoms et services numériques (PNACC-3, mesure 32)",
            "Plan massif de relocalisation des activités hors zones à risque",
            "Création d'un fonds souverain d'adaptation climatique",
            "Valeur carbone >800 €/tCO₂ en 2050 (France Stratégie, trajectoire haute)",
        ],
        "investissement_mds": 25.0,
        "horizon": "2025-2070",
        "ratio_benefice": 5.0,
    },
}


def _severity_level(anomaly: float) -> str:
    """Détermine le niveau de sévérité selon l'anomalie régionale."""
    if anomaly < 2.5:
        return "faible"
    elif anomaly < 4.0:
        return "moyen"
    return "fort"


def generate_recommendations(
    region: str,
    scenario: str,
    target_year: int,
    national_anomaly: float,
) -> dict:
    """
    Génère les 3 fiches d'action prioritaires pour une région donnée.

    Args:
        region: Nom de la région
        scenario: Nom du scénario GIEC
        target_year: Année cible de la projection
        national_anomaly: Anomalie nationale (°C vs préindustriel)

    Returns:
        Dict avec les 3 fiches + métriques coût/investissement
    """
    # Calcul de l'anomalie régionale
    factor = REGIONS_AMPLIFICATION.get(region, 1.0)
    regional_anomaly = round(national_anomaly * factor, 2)
    severity = _severity_level(regional_anomaly)

    # Récupération des fiches
    agriculture = FICHES_AGRICULTURE[severity].copy()
    sante = FICHES_SANTE_URBANISME[severity].copy()
    economie = FICHES_ECONOMIE[severity].copy()

    # Calcul du coût de l'inaction pour cette région
    cout_total_inaction = sum(COUT_INACTION_PAR_DEGRE.values()) * regional_anomaly
    investissement_total = (
        agriculture["investissement_mds"]
        + sante["investissement_mds"]
        + economie["investissement_mds"]
    )

    # Part régionale (proportionnelle à la population/PIB approximatif)
    part_regionale = _get_regional_weight(region)
    cout_regional = round(cout_total_inaction * part_regionale, 2)
    invest_regional = round(investissement_total * part_regionale, 2)

    return {
        "region": region,
        "scenario": scenario,
        "target_year": target_year,
        "anomaly_national": national_anomaly,
        "anomaly_regional": regional_anomaly,
        "severity": severity,
        "temp_base": REGIONS_TEMP_BASE.get(region, 12.0),
        "temp_projected": round(REGIONS_TEMP_BASE.get(region, 12.0) + regional_anomaly - 1.5, 2),
        "fiches": {
            "agriculture": agriculture,
            "sante_urbanisme": sante,
            "economie": economie,
        },
        "metriques": {
            "cout_inaction_national_mds": round(cout_total_inaction, 1),
            "cout_inaction_regional_mds": cout_regional,
            "investissement_regional_mds": invest_regional,
            "ratio_benefice": economie.get("ratio_benefice", 3.0),
            "degats_evites_mds": round(invest_regional * economie.get("ratio_benefice", 3.0), 1),
        },
    }


def _get_regional_weight(region: str) -> float:
    """
    Poids économique/démographique approximatif de chaque région.
    Source : Insee, PIB régional 2023.
    """
    weights = {
        "Île-de-France": 0.31,
        "Auvergne-Rhône-Alpes": 0.12,
        "Nouvelle-Aquitaine": 0.08,
        "Occitanie": 0.07,
        "Hauts-de-France": 0.07,
        "Grand Est": 0.07,
        "Provence-Alpes-Côte d'Azur": 0.07,
        "Pays de la Loire": 0.05,
        "Bretagne": 0.05,
        "Normandie": 0.04,
        "Centre-Val de Loire": 0.03,
        "Bourgogne-Franche-Comté": 0.03,
        "Corse": 0.01,
    }
    return weights.get(region, 0.05)


# ────────────────────────────────────────────────────────────
# Mapping code postal → région
# ────────────────────────────────────────────────────────────
CP_TO_REGION = {
    "01": "Auvergne-Rhône-Alpes", "03": "Auvergne-Rhône-Alpes",
    "07": "Auvergne-Rhône-Alpes", "15": "Auvergne-Rhône-Alpes",
    "26": "Auvergne-Rhône-Alpes", "38": "Auvergne-Rhône-Alpes",
    "42": "Auvergne-Rhône-Alpes", "43": "Auvergne-Rhône-Alpes",
    "63": "Auvergne-Rhône-Alpes", "69": "Auvergne-Rhône-Alpes",
    "73": "Auvergne-Rhône-Alpes", "74": "Auvergne-Rhône-Alpes",
    "21": "Bourgogne-Franche-Comté", "25": "Bourgogne-Franche-Comté",
    "39": "Bourgogne-Franche-Comté", "58": "Bourgogne-Franche-Comté",
    "70": "Bourgogne-Franche-Comté", "71": "Bourgogne-Franche-Comté",
    "89": "Bourgogne-Franche-Comté", "90": "Bourgogne-Franche-Comté",
    "22": "Bretagne", "29": "Bretagne", "35": "Bretagne", "56": "Bretagne",
    "18": "Centre-Val de Loire", "28": "Centre-Val de Loire",
    "36": "Centre-Val de Loire", "37": "Centre-Val de Loire",
    "41": "Centre-Val de Loire", "45": "Centre-Val de Loire",
    "2A": "Corse", "2B": "Corse", "20": "Corse",
    "08": "Grand Est", "10": "Grand Est", "51": "Grand Est",
    "52": "Grand Est", "54": "Grand Est", "55": "Grand Est",
    "57": "Grand Est", "67": "Grand Est", "68": "Grand Est",
    "88": "Grand Est",
    "02": "Hauts-de-France", "59": "Hauts-de-France",
    "60": "Hauts-de-France", "62": "Hauts-de-France",
    "80": "Hauts-de-France",
    "75": "Île-de-France", "77": "Île-de-France",
    "78": "Île-de-France", "91": "Île-de-France",
    "92": "Île-de-France", "93": "Île-de-France",
    "94": "Île-de-France", "95": "Île-de-France",
    "14": "Normandie", "27": "Normandie", "50": "Normandie",
    "61": "Normandie", "76": "Normandie",
    "16": "Nouvelle-Aquitaine", "17": "Nouvelle-Aquitaine",
    "19": "Nouvelle-Aquitaine", "23": "Nouvelle-Aquitaine",
    "24": "Nouvelle-Aquitaine", "33": "Nouvelle-Aquitaine",
    "40": "Nouvelle-Aquitaine", "47": "Nouvelle-Aquitaine",
    "64": "Nouvelle-Aquitaine", "79": "Nouvelle-Aquitaine",
    "86": "Nouvelle-Aquitaine", "87": "Nouvelle-Aquitaine",
    "09": "Occitanie", "11": "Occitanie", "12": "Occitanie",
    "30": "Occitanie", "31": "Occitanie", "32": "Occitanie",
    "34": "Occitanie", "46": "Occitanie", "48": "Occitanie",
    "65": "Occitanie", "66": "Occitanie", "81": "Occitanie",
    "82": "Occitanie",
    "44": "Pays de la Loire", "49": "Pays de la Loire",
    "53": "Pays de la Loire", "72": "Pays de la Loire",
    "85": "Pays de la Loire",
    "04": "Provence-Alpes-Côte d'Azur", "05": "Provence-Alpes-Côte d'Azur",
    "06": "Provence-Alpes-Côte d'Azur", "13": "Provence-Alpes-Côte d'Azur",
    "83": "Provence-Alpes-Côte d'Azur", "84": "Provence-Alpes-Côte d'Azur",
}


def get_region_from_postal_code(postal_code: str) -> str | None:
    """Retourne la région correspondant à un code postal."""
    dept = postal_code[:2]
    return CP_TO_REGION.get(dept)
