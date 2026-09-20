from datetime import datetime
from sqlmodel import Field, SQLModel


class Notification(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    recipient_type: str
    recipient_id: int

    notification_type: str
    title: str
    message: str

    status: str = "PENDING"

    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: datetime | None = None
