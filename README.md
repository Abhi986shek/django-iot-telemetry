# Industrial IoT Telemetry Analytics Platform

A production-grade web application built with **Django** for ingesting, processing, and visualizing time-series telemetry data from industrial machine sensor nodes. The platform provides an authenticated dashboard, a flexible ETL data pipeline that handles multiple sensor data formats, advanced analytics engines, SAML 2.0 Single Sign-On (SSO) support, and a secured administration API.

---

## Table of Contents

1. [What is Django?](#what-is-django)
2. [Architecture Overview](#architecture-overview)
3. [Project Structure](#project-structure)
4. [Prerequisites](#prerequisites)
5. [Installation & Local Setup](#installation--local-setup)
6. [Running the Application](#running-the-application)
7. [Configuring SAML Single Sign-On (SSO)](#configuring-saml-single-sign-on-sso)
8. [Connecting PostgreSQL](#connecting-postgresql)
9. [API Endpoints](#api-endpoints)
10. [Supported Telemetry Formats](#supported-telemetry-formats)
11. [Environment Variables Reference](#environment-variables-reference)
12. [Deployment Notes](#deployment-notes)
13. [License](#license)

---

## What is Django?

[Django](https://www.djangoproject.com/) is a high-level Python web framework that encourages rapid development and clean, pragmatic design. It follows the **Model-View-Template (MVT)** pattern and comes with a built-in ORM, authentication system, admin interface, URL routing, and a robust middleware stack.

This project uses Django as the backbone of the backend API and dashboard, with a strictly decoupled frontend layer (HTML templates + CSS/JS) to keep presentation concerns separate from business logic.

---

## Architecture Overview

This platform follows a clean **Controller → Service → Repository** architecture:

| Layer | Role |
|---|---|
| **Controllers** (`controllers/`) | Accept HTTP requests, validate inputs, return responses. No business logic. |
| **Services** (`services/`) | All business logic, ETL processing, analytics algorithms. No HTTP or ORM code. |
| **Repositories** (`repositories/`) | All database read queries via Django ORM. Isolated from views and services. |
| **Models** (`models.py`) | Django ORM schema definitions for the database tables. |
| **Authentication** (`authentication/`) | Handles local login, logout, and SAML 2.0 SSO integration. |
| **Frontend** (`frontend/`) | Decoupled HTML templates and static assets (CSS/JS). |

---

## Project Structure

```
EnterpriseTelemetry/
├── manage.py                        # Django CLI entry point
├── requirements.txt                 # Python package dependencies
├── .env.example                     # Environment variable template
├── .gitignore
├── README.md
│
├── backend/
│   ├── core/
│   │   ├── settings.py              # Django configuration (DB, auth, static files, logging)
│   │   ├── urls.py                  # Root URL router
│   │   └── wsgi.py                  # WSGI entry point for production servers
│   │
│   ├── telemetry_app/
│   │   ├── models.py                # ORM: MachineNode, TelemetryRecord, IngestionLog
│   │   ├── urls.py                  # App-level URL routing (8 endpoints)
│   │   ├── apps.py                  # Django app configuration
│   │   │
│   │   ├── controllers/             # HTTP layer — routing and response only
│   │   │   ├── __init__.py
│   │   │   ├── dashboard.py         # Dashboard view, machine list API, telemetry data API
│   │   │   ├── ingestion.py         # File upload view, JSON ingestion API endpoint
│   │   │   └── administration.py    # Ingestion audit logs, secure purge endpoint
│   │   │
│   │   ├── services/                # Business logic — no Django HTTP or ORM code
│   │   │   ├── __init__.py
│   │   │   ├── etl_service.py       # File validation, column mapping, bulk DB persistence
│   │   │   └── analytics_service.py # Stress, thermal, vibration, lifecycle algorithms
│   │   │
│   │   └── repositories/            # Read-only database query layer
│   │       ├── __init__.py
│   │       └── telemetry_repository.py  # All ORM SELECT queries for controllers
│   │
│   └── authentication/
│       ├── apps.py
│       ├── views.py                 # Login, logout, SAML ACS handler, metadata endpoint
│       ├── urls.py                  # Auth URL routing
│       └── saml/
│           ├── settings.json        # SAML SP and IdP configuration
│           └── README.txt           # Certificate generation instructions
│
└── frontend/
    ├── templates/
    │   ├── base.html                # Shared layout with navigation bar
    │   ├── login.html               # Login form with SSO button
    │   ├── dashboard.html           # Main analytics dashboard
    │   └── upload.html              # File upload interface
    └── static/
        ├── css/
        │   └── main.css             # Full dark-theme responsive stylesheet
        └── js/
            └── dashboard.js         # Machine table rendering, chart engine, API calls
```

---

## Prerequisites

- **Python 3.9 or higher** — [Download](https://www.python.org/downloads/)
- **pip** — Comes bundled with Python
- **Git** — [Download](https://git-scm.com/)
- **PostgreSQL 14+** *(optional for local dev — SQLite is used automatically if not configured)*

---

## Installation & Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/EnterpriseTelemetry.git
cd EnterpriseTelemetry
```

### 2. Create and activate a virtual environment

```bash
# Create the virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and set your values:

```env
SECRET_KEY=your-random-secret-key-here
DEBUG=True
DB_PASSWORD=        # Leave blank to use SQLite locally
DELETE_PASSWORD=your-chosen-admin-password
```

> **SQLite fallback**: If `DB_PASSWORD` is not set, the application automatically uses a local SQLite database file (`db.sqlite3`). This is suitable for development only.

### 5. Apply database migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create an admin user

```bash
python manage.py createsuperuser
```

Follow the prompts to set a username and password.

---

## Running the Application

```bash
python manage.py runserver
```

The application will be available at: **http://127.0.0.1:8000/**

You will be redirected to the login page at `/auth/login/`. Sign in with the superuser credentials you created above.

To stop the server, press `CTRL + C` in the terminal.

---

## Configuring SAML Single Sign-On (SSO)

**What is SAML?**
SAML (Security Assertion Markup Language) is an open standard that allows an Identity Provider (IdP) — such as Microsoft Azure AD, Okta, Google Workspace, or any corporate SSO system — to authenticate users on behalf of your application. Instead of managing passwords locally, users log in through their organization's existing identity system.

### Step 1 — Generate SP Certificates

Your application acts as a **Service Provider (SP)**. It needs a certificate/key pair to sign and encrypt SAML messages.

```bash
openssl req -x509 -newkey rsa:2048 \
  -keyout backend/authentication/saml/sp-private-key.pem \
  -out backend/authentication/saml/sp-certificate.crt \
  -days 365 -nodes \
  -subj "/CN=your-app-domain.com"
```

> These files are excluded from version control via `.gitignore`. Never commit them.

### Step 2 — Configure `saml/settings.json`

Edit `backend/authentication/saml/settings.json`:

```json
{
  "sp": {
    "entityId": "https://your-app-domain.com/auth/saml/metadata/",
    "assertionConsumerService": {
      "url": "https://your-app-domain.com/auth/saml/acs/"
    },
    "x509cert": "<contents of sp-certificate.crt, single line>",
    "privateKey": "<contents of sp-private-key.pem, single line>"
  },
  "idp": {
    "entityId": "https://your-idp.example.com/",
    "singleSignOnService": {
      "url": "https://your-idp.example.com/sso/saml"
    },
    "x509cert": "<your IdP's public certificate>"
  }
}
```

### Step 3 — Register your SP with the IdP

Provide your IdP administrator with:
- **Entity ID**: `https://your-app-domain.com/auth/saml/metadata/`
- **ACS URL**: `https://your-app-domain.com/auth/saml/acs/`
- **Metadata URL**: `https://your-app-domain.com/auth/saml/metadata/`

### Step 4 — Test SSO

Navigate to `/auth/login/` and click **Sign in with SSO**. Users are redirected to the IdP login page and returned to the dashboard upon successful authentication.

---

## Connecting PostgreSQL

### 1. Create the database

```sql
CREATE DATABASE iot_telemetry;
```

### 2. Update your `.env` file

```env
DB_NAME=iot_telemetry
DB_USER=postgres
DB_PASSWORD=your-postgres-password
DB_HOST=localhost
DB_PORT=5432
```

### 3. Re-run migrations

```bash
python manage.py migrate
```

The application will automatically detect the `DB_PASSWORD` environment variable and switch from SQLite to PostgreSQL.

---

## API Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/` | Redirects to dashboard or login | — |
| `GET` | `/dashboard/` | Main analytics dashboard view | Yes |
| `GET` | `/upload/` | File upload interface | Yes |
| `POST` | `/upload/` | Submit a telemetry file via browser form | Yes |
| `POST` | `/api/ingest/` | Programmatic JSON telemetry ingestion | CSRF exempt |
| `GET` | `/api/machines/` | Returns list of all registered machine nodes | Yes |
| `GET` | `/api/telemetry/<machine_id>/` | Returns telemetry records for a machine | Yes |
| `GET` | `/admin-panel/logs/` | Ingestion audit log view | Yes |
| `POST` | `/admin-panel/purge/` | Deletes records for a machine (password protected) | Yes |
| `GET` | `/auth/login/` | Login page | — |
| `POST` | `/auth/logout/` | Logout | Yes |
| `POST` | `/auth/saml/acs/` | SAML Assertion Consumer Service | — |
| `GET` | `/auth/saml/metadata/` | SAML SP metadata XML | — |

---

## Supported Telemetry Formats

The ETL pipeline auto-detects and maps the following column naming conventions from uploaded files. Both `.csv` and `.xlsx`/`.xls` formats are supported.

| Platform Metric | Accepted Source Column Names |
|---|---|
| Operational RPM | `RPM`, `Capacity`, `Speed`, `C_Rate`, `C_rate` |
| Vibration Frequency | `Vibration`, `Voltage`, `Hz`, `Vbat`, `Voltage_V` |
| Thermal Pressure | `Pressure`, `Current`, `PSI`, `Current_A`, `Ibat` |
| Power Draw (kW) | `Power`, `Energy`, `kW`, `WhAccu`, `AhAccu` |
| Health Score | `SOC`, `Health`, `StateOfCharge`, `Soc` |
| Shift / Session | `Shift`, `ShiftNo`, `Shift_No`, `Cycle`, `CycleNo` |

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Django secret key. Use a long random string in production. |
| `DEBUG` | No | Set to `False` in production. Default: `True`. |
| `DB_NAME` | No | PostgreSQL database name. Default: `iot_telemetry`. |
| `DB_USER` | No | PostgreSQL username. Default: `postgres`. |
| `DB_PASSWORD` | No | PostgreSQL password. If blank, SQLite is used instead. |
| `DB_HOST` | No | Database host. Default: `localhost`. |
| `DB_PORT` | No | Database port. Default: `5432`. |
| `DELETE_PASSWORD` | Yes | Password required to call the `/admin-panel/purge/` endpoint. |

---

## Deployment Notes

For production deployment:

1. Set `DEBUG=False` in `.env`
2. Set a strong `SECRET_KEY`
3. Run `python manage.py collectstatic` and serve `/staticfiles/` via Nginx or a CDN
4. Use **Gunicorn** as the WSGI server: `gunicorn core.wsgi:application`
5. Ensure PostgreSQL is configured and accessible
6. Replace the SAML dummy certificates with enterprise-issued credentials

---

## License

MIT License. This project is open-source and free to use, modify, and distribute.
