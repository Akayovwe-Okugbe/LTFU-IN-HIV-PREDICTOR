"""
=========================================================
Logger Configuration

LTFU Prediction in HIV Treatment Programmes
Rome Business School Capstone Project

Purpose:
    Configure project-wide logging.

    All preprocessing, feature engineering,
    model training and evaluation activities
    are recorded automatically.

Author:
    Akayovwe Okugbe
=========================================================
"""

import logging

from pathlib import Path

from src.config import REPORTS


# =====================================================
# CREATE REPORT DIRECTORY IF IT DOES NOT EXIST
# =====================================================

REPORTS.mkdir(parents=True, exist_ok=True)


# =====================================================
# LOG FILE LOCATION
# =====================================================

LOG_FILE = REPORTS / "logs" / "project.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


# =====================================================
# CONFIGURE LOGGER
# =====================================================

logging.basicConfig(

    level=logging.INFO,

    format="%(asctime)s | %(levelname)s | %(message)s",

    handlers=[

        logging.FileHandler(
            LOG_FILE,
            encoding="utf-8"
        ),

        logging.StreamHandler()

    ]

)

logger = logging.getLogger("LTFU_HIV")

if not logger.handlers:

    logger.setLevel(logging.INFO)
