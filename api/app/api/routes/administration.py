"""Administrator-only user and clinician-assignment endpoints."""
from __future__ import annotations
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import or_, select
from app.api.dependencies import DbSession, require_roles
from app.core.enums import AccountStatus, UserRole
from app.core.security import hash_password
from app.models.entities import ClinicianPatientAssignment, Patient, User
from app.schemas.administration import (
    AdminPatientSummaryResponse,
    AdminUserCreateRequest,
    AdminUserResponse,
    AdminUserUpdateRequest,
    ClinicianAssignmentCreateRequest,
    ClinicianAssignmentResponse,
    PatientUserLinkRequest,
    UserRoleUpdateRequest,
    UserStatusUpdateRequest,
)
from app.services.audit import write_audit_log
from app.services.notifications import notify_clinician_assignment, send_welcome_message

router = APIRouter(prefix="/admin", tags=["Administration"])

AdminUser = Annotated[
    User,
    Depends(require_roles(UserRole.ADMINISTRATOR.value)),
]
# =====================================================
# REQUEST AUDIT METADATA HELPER
# =====================================================

def _audit_request_metadata(
    request: Request,
) -> tuple[str | None, str | None]:
    """
    Extract request metadata used by audit-log entries.

    Returns
    -------
    tuple[str | None, str | None]
        The client IP address and user-agent string.

    Notes
    -----
    Either value may be unavailable depending on the
    request environment, so both are optional.
    """

    ip_address = (
        request.client.host
        if request.client
        else None
    )

    user_agent = request.headers.get(
        "user-agent"
    )

    return (
        ip_address,
        user_agent,
    )



# =====================================================
# ADMINISTRATION METADATA
# =====================================================

@router.get(
    "/metadata",
)
def administration_metadata(
    current_admin: AdminUser,
) -> dict[str, list[str]]:
    """
    Return backend-supported administration options.

    The frontend uses this endpoint for role and account
    status selectors so it never has to duplicate or guess
    backend enum values.
    """

    return {
        "roles": [
            member.value
            for member in UserRole
        ],
        "account_statuses": [
            member.value
            for member in AccountStatus
        ],
    }


@router.get("/users", response_model=list[AdminUserResponse])
def list_users(
    db: DbSession,
    current_admin: AdminUser,
    search: str | None = None,
    role: str | None = None,
) -> list[User]:
    """List active/non-deleted user accounts with optional filters."""
    statement = select(User).where(User.deleted_at.is_(None))

    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                User.email.ilike(pattern),
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
            )
        )

    if role:
        statement = statement.where(User.role == role)

    return list(db.scalars(statement.order_by(User.created_at.desc())).all())


@router.get("/users/{user_id}", response_model=AdminUserResponse)
def get_user(user_id: UUID, db: DbSession, current_admin: AdminUser) -> User:
    """Return one user without clinical-record contents."""
    user = db.get(User, user_id)
    if user is None or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.post("/users", response_model=AdminUserResponse, status_code=201)
