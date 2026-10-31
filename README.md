# DAARA

**FR** — Plateforme de l'équipe de recherche DAARA (*Données, Apprentissage Automatique et Recherche en Afrique*) : catalogue et vitrine des publications, jeux de données, modèles, projets et formations, en partenariat avec des universités.
**EN** — Platform of the DAARA research team (*Data & AI Research Alliance for Africa*): catalogue and showcase of publications, datasets, models, projects and training, in partnership with universities.

Stack : Django 5.2 · PostgreSQL 16 · Tailwind CSS 4 · HTMX 2 · Docker Compose.

---

## Français

### Démarrer

Prérequis : Docker Desktop. Rien d'autre à installer sur le poste : Python, Node et PostgreSQL tournent dans des conteneurs.

```sh
docker compose up
```

Puis ouvrir http://localhost:8000 (redirige vers `/fr/` ou `/en/` selon le navigateur).

- `web` : Django (`runserver`), applique les migrations et compile les traductions au démarrage.
- `assets` : recompile Tailwind à chaque modification d'un gabarit ou d'une feuille de style.
- `db`, `redis` : PostgreSQL 16 et Redis 7.

Pour surcharger la configuration, copier `.env.example` en `.env`.

### Commandes utiles

```sh
docker compose run --rm web pytest                      # tests
docker compose run --rm --no-deps web ruff check .      # analyse statique
docker compose run --rm --no-deps web ruff format .     # formatage
docker compose run --rm web python manage.py createsuperuser
docker compose run --rm web python manage.py seed_demo  # comptes de démonstration
docker compose run --rm --no-deps web python manage.py makemessages -l fr -l en --ignore=node_modules --ignore=static --ignore=tests
```

Comptes de démonstration (`seed_demo`, mot de passe `daara-demo-2026`) : `awa` (doctorante), `moussa` (chercheur, responsable d'axe et éditeur), `fatou` (observatrice), `admin` (administratrice). Connexion sur http://localhost:8000/fr/account/login/.

Page de travail du logo (développement seulement) : http://localhost:8000/fr/dev/logo/

### Organisation

| Dossier | Contenu |
|---|---|
| `config/` | réglages (`base`, `dev`, `test`, `prod`), URL racines |
| `apps/` | une application par domaine : `core`, `members`, `research`, `projects`, `training`, `news`, `interop`, `dashboard` (chacune a son README) |
| `templates/`, `assets/`, `static/` | gabarits, sources CSS, fichiers statiques (`static/dist` est généré) |
| `locale/` | traductions de l'interface (`.po`) |
| `docs/` | documentation technique et notes de passation |
| `scripts/` | scripts d'outillage |
| `tests/` | tests `pytest` |

### Conventions

Branches `feat/`, `fix/`, `docs/`, `chore/` ; toute modification passe par une pull request relue. Messages de commit en anglais au format Conventional Commits. Aucun secret dans le dépôt. La CI (GitHub Actions) lance ruff, les tests et la construction de l'image de production.

---

## English

### Getting started

Requirement: Docker Desktop. Python, Node and PostgreSQL all run in containers.

```sh
docker compose up
```

Then open http://localhost:8000 (redirects to `/fr/` or `/en/` based on the browser language).

- `web`: Django (`runserver`); applies migrations and compiles translations on start.
- `assets`: rebuilds Tailwind whenever a template or stylesheet changes.
- `db`, `redis`: PostgreSQL 16 and Redis 7.

Copy `.env.example` to `.env` to override settings.

### Useful commands

```sh
docker compose run --rm web pytest
docker compose run --rm --no-deps web ruff check .
docker compose run --rm --no-deps web ruff format .
docker compose run --rm web python manage.py createsuperuser
```

### Conventions

Branches `feat/`, `fix/`, `docs/`, `chore/`; every change goes through a reviewed pull request. Commit messages in English, Conventional Commits format. No secrets in the repository. CI (GitHub Actions) runs ruff, the test suite and the production image build.
