from sqlmodel import Field, SQLModel


class QuestionnaireResponse(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    questionnaire_id: int = Field(foreign_key="questionnaire.id")
    question_id: int = Field(foreign_key="question.id")
    appointment_id: int = Field(foreign_key="appointment.id")
    patient_id: int = Field(foreign_key="patient.id")

    answer: str
