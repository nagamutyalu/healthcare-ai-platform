from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from pydantic import BaseModel
from app.database.database import get_session
from app.models.availability import Availability

router = APIRouter(prefix="/availability", tags=["Availability"])

class AvailabilityCreate(BaseModel):
    doctor_id: int
    calendar_id: int
    start_time: datetime
    end_time: datetime
    appointment_type: str = "IN_PERSON"
    is_available: bool = True

@router.post("/")
def create_availability(
    data: AvailabilityCreate,
    session: Session = Depends(get_session),
):
    if data.end_time <= data.start_time:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

    availability = Availability(
        doctor_id=data.doctor_id,
        calendar_id=data.calendar_id,
        start_time=data.start_time,
        end_time=data.end_time,
        appointment_type=data.appointment_type,
        is_available=data.is_available,
    )

    session.add(availability)
    session.flush()
    availability_id = availability.id
    session.commit()

    return session.get(Availability, availability_id)

@router.get("/")
def get_availability(
    doctor_id: int | None = Query(default=None),
    calendar_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
):
    statement = select(Availability)

    if doctor_id is not None:
        statement = statement.where(Availability.doctor_id == doctor_id)

    if calendar_id is not None:
        statement = statement.where(Availability.calendar_id == calendar_id)

    statement = statement.order_by(Availability.start_time)

    return session.exec(statement).all()
