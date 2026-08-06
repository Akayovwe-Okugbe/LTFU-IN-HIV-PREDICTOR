from typing import Any
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.entities import AuditLog

def write_audit_log(db: Session, *, action: str, outcome: str,
                    actor_user_id: UUID | None = None,
                    resource_type: str | None = None,
                    resource_id: UUID | None = None,
                    ip_address: str | None = None,
                    user_agent: str | None = None,
                    details: dict[str, Any] | None = None) -> AuditLog:
    event = AuditLog(actor_user_id=actor_user_id, action=action,
                     resource_type=resource_type, resource_id=resource_id,
                     outcome=outcome, ip_address=ip_address,
                     user_agent=user_agent, details=details)
    db.add(event)
    return event
