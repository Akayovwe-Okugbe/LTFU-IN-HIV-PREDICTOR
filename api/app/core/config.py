"""
=========================================================
MEDISCOPE Application Configuration

LTFU Prediction in HIV Treatment Programmes
Rome Business School Capstone Project

Purpose:
    Define typed, environment-backed configuration for the
    MEDISCOPE FastAPI backend.

Configuration includes:

    - application environment;
    - frontend integration;
    - PostgreSQL connectivity;
    - JWT access-token configuration;
    - password and OTP policies;
    - refresh-token lifecycle;
    - TOTP multi-factor authentication;
    - email and SMTP delivery;
    - synthetic-data governance;
    - machine-learning model locations and threshold.

Security:
    Real credentials and secrets must be supplied through
    environment variables or the local project-root .env
    file.

    The .env file must never be committed to source
    control.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations


# =====================================================
# STANDARD LIBRARY IMPORTS
# =====================================================

from functools import lru_cache
from pathlib import Path
from typing import Literal


# =====================================================
# PYDANTIC IMPORTS
# =====================================================

from pydantic import (
    EmailStr,
    Field,
    model_validator,
)

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


# =====================================================
# PROJECT PATHS
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

    Operating-system environment variables take
    precedence over values supplied through the local
    project-root .env file.

    This allows the same application configuration model
    to support:

        - local development;
        - automated testing;
        - container deployment;
        - hosted production environments.
    """

    # -------------------------------------------------
    # PYDANTIC SETTINGS CONFIGURATION
    # -------------------------------------------------

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


    # =================================================
    # GENERAL APPLICATION SETTINGS
    # =================================================

    app_name: str = "MEDISCOPE"

    environment: Literal[
        "development",
        "testing",
        "production",
    ] = "development"

    debug: bool = False

    # Used when constructing browser-facing application
    # links such as password-reset URLs.
    frontend_base_url: str = (
        "http://localhost:5173"
    )


    # =================================================
    # DATABASE SETTINGS
    # =================================================

    # Development placeholder only.
    #
    # Production validation below prevents MEDISCOPE from
    # starting with this value.
    database_url: str = (
        "postgresql+psycopg://"
        "mediscope:change-me@"
        "localhost:5432/mediscope"
    )


    # =================================================
    # JWT ACCESS-TOKEN SETTINGS
    # =================================================

    secret_key: str = Field(
        default=(
            "CHANGE-THIS-IN-.ENV-WITH-A-"
            "LONG-RANDOM-SECRET"
        ),
        min_length=32,
    )

    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = Field(
        default=30,
        ge=1,
        le=1440,
    )


    # =================================================
    # REFRESH-TOKEN SETTINGS
    # =================================================

    refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        le=90,
    )


    # =================================================
    # PASSWORD SECURITY SETTINGS
    # =================================================

    password_min_length: int = Field(
        default=12,
        ge=12,
        le=200,
    )


    # =================================================
    # EMAIL VERIFICATION OTP SETTINGS
    # =================================================

    otp_expire_minutes: int = Field(
        default=10,
        ge=1,
        le=60,
    )

    otp_max_attempts: int = Field(
        default=5,
        ge=1,
        le=20,
    )


    # =================================================
    # PASSWORD-RESET SETTINGS
    # =================================================

    password_reset_expire_minutes: int = Field(
        default=20,
        ge=1,
        le=120,
    )


    # =================================================
    # TOTP MULTI-FACTOR AUTHENTICATION
    # =================================================

    # Dedicated Fernet key used to protect TOTP secrets
    # at rest.
    #
    # This key must be generated independently from the
    # JWT SECRET_KEY and must remain stable for as long as
    # encrypted MFA secrets need to be decrypted.
    #
    # Generate with:
    #
    # python -c "from cryptography.fernet import Fernet; \
    # print(Fernet.generate_key().decode())"
    #
    # Fernet keys are URL-safe Base64 encoded 32-byte keys
    # and are normally 44 characters long.
    totp_encryption_key: str = Field(
        default="",
        max_length=44,
    )

    # Name displayed inside authenticator applications.
    totp_issuer_name: str = "MEDISCOPE"

    mfa_challenge_expire_minutes: int = Field(
        default=5,
        ge=1,
        le=30,
    )

    mfa_recovery_code_count: int = Field(
        default=10,
        ge=1,
        le=50,
    )


    # =================================================
    # EMAIL DELIVERY SETTINGS
    # =================================================

    email_from: EmailStr = (
        "noreply@example.com"
    )

    # Local-development convenience only.
    # Production validation below prevents console email
    # delivery from being accidentally enabled.
    email_console_backend: bool = True

    smtp_host: str | None = None

    smtp_port: int = Field(
        default=587,
        ge=1,
        le=65535,
    )

    smtp_username: str | None = None

    smtp_password: str | None = None

    smtp_use_tls: bool = True


    # =================================================
    # DATA GOVERNANCE
    # =================================================

    synthetic_data_only: bool = True


    # =================================================
    # MACHINE-LEARNING MODEL SETTINGS
    # =================================================

    logistic_model_path: str = str(
        PROJECT_ROOT
        / "models"
        / "trained"
        / "logistic_regression_pipeline.joblib"
    )

    xgboost_model_path: str = str(
        PROJECT_ROOT
        / "models"
        / "trained"
        / "xgboost_pipeline.joblib"
    )

    decision_threshold: float = Field(
        default=0.50,
        ge=0.0,
        le=1.0,
    )


    # =================================================
    # SECURITY CONFIGURATION VALIDATION
    # =================================================

    @model_validator(
        mode="after"
    )
    def validate_security_settings(
        self,
    ) -> "Settings":
        """
        Validate security-critical MEDISCOPE settings.

        TOTP encryption is required in every environment
        because authenticator secrets must never silently
        fall back to plaintext persistence.

        Additional deployment safeguards are enforced when
        ENVIRONMENT=production.
        """


        # ---------------------------------------------
        # TOTP ENCRYPTION KEY
        # ---------------------------------------------

        if not self.totp_encryption_key:
            raise ValueError(
                "TOTP_ENCRYPTION_KEY must be configured."
            )

        if (
            len(
                self.totp_encryption_key
            )
            != 44
        ):
            raise ValueError(
                "TOTP_ENCRYPTION_KEY must be a valid "
                "44-character Fernet key."
            )


        # ---------------------------------------------
        # DEVELOPMENT / TESTING
        #
        # The remaining checks are production-specific.
        # ---------------------------------------------

        if (
            self.environment
            != "production"
        ):
            return self


        # ---------------------------------------------
        # SECRET KEY
        # ---------------------------------------------

        if (
            "CHANGE-THIS"
            in self.secret_key.upper()
            or
            "REPLACE"
            in self.secret_key.upper()
        ):
            raise ValueError(
                "A production SECRET_KEY must be "
                "configured."
            )


        # ---------------------------------------------
        # DATABASE CREDENTIALS
        # ---------------------------------------------

        if (
            "change-me"
            in self.database_url.lower()
            or
            "replace-me"
            in self.database_url.lower()
        ):
            raise ValueError(
                "A production DATABASE_URL must be "
                "configured."
            )


        # ---------------------------------------------
        # EMAIL DELIVERY
        # ---------------------------------------------

        if self.email_console_backend:
            raise ValueError(
                "EMAIL_CONSOLE_BACKEND must be false "
                "in production."
            )


        # ---------------------------------------------
        # DATA GOVERNANCE
        # ---------------------------------------------

        if not self.synthetic_data_only:
            raise ValueError(
                "This MEDISCOPE prototype requires "
                "SYNTHETIC_DATA_ONLY=true."
            )


        return self


# =====================================================
# CACHED SETTINGS ACCESSOR
# =====================================================

@lru_cache(
    maxsize=1,
)
def get_settings() -> Settings:
    """
    Return the shared MEDISCOPE configuration instance.

    Caching prevents the settings object and local .env
    file from being reconstructed for every API request.
    """

    return Settings()
