"""
Pipeline d'ingestion des données climatiques historiques pour la France.

Sources (Défi Changement Climatique - defis.data.gouv.fr) :
- Données SIM mensuelle (Safran-Isba, Météo-France) : 9892 points de grille, 1959-présent
  → Dataset : meteo.data.gouv.fr/datasets/65e040c50a5c6872ebebc711
  → Vraie moyenne nationale France métropolitaine
- Données LSH (Longues Séries Homogénéisées, Météo-France) : stations métropole, ~1900-présent
  → Dataset : meteo.data.gouv.fr/datasets/6569b2c4f1937611d4c8b1a3
  → Séries corrigées par homogénéisation statistique (TN, TX)
- Référence : Rapport annuel 2025 du Haut Conseil pour le Climat
  → Réchauffement observé en France métropolitaine : +1.64°C (2015-2024 vs 1961-1990)
"""

import pandas as pd
import numpy as np
import requests
import io
import zipfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Constantes ──
BASELINE_TEMP_FRANCE = 9.82  # °C, moyenne nationale 1961-1990 (calculée sur données SIM)
RÉCHAUFFEMENT_MONDIAL_2024 = 1.52  # °C, GIEC/HCC
CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"

# Scénarios GIEC (réchauffement planétaire fin de siècle vs préindustriel)
SCENARIOS = {
    "Optimiste (SSP1-1.9)": {"global_2100": 1.4, "france_factor": 1.5},
    "Intermédiaire (SSP2-4.5)": {"global_2100": 2.7, "france_factor": 1.5},
    "Pessimiste (SSP5-8.5)": {"global_2100": 4.4, "france_factor": 1.5},
}

# ── URLs des données (Défi data.gouv.fr) ──
SIM_MENS_BASE_URL = (
    "https://object.files.data.gouv.fr/meteofrance/data/synchro_ftp/REF_CC/SIM_MENS/"
)
SIM_MENS_FILES = [
    "MENS_SIM2_1958-1959.csv.gz",
    "MENS_SIM2_1960-1969.csv.gz",
    "MENS_SIM2_1970-1979.csv.gz",
    "MENS_SIM2_1980-1989.csv.gz",
    "MENS_SIM2_1990-1999.csv.gz",
    "MENS_SIM2_2000-2009.csv.gz",
    "MENS_SIM2_2010-2019.csv.gz",
    "MENS_SIM2_latest-2020-2026.csv.gz",
]

LSH_TN_URL = (
    "https://object.files.data.gouv.fr/meteofrance/data/synchro_ftp/REF_CC/LSH/"
    "SH_TN_metropole.zip"
)
LSH_TX_URL = (
    "https://object.files.data.gouv.fr/meteofrance/data/synchro_ftp/REF_CC/LSH/"
    "SH_TX_metropole.zip"
)


