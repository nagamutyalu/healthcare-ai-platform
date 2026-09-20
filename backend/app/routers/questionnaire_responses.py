from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database.database import get_session
from app.models.questionnaire_response import QuestionnaireResponse
from app.models.questionnaire import Questionnaire
from app.models.question import Question
from app.models.appointment import Appointment
from app.models.patient import Patient


router = APIRouter(
    prefix="/questionnaire-responses",
    tags=["Questionnaire Responses"]
)


@router.post("/")
def submit_response(
    response: QuestionnaireResponse,
    session: Session = Depends(get_session)
):
    questionnaire = session.get(
        Questionnaire,
        response.questionnaire_id
    )

    if not questionnaire:
        raise HTTPException(
            status_code=404,
            detail="Questionnaire not found"
        )

    question = session.get(
        Question,
        response.question_id
    )

    if not question:
        raise HTTPException(
            status_code=404,
            detail="Question not found"
        )

    appointment = session.get(
        Appointment,
        response.appointment_id
    )

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    patient = session.get(
        Patient,
        response.patient_id
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    if question.questionnaire_id != response.questionnaire_id:
        raise HTTPException(
            status_code=400,
            detail="Question does not belong to this questionnaire"
        )

    session.add(response)
    session.commit()

    return response


@router.get("/appointment/{appointment_id}")
def get_appointment_responses(
    appointment_id: int,
    session: Session = Depends(get_session)
):
    appointment = session.get(Appointment, appointment_id)

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    statement = select(QuestionnaireResponse).where(
        QuestionnaireResponse.appointment_id == appointment_id
    )

    return session.exec(statement).all()
