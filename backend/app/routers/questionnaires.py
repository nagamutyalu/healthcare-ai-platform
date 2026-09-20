from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database.database import get_session
from app.models.questionnaire import Questionnaire
from app.models.question import Question
from app.models.hospital import Hospital
from app.models.doctor import Doctor

router = APIRouter(
    prefix="/questionnaires",
    tags=["Questionnaires"],
)


@router.post("/")
def create_questionnaire(
    questionnaire: Questionnaire,
    session: Session = Depends(get_session),
):
    hospital = session.get(
        Hospital,
        questionnaire.hospital_id,
    )

    if not hospital:
        raise HTTPException(
            status_code=404,
            detail="Hospital not found",
        )

    if questionnaire.doctor_id:
        doctor = session.get(
            Doctor,
            questionnaire.doctor_id,
        )

        if not doctor:
            raise HTTPException(
                status_code=404,
                detail="Doctor not found",
            )

    session.add(questionnaire)
    session.commit()
    session.refresh(questionnaire)

    return questionnaire


@router.get("/")
def get_questionnaires(
    session: Session = Depends(get_session),
):
    return session.exec(
        select(Questionnaire)
    ).all()


@router.get("/appointment/{appointment_id}")
def get_questionnaire_for_appointment(
    appointment_id: int,
    session: Session = Depends(get_session),
):
    from app.models.appointment import Appointment

    appointment = session.get(Appointment, appointment_id)

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found",
        )

    questionnaire = session.exec(
        select(Questionnaire).where(
            Questionnaire.hospital_id == appointment.hospital_id,
            Questionnaire.is_active == True,
            Questionnaire.appointment_type == appointment.appointment_type,
            (
                (Questionnaire.doctor_id == appointment.doctor_id)
                | (Questionnaire.doctor_id == None)
            ),
        )
    ).first()

    if not questionnaire:
        raise HTTPException(
            status_code=404,
            detail="No questionnaire configured for this appointment",
        )

    return questionnaire


@router.get("/{questionnaire_id}")
def get_questionnaire(
    questionnaire_id: int,
    session: Session = Depends(get_session),
):
    questionnaire = session.get(
        Questionnaire,
        questionnaire_id,
    )

    if not questionnaire:
        raise HTTPException(
            status_code=404,
            detail="Questionnaire not found",
        )

    return questionnaire


@router.post("/{questionnaire_id}/questions")
def add_question(
    questionnaire_id: int,
    question: Question,
    session: Session = Depends(get_session),
):
    questionnaire = session.get(
        Questionnaire,
        questionnaire_id,
    )

    if not questionnaire:
        raise HTTPException(
            status_code=404,
            detail="Questionnaire not found",
        )

    question.questionnaire_id = questionnaire_id

    session.add(question)
    session.commit()
    session.refresh(question)

    return question


@router.get("/{questionnaire_id}/questions")
def get_questions(
    questionnaire_id: int,
    session: Session = Depends(get_session),
):
    questionnaire = session.get(
        Questionnaire,
        questionnaire_id,
    )

    if not questionnaire:
        raise HTTPException(
            status_code=404,
            detail="Questionnaire not found",
        )

    return session.exec(
        select(Question).where(
            Question.questionnaire_id == questionnaire_id
        )
    ).all()
