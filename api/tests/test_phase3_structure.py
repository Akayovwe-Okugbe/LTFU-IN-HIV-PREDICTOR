"""Small structural tests for MEDISCOPE Phase 3."""
from app.core.enums import UserRole


def test_primary_roles_are_distinct():
    """The three primary application roles should remain distinct."""
    roles = {
        UserRole.USER.value,
        UserRole.CLINICIAN.value,
        UserRole.ADMINISTRATOR.value,
    }
    assert len(roles) == 3
