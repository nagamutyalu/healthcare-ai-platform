from datetime import datetime
from sqlmodel import Field, SQLModel


class MockEHRAppointment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    external_appointment_id: str = Field(index=True)

    patient_id: int
    doctor_id: int
    hospital_id: int

    start_time: datetime
    end_time: datetime

    appointment_type: str = "IN_PERSON"
    status: str = "CONFIRMED"

    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )
