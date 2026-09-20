from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database.database import get_session
from app.models.appointment import Appointment
from app.models.availability import Availability
from app.capabilities.appointment_booking import create_appointment_capability
from app.capabilities.availability_search import check_availability
from app.capabilities.doctor_search import search_doctors
from app.integrations.mock_ehr import (
    cancel_external_appointment,
    reschedule_external_appointment,
    verify_external_appointment,
)
from app.security.audit import create_audit_log


router = APIRouter(
    prefix="/capabilities",
    tags=["Capabilities"],
)


@router.get("/search-doctors")
def capability_search_doctors(
    specialty: str | None = None,
    hospital_id: int | None = None,
    session: Session = Depends(get_session),
):
    return search_doctors(
        session=session,
        specialty=specialty,
        hospital_id=hospital_id,
    )


@router.get("/check-availability")
def capability_check_availability(
    doctor_id: int,
    appointment_type: str = "IN_PERSON",
    session: Session = Depends(get_session),
):
    return check_availability(
        session=session,
        doctor_id=doctor_id,
        appointment_type=appointment_type,
    )


@router.post("/create-appointment")
def capability_create_appointment(
    patient_id: int,
    hospital_id: int,
    doctor_id: int,
    appointment_type: str,
    start_time: datetime,
    end_time: datetime,
    idempotency_key: str | None = None,
    simulate_unknown_outcome: bool = False,
    session: Session = Depends(get_session),
):
    result = create_appointment_capability(
        session=session,
        patient_id=patient_id,
        hospital_id=hospital_id,
        doctor_id=doctor_id,
        appointment_type=appointment_type,
        start_time=start_time,
        end_time=end_time,
        idempotency_key=idempotency_key,
        simulate_unknown_outcome=simulate_unknown_outcome,
    )

    if result.get("success"):
        appointment = result.get("appointment")

        if appointment:
            action = "CREATE_APPOINTMENT"

            if result.get("recovery") == "UNKNOWN_OUTCOME_RECOVERED":
                action = "RECOVER_UNKNOWN_APPOINTMENT"

            create_audit_log(
                session=session,
                user_role="PATIENT",
                action=action,
                resource_type="Appointment",
                resource_id=appointment.id,
                success=True,
                details=result.get(
                    "message",
                    "Appointment operation completed successfully.",
                ),
            )

    return result


@router.get("/get-appointment/{appointment_id}")
def capability_get_appointment(
    appointment_id: int,
    session: Session = Depends(get_session),
):
    appointment = session.get(Appointment, appointment_id)

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found.",
        )

    return appointment


@router.delete("/cancel-appointment/{appointment_id}")
def capability_cancel_appointment(
    appointment_id: int,
    session: Session = Depends(get_session),
):
    appointment = session.get(Appointment, appointment_id)

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found.",
        )

    if appointment.status == "CANCELLED":
        return {
            "success": True,
            "message": "Appointment is already cancelled.",
            "appointment": appointment,
        }

    if appointment.external_appointment_id:
        external = cancel_external_appointment(
            appointment.external_appointment_id
        )

        if not external:
            raise HTTPException(
                status_code=404,
                detail="External appointment not found.",
            )

        verification = verify_external_appointment(
            appointment.external_appointment_id
        )

        if not verification["verified"]:
            appointment.status = "SYNCHRONIZATION_PENDING"

            session.add(appointment)
            session.commit()
            session.refresh(appointment)

            return {
                "success": False,
                "message": "External cancellation could not be verified.",
                "appointment": appointment,
            }

    appointment.status = "CANCELLED"

    session.add(appointment)
    session.commit()
    session.refresh(appointment)

    create_audit_log(
        session=session,
        user_role="PATIENT",
        action="CANCEL_APPOINTMENT",
        resource_type="Appointment",
        resource_id=appointment.id,
        success=True,
        details="Appointment cancelled successfully.",
    )

    return {
        "success": True,
        "message": "Appointment cancelled successfully.",
        "appointment": appointment,
    }


