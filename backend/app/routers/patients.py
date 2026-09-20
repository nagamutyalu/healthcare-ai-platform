from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database.database import get_session
from app.models.patient import Patient

router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
)


@router.post("/")
def create_patient(
    patient: Patient,
    session: Session = Depends(get_session),
):
    session.add(patient)
    session.commit()
    session.refresh(patient)

    return patient


@router.get("/")
def get_patients(
    session: Session = Depends(get_session),
):
    patients = session.exec(
        select(Patient)
    ).all()

    return patients


@router.get("/{patient_id}")
def get_patient(
    patient_id: int,
    session: Session = Depends(get_session),
):
    patient = session.get(Patient, patient_id)

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    return patient
