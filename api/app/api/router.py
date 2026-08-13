"""
=========================================================
MEDISCOPE API Router

Purpose:
    Register all versioned API route modules used by the
    MEDISCOPE backend.

Responsibilities:
    - Apply the global /api/v1 prefix.
    - Register authentication routes.
    - Register user-management routes.
    - Register patient-management routes.
    - Provide a single router consumed by app.main.

Author:
    Akayovwe Okugbe

=========================================================
"""

from fastapi import APIRouter

from app.api.routes import (
    administration,
    audit_logs,
    auth,
    authentication_phase2,
    change_requests,
    clinical_records,
    clinician_intelligence,
    messaging,
    patients,
    users,
    predictions,
)


# =====================================================
# CREATE VERSIONED API ROUTER
# =====================================================

api_router = APIRouter(
    prefix="/api/v1",
)


# =====================================================
# AUTHENTICATION ROUTES
#
# auth.py contains registration and password login.
#
# authentication_phase2.py contains:
# - email verification
# - password recovery
# - refresh-token rotation
# - logout
# - TOTP MFA
#
# Both appear under the same "Authentication" section
# in Swagger.
# =====================================================

api_router.include_router(
    auth.router
)

api_router.include_router(
    authentication_phase2.router
)

# =====================================================
# USER ROUTES
# =====================================================

api_router.include_router(
    users.router
)

# =====================================================
# PATIENT ROUTES
# =====================================================

api_router.include_router(
    patients.router
)

# =====================================================
# ADMINISTRATION ROUTES
# =====================================================

api_router.include_router(
    administration.router
)

api_router.include_router(
    audit_logs.router
)

# =====================================================
# CLINICAL RECORDS ROUTES
# =====================================================
api_router.include_router(
    clinical_records.router
)

api_router.include_router(
    clinician_intelligence.router
)

# =====================================================
# CHANGE REQUESTS ROUTES
# =====================================================
api_router.include_router(
    change_requests.router
)

# =====================================================
# MESSAGING ROUTES
# =====================================================

api_router.include_router(
    messaging.router
)

# =====================================================
# PREDICTION ROUTES
# =====================================================

api_router.include_router(
    predictions.router
)
