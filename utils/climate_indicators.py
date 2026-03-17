"""
Indicateurs climatiques et recommandations citoyennes.

Basé sur les annexes du hackathon :
- PNACC-3 : 51 mesures d'adaptation (Annexe 5)
- HCC 2025 : chiffres récents sur les émissions et impacts (Annexe 6)
- Chiffres clés du climat 2024 : émissions GES par secteur (Annexe 2)
- Earth Action Report 2025 : 5 priorités mondiales (Annexe 3)
"""

# Émissions GES France (HCC 2025, Annexe 6)
# Émissions brutes moyennes 2019-2023 : 406 Mt éqCO2/an
# Composition : CO2 74%, CH4 16%, N2O 7%, gaz fluorés 2%
EMISSIONS_FRANCE = {
    "total_mt_eqco2": 406,
    "composition": {
        "CO2": 0.74,
        "CH4": 0.16,
        "N2O": 0.07,
        "Gaz fluorés": 0.02,
        "Autres": 0.01,
    },
    "par_secteur": {
        "Transports": 0.31,
        "Agriculture": 0.19,
        "Industrie": 0.18,
        "Bâtiments": 0.16,
        "Énergie": 0.10,
        "Déchets": 0.04,
        "Autres": 0.02,
    },
}

# Indicateurs d'évolution climatique (cahier des charges p.6)
INDICATEURS_CLIMATIQUES = [
    {
        "id": "temp_moyenne",
        "nom": "Température moyenne annuelle",
        "description": "Évolution de la température moyenne depuis 1900",
        "unite": "°C",
        "source": "Météo France / meteo.data.gouv.fr",
        "categorie": "Évolution climatique",
    },
    {
        "id": "jours_chaleur",
        "nom": "Jours > 30°C",
        "description": "Nombre de jours de forte chaleur par an",
        "unite": "jours/an",
        "source": "Météo France",
        "categorie": "Évolution climatique",
    },
    {
        "id": "jours_gel",
        "nom": "Jours de gel",
        "description": "Nombre de jours de gel par an (en diminution)",
        "unite": "jours/an",
        "source": "Météo France",
        "categorie": "Évolution climatique",
    },
    {
        "id": "precipitations",
        "nom": "Précipitations annuelles",
        "description": "Cumul des précipitations et épisodes de sécheresse",
        "unite": "mm/an",
        "source": "Météo France",
        "categorie": "Évolution climatique",
    },
    {
        "id": "niveau_mer",
        "nom": "Niveau des mers",
        "description": "Élévation du niveau moyen (+4.3mm/an, HCC 2025)",
        "unite": "mm",
        "source": "NOAA / HCC",
        "categorie": "Évolution climatique",
    },
    {
        "id": "feux_foret",
        "nom": "Feux de forêt",
        "description": "Surface brûlée et fréquence des incendies (x2.5, PNACC-3)",
        "unite": "hectares/an",
        "source": "EFFIS / ONF",
        "categorie": "Évolution climatique",
    },
    {
        "id": "emissions_ges",
        "nom": "Émissions GES par secteur",
        "description": "Répartition des 406 Mt éqCO2/an (HCC 2025)",
        "unite": "Mt éqCO2",
        "source": "CITEPA / Secten",
        "categorie": "Pressions humaines",
    },
    {
        "id": "empreinte_carbone",
        "nom": "Empreinte carbone individuelle",
        "description": "Émissions importées + produites par habitant",
        "unite": "t éqCO2/hab",
        "source": "Insee / SDES",
        "categorie": "Pressions humaines",
    },
    {
        "id": "vagues_chaleur",
        "nom": "Vagues de chaleur",
        "description": "Jours de canicule x6 (2015-2024 vs 1961-1990, HCC 2025)",
        "unite": "jours/an",
        "source": "HCC / Météo France",
        "categorie": "Impacts visibles",
    },
    {
        "id": "cout_catastrophes",
        "nom": "Coût des catastrophes climatiques",
        "description": "Inondations hiver 2023-2024 : 520 à 615 M€ (HCC 2025)",
        "unite": "M€",
        "source": "HCC / CCR",
        "categorie": "Impacts visibles",
    },
]

# Préconisations citoyennes (PNACC-3, Annexe 5 + cahier des charges p.7)
PRECONISATIONS = {
    "Risque canicule": {
        "seuil": "Augmentation > +2°C",
        "actions": [
            "Végétaliser les espaces urbains (PNACC-3, mesure 13)",
            "Adapter les logements au risque chaleur (PNACC-3, mesure 9)",
            "Déployer les technologies de froid renouvelable (PNACC-3, mesure 10)",
            "Protéger les populations précaires (PNACC-3, mesure 14)",
            "Adapter les comportements individuels : hydratation, horaires décalés",
        ],
        "icon": "🌡️",
    },
    "Risque sécheresse": {
        "seuil": "Précipitations < -15%",
        "actions": [
            "Préserver la ressource en eau (PNACC-3, mesure 21)",
            "Réduire la consommation d'eau domestique",
            "Choisir des plantes résistantes à la sécheresse",
            "Installer des systèmes de récupération d'eau de pluie",
        ],
        "icon": "💧",
    },
    "Risque incendie": {
        "seuil": "Surface à risque x2.5",
        "actions": [
            "Se préparer à l'augmentation des incendies (PNACC-3, mesure 7)",
            "Débroussailler autour des habitations",
            "Aménagements anti-incendie",
            "Connaître les procédures d'urgence",
        ],
        "icon": "🔥",
    },
    "Réduction empreinte carbone": {
        "seuil": "Objectif neutralité 2050",
        "actions": [
            "Mobilité douce : vélo, transports en commun (PNACC-3, mesure 30)",
            "Alimentation bas carbone : réduire viande, privilégier local et de saison",
            "Rénovation énergétique du logement (PNACC-3, mesure 9)",
            "Transition énergétique : énergies renouvelables",
            "Réduire les émissions de 50% d'ici 2030 (objectif GIEC)",
        ],
        "icon": "🌱",
    },
    "Risque inondation": {
        "seuil": "Montée du niveau de la mer +4.3mm/an",
        "actions": [
            "Protéger la population des inondations (PNACC-3, mesure 3)",
            "Repenser l'aménagement du trait de côte (PNACC-3, mesure 4)",
            "S'assurer contre les risques naturels (PNACC-3, mesure 2)",
            "Solutions fondées sur la nature (PNACC-3, mesure 20)",
        ],
        "icon": "🌊",
    },
}


def get_indicators_by_category(category: str) -> list:
    """Retourne les indicateurs d'une catégorie donnée."""
    return [ind for ind in INDICATEURS_CLIMATIQUES if ind["categorie"] == category]


def get_all_categories() -> list:
    """Retourne la liste des catégories d'indicateurs."""
    return list(set(ind["categorie"] for ind in INDICATEURS_CLIMATIQUES))


def get_preconisations_for_scenario(scenario_warming: float) -> list:
    """
    Retourne les préconisations pertinentes selon le niveau de réchauffement.
    Plus le réchauffement est élevé, plus les recommandations sont urgentes.
    """
    active = []
    if scenario_warming >= 1.5:
        active.append("Réduction empreinte carbone")
    if scenario_warming >= 2.0:
        active.append("Risque canicule")
        active.append("Risque sécheresse")
    if scenario_warming >= 2.5:
        active.append("Risque incendie")
    if scenario_warming >= 3.0:
        active.append("Risque inondation")

    return {k: v for k, v in PRECONISATIONS.items() if k in active}
