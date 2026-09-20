from sqlmodel import Field, SQLModel


class Questionnaire(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    hospital_id: int = Field(foreign_key="hospital.id")
    doctor_id: int | None = Field(
        default=None,
        foreign_key="doctor.id"
    )

    title: str
    description: str | None = None

    appointment_type: str = "IN_PERSON"

    is_active: bool = True
