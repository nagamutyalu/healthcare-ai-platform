from datetime import datetime

from sqlmodel import Field, SQLModel


class AIContext(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    patient_id: int = Field(foreign_key="patient.id")
    session_id: str

    current_intent: str | None = None
    selected_hospital_id: int | None = None
    selected_doctor_id: int | None = None
    selected_appointment_id: int | None = None
    selected_slot: str | None = None

    context_data: str | None = None

    updated_at: datetime = Field(default_factory=datetime.utcnow)
