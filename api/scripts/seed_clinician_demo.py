"""
=========================================================
MEDISCOPE Clinician Demonstration Seeder

File:
    scripts/seed_clinician_demo.py

Purpose:
    Populate MEDISCOPE with a rich synthetic demonstration
    cohort for clinician-dashboard and patient-intelligence
    visualisation.

IMPORTANT:
    - ALL created patients are synthetic.
    - Generated prediction probabilities are DEMONSTRATION
      DATA ONLY.
    - They are NOT outputs from the trained MEDISCOPE
      machine-learning models.
    - They must NOT be used as model-performance evidence
      in the capstone report.

Creates:
    - administrator account if required;
    - several clinician accounts;
    - standard USER accounts;
    - synthetic patient profiles;
    - patient-user links;
    - clinician-patient assignments;
    - longitudinal clinical records;
    - Logistic Regression / XGBoost model-registry entries;
    - historical stored prediction snapshots;
    - deliberate missing-data patterns;
    - model-agreement and disagreement examples.

Design:
    The dataset is deterministic and safe to rerun.
    Existing records identified by demo email addresses and
    synthetic patient numbers are reused rather than
    duplicated.

Author:
    Akayovwe Okugbe

=========================================================
"""

from __future__ import annotations


# =====================================================
# STANDARD LIBRARY
# =====================================================

import random

from datetime import (
    UTC,
    date,
    datetime,
    timedelta,
)

from uuid import UUID


# =====================================================
# SQLALCHEMY
# =====================================================

from sqlalchemy import (
    select,
)


# =====================================================
# APPLICATION IMPORTS
# =====================================================

from app.core.enums import (
    AccountStatus,
    UserRole,
)

from app.core.security import (
    hash_password,
)

from app.models.entities import (
    ClinicalRecord,
    ClinicianPatientAssignment,
    ModelRegistry,
    Patient,
    Prediction,
    User,
)

# -----------------------------------------------------
# IMPORTANT:
# If your session factory lives somewhere else,
# change ONLY this import.
# -----------------------------------------------------

from app.db.session import SessionLocal


# =====================================================
# DETERMINISTIC RANDOMNESS
# =====================================================

RANDOM_SEED = 20260813

random.seed(
    RANDOM_SEED
)


# =====================================================
# DEMONSTRATION CONFIGURATION
# =====================================================

DEMO_PASSWORD = (
    "MediScopeDemo2026!"
)

PATIENT_COUNT = 52

USER_LINK_RATE = 0.78

PREDICTION_COVERAGE_RATE = 0.86


# =====================================================
# NIGERIAN CONTEXT
# =====================================================

LOCATIONS = [
    (
        "Lagos",
        [
            "Ikeja",
            "Surulere",
            "Alimosho",
            "Kosofe",
            "Lagos Mainland",
        ],
    ),
    (
        "Federal Capital Territory",
        [
            "Abuja Municipal",
            "Bwari",
            "Gwagwalada",
            "Kuje",
        ],
    ),
    (
        "Kano",
        [
            "Tarauni",
            "Nassarawa",
            "Gwale",
            "Dala",
        ],
    ),
    (
        "Kaduna",
        [
            "Kaduna North",
            "Kaduna South",
            "Chikun",
            "Zaria",
        ],
    ),
    (
        "Rivers",
        [
            "Port Harcourt",
            "Obio/Akpor",
            "Eleme",
        ],
    ),
    (
        "Oyo",
        [
            "Ibadan North",
            "Ibadan South-West",
            "Akinyele",
        ],
    ),
    (
        "Enugu",
        [
            "Enugu North",
            "Enugu South",
            "Nsukka",
        ],
    ),
    (
        "Anambra",
        [
            "Awka South",
            "Onitsha North",
            "Nnewi North",
        ],
    ),
    (
        "Delta",
        [
            "Warri South",
            "Oshimili South",
            "Uvwie",
        ],
    ),
    (
        "Edo",
        [
            "Oredo",
            "Egor",
            "Ikpoba-Okha",
        ],
    ),
]


