from datetime import datetime

from sqlmodel import Field, SQLModel


class Workflow(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    name: str
    event_type: str

    description: str | None = None

    is_active: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)
