from sqlmodel import Field, SQLModel


class Patient(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    first_name: str
    last_name: str

    phone: str
    email: str | None = None

    date_of_birth: str | None = None

    preferred_language: str = "English"
    communication_preference: str = "SMS"
