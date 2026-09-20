from datetime import datetime

from sqlmodel import Field, SQLModel


class BlockedSlot(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    doctor_id: int = Field(foreign_key="doctor.id")

    start_time: datetime
    end_time: datetime

    reason: str | None = None