MALE_FIRST_NAMES = [
    "Chinedu",
    "Emeka",
    "Ibrahim",
    "Musa",
    "Tunde",
    "Kunle",
    "Samuel",
    "Daniel",
    "David",
    "Victor",
    "Sani",
    "Ahmed",
    "Femi",
    "Joseph",
    "Peter",
    "Collins",
    "Uche",
    "Obinna",
    "Adewale",
    "Sunday",
]


FEMALE_FIRST_NAMES = [
    "Adaeze",
    "Ngozi",
    "Amina",
    "Fatima",
    "Blessing",
    "Grace",
    "Esther",
    "Chioma",
    "Yetunde",
    "Bisi",
    "Hauwa",
    "Zainab",
    "Mercy",
    "Joy",
    "Amaka",
    "Ifeoma",
    "Mary",
    "Ruth",
    "Temitope",
    "Halima",
]


LAST_NAMES = [
    "Okafor",
    "Adeyemi",
    "Bello",
    "Musa",
    "Eze",
    "Nwankwo",
    "Ibrahim",
    "Balogun",
    "Ogunleye",
    "Mohammed",
    "Okoro",
    "Abubakar",
    "Ojo",
    "Chukwu",
    "Adebayo",
    "Umar",
    "Onyeka",
    "Lawal",
    "Aliyu",
    "Obi",
    "Osei",
    "Ekanem",
    "Edet",
    "Okon",
    "Usman",
]


REGIMENS = [
    "TLD",
    "TDF/3TC/DTG",
    "ABC/3TC/DTG",
    "AZT/3TC/DTG",
]


# =====================================================
# CLINICIAN DEFINITIONS
# =====================================================

CLINICIANS = [
    {
        "email":
            "dr.adaeze.okafor@mediscope.demo",

        "first_name":
            "Adaeze",

        "last_name":
            "Okafor",

        "phone":
            "+2348035550101",
    },
    {
        "email":
            "dr.ibrahim.bello@mediscope.demo",

        "first_name":
            "Ibrahim",

        "last_name":
            "Bello",

        "phone":
            "+2348035550102",
    },
    {
        "email":
            "dr.temitope.adeyemi@mediscope.demo",

        "first_name":
            "Temitope",

        "last_name":
            "Adeyemi",

        "phone":
            "+2348035550103",
    },
    {
        "email":
            "dr.chinedu.eze@mediscope.demo",

        "first_name":
            "Chinedu",

        "last_name":
            "Eze",

        "phone":
            "+2348035550104",
    },
]


# =====================================================
# GENERIC HELPERS
# =====================================================

def utcnow() -> datetime:
    """
    Return a timezone-aware UTC timestamp.
    """

    return datetime.now(
        UTC
    )


def random_date_between(
    start: date,
    end: date,
) -> date:
    """
    Return a deterministic random date between two dates.
    """

    days = (
        end
        -
        start
    ).days

    return (
        start
        +
        timedelta(
            days=random.randint(
                0,
                days,
            )
        )
    )


def probability_clamp(
    value: float,
) -> float:
    """
    Keep demonstration probability inside a sensible
    display range.
    """

    return round(
        min(
            0.98,
            max(
                0.02,
                value,
            ),
        ),
        4,
    )


# =====================================================
# ACCOUNT HELPERS
# =====================================================

def get_or_create_user(
    db,
    *,
    email: str,
    first_name: str,
    last_name: str,
    role: str,
    phone: str | None = None,
    gender: str | None = None,
    date_of_birth: date | None = None,
) -> User:
    """
    Retrieve an existing demo account or create it.
    """

    normalised_email = (
        email
        .strip()
        .lower()
    )

    existing = db.scalar(
        select(
            User
        ).where(
            User.email
            == normalised_email
        )
    )

    if existing is not None:
        return existing

    user = User(
        email=normalised_email,

        password_hash=hash_password(
            DEMO_PASSWORD
        ),

        first_name=first_name,

        last_name=last_name,

        date_of_birth=date_of_birth,

        phone=phone,

        gender=gender,

        role=role,

        account_status=(
            AccountStatus
            .ACTIVE
            .value
        ),

        email_verified_at=(
            utcnow()
        ),

        # Standard users may demonstrate optional MFA.
        # Privileged accounts are marked enabled so they
        # remain compatible with the mandatory-MFA UX.
        mfa_enabled=False
    )

    db.add(
        user
    )

    db.flush()

    return user


