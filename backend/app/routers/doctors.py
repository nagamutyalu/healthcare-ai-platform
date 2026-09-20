from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database.database import get_session
from app.models.doctor import Doctor
from app.models.hospital import Hospital


router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.post("/")
def create_doctor(
    doctor: Doctor,
    session: Session = Depends(get_session),
):
    hospital = session.get(Hospital, doctor.hospital_id)

    if not hospital:
        raise HTTPException(
            status_code=404,
            detail="Hospital not found",
        )

    session.add(doctor)
    session.commit()
    session.refresh(doctor)

    return doctor


@router.get("/")
def get_doctors(
    session: Session = Depends(get_session),
):
    doctors = session.exec(select(Doctor)).all()

    return doctors


@router.get("/{doctor_id}")
def get_doctor(
    doctor_id: int,
    session: Session = Depends(get_session),
):
    doctor = session.get(Doctor, doctor_id)

    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found",
        )

    return doctor
