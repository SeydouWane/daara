"""Pages éditoriales de départ, en français et en anglais.

Textes tirés de la documentation de la plateforme, à relire et compléter par l'éditeur dans
l'administration. Les mentions légales et la politique de confidentialité restent en brouillon :
elles attendent des informations à trancher au lot 0 (éditeur juridique, hébergeur).
"""

from django.db import migrations

ABOUT_FR = """DAARA — *Données, Apprentissage Automatique et Recherche en Afrique* — est le catalogue et la vitrine des productions d'une équipe de chercheurs en intelligence artificielle et en science des données, appliquées à des problématiques africaines.

## Ce que vous trouverez ici

- des **publications scientifiques**, avec leurs DOI et leurs versions en accès ouvert ;
- des **jeux de données**, notamment des corpus en langues africaines ;
- des **modèles et du code**, publiés sur Hugging Face et GitHub ;
- des **projets de recherche** et leurs partenaires ;
- des **formations et des webinaires** archivés.

## Nos principes

1. **Des métadonnées, pas des téraoctets.** Les corpus et les modèles sont déposés sur Zenodo et Hugging Face ; DAARA en est le catalogue enrichi.
2. **Multilingue par conception.** Français et anglais aujourd'hui, ouvert aux langues africaines demain.
3. **Aucune saisie redondante.** Un DOI suffit à remplir une fiche.
4. **Utilisable à 1 Mbit/s et sur mobile.** La légèreté est une contrainte de conception, pas une optimisation tardive.
5. **Interopérable ou invisible.** DOI, ORCID, OAI-PMH et JSON-LD rendent nos travaux visibles des moteurs académiques du monde entier.
"""

ABOUT_EN = """DAARA — *Data & AI Research Alliance for Africa* — is the catalogue and showcase of the work of a team of researchers in artificial intelligence and data science, applied to African challenges.

## What you will find here

- **scientific publications**, with their DOIs and open access versions;
- **datasets**, including corpora in African languages;
- **models and code**, published on Hugging Face and GitHub;
- **research projects** and their partners;
- archived **training courses and webinars**.

## Our principles

1. **Metadata, not terabytes.** Corpora and models are deposited on Zenodo and Hugging Face; DAARA is their enriched catalogue.
2. **Multilingual by design.** French and English today, open to African languages tomorrow.
3. **No redundant data entry.** A DOI is enough to fill in a record.
4. **Usable at 1 Mbit/s and on mobile.** Lightness is a design constraint, not a late optimisation.
5. **Interoperable or invisible.** DOI, ORCID, OAI-PMH and JSON-LD make our work visible to academic search engines worldwide.
"""

GOVERNANCE_FR = """La règle structurante de DAARA est l'équilibre entre partenaires : aucune décision, aucun compte et aucun actif ne dépend d'une seule université ni d'une seule personne.

## Instances

| Instance | Composition | Fréquence | Rôle |
|---|---|---|---|
| Comité de pilotage | Professeurs titulaires des universités partenaires | Trimestrielle | Oriente, arbitre le périmètre, valide le budget |
| Comité technique | Chef de projet, lead technique, responsable données, responsable éditorial | Mensuelle | Suit l'avancement, tranche les choix techniques |
| Assemblée des membres | Tous les membres | Annuelle | Valide le rapport d'activité, élit les responsables d'axe |
| Responsables d'axe | Un par axe thématique | Continue | Valident les contenus de leur axe, animent leurs membres |

## Règles de décision

- Les décisions courantes se prennent en comité technique, à la majorité simple.
- Les décisions qui engagent le périmètre, le budget ou l'image de DAARA relèvent du comité de pilotage.
- Un désaccord persistant entre universités partenaires conduit à reporter la décision, jamais à la trancher par un vote majoritaire.
- L'adhésion d'un nouveau membre ou d'un partenaire est proposée par un chercheur et validée par un responsable d'axe.

## Propriété intellectuelle

Les droits moraux restent aux auteurs ; DAARA obtient une licence non exclusive de diffusion lors du dépôt. Les contenus éditoriaux du site sont publiés sous licence CC BY 4.0.
"""

GOVERNANCE_EN = """DAARA's founding rule is balance between partners: no decision, account or asset depends on a single university or a single person.

## Bodies

| Body | Members | Frequency | Role |
|---|---|---|---|
| Steering committee | Full professors from the partner universities | Quarterly | Sets the direction, arbitrates the scope, approves the budget |
| Technical committee | Project manager, technical lead, data manager, editorial manager | Monthly | Monitors progress, settles technical choices |
| General assembly | All members | Yearly | Approves the activity report, elects the axis leads |
| Axis leads | One per research axis | Ongoing | Validate the contents of their axis, lead its members |

## Decision rules

- Day-to-day decisions are taken by the technical committee, by simple majority.
- Decisions affecting DAARA's scope, budget or image belong to the steering committee.
- A lasting disagreement between partner universities postpones the decision; it is never settled by a majority vote.
- A new member or partner is proposed by a researcher and approved by an axis lead.

## Intellectual property

Moral rights remain with the authors; DAARA receives a non-exclusive licence to disseminate on deposit. The site's editorial content is published under the CC BY 4.0 licence.
"""

