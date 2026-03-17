# ClimaVision France — Guide de Pitch (3 minutes)

## La phrase d'accroche (Hook)

> "En 2050, vous aurez [âge] ans. Dans votre région, il fera en moyenne [X]°C.
> Ne rien faire coûtera [Y] milliards d'euros par an à la France.
> Mais chaque euro investi aujourd'hui en évite 4 de dégâts.
> ClimaVision transforme les données climatiques en actions concrètes pour chaque territoire."

---

## Scénario de démo idéal (3 minutes)

### Minute 1 — Le constat global (30s sidebar + 30s tab 1)

1. **Ouvrir le dashboard** — Montrer les 4 KPIs en haut : température actuelle, projection 2050, projection 2100, année de bascule +2°C
2. **Sidebar "En résumé"** — Pointer les 3 chiffres chocs : année de bascule, coût de l'inaction d'ici 2050, nombre de mesures PNACC-3 activables
3. **Tab "Températures"** — Montrer les 3 courbes de scénarios avec les zones d'incertitude. Dire : *"Voici ce que dit la science : entre +2.1°C et +6.6°C pour la France selon nos choix collectifs."*
4. **Switcher le scénario** dans la sidebar (de Intermédiaire à Pessimiste) — les courbes et chiffres se mettent à jour en temps réel

### Minute 2 — L'impact territorial (30s tab 2 + 30s tab 3)

5. **Tab "Carte régionale"** — Montrer la carte choroplèthe de France, survol de PACA (zone la plus touchée, +20% d'amplification). Dire : *"Toutes les régions ne sont pas égales face au climat."*
6. **Slider année** — Glisser de 2050 à 2100, montrer l'aggravation progressive des couleurs
7. **Tab "Émissions GES"** — Montrer rapidement la répartition par secteur : *"Les transports = 31% des émissions. C'est le premier levier."* Montrer la trajectoire de décarbonation : *"On doit passer de 406 à 80 Mt éqCO2 d'ici 2050."*

### Minute 3 — L'action locale (tab 5 Simulateur)

8. **Cliquer "Nice — Canicule & littoral"** (bouton Exemple Rapide) — le simulateur se pré-remplit
9. **Montrer le message personnalisé** : *"En 2050, vous aurez 54 ans. À Nice, il fera X°C."*
10. **Montrer les 3 fiches d'action** : Agriculture, Santé/Urbanisme, Économie — toutes sourcées PNACC-3
11. **Montrer le graphique coût-bénéfice** : *"1€ investi = 4€ de dégâts évités. L'adaptation est rentable."*
12. **Cliquer "Télécharger le bilan PDF"** — Dire : *"Chaque citoyen repart avec un livrable actionnable pour son territoire."*

**Phrase de clôture** : *"ClimaVision, c'est la data climatique au service de l'action locale. Du constat global à la recommandation personnalisée, en un clic."*

---

## 3 Questions techniques "pièges" et réponses

### 1. "D'où vient le ratio coût/bénéfice de 1€ = 3.5-5€ ?"

**Source** : Rapport France Stratégie, *"La valeur de l'action pour le climat"* (mars 2025, Annexe 1 du hackathon).

- Le rapport établit une **valeur tutélaire du carbone** : 250 €/tCO2 en 2030, montant à 500-800 €/tCO2 en 2050
- Les ratios bénéfice/coût proviennent de l'analyse croisée entre le coût des dégâts climatiques (inondations 2023-2024 : 520-615 M€ selon le HCC) et le coût des mesures d'adaptation du PNACC-3
- **Chiffre clé à citer** : le HCC estime que les inondations de l'hiver 2023-2024 ont coûté 520 à 615 M€. L'adaptation aurait réduit ces coûts de 60-80%

### 2. "Comment sont calibrées vos projections ? Ce sont de vraies données ?"

**Réponse** :
- Les **données historiques** (1900-2024) sont calibrées sur les observations Météo France. Le chiffre de **+2.2°C de réchauffement observé en France** est issu du rapport HCC 2025 (Annexe 6)
- Le modèle **Prophet** (Facebook/Meta) est entraîné sur cette série temporelle pour capturer la tendance
- Les **projections futures** sont alignées sur les 3 scénarios SSP du GIEC AR6 : SSP1-1.9 (+1.4°C mondial), SSP2-4.5 (+2.7°C), SSP5-8.5 (+4.4°C)
- Le **facteur d'amplification France = 1.5x** est documenté par le HCC 2025 et le programme TRACC (Trajectoires de Réchauffement Adaptées au Changement Climatique)
- Les **amplifications régionales** (PACA +20%, Bretagne -15%) proviennent des données DRIAS de Météo France
- **Chiffre clé à citer** : *"Le GIEC confirme que la France se réchauffe 50% plus vite que la moyenne mondiale. C'est un fait établi, pas une projection."*

### 3. "Quelles sont les 51 mesures du PNACC-3 que vous utilisez ?"

**Réponse** :
- Le PNACC-3 (Plan National d'Adaptation au Changement Climatique, 3ème version, Annexe 5) contient **51 mesures** réparties en 5 axes
- Notre moteur de recommandations mobilise **19 mesures distinctes** selon 3 niveaux de sévérité (modéré, élevé, critique)
- Exemples concrets :
  - **Mesure 9** : Adapter les logements au risque chaleur
  - **Mesure 13** : Végétaliser les espaces urbains (îlots de fraîcheur)
  - **Mesure 21** : Préserver la ressource en eau (Plan Eau)
  - **Mesure 27** : Intégrer le risque climatique dans les financements publics
  - **Mesure 1** : Renforcer le Fonds Barnier pour la prévention
- Les mesures sont **graduées** : on n'active pas les mêmes actions pour +2°C et pour +5°C
- **Chiffre clé à citer** : *"19 mesures activables immédiatement parmi les 51 du PNACC-3, priorisées par notre IA selon le territoire et le scénario."*

---

## Récapitulatif des sources institutionnelles

| Source | Contenu clé | Annexe |
|--------|-------------|--------|
| France Stratégie | Valeur carbone 250-800 €/tCO2, ratio coût/bénéfice | Annexe 1 |
| GIEC AR6 | 3 scénarios SSP, budgets carbone, seuils | Annexe 4 |
| Earth Action Report 2025 | 5 priorités mondiales, Tipping Points | Annexe 3 |
| PNACC-3 | 51 mesures d'adaptation, 5 axes | Annexe 5 |
| HCC 2025 | +2.2°C France, 406 Mt éqCO2/an, coûts inondations | Annexe 6 |
| DRIAS / Météo France | Amplifications régionales, données historiques | Données |
| CITEPA | Émissions GES par secteur et par gaz | Annexe 2 |

---

## Tips pour la démo

- **Commencer par le Pessimiste** (SSP5-8.5) pour l'impact émotionnel, puis switcher vers l'Intermédiaire pour montrer que les choix comptent
- **Utiliser le bouton "Nice — Canicule"** comme exemple : tout le monde connaît la Côte d'Azur
- **Ouvrir le PDF téléchargé** à la fin pour montrer la qualité du livrable citoyen
- **Toujours citer les sources** : "selon le HCC", "d'après France Stratégie", "conformément au PNACC-3"
- En cas de question sur la fiabilité des données : *"Toutes nos sources sont institutionnelles et publiques : GIEC, HCC, France Stratégie, Météo France"*
