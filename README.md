# JBI One

JBI One is a Flask-based web dashboard for tracking jobs, commissions, sales teams, and engineering tasks for the JBI Job Management System. It combines a MySQL-backed data model with responsive HTML templates and reusable static assets so that sales and operations teams can review project pipelines and keep supporting data in sync.

## Key features

- **Job index and filtering** – Quickly search projects by project name, account, contractor, market, or JBI number from the landing page, with aggregate totals calculated for purchase amounts and commissions.
- **Detailed job views** – Inspect or edit a job, including project metadata, sales assignments, engineering contacts, commission schedules, and Judy task checklists. Each detail view reuses the same SQLAlchemy models to hydrate templates across read-only and edit modes.
- **Commission and task management** – Add commission disbursement lines, mark Judy tasks complete or incomplete, and synchronize totals so the finance team can reconcile payouts accurately.
- **Reusable layout** – Shared navigation, toolbar, and footer partials along with Sass-driven styles ensure a consistent experience across pages.

## Repository layout

| Path | Purpose |
| ---- | ------- |
| `app.py` | Flask application, SQLAlchemy models, and HTTP routes for jobs, engineers, commissions, and Judy tasks. |
| `templates/` | Jinja templates for dashboards, edit forms, and shared partials. |
| `static/` | Compiled CSS/JS assets plus Sass sources and fonts that power the front-end theme. |
| `requirements.txt` | Python dependencies needed by the web server. |
| `Dockerfile` / `docker-compose.yml` | Container definition and compose configuration for running the app with Docker. |
| `Procfile` | Declares the production command (`python app.py`) for Heroku-style deployments. |

## Prerequisites

- Python 3.11+ with `pip`
- A MySQL-compatible database that exposes the tables referenced in `app.py`
- Optional: Docker Desktop (if you prefer to use `docker compose`)

## Configuration

The application expects credentials and secrets to live in a **`config.py`** module placed at the repository root. This file is intentionally excluded from source control for security reasons. Create it manually before running the application:

```python
# config.py
mysql_username = "your_db_user"
mysql_password = "your_db_password"
mysql_host = "127.0.0.1"
mysql_port = 3306
mysql_dbname = "jbi"
```

You can also provide the same values via environment variables when running inside Docker:

```env
MYSQL_USERNAME=your_db_user
MYSQL_PASSWORD=your_db_password
MYSQL_HOST=your_db_host
MYSQL_PORT=3306
MYSQL_DBNAME=jbi
```

Set `FLASK_DEBUG=true` during development for auto-reloads and verbose error output.

## Local development

1. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Create `config.py`** using the template above.
3. **Run database migrations or import data** so the tables referenced by the SQLAlchemy models exist.
4. **Launch the Flask server**
   ```bash
   python app.py
   ```
   By default the app listens on `http://127.0.0.1:38291` (or `0.0.0.0` if `DOCKER_ENV` is set).

When the server is running, browse to `/` to reach the job index. Navigation links lead to detailed job, engineer, sales, and commission views.

## Running with Docker

1. Create `config.py` locally (the app still imports it even when containerized).
2. Export the database environment variables or place them in a `.env` file.
3. Build and start the service:
   ```bash
   docker compose up --build
   ```
   The service binds to port `38291` on your host machine as configured in `docker-compose.yml`.

## Styling workflow

All theme styles originate in `static/sass/` and are compiled into `static/css/`. If you update Sass partials, ensure you recompile them using your preferred Sass toolchain before committing the generated CSS.

## Deployment considerations

- The production command is `python app.py`, as reflected in both the `Procfile` and Docker configuration.
- Ensure the deployment environment provides the same database credentials as the local `config.py`.
- Configure logging destinations if you need more than the default STDOUT logging defined in `app.py`.

## Troubleshooting

| Symptom | Possible cause |
| ------- | -------------- |
| `ModuleNotFoundError: No module named 'config'` | `config.py` is missing from the project root. Create it using the template above. |
| `pymysql.err.OperationalError` on startup | Database credentials in `config.py` or environment variables are incorrect, or the database host is unreachable. |
| CSS or JS not updating | Recompile Sass or clear browser cache to load the latest assets from `static/`. |

## License

This repository does not include explicit licensing information. Contact the project maintainers before redistributing or deploying it publicly.
