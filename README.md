# MEDISCOPE

> **Machine-learning-assisted Loss to Follow-Up (LTFU) prediction and clinical retention support for HIV treatment programmes**

MEDISCOPE is a full-stack clinical decision-support prototype developed as a Rome Business School capstone project. It combines a reproducible machine-learning workflow with a secure FastAPI backend, PostgreSQL persistence, a role-aware React frontend, model governance, clinical-history management, audit logging, multi-factor authentication, and Docker-based deployment.

The project addresses a practical question:

> **How can routinely available HIV treatment-programme data be transformed into a secure decision-support system that helps clinicians identify patients who may be at increased risk of Loss to Follow-Up?**

MEDISCOPE does **not** diagnose disease, prescribe treatment, or replace professional clinical judgement. Its purpose is to demonstrate how predictive analytics can be operationalised responsibly inside a clinical workflow.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [What Loss to Follow-Up Means](#3-what-loss-to-follow-up-means)
4. [Project Aim and Objectives](#4-project-aim-and-objectives)
5. [Scope and Design Philosophy](#5-scope-and-design-philosophy)
6. [End-to-End Architecture](#6-end-to-end-architecture)
7. [Data Science Methodology](#7-data-science-methodology)
8. [Final Modelling Dataset](#8-final-modelling-dataset)
9. [Feature Engineering](#9-feature-engineering)
10. [Models Trained](#10-models-trained)
11. [Final Model Evaluation](#11-final-model-evaluation)
12. [Why MEDISCOPE Uses Logistic Regression and XGBoost](#12-why-mediscope-uses-logistic-regression-and-xgboost)
13. [Application Roles and Workflows](#13-application-roles-and-workflows)
14. [Database and Backend Architecture](#14-database-and-backend-architecture)
15. [Frontend Architecture](#15-frontend-architecture)
16. [Security Architecture](#16-security-architecture)
17. [Synthetic Demonstration Data](#17-synthetic-demonstration-data)
18. [Technology Stack](#18-technology-stack)
19. [Repository Structure](#19-repository-structure)
20. [Repository Data and Generated Artefacts](#20-repository-data-and-generated-artefacts)
21. [Environment Configuration](#21-environment-configuration)
22. [Local and Containerised Execution](#22-local-and-containerised-execution)
23. [Database Migrations](#23-database-migrations)
24. [Demo Seeding](#24-demo-seeding)
25. [Testing](#25-testing)
26. [Production Build and Docker Deployment](#26-production-build-and-docker-deployment)
27. [Health Checks, CORS and Persistence](#27-health-checks-cors-and-persistence)
28. [API Documentation](#28-api-documentation)
29. [Model Artefacts and Reproducibility](#29-model-artefacts-and-reproducibility)
30. [Data Governance, Privacy and Ethics](#30-data-governance-privacy-and-ethics)
31. [Limitations](#31-limitations)
32. [Future Development](#32-future-development)
33. [Academic Context](#33-academic-context)
34. [Clinical Disclaimer](#34-clinical-disclaimer)

---

# 1. Project Overview

MEDISCOPE is a prototype platform for **predicting and reviewing the risk of Loss to Follow-Up (LTFU) in HIV treatment programmes**.

The project spans two connected layers:

- **Data-science and machine-learning** — data inspection, cleaning, feature engineering, target construction, train/test separation, model training, evaluation, persistence and inference.
- **Secure clinical application** — authentication, patient administration, clinician assignment, clinical records, prediction, patient intelligence, governance workflows, audit logging and Docker deployment.

The result is therefore more than a model notebook. MEDISCOPE demonstrates the movement from research data to a reproducible predictive pipeline and then into a secure, role-aware application.

# 2. Problem Statement

HIV treatment programmes may contain large longitudinal datasets covering demographics, ART history, refill behaviour, viral-load measurements, clinic attendance and treatment status. Risk signals may be distributed across many fields, while clinical teams must prioritise finite time and resources.

MEDISCOPE addresses this by transforming treatment-programme information into model-assisted retention support. It estimates LTFU risk, keeps model outputs transparent, presents results alongside longitudinal context, preserves auditability and role boundaries, and prevents the model from acting autonomously.

# 3. What Loss to Follow-Up Means

Within this project, **Loss to Follow-Up (LTFU)** is represented as a binary outcome/state derived from the treatment-programme dataset and the implemented target-building logic:

- **Class 0 — Active / retained**
- **Class 1 — Inactive / LTFU**

The final training target was close to balanced:

| Class             | Training records |  Share |
| ----------------- | ---------------: | -----: |
| Active / retained |          125,923 | 51.73% |
| Inactive / LTFU   |          117,495 | 48.27% |

The authoritative operational target logic is implemented in the repository's target/feature-building code and should be used for exact reproducibility.

# 4. Project Aim and Objectives

## Main aim

To design, implement and validate a secure machine-learning decision-support prototype that estimates LTFU risk in HIV treatment programmes and presents the resulting information in a clinically interpretable workflow.

## Specific objectives

The project aims to:

- clean and validate a large HIV treatment-programme dataset;
- engineer demographic, treatment, temporal and clinical predictors;
- construct a reproducible binary LTFU target;
- preserve a held-out test dataset that is not used during model training;
- train and compare multiple classification algorithms;
- evaluate models using metrics beyond accuracy;
- persist trained pipelines for reproducible inference;
- expose prediction functionality through a secure API;
- implement role-aware workflows for users, clinicians and administrators;
- store prediction history together with model-version information;
- incorporate modern authentication, MFA, audit and access controls;
- support governed patient-record correction;
- use synthetic application data for demonstration;
- package and validate the complete stack with Docker.

# 5. Scope and Design Philosophy

MEDISCOPE follows five core principles:

**Decision support, not automation.** A model probability supports review; it is not a clinical instruction.

**Two-model transparency.** Logistic Regression and XGBoost outputs are shown separately rather than silently averaged.

**Longitudinal context.** Predictions are reviewed alongside patient history.

**Explicit governance.** Users propose corrections; authorised clinicians review them before authoritative records change.

**Security by design.** Authentication, privileged-role MFA, token rotation, encrypted TOTP secrets and audit logging are part of the core architecture.

# 6. End-to-End Architecture

```text
Research HIV Treatment Dataset
            │
            ▼
  Data Cleaning / Validation
            │
            ▼
     Feature Engineering
            │
            ▼
   Train / Held-out Test
            │
            ▼
 LR / Random Forest / AdaBoost / XGBoost
            │
            ▼
      Persisted Pipelines
            │
            ▼
┌───────────────┐    ┌──────────────────┐    ┌──────────────┐
│ React + Vite  │───▶│ FastAPI Backend  │───▶│ PostgreSQL   │
│ Nginx/Docker  │◀───│ Auth + Clinical  │◀───│ Persistence  │
└───────────────┘    │ + ML Inference   │    └──────────────┘
                     └──────────────────┘
```

The Docker deployment separates the application into `postgres`, `backend` and `frontend` services.

# 7. Data Science Methodology

The ML work was implemented as a reproducible code pipeline with dedicated modules for configuration, preprocessing, validation, feature construction, splitting, modelling, evaluation, persistence and inference.

## Raw-data audit

The source dataset contained **304,273 records** and fields including State, LGA, sex, date of birth, age at ART initiation, ART start date, drug-pickup dates, regimen, clinic-visit date, ARV refill days, pregnancy status, viral-load information, transfer information and treatment-status fields.

## Date conversion and validation

Date-like columns were converted and validated. Missingness varied considerably: for example, Last Drug Pickup Date was about 4.29% missing/invalid, Last Clinic Visit Date about 3.58%, Current Viral Load Date about 21.74%, while some historical/quarterly fields had much greater missingness.

## Age validation

`Age at ART Initiation` was cleaned explicitly:

- 50 negative values were converted to missing;
- 2 values above 100 were converted to missing;
- 304,197 valid numeric ages remained;
- 76 values were missing/invalid after cleaning.

## Processed artefacts

The workflow creates reproducible intermediate files under `data/processed/`, including date-converted, feature-engineered, training and held-out testing datasets.

# 8. Final Modelling Dataset

| Item                        |   Value |
| --------------------------- | ------: |
| Total records               | 304,273 |
| Training records            | 243,418 |
| Held-out test records       |  60,855 |
| Predictors                  |     141 |
| Numeric predictors          |      11 |
| Boolean/encoded predictors  |     130 |
| Test data used for training |      No |

Final training metadata records:

- Python 3.11.15
- pandas 3.0.5
- scikit-learn 1.9.0
- XGBoost 3.2.0

Metadata is persisted in `models/trained/training_metadata.json`.

# 9. Feature Engineering

The final representation contains 11 numeric and 130 boolean/encoded predictors.

Numeric features include:

- Age at ART Initiation;
- Current Age;
- Days Of ARV Refill;
- Current Viral Load;
- Current Status Q3 (28 Days);
- Current Status Q3 (90 Days);
- Is Child;
- Is Adult;
- Is Elderly;
- Months on ART;
- Missing Viral Load.

Encoded feature families cover:

- State and LGA;
- sex;
- age group;
- ART-initiation age group;
- pregnancy status;
- ARV refill category;
- regimen;
- patient transfer status;
- viral-load category.

The exact final feature order is stored in `training_metadata.json`.

# 10. Models Trained

Four models were trained and persisted:

1. Logistic Regression
2. Random Forest
3. AdaBoost
4. XGBoost

Artefacts are stored under `models/trained/`:

```text
logistic_regression_pipeline.joblib
random_forest_pipeline.joblib
adaboost_pipeline.joblib
xgboost_pipeline.joblib
training_metadata.json
```

Recorded training durations were approximately:

| Model               | Training time |
| ------------------- | ------------: |
| Logistic Regression |    1,549.93 s |
| Random Forest       |       29.91 s |
| AdaBoost            |       46.13 s |
| XGBoost             |        8.69 s |

# 11. Final Model Evaluation

All four models were evaluated on the same **60,855-record held-out test set** at the stored **0.50 threshold**.

| Model                   |   Accuracy | Balanced Accuracy |  Precision | Recall / Sensitivity | Specificity |         F1 |    ROC-AUC |     PR-AUC |
| ----------------------- | ---------: | ----------------: | ---------: | -------------------: | ----------: | ---------: | ---------: | ---------: |
| **Logistic Regression** | **98.49%** |        **98.49%** | **98.64%** |           **98.24%** |  **98.73%** | **98.44%** | **99.83%** | **99.85%** |
| **XGBoost**             |     97.15% |            97.14% |     97.12% |               96.96% |      97.32% |     97.04% |     99.65% |     99.65% |
| Random Forest           |     96.27% |            96.27% |     95.86% |               96.44% |      96.11% |     96.15% |     99.37% |     99.35% |
| AdaBoost                |     87.41% |            87.76% |     80.37% |               97.81% |      77.70% |     88.23% |     97.17% |     95.96% |

The complete comparison is stored under `reports/evaluation/metrics/model_comparison.csv`.

The held-out test set contained **29,374 actual LTFU** and **31,481 actual retained** records.

### Logistic Regression confusion counts

- TN: 31,082
- FP: 399
- FN: 517
- TP: 28,857

### XGBoost confusion counts

- TN: 30,637
- FP: 844
- FN: 892
- TP: 28,482

Model evaluation included accuracy, balanced accuracy, precision, recall, specificity, NPV, F1, ROC-AUC, PR-AUC, MCC, Brier score, log loss, false-positive/false-negative rates, prediction speed and artefact size.

# 12. Why MEDISCOPE Uses Logistic Regression and XGBoost

**Logistic Regression** achieved the strongest overall held-out performance and provides a compact, probabilistic and relatively interpretable baseline. The persisted pipeline is about 4.6 KB.

**XGBoost** provides a strong non-linear comparison and retained excellent discrimination, with ROC-AUC above 99.6%. Its persisted pipeline is about 352 KB.

The application does not average these two outputs into one unexplained score. It preserves each probability and classification and derives an agreement status so clinicians can see whether the models tell the same story.

# 13. Application Roles and Workflows

MEDISCOPE supports three roles:

### USER

A standard user can manage their account and, when linked by an administrator to a synthetic patient, use appropriate patient-facing features.

### CLINICIAN

Clinicians can:

- view assigned patients;
- open patient details;
- add clinical records;
- update the latest appropriate record;
- review longitudinal history;
- generate fresh LTFU predictions;
- open patient intelligence;
- review clinician-level analytics;
- process change requests;
- use internal messaging.

### ADMINISTRATOR

Administrators can:

- manage the account directory;
- govern role/status;
- create synthetic patients;
- link users to patient profiles;
- assign clinicians to patients;
- manage active relationships;
- review audit logs;
- perform administrative governance actions.

### Core relationship flow

```text
USER account
    ↓
Synthetic patient profile
    ↓
User ↔ Patient link
    ↓
Clinician ↔ Patient assignment
    ↓
Clinical records / predictions / intelligence
```

### Record-correction flow

```text
User proposes correction
        ↓
Change request
        ↓
Clinician reviews Current → Proposed
        ↓
Approve / Reject + Review comment
        ↓
Audit trail / authoritative update when approved
```

# 14. Database and Backend Architecture

SQLAlchemy entities cover:

- users and authentication records;
- email verification and password reset tokens;
- refresh-token sessions;
- pending TOTP enrolments;
- MFA recovery codes;
- synthetic patients;
- clinician-patient assignments;
- clinical records;
- health-record change requests;
- model registry;
- saved predictions;
- messages and recipients;
- audit logs.

The FastAPI backend is layered under:

```text
api/app/
├── api/
│   ├── dependencies.py
│   ├── router.py
│   └── routes/
├── core/
├── db/
├── models/
├── schemas/
├── services/
└── main.py
```

Route groups include authentication, users, patients, clinical records, clinician intelligence, change requests, predictions, administration, messaging and audit logs.

Service modules separate access control, audit, authentication, email, MFA, model registry, notifications, prediction logic and token handling.

# 15. Frontend Architecture

The frontend uses React, TypeScript, Vite and React Router.

Representative pages include:

```text
LandingPage
AuthPages
DashboardPage
PatientsPage
PatientDetailPage
PatientIntelligencePage
PredictionsPage
ChangeRequestsPage
AdministrationPage
AuditLogsPage
MessagesPage
ProfilePage
SettingsPage
RequiredMfaSetupPage
NotFoundPage
```

Reusable components include the app shell, protected routes, common UI components, password input, synthetic-patient modal and clinical-record modal.

The frontend API wrapper is under `frontend/src/lib/api.ts`, with shared contracts under `frontend/src/lib/types.ts`.

# 16. Security Architecture

MEDISCOPE implements multiple security controls.

### Passwords

Passwords are hashed using **Argon2id**. Plaintext passwords are never persisted.

### JWT access tokens

Short-lived signed JWTs include user identity, role, token type, MFA status, timestamps and a unique token ID.

### Email verification

Verification uses time-limited one-time codes. Only hashes are stored.

### Password reset

Reset tokens are high entropy, time limited, single use and stored as hashes.

### Refresh-token rotation

Database-backed refresh sessions support rotation, revocation, token families, replacement tracking and reuse detection.

### TOTP MFA

Authenticator-app MFA is supported. **CLINICIAN** and **ADMINISTRATOR** accounts must enrol MFA before normal application access is issued.

### Recovery codes

Recovery codes are generated once, stored only as hashes and consumed after use.

### Encrypted TOTP secrets

TOTP shared secrets must remain recoverable for verification, so they are encrypted at rest using Fernet and a dedicated environment-provided encryption key.

### Role-based access control

Protected routes enforce role boundaries and clinician-patient relationships.

### Audit logging

Security and governance events can record actor, action, resource, outcome, time, IP and user agent while excluding sensitive secrets.

### Account-enumeration resistance

Selected authentication workflows return uniform responses so they do not reveal whether an account exists.

# 17. Synthetic Demonstration Data

The **web application uses synthetic patient records only**. This is intentionally separate from the historical/research dataset used to train and evaluate the models.

The demonstration seeder can create:

- users;
- clinicians;
- administrator;
- patient profiles;
- linked user-patient relationships;
- clinician assignments;
- multiple clinical records;
- deliberately incomplete fields;
- demonstration prediction history.

The heterogeneity is intentional so dashboards and intelligence views can demonstrate data quality, coverage, risk, longitudinal history and model agreement/disagreement.

# 18. Technology Stack

| Layer        | Technologies                                                                       |
| ------------ | ---------------------------------------------------------------------------------- |
| Data science | Python, pandas, NumPy, scikit-learn, XGBoost, Joblib, PyArrow, Matplotlib, Jupyter |
| Backend      | FastAPI, Pydantic, SQLAlchemy 2, Alembic, PostgreSQL, psycopg 3, Uvicorn           |
| Security     | Argon2id, PyJWT, PyOTP, `cryptography`/Fernet                                      |
| Frontend     | React, TypeScript, Vite, React Router, Lucide React, QRCode React                  |
| Deployment   | Docker, Docker Compose, PostgreSQL 17, Nginx                                       |

# 19. Repository Structure

```text
LTFU-IN-HIV-PREDICTOR/
├── api/
│   ├── alembic/
│   ├── app/
│   ├── scripts/
│   ├── tests/
│   └── Dockerfile
├── data/
│   ├── raw/
│   ├── processed/
│   └── external/
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── vite.config.ts
├── models/
│   └── trained/
├── notebooks/
├── reports/
│   └── evaluation/
├── src/
│   ├── evaluation/
│   ├── feature_builders/
│   ├── feature_selection/
│   ├── inference/
│   └── modelling/
├── tests/
├── .dockerignore
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt
├── requirements-ml.txt
├── project_structure.txt
└── README.md
```

Research datasets are intentionally excluded from Git while the `data/*/README.md` files document the expected local layout. Local logs are also excluded from version control. The tracked `project_structure.txt` provides a generated snapshot of the repository hierarchy.

# 20. Repository Data and Generated Artefacts

The repository intentionally separates **source code and reproducibility documentation** from **local research data and generated runtime artefacts**.

The original research workbook and generated Parquet datasets are retained locally for analysis and reproducibility work, but are excluded from Git tracking. This reduces repository size, avoids distributing research data unintentionally, and keeps the published repository focused on code, documentation, trained model artefacts and evaluation outputs.

The local data layout is documented through tracked README files:

```text
data/
├── raw/
│   └── README.md
├── processed/
│   └── README.md
└── external/
    └── README.md
```

Research files inside these directories are intentionally ignored while the README files remain tracked. Runtime/project logs under `reports/logs/` are also retained locally and excluded from Git.

Python bytecode/cache artefacts, frontend dependency/build directories, IDE settings, environment files and temporary files are excluded through `.gitignore`.

`project_structure.txt` is intentionally retained as a tracked repository artefact to provide a generated snapshot of the project hierarchy for review and documentation.

Docker uses a separate `.dockerignore` so research-only datasets, notebooks, reports, local secrets, development dependencies and other unnecessary files are not sent into the Docker build context.

# 21. Environment Configuration

MEDISCOPE uses environment variables for database connectivity, authentication, MFA, email delivery, model paths, CORS and frontend/backend integration.

Create a local configuration from the committed example:

```powershell
Copy-Item .env.example .env
```

Then replace placeholder values with development or deployment-specific values.

> **Never commit `.env`.** The committed `.env.example` contains placeholders and documentation only. Real credentials, encryption keys and passwords must remain outside source control.

## Key configuration groups

| Variable group | Purpose |
| --- | --- |
| `APP_NAME`, `ENVIRONMENT`, `DEBUG` | Application runtime configuration |
| `DATABASE_URL`, `POSTGRES_*` | PostgreSQL connectivity and Compose database configuration |
| `SECRET_KEY`, `JWT_*`, `REFRESH_*` | Access-token and refresh-token security |
| `PASSWORD_*`, `OTP_*` | Password, verification and recovery policy |
| `TOTP_*`, `MFA_*` | Multi-factor authentication and TOTP secret protection |
| `EMAIL_*`, `SMTP_*` | Authentication-email delivery |
| `SYNTHETIC_DATA_ONLY` | Prototype data-governance boundary |
| `LOGISTIC_MODEL_PATH`, `XGBOOST_MODEL_PATH`, `DECISION_THRESHOLD` | Runtime ML model configuration |
| `FRONTEND_BASE_URL` | Frontend URL used by backend-generated browser links |
| `VITE_API_BASE_URL` | Public browser-facing API URL compiled into the Vite frontend |
| `ALLOWED_ORIGINS_CSV` | Explicit CORS allow-list |

## Database URL: local versus Docker

For a backend running directly on the host machine, PostgreSQL is normally reached through `localhost`:

```text
postgresql+psycopg://mediscope:<password>@localhost:5432/mediscope
```

When the backend runs through Docker Compose, Compose supplies its own `DATABASE_URL` and the backend reaches PostgreSQL through the internal service hostname `postgres:5432`.

This distinction matters because `localhost` inside the backend container refers to the backend container itself, not the PostgreSQL container.

## Frontend/backend URLs

`FRONTEND_BASE_URL` is used by backend workflows that need to generate browser-facing links.

`VITE_API_BASE_URL` is a frontend build variable. Vite compiles it into the browser bundle, so it must contain the URL through which the user's browser can reach the MEDISCOPE API. It must never contain a secret.

For local/containerised demonstration:

```text
FRONTEND_BASE_URL=http://localhost:5173
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

For remote deployment, both values must be changed to the corresponding public HTTPS endpoints before deployment/build as appropriate.

## Environment-driven CORS

Permitted browser origins are configured with `ALLOWED_ORIGINS_CSV`, for example:

```text
ALLOWED_ORIGINS_CSV=http://localhost:5173,http://127.0.0.1:5173
```

Production deployments should replace these with the actual deployed frontend origin(s). Wildcard CORS is deliberately avoided for authenticated application traffic.

## Generating the TOTP encryption key

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Keep `TOTP_ENCRYPTION_KEY` separate from `SECRET_KEY`.

## Email behaviour

During local development, `EMAIL_CONSOLE_BACKEND=true` can be used so authentication messages are printed to the backend console rather than delivered externally.

A remote/production-style deployment should use a configured SMTP provider and set `EMAIL_CONSOLE_BACKEND=false`, with the relevant `SMTP_*` values supplied securely by the deployment environment.


# 22. Local and Containerised Execution

MEDISCOPE supports two practical execution modes: running the application components directly for development, or running the complete stack through Docker Compose.

## Local development

### Python environment

```powershell
conda create -n ltfu python=3.11
conda activate ltfu
pip install -r requirements.txt
```

Additional dependency sets are available in `requirements-dev.txt` and `requirements-ml.txt`.

### Frontend dependencies

```powershell
cd frontend
npm install
cd ..
```

### Database

A PostgreSQL instance must be available and the local `DATABASE_URL` must point to it, normally through `localhost:5432`. Apply migrations before using the application.

### Run the API

```powershell
cd api
uvicorn app.main:app --reload
```

Typical local API:

```text
http://127.0.0.1:8000
```

### Run the frontend

In another terminal:

```powershell
cd frontend
npm run dev
```

Typical local frontend:

```text
http://localhost:5173
```

## Containerised execution

Docker Compose packages the application as three cooperating services:

```text
postgres  → PostgreSQL 17 persistence
backend   → FastAPI + ML inference
frontend  → Nginx-served React production build
```

Validate the resolved Compose configuration:

```powershell
docker compose config
```

> Resolved Compose output may contain environment values. Do not publish or paste the full output when it contains secrets.

Build the application images:

```powershell
docker compose build
```

For a new database, start PostgreSQL and apply migrations:

```powershell
docker compose up -d postgres
docker compose run --rm backend alembic upgrade head
```

Then start the backend and frontend:

```powershell
docker compose up -d backend frontend
docker compose ps
```

Typical host-accessible endpoints:

```text
Frontend: http://localhost:5173
Backend:  http://localhost:8000
Postgres: localhost:5432
```

Inside the Compose network, the backend reaches the database as `postgres:5432`.


# 23. Database Migrations

Alembic configuration lives at repository root in `alembic.ini`, with migration revisions under `api/alembic/`.

Local:

```powershell
alembic current
alembic upgrade head
```

Docker:

```powershell
docker compose run --rm backend alembic upgrade head
docker compose run --rm backend alembic current
```

The validated containerised database was successfully upgraded to the current Alembic head before application startup.

Migrations should be applied whenever a deployment introduces schema changes and before the updated application begins serving normal traffic.


# 24. Demo Seeding

The synthetic demonstration seeder is located at:

```text
api/scripts/seed_clinician_demo.py
```

It prepares application data for demonstration/testing workflows, including synthetic accounts, patient profiles, clinician relationships and associated clinical information.

Local:

```powershell
cd api
python scripts\seed_clinician_demo.py
```

Docker, after the backend is running:

```powershell
docker compose exec backend python /workspace/api/scripts/seed_clinician_demo.py
```

The seeder is strictly for development, demonstration and testing. It must not be interpreted as a production data-loading workflow and must not be replaced with real patient-identifiable information in the capstone environment.


# 25. Testing and Validation

MEDISCOPE was validated at multiple levels: automated regression testing, security and authentication testing, application compilation, frontend production building, container health validation, CORS validation, persistence testing and manual end-to-end workflow validation.

## Automated test suite

Run the complete regression suite from the repository root:

```powershell
pytest -q
```

The current validated baseline is **30 passed, 1 warning**. The remaining warning is a Starlette/FastAPI TestClient deprecation warning rather than a failing MEDISCOPE test. Backend and machine-learning tests can also be run independently:

```powershell
pytest api/tests -q
pytest tests -q
python -m compileall api/app
```

Validate the React/TypeScript production application with:

```powershell
cd frontend
npm run build
cd ..
```

## Authentication and security validation

Authentication and security behaviour formed an important part of validation. Implemented and exercised workflows include password authentication, JWT-protected API access, rejection of unauthenticated protected requests, email-verification and password-reset infrastructure, refresh-token rotation and revocation, TOTP MFA, mandatory MFA enrolment for privileged roles, recovery codes, encrypted TOTP-secret storage, role-based access restrictions and clinician-patient access boundaries.

A legacy MFA reset/migration path was exercised during development, followed by successful manual MFA re-enrolment using a privileged demonstration account. Dedicated automated testing for TOTP-secret encryption was subsequently added before the regression baseline reached 30 passing tests.

## Container health validation

The containerised stack uses health-aware service dependencies. PostgreSQL must pass `pg_isready`; the backend must then respond successfully to `GET /health` before Docker marks it healthy and the frontend dependency is satisfied. Backend health was manually verified with:

```powershell
docker inspect mediscope-backend --format='{{.State.Health.Status}}'
```

which returned `healthy`.

## CORS validation

CORS is environment-driven through `ALLOWED_ORIGINS_CSV`. Validation confirmed that an approved local frontend origin received the expected `Access-Control-Allow-Origin` header, while a deliberately unapproved origin did not. This verifies that MEDISCOPE does not rely on an unrestricted wildcard CORS policy.

## Persistence and restart validation

PostgreSQL persistence was tested across container shutdown and restart without deleting the named database volume. Existing demonstration state remained available afterwards, including user accounts, MFA state, synthetic patients, clinician-patient assignments and clinical records. This confirms that application state persists independently of individual container lifecycles.

## Manual end-to-end validation

The complete containerised application was exercised manually through the browser. The validated workflow included starting PostgreSQL, backend and frontend services; applying Alembic migrations; seeding demonstration data; loading the Nginx-served frontend; confirming React Router refresh/fallback behaviour; authenticating as a clinician; completing mandatory MFA enrolment; viewing assigned synthetic patients and clinical records; generating a fresh LTFU prediction through the containerised backend; and verifying persisted application state after restart.

Together, these checks demonstrate that the production-style frontend, FastAPI backend, PostgreSQL database and persisted machine-learning pipelines operate as an integrated local containerised demonstration system.

## Testing boundary

Passing automated and manual tests demonstrates expected behaviour under the tested development and demonstration scenarios. It does **not** constitute clinical validation, regulatory approval, penetration testing, formal cybersecurity certification or evidence that MEDISCOPE is suitable for use with real patients.

# 26. Production Build and Docker Deployment

## Frontend production build

The frontend production build performs TypeScript compilation followed by Vite bundling:

```powershell
cd frontend
npm run build
```

The Docker frontend uses a multi-stage build: Node creates the Vite production bundle, then Nginx serves the generated static files. The Nginx configuration provides the SPA fallback required for React Router routes.

## Complete Compose build

```powershell
docker compose config
docker compose build
docker compose up -d
docker compose ps
```

The containerised application has been validated locally with PostgreSQL, FastAPI and the Nginx-served React frontend operating together.

## Local containerisation versus remote deployment

Running Docker Compose on a development computer is a **containerised local deployment**. It demonstrates that the services can be built and operated together, but it does not by itself make MEDISCOPE publicly available on the internet.

A remote/cloud demo deployment would additionally require:

- a hosting platform or server for the application services;
- a hosted PostgreSQL database or persistent database service;
- public HTTPS URLs for the frontend and API;
- deployment-specific environment variables and secrets;
- `VITE_API_BASE_URL` configured for the public API URL;
- `FRONTEND_BASE_URL` configured for the public frontend URL;
- `ALLOWED_ORIGINS_CSV` restricted to the deployed frontend origin(s);
- database migrations against the hosted database;
- optional synthetic demo seeding;
- SMTP configuration if real authentication emails are required;
- persistence, backup and monitoring appropriate to the hosting environment.

Even when remotely hosted, MEDISCOPE remains a **research/academic demonstration deployment**, not a validated production health-information system.


# 27. Health Checks, CORS and Persistence

## Health-aware startup

The validated startup chain is:

```text
PostgreSQL starts
      ↓
pg_isready succeeds
      ↓
Backend starts
      ↓
GET /health succeeds
      ↓
Backend becomes healthy
      ↓
Frontend starts
```

Backend health can be inspected with:

```powershell
docker inspect mediscope-backend --format='{{.State.Health.Status}}'
```

## Environment-driven CORS

Allowed origins are supplied through `ALLOWED_ORIGINS_CSV`, avoiding hard-coded deployment domains. The project verified that an approved frontend origin receives `Access-Control-Allow-Origin` and an unapproved origin does not.

## Persistence

PostgreSQL uses a named Docker volume. Persistence was verified across:

```powershell
docker compose down
docker compose up -d
```

without `-v`, preserving accounts, MFA state, patients, assignments and clinical data.

# 28. API Documentation

FastAPI exposes:

```text
/docs
/redoc
/openapi.json
```

System endpoints include:

```text
GET /
GET /health
```

Protected endpoints require Bearer authentication. An unauthenticated prediction-model request was verified to be rejected.

# 29. Model Artefacts and Reproducibility

The trained pipelines are stored under `models/trained/`.

The Docker backend includes both the FastAPI application and the root ML `src` package because persisted pipelines and inference utilities may require those modules when Joblib deserialises the model.

The container therefore supports imports from both:

```text
/workspace/api/app
/workspace/src
```

This was essential to successful containerised inference.

# 30. Data Governance, Privacy and Ethics

MEDISCOPE is deliberately configured for **synthetic application data only**.

The ML research dataset and the synthetic application database are separate concepts:

- the research dataset supports modelling/evaluation;
- the application database demonstrates secure workflow using synthetic patient profiles.

Prediction snapshots should contain only inputs needed for reproducibility, not passwords, tokens or unnecessary identifiers.

Role-based access and clinician-patient assignment boundaries implement least privilege.

Human oversight remains mandatory: prediction outputs are advisory evidence, not autonomous clinical actions.

# 31. Limitations

MEDISCOPE is a capstone prototype.

Key limitations include:

- application deployment has been validated with synthetic demonstration records;
- model performance on the project dataset does not guarantee external performance;
- prospective validation has not been performed;
- the target definition is programme/dataset-specific;
- some source fields contain substantial missingness;
- the 0.50 threshold may not be optimal for every operational context;
- real deployment would require stronger operational monitoring, formal clinical-safety review, security review and privacy governance;
- MEDISCOPE must not take autonomous clinical action.

# 32. Future Development

Potential future work includes:

- prospective and external validation;
- probability calibration/recalibration;
- intervention-capacity-based threshold optimisation;
- fairness analysis across demographic/geographic groups;
- drift monitoring;
- richer model explainability;
- formal model cards;
- production secrets management;
- HTTPS/TLS and hardened reverse proxy configuration;
- managed PostgreSQL deployment;
- observability and alerting;
- CI/CD;
- backup/disaster recovery;
- automated browser end-to-end tests;
- formal privacy/security assessment;
- structured clinician user testing.

# 33. Academic Context and Alignment with Capstone Objectives

MEDISCOPE was developed as a Rome Business School capstone project and demonstrates the application of data-science, machine-learning, software-engineering, security and governance concepts to a healthcare decision-support problem. The project was intentionally developed beyond a standalone predictive model: it demonstrates the path from a healthcare/business challenge to an analytical solution and then to an operational prototype.

## Alignment between objectives and implementation

| Capstone objective | MEDISCOPE implementation |
| --- | --- |
| Investigate LTFU risk using treatment-programme data | Structured exploratory analysis, preprocessing and target construction |
| Develop relevant predictive variables | Demographic, treatment, temporal, refill and viral-load feature engineering |
| Develop predictive models | Logistic Regression, Random Forest, AdaBoost and XGBoost |
| Evaluate predictive performance objectively | Independent 60,855-record held-out test set and multi-metric evaluation |
| Select appropriate models for operational use | Logistic Regression and XGBoost integrated as complementary deployed models |
| Translate analytics into usable decision support | FastAPI inference layer and React clinician workflow |
| Preserve accountability and human oversight | Prediction history, model metadata, audit logging and explicit model agreement/disagreement presentation |
| Protect application access | Argon2id passwords, JWT authentication, token rotation, MFA and role-based access control |
| Demonstrate responsible health-data handling | Synthetic application records, least-privilege access and explicit privacy boundaries |
| Demonstrate reproducible implementation | Persisted model pipelines, metadata, Alembic migrations, automated tests and Docker Compose deployment |

## Architectural rationale

A layered architecture was selected because MEDISCOPE contains responsibilities that should remain independently maintainable. The machine-learning layer handles reproducible transformation, training, evaluation and inference. FastAPI provides a typed API and separates predictive logic from presentation. PostgreSQL provides relational persistence for accounts, patient relationships, clinical records, predictions and audit information. React and TypeScript provide the interactive, role-aware frontend. Docker and Docker Compose make these components reproducible as a single deployment unit while preserving service separation.

This architecture therefore supports both the analytical objective of the capstone and the practical objective of demonstrating how trained models can be incorporated into a controlled application workflow.

## Machine-learning rationale

Multiple classification algorithms were compared rather than assuming one model family would be optimal. Logistic Regression provided an interpretable probabilistic baseline and achieved the strongest overall held-out performance. XGBoost was retained as a complementary non-linear model because it can represent relationships that a linear decision boundary may not capture while still achieving excellent held-out discrimination. Random Forest and AdaBoost provided additional comparative evidence but were not selected for application deployment.

MEDISCOPE presents Logistic Regression and XGBoost separately rather than averaging their probabilities. This preserves model transparency and allows agreement or disagreement between two modelling approaches to remain visible to the clinician.

## Ethical and privacy considerations

Healthcare prediction involves information that would be highly sensitive if associated with real individuals. MEDISCOPE therefore maintains an explicit distinction between the research dataset used for machine-learning development and the synthetic patient records used by the demonstration application. Real patient-identifiable health information must not be entered into the development or demonstration environment.

Authentication, role-based access, clinician-patient assignment boundaries, MFA, encrypted TOTP secrets and audit logging demonstrate how privacy and accountability concerns can be incorporated into system design. These controls demonstrate responsible design principles; they are not proof of regulatory compliance or production readiness.

## Decision-support boundary

MEDISCOPE implements **clinical decision support, not autonomous clinical decision-making**. A predicted probability represents model-generated evidence about LTFU risk. It does not determine treatment, diagnose a condition, prescribe an intervention or automatically change a patient's care. Clinical professionals remain responsible for interpreting predictions alongside the wider clinical and social context and determining whether action is appropriate. This human-in-the-loop boundary is fundamental to the project design.

## Limitations and academic interpretation

The prototype must be interpreted within the limitations documented in this repository, including the absence of external and prospective clinical validation, programme-specific target construction, potential effects of missingness and dataset shift, the need for threshold calibration in deployment contexts, and the need for deeper fairness, drift, security and regulatory assessment before any real-world clinical use. These limitations are not treated as implementation defects; they define the boundary between a capstone demonstration and a clinically validated health system.

## Academic contribution

The principal contribution of MEDISCOPE is the integration of stages that are often demonstrated independently:

```text
Healthcare problem
        ↓
Data preparation
        ↓
Feature engineering
        ↓
Machine-learning comparison
        ↓
Held-out evaluation
        ↓
Persisted inference
        ↓
Secure API
        ↓
Role-aware clinical interface
        ↓
Governance and auditability
        ↓
Reproducible containerised prototype
```

The project therefore demonstrates not only predictive modelling but the broader process required to translate analytical work into a governed decision-support prototype.

# 34. Clinical Disclaimer

> **MEDISCOPE is a research and educational clinical decision-support prototype.**

It is **not**:

- a diagnostic system;
- an autonomous clinical decision maker;
- a treatment-prescription system;
- a substitute for professional medical judgement;
- validated for unsupervised use with real patient care.

Machine-learning outputs must be interpreted alongside appropriate clinical context.

The application is intended for **synthetic demonstration records only**. Do not enter real patient-identifiable health information into the development or demonstration environment.

---

## Project Status

```text
Machine-learning pipeline                COMPLETE
Four-model held-out evaluation           COMPLETE
Logistic Regression deployment           COMPLETE
XGBoost deployment                       COMPLETE
FastAPI backend                          COMPLETE
PostgreSQL persistence                   COMPLETE
React / TypeScript frontend              COMPLETE
Role-based workflows                     COMPLETE
Mandatory privileged MFA                 COMPLETE
Encrypted TOTP storage                   COMPLETE
Clinical governance workflow             COMPLETE
Docker backend                           COMPLETE
Docker frontend / Nginx                  COMPLETE
Docker Compose stack                     COMPLETE
Backend health check                     COMPLETE
Environment-driven CORS                  COMPLETE
Persistence restart test                 COMPLETE
Repository hygiene review                 COMPLETE
Environment/deployment documentation      COMPLETE
Research data removed from Git tracking   COMPLETE
Automated tests                          30 PASSING
Containerised end-to-end prediction      VERIFIED
```

---

## Author

**Akayovwe Okugbe**

Rome Business School Capstone Project
MEDISCOPE — LTFU Prediction in HIV Treatment Programmes

---

## Use and Reuse

This repository is primarily an academic capstone and demonstration project.

Before reuse outside the academic/development context, review dataset permissions, dependency licences, privacy obligations, clinical-safety requirements, cybersecurity requirements and applicable healthcare/data-protection regulation.

Working prediction functionality must not be interpreted as regulatory, clinical or production approval.