# =====================================================
# ADMINISTRATOR
# =====================================================

def ensure_demo_administrator(
    db,
) -> User:
    """
    Create or reuse one administrator used as the
    assignment creator.
    """

    return get_or_create_user(
        db,

        email=(
            "admin.clinicaldemo@mediscope.demo"
        ),

        first_name="Clinical",

        last_name="Administrator",

        role=(
            UserRole
            .ADMINISTRATOR
            .value
        ),

        phone=(
            "+2348035550001"
        ),

        gender="Female",
    )


# =====================================================
# MODEL REGISTRY
# =====================================================

def ensure_demo_model(
    db,
    *,
    model_name: str,
    version: str,
    algorithm: str,
) -> ModelRegistry:
    """
    Create a clearly marked DEMONSTRATION model-registry
    entry.

    These registry rows exist only so seeded prediction
    snapshots preserve referential integrity.
    """

    existing = db.scalar(
        select(
            ModelRegistry
        ).where(
            ModelRegistry.model_name
            == model_name,

            ModelRegistry.model_version
            == version,
        )
    )

    if existing is not None:
        return existing

    model = ModelRegistry(
        model_name=model_name,

        model_version=version,

        algorithm=algorithm,

        artifact_path=(
            "DEMO_ONLY/"
            "not_a_trained_model.joblib"
        ),

        trained_at=(
            utcnow()
            -
            timedelta(
                days=180
            )
        ),

        deployed_at=(
            utcnow()
            -
            timedelta(
                days=150
            )
        ),

        threshold=0.50,

        feature_schema_version=(
            "demo-clinician-v1"
        ),

        evaluation_metrics={
            "demo_only": True,

            "warning": (
                "Synthetic UI demonstration registry "
                "entry. Not model-performance evidence."
            ),
        },

        is_active=False,

        notes=(
            "DEMONSTRATION ONLY. Prediction values seeded "
            "for frontend and clinician-dashboard testing."
        ),
    )

    db.add(
        model
    )

    db.flush()

    return model


# =====================================================
# PATIENT GENERATION
# =====================================================

def build_patient_identity(
    index: int,
) -> dict:
    """
    Generate a deterministic Nigerian-context synthetic
    patient identity.
    """

    sex = random.choice(
        [
            "Male",
            "Female",
        ]
    )

    if sex == "Male":
        first_name = random.choice(
            MALE_FIRST_NAMES
        )
    else:
        first_name = random.choice(
            FEMALE_FIRST_NAMES
        )

    last_name = random.choice(
        LAST_NAMES
    )

    state, lgas = random.choice(
        LOCATIONS
    )

    lga = random.choice(
        lgas
    )

    dob = random_date_between(
        date(
            1965,
            1,
            1,
        ),
        date(
            2004,
            12,
            31,
        ),
    )

    return {
        "synthetic_patient_number":
            f"MED-DEMO-{index:04d}",

        "first_name":
            first_name,

        "last_name":
            last_name,

        "date_of_birth":
            dob,

        "sex":
            sex,

        "state":
            state,

        "lga":
            lga,

        "status":
            (
                "ACTIVE"
                if random.random()
                < 0.94
                else
                "INACTIVE"
            ),
    }


def get_or_create_patient(
    db,
    *,
    patient_data: dict,
) -> tuple[
    Patient,
    bool,
]:
    """
    Return the patient and whether it was newly created.
    """

    existing = db.scalar(
        select(
            Patient
        ).where(
            (
                Patient
                .synthetic_patient_number
                ==
                patient_data[
                    "synthetic_patient_number"
                ]
            )
        )
    )

    if existing is not None:
        return (
            existing,
            False,
        )

    patient = Patient(
        **patient_data,

        is_synthetic=True,
    )

    db.add(
        patient
    )

    db.flush()

    return (
        patient,
        True,
    )


# =====================================================
# STANDARD USER LINK
# =====================================================

