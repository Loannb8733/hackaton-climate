"""
Modèle de prédiction climatique basé sur Prophet.

Objectif : produire des projections de température pour 2030, 2050, 2100
selon les scénarios du GIEC (cahier des charges, étape 3).

Alignement sur les scénarios SSP :
- Optimiste (SSP1-1.9) : +1.4°C mondial → +2.1°C France
- Intermédiaire (SSP2-4.5) : +2.7°C mondial → +4.05°C France
- Pessimiste (SSP5-8.5) : +4.4°C mondial → +6.6°C France

Source : HCC 2025, TRACC, GIEC AR6
"""

import pandas as pd
import numpy as np
from prophet import Prophet

from utils.data_ingestion import BASELINE_TEMP_FRANCE, SCENARIOS, RÉCHAUFFEMENT_MONDIAL_2024


def prepare_data_for_prophet(df: pd.DataFrame) -> pd.DataFrame:
    """Formate les données historiques pour Prophet (colonnes ds, y)."""
    prophet_df = pd.DataFrame({
        "ds": pd.to_datetime(df["year"], format="%Y"),
        "y": df["temp_mean"],
    })
    return prophet_df


def train_prophet_model(df: pd.DataFrame) -> Prophet:
    """
    Entraîne un modèle Prophet sur les données historiques.

    Paramétrage adapté aux séries climatiques annuelles :
    - Pas de saisonnalité (données annuelles)
    - changepoint_prior_scale faible pour tendance lissée
    """
    model = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
        interval_width=0.90,
    )
    model.fit(df)
    return model


def make_forecast(model: Prophet, periods: int = 76) -> pd.DataFrame:
    """
    Génère des prédictions futures avec Prophet (tendance naturelle).
    Par défaut : 76 ans (2024 → 2100).
    """
    future = model.make_future_dataframe(periods=periods, freq="YE")
    forecast = model.predict(future)
    forecast["year"] = forecast["ds"].dt.year
    return forecast[["year", "ds", "yhat", "yhat_lower", "yhat_upper"]]


def generate_scenario_projections(
    historical_df: pd.DataFrame,
    scenario: str,
    start_year: int = 2025,
    end_year: int = 2100,
) -> pd.DataFrame:
    """
    Génère des projections annuelles continues alignées sur un scénario GIEC.

    Méthode :
    1. On part de la dernière température observée
    2. On interpole le réchauffement additionnel France entre aujourd'hui et 2100
    3. On ajoute une variabilité simulée (±0.3°C) pour réalisme
    4. On calcule les bornes d'incertitude (croissantes avec le temps)
    """
    config = SCENARIOS[scenario]
    global_2100 = config["global_2100"]
    france_factor = config["france_factor"]

    # Température de départ (dernière observation)
    last_obs_year = historical_df["year"].max()
    last_obs_temp = historical_df.loc[
        historical_df["year"] == last_obs_year, "temp_mean"
    ].values[0]

    # Réchauffement France attendu d'ici 2100
    current_anomaly_france = last_obs_temp - BASELINE_TEMP_FRANCE
    target_anomaly_france = global_2100 * france_factor
    remaining_warming = target_anomaly_france - current_anomaly_france

    years = np.arange(start_year, end_year + 1)
    n = len(years)

    np.random.seed(hash(scenario) % 2**31)

    projections = []
    for i, year in enumerate(years):
        # Progression non-linéaire (légère accélération pour SSP5, plateau pour SSP1)
        progress = (year - last_obs_year) / (end_year - last_obs_year)

        if "Optimiste" in scenario:
            # Plateau rapide puis stabilisation
            adjusted_progress = 1 - (1 - progress) ** 0.7
        elif "Pessimiste" in scenario:
            # Accélération continue
            adjusted_progress = progress ** 1.4
        else:
            # Linéaire
            adjusted_progress = progress

        additional_warming = remaining_warming * adjusted_progress
        base_temp = last_obs_temp + additional_warming

        # Variabilité interannuelle
        noise = np.random.normal(0, 0.3)
        temp = base_temp + noise

        # Incertitude croissante avec le temps
        years_ahead = year - last_obs_year
        uncertainty = 0.3 + (years_ahead / (end_year - last_obs_year)) * 1.5

        anomaly = temp - BASELINE_TEMP_FRANCE

        projections.append({
            "year": year,
            "scenario": scenario,
            "temp_mean": round(temp, 2),
            "anomaly": round(anomaly, 2),
            "temp_lower": round(temp - uncertainty, 2),
            "temp_upper": round(temp + uncertainty, 2),
            "global_warming": round(
                RÉCHAUFFEMENT_MONDIAL_2024 + (global_2100 - RÉCHAUFFEMENT_MONDIAL_2024) * adjusted_progress, 2
            ),
        })

    return pd.DataFrame(projections)


def compute_crossing_year(projections_df: pd.DataFrame, threshold_anomaly: float = 2.0) -> int | None:
    """
    Calcule l'année où l'anomalie France franchit un seuil donné (ex: +2°C).

    Utilise la moyenne lissée (rolling 5 ans) pour éviter le bruit.
    """
    df = projections_df.copy()
    df["anomaly_smooth"] = df["anomaly"].rolling(window=5, min_periods=1, center=True).mean()

    crossed = df[df["anomaly_smooth"] >= threshold_anomaly]
    if crossed.empty:
        return None
    return int(crossed.iloc[0]["year"])


def generate_all_scenario_projections(historical_df: pd.DataFrame) -> pd.DataFrame:
    """Génère les projections pour les 3 scénarios GIEC."""
    all_dfs = []
    for scenario_name in SCENARIOS:
        proj_df = generate_scenario_projections(historical_df, scenario_name)
        all_dfs.append(proj_df)
    return pd.concat(all_dfs, ignore_index=True)


if __name__ == "__main__":
    from utils.data_ingestion import generate_historical_temperatures, compute_deviation_from_baseline

    print("=== Entraînement Prophet + Projections scénarios ===\n")

    # Données historiques
    hist_df = generate_historical_temperatures()
    hist_df = compute_deviation_from_baseline(hist_df)

    # Entraînement Prophet
    print("1. Entraînement du modèle Prophet...")
    prophet_df = prepare_data_for_prophet(hist_df)
    model = train_prophet_model(prophet_df)
    forecast = make_forecast(model, periods=80)
    print(f"   → Forecast Prophet : {len(forecast)} points")
    last_yr = forecast["year"].max()
    last_val = forecast[forecast["year"] == last_yr]["yhat"].values[0]
    print(f"   → Temp {last_yr} (Prophet brut) : {last_val:.2f}°C")

    # Projections par scénario
    print("\n2. Projections par scénario GIEC...")
    for scenario_name in SCENARIOS:
        proj = generate_scenario_projections(hist_df, scenario_name)

        # Année de franchissement +2°C
        crossing = compute_crossing_year(proj, threshold_anomaly=2.0)
        crossing_str = str(crossing) if crossing else "jamais"

        row_2050 = proj[proj["year"] == 2050].iloc[0]
        row_2100 = proj[proj["year"] == 2100].iloc[0]

        print(f"\n   {scenario_name}:")
        print(f"     2050 : {row_2050['temp_mean']}°C (anomalie +{row_2050['anomaly']}°C)")
        print(f"     2100 : {row_2100['temp_mean']}°C (anomalie +{row_2100['anomaly']}°C)")
        print(f"     Franchissement +2°C France : {crossing_str}")

    print("\n=== Terminé ===")
