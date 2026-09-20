from datetime import timedelta

from sqlmodel import Session, select

from app.models.doctor import Doctor
from app.models.availability import Availability
from app.models.appointment import Appointment
from app.models.blocked_slot import BlockedSlot


def check_availability(session: Session, doctor_id: int, start_time=None, end_time=None):

    doctor = session.get(Doctor, doctor_id)

    if not doctor:
        return {
            "error": "Doctor not found",
            "slots": []
        }

    if doctor.status != "ACTIVE":
        return {
            "error": "Doctor is not active",
            "slots": []
        }

    duration = doctor.consultation_duration or 30

    statement = select(Availability).where(
        Availability.doctor_id == doctor_id,
        Availability.is_available == True
    )

    if start_time:
        statement = statement.where(
            Availability.start_time >= start_time
        )

    if end_time:
        statement = statement.where(
            Availability.end_time <= end_time
        )

    availability_windows = session.exec(statement).all()

    # Active appointments that must block slots
    appointment_statement = select(Appointment).where(
        Appointment.doctor_id == doctor_id,
        Appointment.status.in_(["PENDING", "CONFIRMED"])
    )

    existing_appointments = session.exec(
        appointment_statement
    ).all()

    # Blocked slots such as leave/breaks
    blocked_statement = select(BlockedSlot).where(
        BlockedSlot.doctor_id == doctor_id
    )

    blocked_slots = session.exec(
        blocked_statement
    ).all()

    bookable_slots = []

    for window in availability_windows:

        current = window.start_time

        while current + timedelta(minutes=duration) <= window.end_time:

            slot_end = current + timedelta(minutes=duration)

            # Check existing appointment overlap
            appointment_conflict = False

            for appointment in existing_appointments:

                if (
                    current < appointment.end_time
                    and slot_end > appointment.start_time
                ):
                    appointment_conflict = True
                    break

            if appointment_conflict:
                current += timedelta(minutes=duration)
                continue

            # Check blocked slot overlap
            blocked_conflict = False

            for blocked in blocked_slots:

                if (
                    current < blocked.end_time
                    and slot_end > blocked.start_time
                ):
                    blocked_conflict = True
                    break

            if blocked_conflict:
                current += timedelta(minutes=duration)
                continue

            bookable_slots.append({
                "id": f"{doctor_id}-{current.isoformat()}",
                "doctor_id": doctor_id,
                "start_time": current,
                "end_time": slot_end,
                "appointment_type": window.appointment_type
            })

            current += timedelta(minutes=duration)

    return bookable_slots
