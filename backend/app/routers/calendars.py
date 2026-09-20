from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database.database import get_session
from app.models.calendar import Calendar
from app.models.doctor import Doctor


router = APIRouter(
    prefix="/calendars",
    tags=["Calendars"],
)


@router.post("/")
def create_calendar(
    calendar: Calendar,
    session: Session = Depends(get_session),
):
    doctor = session.get(Doctor, calendar.doctor_id)

    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found",
        )

    session.add(calendar)
    session.commit()
    session.refresh(calendar)

    return calendar


@router.get("/doctor/{doctor_id}")
def get_doctor_calendars(
    doctor_id: int,
    session: Session = Depends(get_session),
):
    doctor = session.get(Doctor, doctor_id)

    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found",
        )

    statement = select(Calendar).where(
        Calendar.doctor_id == doctor_id
    )

    return session.exec(statement).all()

