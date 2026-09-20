from sqlmodel import Field, SQLModel


class Doctor(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    hospital_id: int = Field(foreign_key="hospital.id")

    name: str
    specialty: str
    department: str

    qualifications: str | None = None
    experience_years: int | None = None
    languages: str | None = None

    consultation_type: str = "IN_PERSON"
    consultation_duration: int = 30

    external_provider_id: str | None = None

    status: str = "INVITED"
