# =========================================================
# MEDISCOPE FastAPI Backend
#
# Purpose:
#     Build the production container for the MEDISCOPE
#     FastAPI application and deployed ML inference models.
#
# Repository layout is deliberately preserved inside the
# image so that:
#
#     api/app/core/config.py -> parents[3] -> /workspace
#
# This matches the local project-root relationship and
# keeps model and Alembic paths consistent.
# =========================================================


# ---------------------------------------------------------
# BASE PYTHON IMAGE
# ---------------------------------------------------------

FROM python:3.11-slim


# ---------------------------------------------------------
# PYTHON RUNTIME SETTINGS
# ---------------------------------------------------------

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose /workspace/api as a Python import root so imports
# such as:
#
#     from app.core.config import ...
#
# work while the container itself remains rooted at the
# repository-equivalent /workspace directory.
ENV PYTHONPATH=/workspace/api


# ---------------------------------------------------------
# CONTAINER PROJECT ROOT
# ---------------------------------------------------------

WORKDIR /workspace


# ---------------------------------------------------------
# SYSTEM RUNTIME DEPENDENCIES
#
# libpq5:
#     PostgreSQL client library required by psycopg.
#
# libgomp1:
#     OpenMP runtime used by libraries such as XGBoost.
# ---------------------------------------------------------

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    libpq5 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*


# ---------------------------------------------------------
# PYTHON DEPENDENCIES
#
# Copy first so Docker can reuse this layer when only
# application source code changes.
# ---------------------------------------------------------

COPY requirements.txt /workspace/requirements.txt

RUN pip install \
    --no-cache-dir \
    --upgrade pip \
    && pip install \
    --no-cache-dir \
    -r /workspace/requirements.txt


# ---------------------------------------------------------
# FASTAPI APPLICATION
# ---------------------------------------------------------

COPY api/app /workspace/api/app


# ---------------------------------------------------------
# ALEMBIC MIGRATIONS
#
# alembic.ini expects:
#
#     %(here)s/api/alembic
#
# Because alembic.ini is copied to /workspace, preserving
# /workspace/api/alembic keeps that configuration valid.
# ---------------------------------------------------------

COPY api/alembic /workspace/api/alembic

COPY alembic.ini /workspace/alembic.ini


# ---------------------------------------------------------
# DEPLOYED MACHINE-LEARNING MODELS
#
# The repository-equivalent location means the default
# paths resolved by config.py become:
#
#     /workspace/models/trained/...
# ---------------------------------------------------------

COPY models /workspace/models


# ---------------------------------------------------------
# API PORT
# ---------------------------------------------------------

EXPOSE 8000


# ---------------------------------------------------------
# PRODUCTION ASGI ENTRY POINT
#
# Docker's JSON-form CMD must remain one Docker
# instruction. Keeping it on one line avoids the parsing
# problem reported by the Dockerfile language server.
# ---------------------------------------------------------

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
