"""
Export PDF du bilan territorial — livrable citoyen.

Génère un rapport synthétique avec :
- Identité territoriale (région, scénario, horizon)
- Projections climatiques
- 3 fiches d'action (Agriculture, Santé/Urbanisme, Économie)
- Métriques coût/investissement
"""

from fpdf import FPDF
from datetime import datetime


def _sanitize(text: str) -> str:
    """Remplace les caractères Unicode non-latin1 pour compatibilité FPDF."""
    replacements = {
        "\u2014": "-",   # em dash
        "\u2013": "-",   # en dash
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2026": "...", # ellipsis
        "\u2022": "-",   # bullet
        "\u20ac": "E",   # euro sign
        "\u2192": "->",  # arrow
        "\u2248": "~",   # approximately
        "\u2265": ">=",  # greater or equal
        "\u2264": "<=",  # less or equal
        "\u00b2": "2",   # superscript 2
        "\u2082": "2",   # subscript 2 (CO2)
        "\u2083": "3",   # subscript 3
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Fallback: encode to latin-1, replacing anything that doesn't fit
    text = text.encode("latin-1", errors="replace").decode("latin-1")
    return text


class BilanTerritorialPDF(FPDF):
    """PDF personnalisé pour le bilan territorial ClimaVision."""

    def cell(self, *args, **kwargs):
        # Sanitize text arguments
        args = list(args)
        if len(args) >= 3 and isinstance(args[2], str):
            args[2] = _sanitize(args[2])
        if "text" in kwargs and isinstance(kwargs["text"], str):
            kwargs["text"] = _sanitize(kwargs["text"])
        return super().cell(*args, **kwargs)

    def multi_cell(self, *args, **kwargs):
        args = list(args)
        if len(args) >= 3 and isinstance(args[2], str):
            args[2] = _sanitize(args[2])
        if "text" in kwargs and isinstance(kwargs["text"], str):
            kwargs["text"] = _sanitize(kwargs["text"])
        return super().multi_cell(*args, **kwargs)

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "ClimaVision France — Bilan Territorial", align="L")
        self.cell(0, 8, f"Généré le {datetime.now().strftime('%d/%m/%Y')}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(46, 204, 113)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(
            0, 10,
            f"Sources : PNACC-3, HCC 2025, France Stratégie, GIEC AR6 — Page {self.page_no()}/{{nb}}",
            align="C",
        )

    def section_title(self, title, color=(44, 62, 80)):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*color)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def subsection_title(self, title, color=(52, 73, 94)):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*color)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(60, 60, 60)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def bullet_point(self, text):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(60, 60, 60)
        x = self.get_x()
        self.cell(8, 5, "  - ", new_x="END")
        self.multi_cell(0, 5, _sanitize(text))
        self.set_x(x)

    def metric_box(self, label, value, unit="", color=(41, 128, 185)):
        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 18)

        x = self.get_x()
        y = self.get_y()
        box_w = 58
        box_h = 22

        self.rect(x, y, box_w, box_h, "F")
        self.set_xy(x, y + 3)
        self.cell(box_w, 8, f"{value}{unit}", align="C")
        self.set_font("Helvetica", "", 8)
        self.set_xy(x, y + 12)
        self.cell(box_w, 6, label, align="C")

        self.set_xy(x + box_w + 4, y)
        self.set_text_color(60, 60, 60)


