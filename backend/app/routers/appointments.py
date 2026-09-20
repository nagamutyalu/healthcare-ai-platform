from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database.database import get_session
from app.models.appointment import Appointment
from app.models.hospital import Hospital
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.availability import Availability

from app.integrations.mock_ehr import (
    create_external_appointment,
    verify_external_appointment,
    cancel_external_appointment,
    reschedule_external_appointment,
)

router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"],
)
@router.post("/")
def create_appointment(
    appointment: Appointment,
    session: Session = Depends(get_session),
):
    # Check hospital
    hospital = session.get(Hospital, appointment.hospital_id)

    if not hospital:
        raise HTTPException(
            status_code=404,
            detail="Hospital not found",
        )

    # Check doctor
    doctor = session.get(Doctor, appointment.doctor_id)

    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found",
        )

    # Check patient
    patient = session.get(Patient, appointment.patient_id)

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    # Check availability
    statement = select(Availability).where(
        Availability.doctor_id == appointment.doctor_id,
        Availability.is_available == True,
        Availability.start_time <= appointment.start_time,
        Availability.end_time >= appointment.end_time,
    )

    available_slot = session.exec(statement).first()

    if not available_slot:
        raise HTTPException(
            status_code=400,
            detail="Doctor is not available for this time slot",
        )

    # Check double booking
    existing = session.exec(
        select(Appointment).where(
            Appointment.doctor_id == appointment.doctor_id,
            Appointment.start_time == appointment.start_time,
            Appointment.status.in_([
                "REQUESTED",
                "PENDING",
                "CONFIRMED",
            ]),
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="This time slot is already booked",
        )

    # Create internal appointment
    appointment.status = "PENDING"

    session.add(appointment)
    session.commit()
    session.refresh(appointment)

    # Create appointment in Mock EHR
    external_appointment = create_external_appointment(
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        hospital_id=appointment.hospital_id,
        start_time=appointment.start_time,
        end_time=appointment.end_time,
        appointment_type=appointment.appointment_type,
    )

    # Save external ID
    appointment.external_appointment_id = (
        external_appointment["external_appointment_id"]
    )

    session.commit()
    session.refresh(appointment)

    # Verify external appointment
    verification = verify_external_appointment(
        appointment.external_appointment_id
    )

    if not verification["verified"]:
        appointment.status = "SYNCHRONIZATION_PENDING"

        session.commit()
        session.refresh(appointment)

        return appointment

    # External appointment verified
    appointment.status = "CONFIRMED"

    session.commit()
    session.refresh(appointment)

    return appointment



@router.get("/")
def get_appointments(
    session: Session = Depends(get_session),
):
    appointments = session.exec(
        select(Appointment)
    ).all()

    return appointments


@router.get("/{appointment_id}")
def get_appointment(
    appointment_id: int,
    session: Session = Depends(get_session),
):
    appointment = session.get(
        Appointment,
        appointment_id,
    )

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found",
        )

    return appointment
@router.delete("/{appointment_id}")
def cancel_appointment(
    appointment_id: int,
    session: Session = Depends(get_session),
):
    appointment = session.get(
        Appointment,
        appointment_id,
    )

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found",
        )

    if appointment.status == "CANCELLED":
        raise HTTPException(
            status_code=400,
            detail="Appointment is already cancelled",
        )

    # Cancel in Mock EHR
    if appointment.external_appointment_id:
        external_appointment = cancel_external_appointment(
            appointment.external_appointment_id
        )

        if not external_appointment:
            raise HTTPException(
                status_code=404,
                detail="External appointment not found",
            )

    # Cancel internal appointment
    appointment.status = "CANCELLED"

    session.commit()
    session.refresh(appointment)

    return appointment
@router.put("/{appointment_id}/reschedule")
def reschedule_appointment(
    appointment_id: int,
    new_start_time: datetime,
    new_end_time: datetime,
    session: Session = Depends(get_session),
):
    appointment = session.get(
        Appointment,
        appointment_id,
    )

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found",
        )

    if appointment.status != "CONFIRMED":
        raise HTTPException(
            status_code=400,
            detail="Only confirmed appointments can be rescheduled",
        )

    # Check new availability
    statement = select(Availability).where(
        Availability.doctor_id == appointment.doctor_id,
        Availability.is_available == True,
        Availability.start_time <= new_start_time,
        Availability.end_time >= new_end_time,
    )

    available_slot = session.exec(statement).first()

    if not available_slot:
        raise HTTPException(
            status_code=400,
            detail="Doctor is not available for the new time",
        )

    # Check double booking
    existing = session.exec(
        select(Appointment).where(
            Appointment.doctor_id == appointment.doctor_id,
            Appointment.id != appointment.id,
            Appointment.start_time == new_start_time,
            Appointment.status.in_([
                "REQUESTED",
                "PENDING",
                "CONFIRMED",
                "RESCHEDULED",
            ]),
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="New time slot is already booked",
        )

    # Update Mock EHR
    if appointment.external_appointment_id:

        external = reschedule_external_appointment(
            appointment.external_appointment_id,
            new_start_time,
            new_end_time,
        )

        if not external:
            raise HTTPException(
                status_code=404,
                detail="External appointment not found",
            )

        verification = verify_external_appointment(
            appointment.external_appointment_id
        )

        if not verification["verified"]:
            appointment.status = "SYNCHRONIZATION_PENDING"

            session.commit()
            session.refresh(appointment)

            return appointment

    # Update internal appointment
    appointment.start_time = new_start_time
    appointment.end_time = new_end_time
    appointment.status = "RESCHEDULED"

    session.commit()
    session.refresh(appointment)

    return appointment