def create_user(
    payload: AdminUserCreateRequest,
    request: Request,
    db: DbSession,
    current_admin: AdminUser,
) -> User:
    """Create a user from the administrator interface."""
    email = str(payload.email).strip().lower()

    if db.scalar(select(User.id).where(User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    allowed_roles = {member.value for member in UserRole}
    if payload.role not in allowed_roles:
        raise HTTPException(status_code=400, detail="Invalid role.")

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        date_of_birth=payload.date_of_birth,
        phone=payload.phone,
        gender=payload.gender,
        role=payload.role,
        account_status=AccountStatus.ACTIVE.value,
        email_verified_at=datetime.now(UTC),
    )
    db.add(user)
    db.flush()

    send_welcome_message(db, user=user)
    ip_address, user_agent = _audit_request_metadata(request)

    write_audit_log(
        db,
        actor_user_id=current_admin.id,
        action="ADMIN_USER_CREATED",
        outcome="SUCCESS",
        resource_type="USER",
        resource_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={"assigned_role": payload.role},
    )

    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
def update_user(
    user_id: UUID,
    payload: AdminUserUpdateRequest,
    request: Request,
    db: DbSession,
    current_admin: AdminUser,
) -> User:
    """Update permitted non-clinical user fields."""
    user = db.get(User, user_id)
    if user is None or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User not found.")

    changes = payload.model_dump(exclude_unset=True)
    for name, value in changes.items():
        setattr(user, name, value)

    ip_address, user_agent = _audit_request_metadata(request)
    write_audit_log(
        db,
        actor_user_id=current_admin.id,
        action="ADMIN_USER_UPDATED",
        outcome="SUCCESS",
        resource_type="USER",
        resource_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={"fields": sorted(changes)},
    )

    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/role", response_model=AdminUserResponse)
def change_user_role(
    user_id: UUID,
    payload: UserRoleUpdateRequest,
    request: Request,
    db: DbSession,
    current_admin: AdminUser,
) -> User:
    """Change a user's MEDISCOPE role."""
    user = db.get(User, user_id)
    if user is None or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User not found.")

    allowed_roles = {member.value for member in UserRole}
    if payload.role not in allowed_roles:
        raise HTTPException(status_code=400, detail="Invalid role.")

    # -------------------------------------------------
    # PREVENT ADMINISTRATOR SELF-DEMOTION
    # -------------------------------------------------

    if (
        user.id == current_admin.id
        and payload.role != UserRole.ADMINISTRATOR.value
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "You cannot remove your own administrator "
                "role from this interface."
            ),
        )

    # -------------------------------------------------
    # PROTECT ACTIVE CLINICIAN ASSIGNMENTS
    #
    # A clinician should not silently become a USER or
    # ADMINISTRATOR while active patient assignments
    # still reference that account.
    # -------------------------------------------------

    if (
        user.role == UserRole.CLINICIAN.value
        and payload.role != UserRole.CLINICIAN.value
    ):
        active_assignment = db.scalar(
            select(
                ClinicianPatientAssignment.id
            ).where(
                ClinicianPatientAssignment.clinician_user_id
                == user.id,
                ClinicianPatientAssignment.is_active.is_(True),
            )
        )

        if active_assignment is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This clinician still has active patient "
                    "assignments. End those assignments before "
                    "changing the account role."
                ),
            )

    # -------------------------------------------------
    # PROTECT PATIENT-USER LINK
    # -------------------------------------------------

    if (
        user.role == UserRole.USER.value
        and payload.role != UserRole.USER.value
    ):
        linked_patient = db.scalar(
            select(
                Patient.id
            ).where(
                Patient.linked_user_id
                == user.id
            )
        )

        if linked_patient is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This USER account is still linked to a "
                    "patient profile. Unlink the account before "
                    "changing its role."
                ),
            )

    previous_role = user.role
    user.role = payload.role

    ip_address, user_agent = _audit_request_metadata(request)
    write_audit_log(
        db,
        actor_user_id=current_admin.id,
        action="USER_ROLE_CHANGED",
        outcome="SUCCESS",
        resource_type="USER",
        resource_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={"previous_role": previous_role, "new_role": payload.role},
    )

    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/status", response_model=AdminUserResponse)
def change_account_status(
    user_id: UUID,
    payload: UserStatusUpdateRequest,
    request: Request,
    db: DbSession,
    current_admin: AdminUser,
) -> User:
    """Change an account to a supported account status."""
    user = db.get(User, user_id)

    # -------------------------------------------------
    # VALIDATE TARGET ACCOUNT
    # -------------------------------------------------

    if user is None or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # -------------------------------------------------
    # PREVENT SELF-SUSPENSION / SELF-DISABLING
    # -------------------------------------------------

    if (
        user.id == current_admin.id
        and payload.account_status
        != AccountStatus.ACTIVE.value
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "You cannot make your own administrator "
                "account inactive from this interface."
            ),
        )

    allowed_statuses = {member.value for member in AccountStatus}
    if payload.account_status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid account status.")

    previous_status = user.account_status
    user.account_status = payload.account_status

    ip_address, user_agent = _audit_request_metadata(request)
    write_audit_log(
        db,
        actor_user_id=current_admin.id,
        action="ACCOUNT_STATUS_CHANGED",
        outcome="SUCCESS",
        resource_type="USER",
        resource_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={"previous_status": previous_status, "new_status": payload.account_status},
    )

    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=204)
