from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database.database import get_session
from app.models.availability import Availability
from app.models.doctor import Doctor
from app.models.calendar import Calendar


router = APIRouter(
    prefix="/availability",
    tags=["Availability"],
)


@router.post("/")
def create_availability(
    availability: Availability,
    session: Session = Depends(get_session),
):
    doctor = session.get(Doctor, availability.doctor_id)

    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found",
        )

    calendar = session.get(Calendar, availability.calendar_id)

    if not calendar:
        raise HTTPException(
            status_code=404,
            detail="Calendar not found",
        )

    if not calendar.is_active:
        raise HTTPException(
            status_code=400,
            detail="Calendar is inactive",
        )

    session.add(availability)
    session.commit()
    session.refresh(availability)

    return availability


@router.get("/doctor/{doctor_id}")
def get_doctor_availability(
    doctor_id: int,
    session: Session = Depends(get_session),
):
    doctor = session.get(Doctor, doctor_id)

    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found",
        )

    statement = select(Availability).where(
        Availability.doctor_id == doctor_id,
        Availability.is_available == True,
    )

    return session.exec(statement).all()
@router.delete("/{availability_id}")
def delete_availability(
    availability_id: int,
    session: Session = Depends(get_session),
):
    availability = session.get(
        Availability,
        availability_id,
    )

    if not availability:
        raise HTTPException(
            status_code=404,
            detail="Availability not found",
        )

    session.delete(availability)
    session.commit()

    return {
        "message": "Availability deleted successfully"
    }
