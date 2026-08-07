"""
=========================================================
Email Delivery Service

MEDISCOPE
LTFU Prediction Platform

Purpose:
    Sends authentication-related emails for:

    - email verification OTPs;
    - forgotten-password reset links.

Development behaviour:
    When EMAIL_CONSOLE_BACKEND is enabled, messages are
    printed in the API terminal instead of being sent
    through an SMTP server.

Security:
    - OTPs and reset tokens are never stored in this file.
    - Sensitive authentication values must not be written
      to database audit logs.
    - Console delivery must only be used with synthetic
      demonstration accounts.

=========================================================
"""

from __future__ import annotations


# =====================================================
# STANDARD LIBRARY IMPORTS
# =====================================================

import logging
import smtplib

from email.message import EmailMessage
from uuid import UUID


# =====================================================
# SQLALCHEMY IMPORTS
# =====================================================

from sqlalchemy.orm import Session


# =====================================================
# APPLICATION IMPORTS
# =====================================================

from app.core.config import get_settings


# =====================================================
# LOGGER CONFIGURATION
# =====================================================

logger = logging.getLogger(
    __name__
)


# =====================================================
# INTERNAL EMAIL DELIVERY FUNCTION
# =====================================================

def deliver_email(
    *,
    recipient: str,
    subject: str,
    body: str,
) -> bool:
    """
    Deliver an email using either the development console
    backend or an SMTP server.

    Parameters
    ----------
    recipient:
        Destination email address.

    subject:
        Email subject line.

    body:
        Plaintext email content.

    Returns
    -------
    bool
        True when delivery succeeds, otherwise False.
    """

    settings = get_settings()

    # -------------------------------------------------
    # DEVELOPMENT CONSOLE DELIVERY
    #
    # This prints the email content in the terminal.
    # It is appropriate only for local development using
    # synthetic demonstration accounts.
    # -------------------------------------------------

    # if settings.email_console_backend:

    #     logger.info(
    #         "\n"
    #         + "=" * 60
    #         + "\nMEDISCOPE DEVELOPMENT EMAIL"
    #         + "\n"
    #         + "=" * 60
    #         + "\nRecipient: %s"
    #         + "\nSubject: %s"
    #         + "\n"
    #         + "-" * 60
    #         + "\n%s"
    #         + "\n"
    #         + "=" * 60,
    #         recipient,
    #         subject,
    #         body,
    #     )

    #     return True

        # -------------------------------------------------
    # DEVELOPMENT CONSOLE DELIVERY
    #
    # Authentication emails are printed directly to the
    # terminal during local development. This avoids
    # dependency on logging levels configured by Uvicorn.
    #
    # IMPORTANT:
    # Console delivery must only be used with synthetic
    # development accounts, never real patient accounts.
    # -------------------------------------------------

    if settings.email_console_backend:

        print()
        print("=" * 60)
        print("MEDISCOPE DEVELOPMENT EMAIL")
        print("=" * 60)
        print(f"Recipient : {recipient}")
        print(f"Subject   : {subject}")
        print("-" * 60)
        print(body)
        print("=" * 60)
        print()

        return True

    # -------------------------------------------------
    # SMTP CONFIGURATION VALIDATION
    # -------------------------------------------------

    if not settings.smtp_host:

        logger.error(
            "Email delivery failed because SMTP_HOST "
            "is not configured."
        )

        return False

    # -------------------------------------------------
    # BUILD EMAIL MESSAGE
    # -------------------------------------------------

    message = EmailMessage()

    message["From"] = str(
        settings.email_from
    )

    message["To"] = recipient

    message["Subject"] = subject

    message.set_content(
        body
    )

    # -------------------------------------------------
    # SEND EMAIL THROUGH SMTP
    # -------------------------------------------------

    try:

        with smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
            timeout=20,
        ) as smtp:

            if settings.smtp_use_tls:

                smtp.starttls()

            if (
                settings.smtp_username
                and settings.smtp_password
            ):

                smtp.login(
                    settings.smtp_username,
                    settings.smtp_password,
                )

            smtp.send_message(
                message
            )

        logger.info(
            "Email sent successfully to %s.",
            recipient,
        )

        return True

    except Exception:

        logger.exception(
            "Email delivery failed for %s.",
            recipient,
        )

        return False


# =====================================================
# EMAIL VERIFICATION OTP
# =====================================================

def send_verification_otp(
    db: Session,
    *,
    user_id: UUID,
    recipient: str,
    otp: str,
) -> bool:
    """
    Send an email-verification OTP.

    The database session and user identifier are included
    for compatibility with the authentication service and
    future delivery-record logging.

    Parameters
    ----------
    db:
        Active SQLAlchemy session.

    user_id:
        Identifier of the account being verified.

    recipient:
        User's registered email address.

    otp:
        Plaintext six-digit verification code.

    Returns
    -------
    bool
        True if delivery succeeds.
    """

    settings = get_settings()

    subject = (
        "Verify your MEDISCOPE email address"
    )

    body = (
        "Welcome to MEDISCOPE.\n\n"
        f"Your email verification code is: {otp}\n\n"
        "The code expires in "
        f"{settings.otp_expire_minutes} minutes.\n\n"
        "Do not share this code with anyone.\n\n"
        "If you did not create a MEDISCOPE account, "
        "you may ignore this message."
    )

    # These parameters will support delivery auditing in
    # a later implementation milestone.
    _ = db
    _ = user_id

    return deliver_email(
        recipient=recipient,
        subject=subject,
        body=body,
    )


# =====================================================
# PASSWORD RESET EMAIL
# =====================================================

def send_password_reset(
    db: Session,
    *,
    user_id: UUID,
    recipient: str,
    reset_token: str,
) -> bool:
    """
    Send password-reset instructions.

    Parameters
    ----------
    db:
        Active SQLAlchemy session.

    user_id:
        Identifier of the account requesting a reset.

    recipient:
        User's registered email address.

    reset_token:
        Plaintext single-use password-reset token.

    Returns
    -------
    bool
        True if delivery succeeds.
    """

    settings = get_settings()

    reset_url = (
        f"{settings.frontend_base_url}"
        "/reset-password"
        f"?token={reset_token}"
    )

    subject = (
        "Reset your MEDISCOPE password"
    )

    body = (
        "A password reset was requested for your "
        "MEDISCOPE account.\n\n"
        "Use the following link to choose a new password:\n\n"
        f"{reset_url}\n\n"
        "The link expires in "
        f"{settings.password_reset_expire_minutes} "
        "minutes.\n\n"
        "If you did not request this password reset, "
        "ignore this message."
    )

    # Retained for future email-delivery audit records.
    _ = db
    _ = user_id

    return deliver_email(
        recipient=recipient,
        subject=subject,
        body=body,
    )