def maybe_link_patient_user(
    db,
    *,
    patient: Patient,
    patient_index: int,
) -> User | None:
    """
    Create a standard account for many, but deliberately
    not all, patients.

    Leaving some patients unlinked gives administration
    views meaningful relationship gaps.
    """

    if (
        patient.linked_user_id
        is not None
    ):
        return db.get(
            User,
            patient.linked_user_id,
        )

    if (
        random.random()
        >
        USER_LINK_RATE
    ):
        return None

    user_email = (
        f"patient{patient_index:04d}"
        "@mediscope.demo"
    )

    gender = (
        "Male"
        if patient.sex
        == "Male"
        else
        "Female"
    )

    user = get_or_create_user(
        db,

        email=user_email,

        first_name=(
            patient.first_name
        ),

        last_name=(
            patient.last_name
        ),

        role=(
            UserRole
            .USER
            .value
        ),

        gender=gender,

        date_of_birth=(
            patient.date_of_birth
        ),

        phone=(
            f"+234810{patient_index:07d}"
        ),
    )

    patient.linked_user_id = (
        user.id
    )

    return user


# =====================================================
# CLINICAL RECORD GENERATION
# =====================================================

def make_clinical_profile(
    *,
    patient: Patient,
    patient_index: int,
) -> dict:
    """
    Generate a latent clinical-demo profile.

    This is NOT a diagnostic profile. It only makes seeded
    records vary enough to exercise the UI.
    """

    # Several demonstration patients deliberately receive
    # more concerning retention-related patterns.
    risk_group_roll = (
        patient_index
        % 10
    )

    if risk_group_roll in {
        0,
        1,
    }:
        profile = (
            "HIGHER_SIGNAL"
        )

    elif risk_group_roll in {
        2,
        3,
        4,
    }:
        profile = (
            "MIXED_SIGNAL"
        )

    else:
        profile = (
            "LOWER_SIGNAL"
        )

    return {
        "profile":
            profile,

        "regimen":
            random.choice(
                REGIMENS
            ),
    }