def _get_cache_path(name: str) -> Path:
    """Retourne le chemin du fichier cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / name


def _fetch_sim_mensuelle() -> pd.DataFrame | None:
    """
    Télécharge les données SIM mensuelle (modèle Safran-Isba, Météo-France).

    Source : Défi Changement Climatique (defis.data.gouv.fr)
    Dataset : Données changement climatique - SIM mensuelle
    9892 points de grille couvrant toute la France métropolitaine.

    Retourne les moyennes annuelles nationales (1959-présent).
    """
    cache_path = _get_cache_path("sim_annual_means.csv")

    # Utiliser le cache si disponible et récent (< 7 jours)
    if cache_path.exists():
        import os
        age_days = (pd.Timestamp.now().timestamp() - os.path.getmtime(cache_path)) / 86400
        if age_days < 7:
            logger.info(f"SIM mensuelle : chargement depuis le cache ({age_days:.1f} jours)")
            return pd.read_csv(cache_path)

    try:
        all_monthly = []
        for filename in SIM_MENS_FILES:
            url = SIM_MENS_BASE_URL + filename
            logger.info(f"Téléchargement {filename}...")
            resp = requests.get(url, timeout=120)
            resp.raise_for_status()

            df = pd.read_csv(
                io.BytesIO(resp.content),
                compression="gzip",
                sep=";",
                usecols=["DATE", "T_MENS"],
            )
            # Moyenne nationale par mois (sur les 9892 points de grille)
            monthly_avg = df.groupby("DATE")["T_MENS"].mean().reset_index()
            monthly_avg.columns = ["date_ym", "temp_mean"]
            all_monthly.append(monthly_avg)

        all_data = pd.concat(all_monthly, ignore_index=True)
        all_data["year"] = all_data["date_ym"].astype(str).str[:4].astype(int)

        # Exclure l'année en cours (potentiellement incomplète)
        current_year = pd.Timestamp.now().year
        all_data = all_data[all_data["year"] < current_year]

        # Ne garder que les années avec 12 mois complets
        months_per_year = all_data.groupby("year").size()
        complete_years = months_per_year[months_per_year == 12].index
        all_data = all_data[all_data["year"].isin(complete_years)]

        annual = all_data.groupby("year")["temp_mean"].mean().reset_index()
        annual["temp_mean"] = annual["temp_mean"].round(2)

        # Sauvegarder en cache
        annual.to_csv(cache_path, index=False)
        logger.info(
            f"SIM mensuelle : {len(annual)} années "
            f"({annual['year'].min()}-{annual['year'].max()}), "
            f"9892 points de grille"
        )
        return annual

    except Exception as e:
        logger.warning(f"Erreur SIM mensuelle : {e}")
        return None


def _fetch_lsh_temperatures() -> pd.DataFrame | None:
    """
    Télécharge les données LSH (Longues Séries Homogénéisées, Météo-France).

    Source : Défi Changement Climatique (defis.data.gouv.fr)
    Dataset : Données changement climatique - LSH
    Séries mensuelles corrigées par homogénéisation statistique.
    TN (temp min) + TX (temp max) → Tmean = (TN + TX) / 2

    Retourne les moyennes annuelles nationales (~1900-présent).
    """
    cache_path = _get_cache_path("lsh_annual_means.csv")

    if cache_path.exists():
        import os
        age_days = (pd.Timestamp.now().timestamp() - os.path.getmtime(cache_path)) / 86400
        if age_days < 7:
            logger.info(f"LSH : chargement depuis le cache ({age_days:.1f} jours)")
            return pd.read_csv(cache_path)

    try:
        def _read_lsh_zip(url: str) -> pd.DataFrame:
            """Lit toutes les stations d'un zip LSH."""
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()

            all_stations = []
            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                for name in z.namelist():
                    if not name.endswith(".csv"):
                        continue
                    with z.open(name) as f:
                        lines = f.read().decode("utf-8", errors="replace").split("\n")
                        # Trouver la ligne d'en-tête (après les commentaires #)
                        data_lines = [l for l in lines if l and not l.startswith("#")]
                        if len(data_lines) < 2:
                            continue
                        station_df = pd.read_csv(
                            io.StringIO("\n".join(data_lines)),
                            sep=";",
                        )
                        station_df.columns = ["date_ym", "value", "q_hom"]
                        all_stations.append(station_df)

            return pd.concat(all_stations, ignore_index=True)

        logger.info("Téléchargement LSH TN (temp min) métropole...")
        tn_df = _read_lsh_zip(LSH_TN_URL)
        tn_df = tn_df.rename(columns={"value": "tn"})

        logger.info("Téléchargement LSH TX (temp max) métropole...")
        tx_df = _read_lsh_zip(LSH_TX_URL)
        tx_df = tx_df.rename(columns={"value": "tx"})

        # Joindre TN et TX par date
        merged = tn_df[["date_ym", "tn"]].merge(
            tx_df[["date_ym", "tx"]], on="date_ym", how="inner"
        )
        merged["tmean"] = (merged["tn"] + merged["tx"]) / 2
        merged["year"] = merged["date_ym"].astype(str).str[:4].astype(int)

        # Exclure année en cours
        current_year = pd.Timestamp.now().year
        merged = merged[merged["year"] < current_year]

        # Moyenne annuelle nationale (toutes stations)
        annual = merged.groupby("year")["tmean"].mean().reset_index()
        annual.columns = ["year", "temp_mean"]
        annual["temp_mean"] = annual["temp_mean"].round(2)

        # Sauvegarder en cache
        annual.to_csv(cache_path, index=False)
        logger.info(
            f"LSH : {len(annual)} années "
            f"({annual['year'].min()}-{annual['year'].max()})"
        )
        return annual

    except Exception as e:
        logger.warning(f"Erreur LSH : {e}")
        return None


