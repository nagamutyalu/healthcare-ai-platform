from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.database.database import get_session
from app.models.audit_log import AuditLog
from app.routers.rbac import get_role


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


@router.get("/")
def get_audit_logs(
    session: Session = Depends(get_session),
    role: str = Depends(get_role),
):
    if role not in {"PLATFORM_ADMIN", "HOSPITAL_ADMIN"}:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=403,
            detail="Only Admin users can view audit logs.",
        )

    statement = select(AuditLog).order_by(
        AuditLog.created_at.desc()
    )

    return session.exec(statement).all()