def soft_delete_user(
    user_id: UUID,
    request: Request,
    db: DbSession,
    current_admin: AdminUser,
) -> None:
    """Soft-delete an account while preserving history."""
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own administrator account here.")

    user = db.get(User, user_id)
    if user is None or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User not found.")

    # -------------------------------------------------
    # PREVENT DELETION WHILE RELATIONSHIPS ARE ACTIVE
    # -------------------------------------------------

    if user.role == UserRole.CLINICIAN.value:
        active_assignment = db.scalar(
            select(
                ClinicianPatientAssignment.id
            ).where(
                ClinicianPatientAssignment.clinician_user_id
                == user.id,
                ClinicianPatientAssignment.is_active.is_(True),
            )
        )

        if active_assignment is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This clinician still has active patient "
                    "assignments. End them before deleting "
                    "the account."
                ),
            )

    if user.role == UserRole.USER.value:
        linked_patient = db.scalar(
            select(
                Patient.id
            ).where(
                Patient.linked_user_id
                == user.id
            )
        )

        if linked_patient is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This user account is still linked to a "
                    "patient profile. Unlink it before deleting "
                    "the account."
                ),
            )

    user.deleted_at = datetime.now(UTC)
    ip_address, user_agent = _audit_request_metadata(request)

    write_audit_log(
        db,
        actor_user_id=current_admin.id,
        action="USER_SOFT_DELETED",
        outcome="SUCCESS",
        resource_type="USER",
        resource_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()


# =====================================================
# LINK USER ACCOUNT TO PATIENT
# =====================================================

@router.patch(
    "/patients/{patient_id}/link-user",
    status_code=status.HTTP_200_OK,
)
def link_user_to_patient(
    patient_id: UUID,
    payload: PatientUserLinkRequest,
    request: Request,
    db: DbSession,
    current_admin: AdminUser,
) -> dict[str, str]:
    """
    Link a standard MEDISCOPE USER account to an existing
    synthetic patient profile.

    Only administrators may create this relationship.

    Security and integrity rules:
        - The patient must exist.
        - The patient must be synthetic.
        - The selected account must exist.
        - The selected account must have the USER role.
        - Deleted accounts cannot be linked.
        - One USER account may only be linked to one
          patient profile.
        - A patient already linked to another account
          cannot be silently reassigned.
    """

    # -------------------------------------------------
    # RETRIEVE PATIENT
    # -------------------------------------------------

    patient = db.get(
        Patient,
        patient_id,
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    # -------------------------------------------------
    # ENFORCE SYNTHETIC DATA ONLY
    # -------------------------------------------------

    if not patient.is_synthetic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Only synthetic patient records may be "
                "linked to user accounts in this prototype."
            ),
        )

    # -------------------------------------------------
    # RETRIEVE USER ACCOUNT
    # -------------------------------------------------

    user = db.get(
        User,
        payload.user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found.",
        )

    # -------------------------------------------------
    # ONLY STANDARD USER ACCOUNTS MAY REPRESENT PATIENTS
    # -------------------------------------------------

    if (
        user.role
        != UserRole.USER.value
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Only a standard USER account may be "
                "linked to a patient profile."
            ),
        )

    # -------------------------------------------------
    # PREVENT LINKING DELETED ACCOUNTS
    # -------------------------------------------------

    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "A deleted user account cannot be linked "
                "to a patient profile."
            ),
        )

    # -------------------------------------------------
    # HANDLE ALREADY-LINKED PATIENT
    # -------------------------------------------------

    if patient.linked_user_id is not None:

        # If the same relationship already exists,
        # return a conflict rather than silently repeating
        # the operation.
        if (
            patient.linked_user_id
            == user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This user account is already linked "
                    "to this patient."
                ),
            )

        # Prevent accidental reassignment of a patient
        # who is linked to another user.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This patient is already linked to "
                "another user account."
            ),
        )

    # -------------------------------------------------
    # PREVENT ONE USER FROM OWNING MULTIPLE PATIENT
    # PROFILES
    # -------------------------------------------------

    existing_patient = db.scalar(
        select(Patient).where(
            Patient.linked_user_id
            == user.id
        )
    )

    if existing_patient is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This user account is already linked "
                "to another patient profile."
            ),
        )

    # -------------------------------------------------
    # CREATE LINK
    # -------------------------------------------------

    patient.linked_user_id = user.id

    # -------------------------------------------------
    # AUDIT RELATIONSHIP CREATION
    # -------------------------------------------------

    ip_address, user_agent = (
        _audit_request_metadata(
            request
        )
    )

    write_audit_log(
        db,
        actor_user_id=current_admin.id,
        action="PATIENT_USER_LINKED",
        outcome="SUCCESS",
        resource_type="PATIENT",
        resource_id=patient.id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={
            "linked_user_id": str(
                user.id
            ),
        },
    )

    db.commit()

    return {
        "message": (
            "User account linked to patient successfully."
        )
    }


