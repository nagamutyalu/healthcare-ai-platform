from datetime import datetime

from sqlmodel import Field, SQLModel


class WorkflowExecution(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    workflow_id: int = Field(foreign_key="workflow.id")

    status: str = "PENDING"

    trigger_data: str | None = None
    result: str | None = None
    error_message: str | None = None

    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