@router.put("/reschedule-appointment/{appointment_id}")
def capability_reschedule_appointment(
    appointment_id: int,
    new_start_time: datetime,
    new_end_time: datetime,
    session: Session = Depends(get_session),
):
    appointment = session.get(Appointment, appointment_id)

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found.",
        )

    if appointment.status != "CONFIRMED":
        raise HTTPException(
            status_code=400,
            detail="Only CONFIRMED appointments can be rescheduled.",
        )

    if new_end_time <= new_start_time:
        raise HTTPException(
            status_code=400,
            detail="Invalid appointment time.",
        )

    availability = session.exec(
        select(Availability).where(
            Availability.doctor_id == appointment.doctor_id,
            Availability.start_time <= new_start_time,
            Availability.end_time >= new_end_time,
            Availability.is_available == True,
        )
    ).first()

    if not availability:
        raise HTTPException(
            status_code=400,
            detail="Doctor is not available for the new time.",
        )

    existing = session.exec(
        select(Appointment).where(
            Appointment.doctor_id == appointment.doctor_id,
            Appointment.id != appointment.id,
            Appointment.start_time < new_end_time,
            Appointment.end_time > new_start_time,
            Appointment.status.in_(
                [
                    "REQUESTED",
                    "PENDING",
                    "CONFIRMED",
                    "RESCHEDULED",
                ]
            ),
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="New time slot is already booked.",
        )

    if appointment.external_appointment_id:
        external = reschedule_external_appointment(
            appointment.external_appointment_id,
            new_start_time,
            new_end_time,
        )

        if not external:
            raise HTTPException(
                status_code=404,
                detail="External appointment not found.",
            )

        verification = verify_external_appointment(
            appointment.external_appointment_id
        )

        if not verification["verified"]:
            appointment.status = "SYNCHRONIZATION_PENDING"

            session.add(appointment)
            session.commit()
            session.refresh(appointment)

            return {
                "success": False,
                "message": "External reschedule could not be verified.",
                "appointment": appointment,
            }

    appointment.start_time = new_start_time
    appointment.end_time = new_end_time
    appointment.status = "RESCHEDULED"

    session.add(appointment)
    session.commit()
    session.refresh(appointment)

    create_audit_log(
        session=session,
        user_role="PATIENT",
        action="RESCHEDULE_APPOINTMENT",
        resource_type="Appointment",
        resource_id=appointment.id,
        success=True,
        details="Appointment rescheduled successfully.",
    )

    return {
        "success": True,
        "message": "Appointment rescheduled successfully.",
        "appointment": appointment,
    }


@router.post("/test-unknown-outcome")
def test_unknown_outcome(
    patient_id: int = 3,
    hospital_id: int = 1,
    doctor_id: int = 1,
    session: Session = Depends(get_session),
):
    """
    Dedicated PRD failure-recovery test.

    Finds any configured availability window and creates a free
    30-minute test slot inside that window. The slot is selected
    from the database rather than relying on the current clock.
    """

    availabilities = session.exec(
        select(Availability).where(
            Availability.doctor_id == doctor_id,
            Availability.is_available == True,
        ).order_by(Availability.start_time)
    ).all()

    selected_slot = None

    for availability in availabilities:
        window_start = availability.start_time
        window_end = availability.end_time

        current = window_start

        while current + timedelta(minutes=30) <= window_end:
            slot_end = current + timedelta(minutes=30)

            existing = session.exec(
                select(Appointment).where(
                    Appointment.doctor_id == doctor_id,
                    Appointment.start_time < slot_end,
                    Appointment.end_time > current,
                    Appointment.status.in_(
                        [
                            "REQUESTED",
                            "PENDING",
                            "CONFIRMED",
                            "RESCHEDULED",
                        ]
                    ),
                )
            ).first()

            if not existing:
                selected_slot = {
                    "start_time": current,
                    "end_time": slot_end,
                }
                break

            current += timedelta(minutes=30)

        if selected_slot:
            break

    if not selected_slot:
        raise HTTPException(
            status_code=409,
            detail=(
                "No free 30-minute slot exists inside the configured "
                "availability windows."
            ),
        )

    idempotency_key = (
        f"unknown-outcome-test-"
        f"{patient_id}-"
        f"{doctor_id}-"
        f"{selected_slot['start_time'].isoformat()}"
    )

    result = create_appointment_capability(
        session=session,
        patient_id=patient_id,
        hospital_id=hospital_id,
        doctor_id=doctor_id,
        appointment_type="IN_PERSON",
        start_time=selected_slot["start_time"],
        end_time=selected_slot["end_time"],
        idempotency_key=idempotency_key,
        simulate_unknown_outcome=True,
    )

    appointment = result.get("appointment")

    if appointment:
        create_audit_log(
            session=session,
            user_role="PATIENT",
            action="RECOVER_UNKNOWN_APPOINTMENT",
            resource_type="Appointment",
            resource_id=appointment.id,
            success=result.get("success", False),
            details=result.get(
                "message",
                "Unknown outcome recovery test executed.",
            ),
        )

    return {
        "test": "UNKNOWN_OUTCOME_RECOVERY",
        "selected_slot": selected_slot,
        "result": result,
    }
