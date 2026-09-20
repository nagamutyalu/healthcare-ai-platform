from datetime import datetime

from sqlmodel import Field, SQLModel


class Appointment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    hospital_id: int = Field(foreign_key="hospital.id")
    doctor_id: int = Field(foreign_key="doctor.id")
    patient_id: int = Field(foreign_key="patient.id")

    appointment_type: str = "IN_PERSON"

    start_time: datetime
    end_time: datetime

    status: str = "REQUESTED"

    external_appointment_id: str | None = None

    idempotency_key: str | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