def seed_clinical_records(
    db,
    *,
    patient: Patient,
    clinician: User,
    patient_index: int,
) -> list[
    ClinicalRecord
]:
    """
    Seed 2-5 longitudinal clinical records.

    Existing records prevent duplicate history on rerun.
    """

    existing = list(
        db.scalars(
            select(
                ClinicalRecord
            ).where(
                ClinicalRecord.patient_id
                == patient.id
            )
        ).all()
    )

    if existing:
        return existing

    profile = (
        make_clinical_profile(
            patient=patient,

            patient_index=(
                patient_index
            ),
        )
    )

    record_count = random.randint(
        2,
        5,
    )

    today = date.today()

    art_start = (
        today
        -
        timedelta(
            days=random.randint(
                500,
                3200,
            )
        )
    )

    if patient.date_of_birth:
        age_at_art = round(
            (
                (
                    art_start
                    -
                    patient.date_of_birth
                ).days
                /
                365.25
            ),
            1,
        )
    else:
        age_at_art = None

    records: list[
        ClinicalRecord
    ] = []

    # Oldest -> newest.
    for sequence in range(
        record_count
    ):
        months_ago = (
            (
                record_count
                -
                sequence
                -
                1
            )
            * 3
        )

        visit_date = (
            today
            -
            timedelta(
                days=(
                    months_ago
                    * 30
                    +
                    random.randint(
                        0,
                        15,
                    )
                )
            )
        )

        profile_name = (
            profile[
                "profile"
            ]
        )

        # ---------------------------------------------
        # VIRAL LOAD
        # ---------------------------------------------

        if (
            profile_name
            == "HIGHER_SIGNAL"
        ):
            viral_load = random.choice(
                [
                    850,
                    1250,
                    1800,
                    3200,
                    5500,
                    9600,
                ]
            )

        elif (
            profile_name
            == "MIXED_SIGNAL"
        ):
            viral_load = random.choice(
                [
                    70,
                    120,
                    280,
                    650,
                    1100,
                ]
            )

        else:
            viral_load = random.choice(
                [
                    20,
                    35,
                    40,
                    50,
                    60,
                    75,
                ]
            )

        # ---------------------------------------------
        # REFILL
        # ---------------------------------------------

        if (
            profile_name
            == "HIGHER_SIGNAL"
        ):
            refill = random.choice(
                [
                    14,
                    21,
                    28,
                    30,
                ]
            )

        elif (
            profile_name
            == "MIXED_SIGNAL"
        ):
            refill = random.choice(
                [
                    30,
                    45,
                    60,
                ]
            )

        else:
            refill = random.choice(
                [
                    60,
                    90,
                    120,
                ]
            )

        # ---------------------------------------------
        # DELIBERATELY MISSING VALUES
        # ---------------------------------------------

        if (
            patient_index
            % 9
            == 0
            and sequence
            ==
            record_count
            -
            1
        ):
            viral_load = None

        if (
            patient_index
            % 11
            == 0
            and sequence
            ==
            record_count
            -
            1
        ):
            refill = None

        last_visit = (
            visit_date
        )

        if (
            patient_index
            % 13
            == 0
            and sequence
            ==
            record_count
            -
            1
        ):
            last_visit = None

        pregnancy_status = None

        if (
            patient.sex
            == "Female"
        ):
            pregnancy_status = (
                random.choice(
                    [
                        "Not pregnant",
                        "Not pregnant",
                        "Not pregnant",
                        "Pregnant",
                        None,
                    ]
                )
            )

        record = ClinicalRecord(
            patient_id=(
                patient.id
            ),

            recorded_by=(
                clinician.id
            ),

            art_start_date=(
                art_start
            ),

            age_at_art_initiation=(
                age_at_art
            ),

            last_regimen=(
                profile[
                    "regimen"
                ]
            ),

            days_of_arv_refill=(
                refill
            ),

            current_viral_load=(
                viral_load
            ),

            pregnancy_status=(
                pregnancy_status
            ),

            last_clinic_visit_date=(
                last_visit
            ),

            notes=(
                "Synthetic demonstration clinical record. "
                "Not associated with a real person."
            ),

            # Give records meaningful historical
            # timestamps for the timeline.
            created_at=(
                datetime.combine(
                    visit_date,
                    datetime.min.time(),
                    tzinfo=UTC,
                )
            ),

            updated_at=(
                datetime.combine(
                    visit_date,
                    datetime.min.time(),
                    tzinfo=UTC,
                )
            ),
        )

        db.add(
            record
        )

        records.append(
            record
        )

    db.flush()

    return records


# =====================================================
# ASSIGNMENT GENERATION
# =====================================================

def ensure_assignment(
    db,
    *,
    clinician: User,
    patient: Patient,
    administrator: User,
) -> ClinicianPatientAssignment:
    """
    Ensure an active clinician-patient assignment exists.
    """

    existing = db.scalar(
        select(
            ClinicianPatientAssignment
        ).where(
            (
                ClinicianPatientAssignment
                .clinician_user_id
                ==
                clinician.id
            ),

            (
                ClinicianPatientAssignment
                .patient_id
                ==
                patient.id
            ),

            (
                ClinicianPatientAssignment
                .is_active
                .is_(
                    True
                )
            ),
        )
    )

    if existing is not None:
        return existing

    assignment = ClinicianPatientAssignment(
        clinician_user_id=(
            clinician.id
        ),

        patient_id=(
            patient.id
        ),

        assigned_by=(
            administrator.id
        ),

        assigned_at=(
            utcnow()
            -
            timedelta(
                days=random.randint(
                    20,
                    400,
                )
            )
        ),

        is_active=True,
    )

    db.add(
        assignment
    )

    db.flush()

    return assignment


# =====================================================
# PREDICTION SNAPSHOT
# =====================================================

