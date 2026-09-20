from datetime import datetime

from sqlmodel import Field, SQLModel


class AIConversation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    patient_id: int = Field(foreign_key="patient.id")

    session_id: str
    role: str
    message: str

    created_at: datetime = Field(default_factory=datetime.utcnow)
