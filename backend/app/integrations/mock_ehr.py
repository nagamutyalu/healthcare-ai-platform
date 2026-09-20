from datetime import datetime
from uuid import uuid4

from sqlmodel import Session, select

from app.database.database import engine
from app.models.mock_ehr_appointment import MockEHRAppointment


def create_external_appointment(
    patient_id: int,
    doctor_id: int,
    hospital_id: int,
    start_time: datetime,
    end_time: datetime,
    appointment_type: str,
    simulate_unknown_outcome: bool = False,
):
    external_id = f"EHR-{uuid4().hex[:8].upper()}"

    with Session(engine) as session:
        appointment = MockEHRAppointment(
            external_appointment_id=external_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
            hospital_id=hospital_id,
            start_time=start_time,
            end_time=end_time,
            appointment_type=appointment_type,
            status="CONFIRMED",
        )

        session.add(appointment)
        session.commit()
        session.refresh(appointment)

        result = {
            "external_appointment_id": appointment.external_appointment_id,
            "patient_id": appointment.patient_id,
            "doctor_id": appointment.doctor_id,
            "hospital_id": appointment.hospital_id,
            "start_time": appointment.start_time,
            "end_time": appointment.end_time,
            "appointment_type": appointment.appointment_type,
            "status": appointment.status,
        }

    # Simulate the real-world case where the external system
    # created the appointment but the response was lost.
    if simulate_unknown_outcome:
        raise TimeoutError(
            f"Mock EHR timeout after creation. "
            f"Unknown outcome. External ID: {external_id}"
        )

    return result


def get_external_appointment(external_id: str):
    with Session(engine) as session:
        statement = select(MockEHRAppointment).where(
            MockEHRAppointment.external_appointment_id == external_id
        )

        appointment = session.exec(statement).first()

        if not appointment:
            return None

        return appointment


def verify_external_appointment(external_id: str):
    appointment = get_external_appointment(external_id)

    if not appointment:
        return {
            "verified": False,
            "appointment": None,
        }

    return {
        "verified": True,
        "appointment": appointment,
    }


def cancel_external_appointment(external_id: str):
    with Session(engine) as session:
        statement = select(MockEHRAppointment).where(
            MockEHRAppointment.external_appointment_id == external_id
        )

        appointment = session.exec(statement).first()

        if not appointment:
            return None

        appointment.status = "CANCELLED"

        session.add(appointment)
        session.commit()
        session.refresh(appointment)

        return appointment


def reschedule_external_appointment(
    external_id: str,
    new_start_time: datetime,
    new_end_time: datetime,
):
    with Session(engine) as session:
        statement = select(MockEHRAppointment).where(
            MockEHRAppointment.external_appointment_id == external_id
        )

        appointment = session.exec(statement).first()

        if not appointment:
            return None

        appointment.start_time = new_start_time
        appointment.end_time = new_end_time
        appointment.status = "RESCHEDULED"

        session.add(appointment)
        session.commit()
        session.refresh(appointment)

        return appointment