def fetch_real_meteo_data(start_year: int = 1900) -> tuple[pd.DataFrame, bool]:
    """
    Récupère l'historique réel des températures annuelles pour la France entière.

    Stratégie en 2 sources (Défi Changement Climatique, defis.data.gouv.fr) :
    1. SIM mensuelle (Safran-Isba) : 9892 points de grille, 1959-présent
       → Référence principale, vraie moyenne nationale
    2. LSH (Longues Séries Homogénéisées) : stations métropole, ~1900-présent
       → Extension historique, calibrée sur SIM via régression linéaire

    La calibration LSH → SIM est faite sur la période de chevauchement (1959-2024)
    pour harmoniser les deux séries.

    Returns:
        (DataFrame, is_real_data): le DataFrame et un bool indiquant si les données
        sont réelles (True) ou de fallback synthétique (False).
    """
    try:
        # ── Source 1 : SIM mensuelle (référence principale) ──
        sim_df = _fetch_sim_mensuelle()

        # ── Source 2 : LSH (extension historique) ──
        lsh_df = _fetch_lsh_temperatures()

        if sim_df is None and lsh_df is None:
            raise RuntimeError("Aucune source de données disponible")

        if sim_df is not None and lsh_df is not None:
            # Calibrer LSH sur SIM via la période de chevauchement
            overlap = sim_df.merge(lsh_df, on="year", suffixes=("_sim", "_lsh"))
            if len(overlap) >= 10:
                sim_vals = overlap["temp_mean_sim"].values
                lsh_vals = overlap["temp_mean_lsh"].values
                a = np.cov(lsh_vals, sim_vals)[0, 1] / np.var(lsh_vals)
                b = sim_vals.mean() - a * lsh_vals.mean()

                logger.info(
                    f"Calibration LSH→SIM sur {len(overlap)} ans : "
                    f"a={a:.4f}, b={b:.2f}"
                )

                # Appliquer la calibration aux années LSH pré-SIM
                sim_min_year = sim_df["year"].min()
                lsh_pre = lsh_df[lsh_df["year"] < sim_min_year].copy()
                lsh_pre["temp_mean"] = np.round(a * lsh_pre["temp_mean"] + b, 2)

                # Combiner : LSH calibré (pré-1959) + SIM (1959+)
                combined = pd.concat(
                    [lsh_pre[["year", "temp_mean"]], sim_df[["year", "temp_mean"]]],
                    ignore_index=True,
                )
            else:
                combined = sim_df[["year", "temp_mean"]].copy()
        elif sim_df is not None:
            combined = sim_df[["year", "temp_mean"]].copy()
        else:
            combined = lsh_df[["year", "temp_mean"]].copy()

        combined = combined.sort_values("year").reset_index(drop=True)

        # ── Anomalies vs baseline 1961-1990 ──
        baseline_mask = (combined["year"] >= 1961) & (combined["year"] <= 1990)
        baseline = combined.loc[baseline_mask, "temp_mean"].mean()
        combined["anomaly"] = np.round(combined["temp_mean"] - baseline, 2)

        # Filtrer
        df = combined[combined["year"] >= start_year].reset_index(drop=True)
        df["source"] = "meteo.data.gouv.fr"

        logger.info(
            f"Données réelles chargées (SIM + LSH) : {len(df)} années "
            f"({df['year'].min()}-{df['year'].max()}), "
            f"baseline 1961-1990 = {baseline:.2f}°C"
        )
        return df[["year", "temp_mean", "anomaly", "source"]], True

    except Exception as e:
        logger.warning(f"Impossible de charger les données réelles : {e}. Fallback synthétique.")
        df = _generate_synthetic_temperatures(start_year)
        return df, False


def _generate_synthetic_temperatures(start_year: int = 1900, end_year: int = 2024) -> pd.DataFrame:
    """Fallback : génère des températures simulées si le fetch échoue."""
    years = np.arange(start_year, end_year + 1)
    n = len(years)

    trend = np.zeros(n)
    for i, year in enumerate(years):
        if year <= 1970:
            progress = (year - start_year) / (1970 - start_year)
            trend[i] = BASELINE_TEMP_FRANCE + 0.3 * progress
        else:
            progress = (year - 1970) / (end_year - 1970)
            trend[i] = BASELINE_TEMP_FRANCE + 0.3 + 1.9 * (progress ** 1.3)

    np.random.seed(42)
    noise = np.random.normal(0, 0.4, n)
    temperatures = trend + noise

    df = pd.DataFrame({
        "year": years,
        "temp_mean": np.round(temperatures, 2),
    })
    df["anomaly"] = np.round(df["temp_mean"] - BASELINE_TEMP_FRANCE, 2)
    df["source"] = "synthetic"
    return df


def generate_historical_temperatures(start_year: int = 1900, end_year: int = 2024) -> pd.DataFrame:
    """
    Charge les températures historiques — données réelles si disponibles,
    sinon fallback synthétique.

    Conservée pour compatibilité avec le reste du code.
    """
    df, is_real = fetch_real_meteo_data(start_year=start_year)

    # Filtrer jusqu'à end_year
    df = df[df["year"] <= end_year].reset_index(drop=True)

    return df