# =====================================================
# UNLINK USER ACCOUNT FROM PATIENT
# =====================================================

@router.delete(
    "/patients/{patient_id}/link-user",
    status_code=status.HTTP_200_OK,
)
def unlink_user_from_patient(
    patient_id: UUID,
    request: Request,
    db: DbSession,
    current_admin: AdminUser,
) -> dict[str, str]:
    """
    Remove the USER-account relationship from a synthetic
    patient without deleting either record.
    """

    patient = db.get(
        Patient,
        patient_id,
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    if patient.linked_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This patient is not currently linked "
                "to a user account."
            ),
        )

    previous_user_id = (
        patient.linked_user_id
    )

    patient.linked_user_id = None

    ip_address, user_agent = (
        _audit_request_metadata(
            request
        )
    )

    write_audit_log(
        db,
        actor_user_id=current_admin.id,
        action="PATIENT_USER_UNLINKED",
        outcome="SUCCESS",
        resource_type="PATIENT",
        resource_id=patient.id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={
            "previous_linked_user_id": str(
                previous_user_id
            ),
        },
    )

    db.commit()

    return {
        "message": (
            "User account unlinked from patient successfully."
        )
    }


# =====================================================
# LIST CLINICIAN-PATIENT ASSIGNMENTS
# =====================================================

@router.get(
    "/assignments",
    response_model=list[ClinicianAssignmentResponse],
)
def list_assignments(
    db: DbSession,
    current_admin: AdminUser,
    clinician_user_id: UUID | None = None,
    patient_id: UUID | None = None,
    active_only: bool = True,
) -> list[ClinicianPatientAssignment]:
    """
    Return clinician-patient assignments for the
    administration workspace.

    Optional filters allow the frontend to inspect:
        - all active assignments;
        - one clinician's patients;
        - clinicians assigned to one patient;
        - historical assignments when active_only=False.
    """

    statement = select(
        ClinicianPatientAssignment
    )

    if active_only:
        statement = statement.where(
            ClinicianPatientAssignment.is_active.is_(True)
        )

    if clinician_user_id is not None:
        statement = statement.where(
            ClinicianPatientAssignment.clinician_user_id
            == clinician_user_id
        )

    if patient_id is not None:
        statement = statement.where(
            ClinicianPatientAssignment.patient_id
            == patient_id
        )

    statement = statement.order_by(
        ClinicianPatientAssignment.assigned_at.desc()
    )

    return list(
        db.scalars(
            statement
        ).all()
    )


