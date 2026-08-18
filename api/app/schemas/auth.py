"""
=========================================================
MEDISCOPE Core Authentication Schemas

Purpose:
    Define the Pydantic request and response models used
    by MEDISCOPE's primary account-registration and login
    entry points.

This module is intentionally focused on the initial
authentication workflow:

    - user registration;
    - username/email and password login;
    - generic authentication responses.

More advanced account-security workflows are defined in:

    app.schemas.authentication

Those workflows include:

    - email OTP verification;
    - verification-code resend;
    - forgotten-password handling;
    - password-reset confirmation;
    - refresh-token rotation;
    - logout and token revocation;
    - TOTP MFA enrolment;
    - MFA login verification;
    - MFA recovery codes;
    - mandatory MFA enrolment for privileged roles.

Security:
    Incoming authentication data is validated before it
    reaches route or service logic.

    Email addresses are normalised to lowercase to reduce
    duplicate-account and comparison inconsistencies.

    Password validation performed here establishes only
    the request-level length requirement. Password hashing,
    credential verification and other authentication
    security controls belong to the security/service layer.

    Sensitive authentication values must never be written
    to application logs or audit metadata.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations


# =====================================================
# STANDARD LIBRARY IMPORTS
# =====================================================

from datetime import date


# =====================================================
# PYDANTIC IMPORTS
# =====================================================

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
)


# =====================================================
# USER REGISTRATION REQUEST
# =====================================================

class RegisterRequest(BaseModel):
    """
    Validate the information supplied when creating a new
    MEDISCOPE user account.

    Registration creates an application user account only.

    Linking a standard USER account to a synthetic patient
    record is a separate administrative workflow and must
    not be inferred automatically from registration data.
    """

    first_name: str = Field(
        min_length=2,
        max_length=100,
    )

    last_name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    phone: str | None = Field(
        default=None,
        max_length=40,
    )

    gender: str = Field(
        min_length=4,
        max_length=6,
    )

    date_of_birth: date

    password: str = Field(
        min_length=12,
        max_length=200,
    )


    # -------------------------------------------------
    # EMAIL NORMALISATION
    # -------------------------------------------------

    @field_validator(
        "email"
    )
    @classmethod
    def normalise_email(
        cls,
        value: EmailStr,
    ) -> str:
        """
        Normalise email addresses before they reach the
        registration workflow.

        Lowercasing and stripping surrounding whitespace
        helps ensure consistent account lookup and
        uniqueness handling.
        """

        return (
            str(value)
            .strip()
            .lower()
        )


    # -------------------------------------------------
    # NAME NORMALISATION
    # -------------------------------------------------

    @field_validator(
        "first_name",
        "last_name",
    )
    @classmethod
    def strip_name(
        cls,
        value: str,
    ) -> str:
        """
        Remove accidental surrounding whitespace from
        supplied first and last names.
        """

        return value.strip()


    # -------------------------------------------------
    # GENDER VALIDATION
    # -------------------------------------------------

    @field_validator(
        "gender"
    )
    @classmethod
    def validate_gender(
        cls,
        value: str,
    ) -> str:
        """
        Restrict the registration value to the gender
        values currently supported by the MEDISCOPE data
        model.
        """

        if value not in {
            "Male",
            "Female",
        }:
            raise ValueError(
                "Gender must be Male or Female."
            )

        return value


# =====================================================
# LOGIN REQUEST
# =====================================================

class LoginRequest(BaseModel):
    """
    Validate credentials supplied to the primary login
    endpoint.

    Successful password verification does not necessarily
    mean that normal authentication tokens are immediately
    issued.

    Depending on account state and role, the authentication
    workflow may instead require:

        - email verification;
        - an MFA challenge; or
        - mandatory MFA enrolment.

    Those workflows are represented by the schemas in
    app.schemas.authentication.
    """

    email: EmailStr

    password: str


    # -------------------------------------------------
    # EMAIL NORMALISATION
    # -------------------------------------------------

    @field_validator(
        "email"
    )
    @classmethod
    def normalise_email(
        cls,
        value: EmailStr,
    ) -> str:
        """
        Normalise the login email so authentication uses
        the same canonical form as registration.
        """

        return (
            str(value)
            .strip()
            .lower()
        )


# =====================================================
# GENERIC AUTHENTICATION RESPONSE
# =====================================================

class GenericResponse(BaseModel):
    """
    Return a simple authentication-related response
    message.

    Generic responses are particularly useful where the
    API should avoid exposing unnecessary account-state
    information.
    """

    message: str
