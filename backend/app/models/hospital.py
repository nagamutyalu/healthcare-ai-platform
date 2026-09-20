from sqlmodel import Field, SQLModel


class Hospital(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    name: str
    address: str
    city: str
    state: str
    phone: str

    status: str = "DRAFT"
