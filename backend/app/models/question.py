from sqlmodel import Field, SQLModel


class Question(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    questionnaire_id: int = Field(
        foreign_key="questionnaire.id"
    )

    question_text: str

    question_type: str = "SHORT_TEXT"

    is_required: bool = True

    display_order: int = 1