def build_prediction_snapshot(
    *,
    patient: Patient,
    latest_record: ClinicalRecord,
    patient_index: int,
) -> dict:
    """
    Build a synthetic model-input snapshot.

    Keys intentionally resemble the clinical inputs
    available in MEDISCOPE.
    """

    snapshot = {
        "age_at_art_initiation":
            latest_record
            .age_at_art_initiation,

        "days_of_arv_refill":
            latest_record
            .days_of_arv_refill,

        "current_viral_load":
            latest_record
            .current_viral_load,

        "last_regimen":
            latest_record
            .last_regimen,

        "last_clinic_visit_date":
            (
                latest_record
                .last_clinic_visit_date
                .isoformat()
                if latest_record
                .last_clinic_visit_date
                else None
            ),

        "sex":
            patient.sex,

        "state":
            patient.state,

        "lga":
            patient.lga,

        "pregnancy_status":
            latest_record
            .pregnancy_status,
    }

    # Additional deliberate missingness specifically
    # exercises input-snapshot quality visualisations.

    if (
        patient_index
        % 8
        == 0
    ):
        snapshot[
            "current_viral_load"
        ] = None

    if (
        patient_index
        % 10
        == 0
    ):
        snapshot[
            "days_of_arv_refill"
        ] = None

    if (
        patient_index
        % 14
        == 0
    ):
        snapshot[
            "last_clinic_visit_date"
        ] = None

    return snapshot


# =====================================================
# DEMONSTRATION PREDICTION PROBABILITIES
# =====================================================

def base_demo_probability(
    *,
    patient_index: int,
) -> float:
    """
    Return a deterministic synthetic probability profile.

    This deliberately creates:
        - above-threshold examples;
        - disagreement examples;
        - below-threshold examples.

    Again: this does NOT invoke a trained ML model.
    """

    category = (
        patient_index
        % 10
    )

    if category in {
        0,
        1,
    }:
        return random.uniform(
            0.69,
            0.91,
        )

    if category in {
        2,
        3,
    }:
        return random.uniform(
            0.48,
            0.68,
        )

    return random.uniform(
        0.15,
        0.47,
    )


def seed_predictions(
    db,
    *,
    patient: Patient,
    clinician: User,
    patient_index: int,
    logistic_model: ModelRegistry,
    xgboost_model: ModelRegistry,
    latest_record: ClinicalRecord,
) -> list[
    Prediction
]:
    """
    Seed historical stored prediction snapshots.

    The seeded values are for dashboard/UI demonstration.
    """

    existing = list(
        db.scalars(
            select(
                Prediction
            ).where(
                Prediction.patient_id
                == patient.id
            )
        ).all()
    )

    if existing:
        return existing

    # Intentionally leave some patients without a stored
    # assessment so prediction coverage is below 100%.
    if (
        random.random()
        >
        PREDICTION_COVERAGE_RATE
    ):
        return []

    prediction_count = random.randint(
        2,
        6,
    )

    threshold = 0.50

    predictions: list[
        Prediction
    ] = []

    current_base = (
        base_demo_probability(
            patient_index=(
                patient_index
            )
        )
    )

    for sequence in range(
        prediction_count
    ):
        months_back = (
            prediction_count
            -
            sequence
            -
            1
        )

        generated_at = (
            utcnow()
            -
            timedelta(
                days=(
                    months_back
                    * 35
                    +
                    random.randint(
                        0,
                        8,
                    )
                )
            )
        )

        # Later assessments broadly move toward the final
        # synthetic risk profile.
        historical_adjustment = (
            (
                sequence
                -
                prediction_count
                +
                1
            )
            *
            random.uniform(
                0.015,
                0.045,
            )
        )

        logistic_probability = (
            probability_clamp(
                current_base
                +
                historical_adjustment
                +
                random.uniform(
                    -0.06,
                    0.06,
                )
            )
        )

        xgboost_probability = (
            probability_clamp(
                current_base
                +
                historical_adjustment
                +
                random.uniform(
                    -0.07,
                    0.07,
                )
            )
        )

        # ---------------------------------------------
        # FORCE SOME EXPLICIT DISAGREEMENTS
        # ---------------------------------------------

        if (
            patient_index
            % 7
            == 0
            and sequence
            ==
            prediction_count
            -
            1
        ):
            logistic_probability = (
                random.uniform(
                    0.58,
                    0.76,
                )
            )

            xgboost_probability = (
                random.uniform(
                    0.26,
                    0.46,
                )
            )

        logistic_classification = (
            "HIGHER_RISK"
            if logistic_probability
            >= threshold
            else
            "LOWER_RISK"
        )

        xgboost_classification = (
            "HIGHER_RISK"
            if xgboost_probability
            >= threshold
            else
            "LOWER_RISK"
        )

        agreement_status = (
            "AGREE"
            if (
                logistic_classification
                ==
                xgboost_classification
            )
            else
            "DISAGREE"
        )

        snapshot = (
            build_prediction_snapshot(
                patient=patient,

                latest_record=(
                    latest_record
                ),

                patient_index=(
                    patient_index
                ),
            )
        )

        review_status = (
            "PENDING"
            if (
                sequence
                ==
                prediction_count
                -
                1
                and patient_index
                % 3
                == 0
            )
            else
            "REVIEWED"
        )

        prediction = Prediction(
            patient_id=(
                patient.id
            ),

            requested_by=(
                clinician.id
            ),

            logistic_model_id=(
                logistic_model.id
            ),

            xgboost_model_id=(
                xgboost_model.id
            ),

            logistic_probability=(
                logistic_probability
            ),

            logistic_classification=(
                logistic_classification
            ),

            xgboost_probability=(
                xgboost_probability
            ),

            xgboost_classification=(
                xgboost_classification
            ),

            agreement_status=(
                agreement_status
            ),

            threshold_used=(
                threshold
            ),

            input_schema_version=(
                "demo-clinician-v1"
            ),

            input_snapshot=(
                snapshot
            ),

            generated_at=(
                generated_at
            ),

            clinical_review_status=(
                review_status
            ),

            reviewed_by=(
                clinician.id
                if review_status
                == "REVIEWED"
                else None
            ),

            reviewed_at=(
                generated_at
                +
                timedelta(
                    hours=4
                )
                if review_status
                == "REVIEWED"
                else None
            ),
        )

        db.add(
            prediction
        )

        predictions.append(
            prediction
        )

    db.flush()

    return predictions


