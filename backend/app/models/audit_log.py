from datetime import datetime

from sqlmodel import Field, SQLModel


class AuditLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    user_role: str
    action: str

    resource_type: str
    resource_id: int | None = None

    success: bool = True
    details: str | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