@router.post("/assignments", response_model=ClinicianAssignmentResponse, status_code=201)
def assign_clinician(
    payload: ClinicianAssignmentCreateRequest,
    request: Request,
    db: DbSession,
    current_admin: AdminUser,
) -> ClinicianPatientAssignment:
    """Assign an active clinician to a synthetic patient."""
    clinician = db.get(User, payload.clinician_user_id)
    patient = db.get(Patient, payload.patient_id)

    if clinician is None or clinician.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Clinician not found.")
    if clinician.role != UserRole.CLINICIAN.value:
        raise HTTPException(status_code=400, detail="Selected user is not a clinician.")
    if clinician.account_status != AccountStatus.ACTIVE.value:
        raise HTTPException(status_code=400, detail="Clinician account is not active.")
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found.")
    if not patient.is_synthetic:
        raise HTTPException(status_code=400, detail="Only synthetic patient records are permitted.")

    existing = db.scalar(
        select(ClinicianPatientAssignment).where(
            ClinicianPatientAssignment.clinician_user_id == clinician.id,
            ClinicianPatientAssignment.patient_id == patient.id,
            ClinicianPatientAssignment.is_active.is_(True),
        )
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="This active assignment already exists.")

    assignment = ClinicianPatientAssignment(
        clinician_user_id=clinician.id,
        patient_id=patient.id,
        assigned_by=current_admin.id,
        is_active=True,
    )
    db.add(assignment)
    db.flush()

    notify_clinician_assignment(
        db,
        clinician=clinician,
        patient_number=patient.synthetic_patient_number,
    )

    ip_address, user_agent = _audit_request_metadata(request)
    write_audit_log(
        db,
        actor_user_id=current_admin.id,
        action="CLINICIAN_PATIENT_ASSIGNED",
        outcome="SUCCESS",
        resource_type="PATIENT",
        resource_id=patient.id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={"clinician_user_id": str(clinician.id)},
    )

    db.commit()
    db.refresh(assignment)
    return assignment


@router.delete("/assignments/{assignment_id}", response_model=ClinicianAssignmentResponse)
def end_assignment(
    assignment_id: UUID,
    request: Request,
    db: DbSession,
    current_admin: AdminUser,
) -> ClinicianPatientAssignment:
    """End an assignment while keeping the historical row."""
    assignment = db.get(ClinicianPatientAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    if assignment.is_active:
        assignment.is_active = False
        assignment.ended_at = datetime.now(UTC)

        ip_address, user_agent = _audit_request_metadata(request)
        write_audit_log(
            db,
            actor_user_id=current_admin.id,
            action="CLINICIAN_PATIENT_UNASSIGNED",
            outcome="SUCCESS",
            resource_type="PATIENT",
            resource_id=assignment.patient_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"clinician_user_id": str(assignment.clinician_user_id)},
        )
        db.commit()
        db.refresh(assignment)

    return assignment



# =====================================================
# LIST SYNTHETIC PATIENTS FOR ADMINISTRATION
# =====================================================

@router.get(
    "/patients",
    response_model=list[AdminPatientSummaryResponse],
)
def list_admin_patients(
    db: DbSession,
    current_admin: AdminUser,
    search: str | None = None,
) -> list[Patient]:
    """
    Return synthetic patient summaries required for user
    linking and clinician-assignment administration.

    Clinical-record contents are intentionally excluded.
    """

    statement = select(
        Patient
    ).where(
        Patient.is_synthetic.is_(True)
    )

    if search:
        pattern = (
            f"%{search.strip()}%"
        )

        statement = statement.where(
            or_(
                Patient.synthetic_patient_number.ilike(
                    pattern
                ),
                Patient.first_name.ilike(
                    pattern
                ),
                Patient.last_name.ilike(
                    pattern
                ),
                Patient.state.ilike(
                    pattern
                ),
                Patient.lga.ilike(
                    pattern
                ),
            )
        )

    statement = statement.order_by(
        Patient.synthetic_patient_number
    )

    return list(
        db.scalars(
            statement
        ).all()
    )