# =====================================================
# MAIN SEED PROCESS
# =====================================================

def seed() -> None:
    """
    Run the complete demonstration population process.
    """

    db = SessionLocal()

    try:
        print(
            "\n"
            "==========================================="
        )

        print(
            " MEDISCOPE CLINICIAN DEMO SEED"
        )

        print(
            "===========================================\n"
        )


        # =============================================
        # ADMINISTRATOR
        # =============================================

        administrator = (
            ensure_demo_administrator(
                db
            )
        )


        # =============================================
        # CLINICIANS
        # =============================================

        clinicians: list[
            User
        ] = []

        for data in CLINICIANS:
            clinician = (
                get_or_create_user(
                    db,

                    email=data[
                        "email"
                    ],

                    first_name=data[
                        "first_name"
                    ],

                    last_name=data[
                        "last_name"
                    ],

                    role=(
                        UserRole
                        .CLINICIAN
                        .value
                    ),

                    phone=data[
                        "phone"
                    ],

                    gender=(
                        "Female"
                        if data[
                            "first_name"
                        ]
                        in {
                            "Adaeze",
                            "Temitope",
                        }
                        else
                        "Male"
                    ),
                )
            )

            clinicians.append(
                clinician
            )


        # =============================================
        # DEMONSTRATION MODEL REGISTRY
        # =============================================

        logistic_model = (
            ensure_demo_model(
                db,

                model_name=(
                    "MEDISCOPE Demo "
                    "Logistic Regression"
                ),

                version=(
                    "demo-1.0"
                ),

                algorithm=(
                    "Logistic Regression"
                ),
            )
        )

        xgboost_model = (
            ensure_demo_model(
                db,

                model_name=(
                    "MEDISCOPE Demo XGBoost"
                ),

                version=(
                    "demo-1.0"
                ),

                algorithm=(
                    "XGBoost"
                ),
            )
        )


        db.commit()


        # =============================================
        # COUNTERS
        # =============================================

        created_patients = 0
        linked_users = 0
        assignments = 0
        clinical_records = 0
        predictions = 0


        # =============================================
        # PATIENT COHORT
        # =============================================

        for index in range(
            1,
            PATIENT_COUNT
            + 1,
        ):
            identity = (
                build_patient_identity(
                    index
                )
            )

            patient, created = (
                get_or_create_patient(
                    db,

                    patient_data=(
                        identity
                    ),
                )
            )

            if created:
                created_patients += 1


            # -----------------------------------------
            # LINK USER
            # -----------------------------------------

            linked_user = (
                maybe_link_patient_user(
                    db,

                    patient=patient,

                    patient_index=(
                        index
                    ),
                )
            )

            if linked_user:
                linked_users += 1


            # -----------------------------------------
            # PRIMARY CLINICIAN
            # -----------------------------------------

            primary_clinician = (
                clinicians[
                    (
                        index
                        -
                        1
                    )
                    %
                    len(
                        clinicians
                    )
                ]
            )

            ensure_assignment(
                db,

                clinician=(
                    primary_clinician
                ),

                patient=patient,

                administrator=(
                    administrator
                ),
            )

            assignments += 1


            # -----------------------------------------
            # SECONDARY CLINICIAN
            #
            # Some patients are deliberately shared.
            # -----------------------------------------

            if (
                index
                % 9
                == 0
            ):
                secondary = (
                    clinicians[
                        index
                        %
                        len(
                            clinicians
                        )
                    ]
                )

                if (
                    secondary.id
                    !=
                    primary_clinician.id
                ):
                    ensure_assignment(
                        db,

                        clinician=(
                            secondary
                        ),

                        patient=(
                            patient
                        ),

                        administrator=(
                            administrator
                        ),
                    )

                    assignments += 1


            # -----------------------------------------
            # CLINICAL HISTORY
            # -----------------------------------------

            records = (
                seed_clinical_records(
                    db,

                    patient=patient,

                    clinician=(
                        primary_clinician
                    ),

                    patient_index=(
                        index
                    ),
                )
            )

            clinical_records += len(
                records
            )

            latest_record = max(
                records,

                key=lambda item:
                    item.created_at,
            )


            # -----------------------------------------
            # PREDICTION HISTORY
            # -----------------------------------------

            patient_predictions = (
                seed_predictions(
                    db,

                    patient=patient,

                    clinician=(
                        primary_clinician
                    ),

                    patient_index=(
                        index
                    ),

                    logistic_model=(
                        logistic_model
                    ),

                    xgboost_model=(
                        xgboost_model
                    ),

                    latest_record=(
                        latest_record
                    ),
                )
            )

            predictions += len(
                patient_predictions
            )


            # Commit periodically so a large seed does not
            # remain entirely in one transaction.
            if (
                index
                % 10
                == 0
            ):
                db.commit()

                print(
                    f"Processed {index}"
                    f"/{PATIENT_COUNT} patients..."
                )


        db.commit()


        # =============================================
        # SUMMARY
        # =============================================

        print(
            "\n"
            "==========================================="
        )

        print(
            " DEMONSTRATION DATA READY"
        )

        print(
            "==========================================="
        )

        print(
            f"Patients processed:       "
            f"{PATIENT_COUNT}"
        )

        print(
            f"New patients created:     "
            f"{created_patients}"
        )

        print(
            f"Linked user relationships:"
            f" {linked_users}"
        )

        print(
            f"Assignments processed:    "
            f"{assignments}"
        )

        print(
            f"Clinical records present: "
            f"{clinical_records}"
        )

        print(
            f"Prediction records present:"
            f" {predictions}"
        )

        print(
            "\nDemo clinician accounts:"
        )

        for clinician in clinicians:
            print(
                f"  {clinician.email}"
            )

        print(
            "\nPassword for demo accounts:"
        )

        print(
            f"  {DEMO_PASSWORD}"
        )

        print(
            "\nIMPORTANT:"
        )

        print(
            "Seeded prediction probabilities are "
            "DEMONSTRATION VALUES ONLY."
        )

        print(
            "They are not outputs from the trained "
            "MEDISCOPE models.\n"
        )


    except Exception:
        db.rollback()

        raise

    finally:
        db.close()


# =====================================================
# SCRIPT ENTRY POINT
# =====================================================

if __name__ == "__main__":
    seed()