def generate_bilan_pdf(recommendations: dict, user_age: int = None) -> bytes:
    """
    Génère le PDF du bilan territorial.

    Args:
        recommendations: Dict issu de resilience_engine.generate_recommendations()
        user_age: Âge de l'utilisateur (optionnel, pour le simulateur)

    Returns:
        Contenu PDF en bytes
    """
    pdf = BilanTerritorialPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    region = recommendations["region"]
    scenario = recommendations["scenario"]
    year = recommendations["target_year"]
    anomaly = recommendations["anomaly_regional"]
    temp_proj = recommendations["temp_projected"]
    severity = recommendations["severity"]
    metriques = recommendations["metriques"]

    # ── Titre ──
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 15, f"Bilan Territorial — {region}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # ── Contexte ──
    severity_labels = {"faible": "Modéré", "moyen": "Élevé", "fort": "Critique"}
    pdf.body_text(
        f"Scénario : {scenario}\n"
        f"Horizon : {year}\n"
        f"Niveau d'alerte : {severity_labels.get(severity, severity)}"
    )

    # ── Message personnalisé ──
    if user_age:
        age_target = user_age + (year - 2026)
        pdf.body_text(
            f"En {year}, vous aurez {age_target} ans. "
            f"Dans votre région, la température moyenne sera d'environ {temp_proj} °C, "
            f"soit une anomalie de +{anomaly} °C par rapport à l'ère préindustrielle."
        )

    # ── Métriques KPI ──
    pdf.ln(2)
    start_x = 15
    pdf.set_xy(start_x, pdf.get_y())
    pdf.metric_box("Anomalie régionale", f"+{anomaly}", " °C", (231, 76, 60))
    pdf.metric_box("Temp. projetée", f"{temp_proj}", " °C", (243, 156, 18))
    pdf.metric_box("Coût inaction", f"{metriques['cout_inaction_regional_mds']}", " Mds€", (192, 57, 43))
    pdf.ln(28)

    # ── Fiches d'action ──
    fiches = recommendations["fiches"]

    fiche_configs = [
        ("agriculture", "Agriculture & Eau", (39, 174, 96)),
        ("sante_urbanisme", "Santé & Urbanisme", (41, 128, 185)),
        ("economie", "Économie & Investissement", (142, 68, 173)),
    ]

    for key, title, color in fiche_configs:
        fiche = fiches[key]
        pdf.section_title(f"{title}", color)
        pdf.subsection_title(fiche["titre"])
        pdf.body_text(
            f"Investissement estimé : {fiche['investissement_mds']} Mds€ (national) — "
            f"Horizon : {fiche['horizon']}"
        )

        pdf.subsection_title("Actions prioritaires :")
        for action in fiche["actions"]:
            pdf.bullet_point(action)
        pdf.ln(3)

        if key == "economie" and "ratio_benefice" in fiche:
            pdf.body_text(
                f"Ratio bénéfice/coût : 1€ investi = {fiche['ratio_benefice']}€ de dégâts évités "
                f"(source : France Stratégie, valeur de l'action pour le climat)"
            )

    # ── Synthèse investissement ──
    pdf.add_page()
    pdf.section_title("Synthèse financière")

    pdf.body_text(
        f"Pour la région {region}, sous le scénario {scenario} à l'horizon {year} :"
    )

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)

    data = [
        ("Coût de l'inaction (dégâts/an)", f"{metriques['cout_inaction_regional_mds']} Mds€"),
        ("Investissement adaptation nécessaire", f"{metriques['investissement_regional_mds']} Mds€"),
        ("Dégâts évités par l'investissement", f"{metriques['degats_evites_mds']} Mds€"),
        ("Ratio bénéfice/coût", f"1€ → {metriques['ratio_benefice']}€ évités"),
    ]

    pdf.set_fill_color(240, 240, 240)
    for i, (label, value) in enumerate(data):
        fill = i % 2 == 0
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(120, 8, f"  {label}", border=0, fill=fill)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 8, value, border=0, fill=fill, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)
    pdf.body_text(
        "Ces estimations s'appuient sur le rapport France Stratégie "
        "\"La valeur de l'action pour le climat\" (mars 2025) et le rapport "
        "annuel 2025 du Haut Conseil pour le Climat."
    )

    # ── Mesures PNACC-3 référencées ──
    pdf.section_title("Mesures PNACC-3 mobilisées")
    all_mesures = set()
    for fiche in fiches.values():
        all_mesures.update(fiche["mesures_pnacc3"])

    for num in sorted(all_mesures):
        pdf.bullet_point(f"Mesure {num} du Plan National d'Adaptation au Changement Climatique (PNACC-3)")

    pdf.ln(6)
    pdf.body_text(
        "Ce bilan est généré par ClimaVision France dans le cadre du "
        "Hackathon #26 Big Data & IA — Changement Climatique. "
        "Les données sont issues de sources institutionnelles : "
        "GIEC AR6, HCC 2025, PNACC-3, France Stratégie, Météo France."
    )

    return bytes(pdf.output())
