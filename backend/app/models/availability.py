from datetime import datetime

from sqlmodel import Field, SQLModel


class Availability(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    doctor_id: int = Field(foreign_key="doctor.id")
    calendar_id: int = Field(foreign_key="calendar.id")

    start_time: datetime
    end_time: datetime

    appointment_type: str = "IN_PERSON"
    is_available: bool = True
