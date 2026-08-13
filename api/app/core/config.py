"""
=========================================================
MEDISCOPE Application Configuration

LTFU Prediction in HIV Treatment Programmes
Rome Business School Capstone Project

File:
    config.py

Purpose:
    Defines the environment-backed configuration used by
    the MEDISCOPE FastAPI backend.

    Configuration includes:

    - application settings;
    - PostgreSQL connectivity;
    - JWT authentication;
    - password and OTP policies;
    - refresh-token settings;
    - TOTP multi-factor authentication;
    - email and SMTP delivery;
    - machine-learning model locations.

Security:
    Real credentials and secrets must be stored in the
    project's local .env file.

    The .env file must never be committed to GitHub.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations
from pathlib import Path


# =====================================================
# STANDARD LIBRARY IMPORTS
# =====================================================

from functools import lru_cache


# =====================================================
# PYDANTIC IMPORTS
# =====================================================

from pydantic import (
    EmailStr,
    Field,
)

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


# =====================================================
# APPLICATION IMPORTS
# =====================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)

ENV_FILE = (
    PROJECT_ROOT
    / ".env"
)


# =====================================================
# APPLICATION SETTINGS
# =====================================================

class Settings(BaseSettings):
    """
    Typed MEDISCOPE configuration.

    Pydantic reads matching values from environment
    variables and from the project-root .env file.

    Environment-variable names are case-insensitive.
    """

    # -------------------------------------------------
    # PYDANTIC SETTINGS CONFIGURATION
    # -------------------------------------------------

    model_config = SettingsConfigDict(
        env_file=   ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # =================================================
    # GENERAL APPLICATION SETTINGS
    # =================================================

    app_name: str = "MEDISCOPE"

    environment: str = "development"

    debug: bool = False

    # Base address of the future frontend application.
    # Password-reset links are constructed from this URL.
    frontend_base_url: str = (
        "http://localhost:3000"
    )

    # =================================================
    # DATABASE SETTINGS
    # =================================================

    # This default is a placeholder only.
    # The real value must be provided in .env.
    database_url: str = (
        "postgresql+psycopg://"
        "mediscope:change-me@"
        "localhost:5432/mediscope"
    )

    # =================================================
    # JWT ACCESS-TOKEN SETTINGS
    # =================================================

    # The real secret must be supplied through .env.
    secret_key: str = Field(
        default=(
            "CHANGE-THIS-IN-.ENV-WITH-A-"
            "LONG-RANDOM-SECRET"
        ),
        min_length=32,
    )

    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = 30

    # =================================================
    # REFRESH-TOKEN SETTINGS
    # =================================================

    refresh_token_expire_days: int = 7

    # =================================================
    # PASSWORD SECURITY SETTINGS
    # =================================================

    password_min_length: int = 12

    # =================================================
    # EMAIL VERIFICATION OTP SETTINGS
    # =================================================

    otp_expire_minutes: int = 10

    otp_max_attempts: int = 5

    # =================================================
    # PASSWORD-RESET SETTINGS
    # =================================================

    password_reset_expire_minutes: int = 20

    # =================================================
    # TOTP MULTI-FACTOR AUTHENTICATION
    # =================================================

    # Name displayed inside authenticator applications.
    totp_issuer_name: str = "MEDISCOPE"

    # MFA challenge tokens should remain short-lived.
    mfa_challenge_expire_minutes: int = 5

    # Number of single-use recovery codes generated when
    # TOTP MFA is successfully enabled.
    mfa_recovery_code_count: int = 10

    # =================================================
    # EMAIL DELIVERY SETTINGS
    # =================================================

    # Sender address displayed in authentication emails.
    email_from: EmailStr = (
        "noreply@example.com"
    )

    # When True, authentication emails are displayed in
    # the Uvicorn terminal rather than sent through SMTP.
    #
    # This should be used only for local development with
    # synthetic demonstration accounts.
    email_console_backend: bool = True

    # SMTP fields can remain empty while console delivery
    # is enabled.
    smtp_host: str | None = None

    smtp_port: int = 587

    smtp_username: str | None = None

    smtp_password: str | None = None

    smtp_use_tls: bool = True

    # =================================================
    # DATA-GOVERNANCE SETTINGS
    # =================================================

    # MEDISCOPE currently permits synthetic application
    # records only.
    synthetic_data_only: bool = True

    # =================================================
    # MACHINE-LEARNING MODEL SETTINGS
    # =================================================

    logistic_model_path: str = (
        "models/trained/"
        "logistic_regression_pipeline.joblib"
    )

    xgboost_model_path: str = (
        "models/trained/"
        "xgboost_pipeline.joblib"
    )

    decision_threshold: float = 0.50


# =====================================================
# CACHED SETTINGS ACCESSOR
# =====================================================

@lru_cache(
    maxsize=1
)
def get_settings() -> Settings:
    """
    Return the shared MEDISCOPE configuration instance.

    Caching prevents the .env file from being repeatedly
    re-read during every API request.
    """

    return Settings()
