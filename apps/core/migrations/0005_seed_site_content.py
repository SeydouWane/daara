"""Contenus de la vitrine jusqu'ici écrits dans les gabarits, désormais modifiables dans
l'administration : accroche de l'accueil, appel à rejoindre, objectifs à douze mois, cartes
de l'accueil, standards ouverts et étapes pour devenir partenaire. Textes FR / EN repris à
l'identique ; les coordonnées et réseaux restent à renseigner.
"""

from django.db import migrations

SETTINGS = {
    "tagline": ("Alliance de recherche en IA", "AI research alliance"),
    "hero_title": (
        "Données, Apprentissage Automatique et Recherche en Afrique",
        "Data & AI Research Alliance for Africa",
    ),
    "description": (
        "Publications, jeux de données, modèles et formations d'une équipe de chercheurs en "
        "intelligence artificielle, en partenariat avec des universités.",
        "Publications, datasets, models and training from a team of AI researchers working "
        "with partner universities.",
    ),
    "cta_title": ("Rejoindre DAARA", "Join DAARA"),
    "cta_text": (
        "Chercheur, doctorant ou institution : contribuez au catalogue de la recherche "
        "africaine en IA.",
        "Researcher, PhD student or institution: help build the catalogue of African AI "
        "research.",
    ),
    "goals_note": (
        "Et deux objectifs de plus : ouvrir les communautés de DAARA dans DICAMES, et faire "
        "moissonner la plateforme par OpenAIRE et BASE.",
        "And two further goals: open DAARA's communities in DICAMES, and have the platform "
        "harvested by OpenAIRE and BASE.",
    ),
}

FEATURES = [
    (
        "document",
        "research:publications",
        ("Publications", "Publications"),
        (
            "Articles, communications et thèses, importés par DOI et exportables en BibTeX.",
            "Articles, papers and theses, imported by DOI and exported to BibTeX.",
        ),
    ),
    (
        "database",
        "research:datasets",
        ("Jeux de données", "Datasets"),
        (
            "Corpus et données africaines déposés sur Zenodo, avec un DOI et une citation.",
            "African corpora and data deposited on Zenodo, with a DOI and a citation.",
        ),
    ),
    (
        "chip",
        "research:models",
        ("Modèles et code", "Models and code"),
        (
            "Modèles et démonstrateurs synchronisés depuis Hugging Face et GitHub.",
            "Models and demonstrators synchronised from Hugging Face and GitHub.",
        ),
    ),
    (
        "cap",
        "training:list",
        ("Formation", "Training"),
        (
            "Formations, webinaires archivés et supports de cours avec DOI.",
            "Courses, archived webinars and teaching materials with a DOI.",
        ),
    ),
]

STANDARDS = [
    (
        "DOI",
        (
            "Identifiant pérenne de chaque publication et de chaque jeu de données.",
            "Persistent identifier of every publication and dataset.",
        ),
    ),
    (
        "ORCID",
        (
            "Identifiant unique et durable de chaque chercheur.",
            "Unique, lasting identifier of every researcher.",
        ),
    ),
    (
        "OpenAlex",
        (
            "Base bibliographique ouverte qui sert à importer les publications.",
            "Open bibliographic database used to import publications.",
        ),
    ),
    (
        "OAI-PMH",
        (
            "Protocole par lequel OpenAIRE et BASE moissonneront le catalogue.",
            "Protocol through which OpenAIRE and BASE will harvest the catalogue.",
        ),
    ),
    (
        "JSON-LD",
        (
            "Données structurées lues par Google Dataset Search.",
            "Structured data read by Google Dataset Search.",
        ),
    ),
    (
        "Zenodo · Hugging Face",
        (
            "Là où sont déposés les jeux de données et les modèles.",
            "Where datasets and models are deposited.",
        ),
    ),
]

STEPS = [
    (
        ("Un chercheur membre le propose", "A member researcher proposes it"),
        (
            "Un chercheur de DAARA présente votre université ou votre laboratoire et ses "
            "travaux.",
            "A DAARA researcher presents your university or laboratory and its research.",
        ),
    ),
    (
        ("Un responsable d'axe le valide", "An axis lead approves it"),
        (
            "Le responsable de l'axe concerné vérifie l'adéquation avec les thèmes de recherche "
            "de DAARA.",
            "The lead of the axis concerned checks the fit with DAARA's research themes.",
        ),
    ),
    (
        ("Votre institution rejoint DAARA", "Your institution joins DAARA"),
        (
            "Elle est représentée au comité de pilotage et ses chercheurs publient leurs "
            "travaux sur la plateforme.",
            "It is represented on the steering committee and its researchers publish their "
            "work on the platform.",
        ),
    ),
]


def translated(**fields):
    """Champs traduits : colonne FR, colonne EN, et colonne d'origine en anglais (langue par
    défaut de modeltranslation)."""
    values = {}
    for name, (french, english) in fields.items():
        values.update({name: english, f"{name}_en": english, f"{name}_fr": french})
    return values


def seed(apps, schema_editor):
    SiteSettings = apps.get_model("core", "SiteSettings")
    HomeFeature = apps.get_model("core", "HomeFeature")
    Standard = apps.get_model("core", "Standard")
    PartnershipStep = apps.get_model("core", "PartnershipStep")

    SiteSettings.objects.update_or_create(pk=1, defaults=translated(**SETTINGS))
    for order, (icon, destination, title, text) in enumerate(FEATURES):
        HomeFeature.objects.create(
            order=order, icon=icon, destination=destination, **translated(title=title, text=text)
        )
    for order, (name, description) in enumerate(STANDARDS):
        Standard.objects.create(order=order, name=name, **translated(description=description))
    for order, (title, text) in enumerate(STEPS):
        PartnershipStep.objects.create(order=order, **translated(title=title, text=text))


def unseed(apps, schema_editor):
    for model in ("SiteSettings", "HomeFeature", "Standard", "PartnershipStep"):
        apps.get_model("core", model).objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0004_site_content")]

    operations = [migrations.RunPython(seed, unseed)]
