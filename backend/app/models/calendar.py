from sqlmodel import Field, SQLModel


class Calendar(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    doctor_id: int = Field(foreign_key="doctor.id")

    name: str = "Primary Calendar"
    is_active: bool = True

    timezone: str = "Asia/Kolkata"
