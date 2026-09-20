from sqlmodel import Session

from app.models.audit_log import AuditLog


def create_audit_log(
    session: Session,
    user_role: str,
    action: str,
    resource_type: str,
    resource_id: int | None = None,
    success: bool = True,
    details: str | None = None,
):
    audit_log = AuditLog(
        user_role=user_role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        success=success,
        details=details,
    )

    session.add(audit_log)
    session.commit()
    session.refresh(audit_log)

    return audit_log