def compute_deviation_from_baseline(df: pd.DataFrame, reference_period: tuple = (1961, 1990)) -> pd.DataFrame:
    """
    Calcule l'écart de température par rapport à une période de référence.

    Par défaut : 1961-1990 (norme OMM).
    """
    mask = (df["year"] >= reference_period[0]) & (df["year"] <= reference_period[1])
    baseline_mean = df.loc[mask, "temp_mean"].mean()

    df["deviation_from_ref"] = np.round(df["temp_mean"] - baseline_mean, 2)
    df["reference_period"] = f"{reference_period[0]}-{reference_period[1]}"

    return df


def generate_projections(
    historical_df: pd.DataFrame,
    scenario: str = "Intermédiaire (SSP2-4.5)",
    target_years: list = None,
) -> pd.DataFrame:
    """
    Génère des projections climatiques pour 2030, 2050 et 2100
    selon les scénarios du GIEC (SSP).

    Les projections sont calibrées sur :
    - TRACC (Trajectoire de Réchauffement de Référence pour l'Adaptation)
    - Rapport HCC 2025 : +1.5°C planétaire → +2°C France
                          +2°C planétaire → +2.7°C France
                          +3°C planétaire → +4°C France
    """
    if target_years is None:
        target_years = [2030, 2050, 2100]

    if scenario not in SCENARIOS:
        raise ValueError(f"Scénario inconnu : {scenario}. Choix : {list(SCENARIOS.keys())}")

    config = SCENARIOS[scenario]
    global_warming_2100 = config["global_2100"]
    france_factor = config["france_factor"]

    # Dernière température observée
    last_year = historical_df["year"].max()
    last_temp = historical_df.loc[historical_df["year"] == last_year, "temp_mean"].values[0]

    # Réchauffement additionnel par rapport à aujourd'hui
    current_global_warming = RÉCHAUFFEMENT_MONDIAL_2024
    remaining_global = global_warming_2100 - current_global_warming

    projections = []
    for target_year in target_years:
        if target_year <= last_year:
            continue

        # Interpolation linéaire du réchauffement restant
        progress = min((target_year - last_year) / (2100 - last_year), 1.0)
        additional_global = remaining_global * progress
        additional_france = additional_global * france_factor

        projected_temp = last_temp + additional_france
        projected_anomaly = projected_temp - BASELINE_TEMP_FRANCE

        projections.append({
            "year": target_year,
            "scenario": scenario,
            "temp_mean": round(projected_temp, 2),
            "anomaly": round(projected_anomaly, 2),
            "global_warming": round(current_global_warming + additional_global, 2),
        })

    return pd.DataFrame(projections)


def save_data(df: pd.DataFrame, filename: str, processed: bool = False) -> Path:
    """Sauvegarde un DataFrame dans le dossier data/."""
    subdir = "processed" if processed else "raw"
    output_dir = Path(__file__).parent.parent / "data" / subdir
    output_dir.mkdir(parents=True, exist_ok=True)

    filepath = output_dir / filename
    df.to_csv(filepath, index=False)
    return filepath


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("=== Pipeline d'ingestion des données climatiques ===\n")
    print("Sources : Défi Changement Climatique (defis.data.gouv.fr)\n")

    # 1. Génération des données historiques
    print("1. Chargement des températures historiques...")
    hist_df, is_real = fetch_real_meteo_data()
    hist_df = compute_deviation_from_baseline(hist_df)
    save_data(hist_df, "temperatures_france.csv", processed=True)
    last_row = hist_df.iloc[-1]
    print(f"   → {len(hist_df)} années ({hist_df['year'].min()}-{hist_df['year'].max()})")
    print(f"   → Source : {'meteo.data.gouv.fr (SIM + LSH)' if is_real else 'synthétique'}")
    print(f"   → Temp {int(last_row['year'])} : {last_row['temp_mean']}°C")
    print(f"   → Anomalie vs 1961-1990 : {'+' if last_row['anomaly'] >= 0 else ''}{last_row['anomaly']}°C")

    # 2. Projections pour chaque scénario
    print("\n2. Génération des projections climatiques...")
    all_projections = []
    for scenario_name in SCENARIOS:
        proj_df = generate_projections(hist_df, scenario=scenario_name)
        all_projections.append(proj_df)
        print(f"   → {scenario_name}:")
        for _, row in proj_df.iterrows():
            print(f"     {int(row['year'])}: {row['temp_mean']}°C (anomalie: +{row['anomaly']}°C)")

    projections_df = pd.concat(all_projections, ignore_index=True)
    save_data(projections_df, "projections_france.csv", processed=True)

    print("\n=== Pipeline terminé ===")
