"""
=========================================================
MEDISCOPE FastAPI Application

LTFU Prediction Platform

Purpose:
    Creates and configures the MEDISCOPE FastAPI backend.

Responsibilities:
    - Configure application metadata
    - Configure Swagger and ReDoc documentation
    - Register versioned API routes
    - Provide root application information
    - Provide application health checks
    - Display clinical and synthetic-data notices

Security:
    MEDISCOPE uses JWT Bearer authentication for protected
    API endpoints.

    This application is currently a prototype using
    synthetic patient records only.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations


# =====================================================
# FASTAPI IMPORTS
# =====================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# =====================================================
# APPLICATION IMPORTS
# =====================================================

from app.api.router import api_router
from app.core.config import get_settings


# =====================================================
# APPLICATION SETTINGS
# =====================================================

settings = get_settings()


# =====================================================
# OPENAPI TAG DOCUMENTATION
#
# These definitions organise endpoints into clear groups
# inside Swagger and ReDoc.
# =====================================================

OPENAPI_TAGS = [

    {
        "name": "Authentication",
        "description": (
            "Registration, login, email verification, "
            "password recovery, refresh-token rotation "
            "and TOTP multi-factor authentication."
        ),
    },

    {
        "name": "Users",
        "description": (
            "Authenticated user profile and account "
            "operations."
        ),
    },

    {
        "name": "Patients",
        "description": (
            "Synthetic patient-management operations "
            "within MEDISCOPE."
        ),
    },

    {
        "name": "Clinical Records",
        "description": (
            "Clinical-record management for authorised "
            "clinicians."
        ),
    },

    {
        "name": "Predictions",
        "description": (
            "Loss-to-follow-up risk predictions using "
            "MEDISCOPE machine-learning models."
        ),
    },

    {
        "name": "Messaging",
        "description": (
            "Internal messages and system-generated "
            "notifications."
        ),
    },

    {
        "name": "Administration",
        "description": (
            "Administrator-only user, role and system "
            "management operations."
        ),
    },

    {
        "name": "System",
        "description": (
            "Application information and health checks."
        ),
    },
]


# =====================================================
# FASTAPI APPLICATION
# =====================================================

app = FastAPI(

    # -------------------------------------------------
    # APPLICATION INFORMATION
    # -------------------------------------------------

    title="MEDISCOPE API",

    version="1.0.0",

    summary=(
        "Secure clinical decision-support platform for "
        "predicting loss to follow-up in HIV treatment "
        "programmes."
    ),

    # -------------------------------------------------
    # OPENAPI / SWAGGER DESCRIPTION
    # -------------------------------------------------

    description="""
## MEDISCOPE

MEDISCOPE is a healthcare decision-support prototype
designed to demonstrate how machine-learning models can
support the identification of patients who may be at risk
of Loss to Follow-Up (LTFU) in HIV treatment programmes.

### Current capabilities

The platform includes:

- secure user authentication;
- email verification;
- password recovery;
- JWT access tokens;
- refresh-token rotation;
- TOTP two-factor authentication;
- role-based access control;
- synthetic patient records;
- clinician-patient assignments;
- clinical records;
- audit logging;
- prediction-history infrastructure;
- machine-learning model integration.

### Authentication

MEDISCOPE uses JWT Bearer authentication.

After successful authentication, protected endpoints
expect an access token in the Authorization header.

Example:

    Authorization: Bearer <access-token>

The Swagger Authorize button can also be used to provide
the access token.

### Current user roles

MEDISCOPE currently supports:

- USER
- CLINICIAN
- ADMINISTRATOR

The architecture can support additional roles later.

### Clinical disclaimer

MEDISCOPE is a decision-support and
resource-prioritisation prototype.

It is not:

- a diagnostic system;
- an autonomous clinical decision maker;
- a replacement for professional medical judgement;
- a treatment-prescription system.

Machine-learning predictions must be interpreted together
with appropriate clinical context.

### Synthetic-data notice

All patient records used within this prototype are
synthetic and exist solely for development, demonstration
and testing.

They do not represent real individuals.

Real patient information must not be entered into the
development environment.

### Security

MEDISCOPE currently incorporates:

- Argon2id password hashing;
- JWT access tokens;
- rotating refresh tokens;
- refresh-token reuse detection;
- email OTP verification;
- single-use password-reset tokens;
- TOTP multi-factor authentication;
- MFA recovery codes;
- role-based endpoint authorisation;
- environment-based credentials;
- SQLAlchemy database access;
- PostgreSQL persistence;
- audit logging.

Further production hardening will be introduced in later
development phases.
""",

    # -------------------------------------------------
    # DOCUMENTATION ENDPOINTS
    # -------------------------------------------------

    docs_url="/docs",

    redoc_url="/redoc",

    openapi_url="/openapi.json",

    # -------------------------------------------------
    # OPENAPI ORGANISATION
    # -------------------------------------------------

    openapi_tags=OPENAPI_TAGS,

    # -------------------------------------------------
    # PROJECT CONTACT
    # -------------------------------------------------

    contact={
        "name": "MEDISCOPE Project",
    },
)


# =====================================================
# CORS CONFIGURATION
# =====================================================

# Browser origins are supplied through environment-backed
# application settings so deployment does not require
# editing source code.
#
# MEDISCOPE does not use "*" because authenticated
# requests include Authorization headers and credentials.
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        settings
        .allowed_origins
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# REGISTER VERSIONED API ROUTES
# =====================================================

app.include_router(
    api_router
)


# =====================================================
# ROOT ENDPOINT
# =====================================================

@app.get(
    "/",
    tags=["System"],
    summary="MEDISCOPE API information",
)
def root() -> dict[str, str]:
    """
    Return general information about the MEDISCOPE API.

    Providing this endpoint means visiting
    http://127.0.0.1:8000/
    will return useful information instead of a 404.
    """

    return {
        "application": "MEDISCOPE",
        "status": "running",
        "api_version": "1.0.0",
        "documentation": "/docs",
        "alternative_documentation": "/redoc",
        "clinical_disclaimer": (
            "MEDISCOPE is a clinical decision-support "
            "prototype and must not be used as an "
            "autonomous diagnostic or treatment system."
        ),
        "data_notice": (
            "All patient records used by this prototype "
            "must be synthetic."
        ),
    }


# =====================================================
# HEALTH CHECK ENDPOINT
# =====================================================

@app.get(
    "/health",
    tags=["System"],
    summary="Application health check",
)
def health_check() -> dict[str, str | bool]:
    """
    Confirm that the MEDISCOPE API process is responding.

    The response also exposes two important prototype
    safety boundaries:

    - only synthetic patient data may be used;
    - MEDISCOPE is a decision-support tool, not a
      diagnostic system.
    """

    return {
        "status": "healthy",
        "application": "MEDISCOPE",
        "environment": settings.environment,
        "synthetic_data_only": True,
        "clinical_disclaimer": (
            "MEDISCOPE provides clinical decision support "
            "only and is not diagnosis, not an autonomous "
            "treatment decision system, and not a "
            "replacement for professional clinical judgement."
        ),
    }