PARTNERS_FR = """Les membres de DAARA sont rattachés à des universités et des organismes de recherche partenaires. Chaque institution partenaire est représentée dans les instances de gouvernance, et la plateforme suit l'équilibre des contributions entre institutions.

Votre université ou votre laboratoire souhaite rejoindre DAARA ? Un chercheur membre propose le partenariat, un responsable d'axe le valide.
"""

PARTNERS_EN = """DAARA members belong to partner universities and research organisations. Each partner institution is represented in the governance bodies, and the platform monitors the balance of contributions between institutions.

Would your university or laboratory like to join DAARA? A member researcher proposes the partnership and an axis lead approves it.
"""

CONTACT_FR = """Une question sur nos publications, nos jeux de données, nos formations ou un partenariat ? Écrivez à l'équipe DAARA.

L'adresse de contact de l'organisation sera publiée sur cette page à l'ouverture de la plateforme.
"""

CONTACT_EN = """A question about our publications, datasets, training courses or a partnership? Write to the DAARA team.

The organisation's contact address will be published on this page when the platform opens.
"""

LEGAL_FR = """## Éditeur

*À compléter : institution qui porte juridiquement DAARA (question ouverte du lot 0).*

## Hébergement

*À compléter après le choix de l'hébergeur.*

## Licence des contenus

Sauf mention contraire, les contenus éditoriaux de ce site sont publiés sous licence [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.fr). Les droits moraux restent aux auteurs.
"""

LEGAL_EN = """## Publisher

*To be completed: institution legally responsible for DAARA (open question of phase 0).*

## Hosting

*To be completed once the host is chosen.*

## Content licence

Unless stated otherwise, the editorial content of this site is published under the [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) licence. Moral rights remain with the authors.
"""

PRIVACY_FR = """## Responsable du traitement

*À compléter.* Les formalités auprès de la Commission de protection des données personnelles du Sénégal sont en cours d'instruction.

## Données traitées

- Comptes des membres : nom, adresse électronique, identifiant ORCID, rattachements.
- Inscriptions aux formations : données d'identification et de participation, conservées trois ans après la dernière formation.
- Lettre d'information : adresse électronique, avec un consentement explicite et traçable.

## Mesure d'audience

DAARA utilise un outil de mesure respectueux de la vie privée, sans service publicitaire.

## Vos droits

Vous disposez d'un droit d'accès, de rectification et d'effacement de vos données. Nous répondons à toute demande dans un délai d'un mois.
"""

PRIVACY_EN = """## Data controller

*To be completed.* Formalities with Senegal's personal data protection authority are under way.

## Data processed

- Member accounts: name, email address, ORCID iD, affiliations.
- Training registrations: identification and attendance data, kept for three years after the last course.
- Newsletter: email address, with explicit and traceable consent.

## Audience measurement

DAARA uses a privacy-friendly analytics tool, never an advertising service.

## Your rights

You have the right to access, correct and delete your data. We answer every request within one month.
"""

PAGES = [
    {
        "slug": "about",
        "status": "published",
        "title": ("Mission et axes", "Mission and research axes"),
        "summary": (
            "DAARA rassemble et rend visibles les productions d'une équipe de chercheurs en "
            "intelligence artificielle, en partenariat avec des universités.",
            "DAARA gathers and showcases the work of a team of artificial intelligence "
            "researchers, in partnership with universities.",
        ),
        "body": (ABOUT_FR, ABOUT_EN),
    },
    {
        "slug": "governance",
        "status": "published",
        "title": ("Gouvernance", "Governance"),
        "summary": (
            "Aucune décision, aucun compte et aucun actif de DAARA ne dépend d'une seule "
            "université ni d'une seule personne.",
            "No decision, account or asset of DAARA depends on a single university or a "
            "single person.",
        ),
        "body": (GOVERNANCE_FR, GOVERNANCE_EN),
    },
    {
        "slug": "partners",
        "status": "published",
        "title": ("Partenaires", "Partners"),
        "summary": (
            "DAARA travaille avec des universités et des organismes de recherche partenaires.",
            "DAARA works with partner universities and research organisations.",
        ),
        "body": (PARTNERS_FR, PARTNERS_EN),
    },
    {
        "slug": "contact",
        "status": "published",
        "title": ("Contact", "Contact"),
        "summary": ("Écrire à l'équipe DAARA.", "Write to the DAARA team."),
        "body": (CONTACT_FR, CONTACT_EN),
    },
    {
        "slug": "legal-notice",
        "status": "draft",
        "title": ("Mentions légales", "Legal notice"),
        "summary": ("", ""),
        "body": (LEGAL_FR, LEGAL_EN),
    },
    {
        "slug": "privacy",
        "status": "draft",
        "title": ("Politique de confidentialité", "Privacy policy"),
        "summary": ("", ""),
        "body": (PRIVACY_FR, PRIVACY_EN),
    },
]


def create_pages(apps, schema_editor):
    Page = apps.get_model("core", "Page")
    for spec in PAGES:
        fields = {"status": spec["status"]}
        for name in ("title", "summary", "body"):
            french, english = spec[name]
            # Le champ d'origine porte la langue par défaut (anglais).
            fields.update({name: english, f"{name}_fr": french, f"{name}_en": english})
        Page.objects.update_or_create(slug=spec["slug"], defaults=fields)


def delete_pages(apps, schema_editor):
    apps.get_model("core", "Page").objects.filter(
        slug__in=[spec["slug"] for spec in PAGES]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]

    operations = [migrations.RunPython(create_pages, delete_pages)]
