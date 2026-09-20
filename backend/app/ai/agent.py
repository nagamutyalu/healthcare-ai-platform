from datetime import datetime, timedelta
import re

from sqlmodel import select

from app.models.ai_context import AIContext
from app.models.appointment import Appointment
from app.models.doctor import Doctor

from app.capabilities.appointment_booking import (
    create_appointment_capability,
)


# ============================================================
# CONTEXT
# ============================================================

def get_or_create_context(
    session,
    patient_id: int,
    session_id: str,
):
    context = session.exec(
        select(AIContext).where(
            AIContext.patient_id == patient_id,
            AIContext.session_id == session_id,
        )
    ).first()

    if not context:
        context = AIContext(
            patient_id=patient_id,
            session_id=session_id,
            current_intent=None,
            selected_hospital_id=None,
            selected_doctor_id=None,
            selected_appointment_id=None,
            selected_slot=None,
            context_data="{}",
        )

        session.add(context)
        session.commit()
        session.refresh(context)

    return context


# ============================================================
# TIME PARSER
# ============================================================

def extract_requested_time(message: str):
    import re

    text = message.lower().strip()

    # --------------------------------------------------
    # 12-hour format
    # Examples:
    # 11:30 AM
    # 11:30AM
    # 2:00 PM
    # 2 PM
    # --------------------------------------------------

    match = re.search(
        r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b",
        text,
        re.IGNORECASE,
    )

    if match:
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        period = match.group(3).lower()

        if hour < 1 or hour > 12:
            return None

        if minute < 0 or minute > 59:
            return None

        if period == "am":
            if hour == 12:
                hour = 0
        else:
            if hour != 12:
                hour += 12

        return hour, minute

    # --------------------------------------------------
    # 24-hour format
    # Examples:
    # 11:30
    # 14:00
    # 09:30
    # --------------------------------------------------

    match = re.search(
        r"\b([01]?\d|2[0-3]):([0-5]\d)\b",
        text,
    )

    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))

        return hour, minute

    # --------------------------------------------------
    # Hour only
    # Examples:
    # 11
    # 2
    # 14
    #
    # We only use this when explicitly followed by
    # "appointment", "slot", "booking", etc.
    # --------------------------------------------------

    match = re.search(
        r"\b(?:at|for)\s+([01]?\d|2[0-3])\b",
        text,
    )

    if match:
        hour = int(match.group(1))

        return hour, 0

    return None

# ============================================================
# FORMAT TIME
# ============================================================

def format_time(value):
    if not value:
        return None

    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except Exception:
            return value

    return value.strftime("%I:%M %p").lstrip("0")


# ============================================================
# FIND ORTHOPEDIC DOCTOR
# ============================================================

def find_orthopedic_doctor(session):

    doctor = session.exec(
        select(Doctor).where(
            Doctor.specialty.ilike("%orthopedic%"),
            Doctor.status == "ACTIVE",
        )
    ).first()

    return doctor


# ============================================================
# GET AVAILABLE SLOTS DIRECTLY FROM DATABASE
# ============================================================

def get_available_slots(
    session,
    doctor_id: int,
):
    from app.models.availability import Availability
    from app.models.blocked_slot import BlockedSlot

    availability_records = session.exec(
        select(Availability).where(
            Availability.doctor_id == doctor_id,
            Availability.is_available == True,
        )
    ).all()

    slots = []

    for availability in availability_records:

        start = availability.start_time
        end = availability.end_time

        if not start or not end:
            continue

        duration = 30

        current = start

        while current + timedelta(minutes=duration) <= end:

            slot_end = current + timedelta(
                minutes=duration
            )

            # ---------------------------------------------
            # Check existing appointments
            # ---------------------------------------------

            existing = session.exec(
                select(Appointment).where(
                    Appointment.doctor_id == doctor_id,
                    Appointment.start_time < slot_end,
                    Appointment.end_time > current,
                    Appointment.status.in_(
                        [
                            "PENDING",
                            "CONFIRMED",
                            "RESCHEDULED",
                        ]
                    ),
                )
            ).first()

            if existing:
                current = slot_end
                continue

            # ---------------------------------------------
            # Check blocked slots
            # ---------------------------------------------

            blocked = session.exec(
                select(BlockedSlot).where(
                    BlockedSlot.doctor_id == doctor_id,
                    BlockedSlot.start_time < slot_end,
                    BlockedSlot.end_time > current,
                )
            ).first()

            if blocked:
                current = slot_end
                continue

            slots.append(
                {
                    "id": (
                        f"{doctor_id}-"
                        f"{current.isoformat()}"
                    ),
                    "doctor_id": doctor_id,
                    "start_time": current,
                    "end_time": slot_end,
                    "appointment_type": (
                        availability.appointment_type
                        or "IN_PERSON"
                    ),
                }
            )

            current = slot_end

    slots.sort(
        key=lambda x: x["start_time"]
    )

    return slots


# ============================================================
# DUPLICATE BOOKING CHECK
# ============================================================

def find_existing_booking(
    session,
    patient_id: int,
    doctor_id: int,
    start_time,
):
    return session.exec(
        select(Appointment).where(
            Appointment.patient_id == patient_id,
            Appointment.doctor_id == doctor_id,
            Appointment.start_time == start_time,
            Appointment.status.in_(
                [
                    "PENDING",
                    "CONFIRMED",
                    "RESCHEDULED",
                ]
            ),
        )
    ).first()


# ============================================================
# MAIN AI HANDLER
# ============================================================

def handle_request(
    session,
    patient_id: int,
    session_id: str,
    message: str,
):
    context = get_or_create_context(
        session,
        patient_id,
        session_id,
    )

    text = message.lower().strip()

    # ========================================================
    # FIND DOCTOR
    # ========================================================

    if (
        (
            "orthopedic" in text
            or "orthopaedic" in text
            or "orthopedics" in text
        )
        and "book" not in text
        and "appointment" not in text
    ):

        doctor = find_orthopedic_doctor(
            session
        )

        if not doctor:
            return {
                "message": (
                    "I couldn't find an active "
                    "orthopedic doctor."
                ),
                "capability_result":
                    "doctor_not_found",
            }

        context.current_intent = "doctor_search"
        context.selected_doctor_id = doctor.id
        context.selected_hospital_id = doctor.hospital_id

        context.context_data = str(
            {
                "doctor_id": doctor.id,
                "hospital_id": doctor.hospital_id,
            }
        )

        session.add(context)
        session.commit()

        return {
            "message": (
                f"I found Dr. {doctor.name}, "
                f"an orthopedic doctor. "
                "Would you like me to check "
                "the available slots?"
            ),
            "capability_result": "doctor_found",
            "doctor": {
                "id": doctor.id,
                "name": doctor.name,
                "specialty": doctor.specialty,
            },
        }

    # ========================================================
    # SHOW AVAILABLE SLOTS
    # ========================================================

    if (
        "available slots" in text
        or "show slots" in text
        or "available" in text
        or "availability" in text
        or text == "slots"
    ) and "book" not in text:

        doctor_id = context.selected_doctor_id

        if not doctor_id:
            doctor = find_orthopedic_doctor(
                session
            )

            if not doctor:
                return {
                    "message": (
                        "Please find a doctor first."
                    ),
                    "capability_result":
                        "doctor_not_found",
                }

            doctor_id = doctor.id
            context.selected_doctor_id = doctor.id
            context.selected_hospital_id = (
                doctor.hospital_id
            )

        slots = get_available_slots(
            session,
            doctor_id,
        )

        context.current_intent = (
            "availability_search"
        )

        # NEVER store the whole slot list.
        context.context_data = str(
            {
                "available_slots_count":
                    len(slots)
            }
        )

        session.add(context)
        session.commit()

        if not slots:
            return {
                "message": (
                    "There are no available "
                    "slots for this doctor."
                ),
                "capability_result": {
                    "type": "availability",
                    "doctor_id": doctor_id,
                    "slots": [],
                },
            }

        return {
            "message": (
                "Here are the available "
                "appointment slots."
            ),
            "capability_result": {
                "type": "availability",
                "doctor_id": doctor_id,
                "slots": slots,
            },
        }

    # ========================================================
    # BOOK APPOINTMENT
    # ========================================================

    if (
        "book" in text
        or "appointment" in text
        or "schedule" in text
        or "reserve" in text
    ):

        doctor_id = context.selected_doctor_id
        hospital_id = context.selected_hospital_id

        if not doctor_id:

            doctor = find_orthopedic_doctor(
                session
            )

            if not doctor:
                return {
                    "message": (
                        "Please select a doctor "
                        "before booking."
                    ),
                    "capability_result":
                        "booking_failed",
                }

            doctor_id = doctor.id
            hospital_id = doctor.hospital_id

        requested_time = (
            extract_requested_time(message)
        )

        if not requested_time:
            return {
                "message": (
                    "Please specify a time, "
                    "for example 11:00 AM."
                ),
                "capability_result":
                    "time_required",
            }

        requested_hour, requested_minute = (
            requested_time
        )

        # IMPORTANT:
        # Fresh slots every single booking request.
        slots = get_available_slots(
            session,
            doctor_id,
        )

        selected_slot = None

        for slot in slots:

            start = slot["start_time"]

            if (
                start.hour == requested_hour
                and start.minute == requested_minute
            ):
                selected_slot = slot
                break

        # ====================================================
        # SLOT NOT AVAILABLE
        # ====================================================

        if not selected_slot:

            requested_display = (
                f"{requested_hour:02d}:"
                f"{requested_minute:02d}"
            )

            available_times = [
                format_time(
                    slot["start_time"]
                )
                for slot in slots
            ]

            available_times = [
                x
                for x in available_times
                if x
            ]

            return {
                "message": (
                    f"{requested_display} is not "
                    "available. Please choose "
                    "another available slot."
                    + (
                        " Available: "
                        + ", ".join(
                            available_times[:10]
                        )
                        if available_times
                        else ""
                    )
                ),
                "capability_result": {
                    "type": "availability",
                    "doctor_id": doctor_id,
                    "slots": slots,
                },
            }

        start_time = selected_slot["start_time"]
        end_time = selected_slot["end_time"]

        # ====================================================
        # DUPLICATE BOOKING
        # ====================================================

        existing = find_existing_booking(
            session,
            patient_id,
            doctor_id,
            start_time,
        )

        if existing:

            return {
                "message": (
                    "You already have an "
                    "appointment at "
                    f"{format_time(start_time)}. "
                    "Please choose another slot."
                ),
                "capability_result": {
                    "type": "already_booked",
                    "appointment_id":
                        existing.id,
                },
            }

        # ====================================================
        # UNIQUE IDEMPOTENCY KEY
        # ====================================================

        idempotency_key = (
            f"patient-{patient_id}"
            f"-doctor-{doctor_id}"
            f"-slot-{start_time.isoformat()}"
        )

        # ====================================================
        # CREATE APPOINTMENT
        # ====================================================

        try:

            result = create_appointment_capability(
                session=session,
                hospital_id=hospital_id,
                doctor_id=doctor_id,
                patient_id=patient_id,
                appointment_type=(
                    selected_slot.get(
                        "appointment_type"
                    )
                    or "IN_PERSON"
                ),
                start_time=start_time,
                end_time=end_time,
                idempotency_key=idempotency_key,
            )

        except Exception as e:

            return {
                "message": (
                    "I couldn't complete the "
                    "appointment booking."
                ),
                "capability_result": {
                    "type": "booking_failed",
                    "error": str(e),
                },
            }

        # ====================================================
        # CAPABILITY FAILURE
        # ====================================================

        if isinstance(result, dict):

            if not result.get(
                "success",
                True,
            ):

                return {
                    "message": result.get(
                        "message",
                        "Booking failed.",
                    ),
                    "capability_result":
                        "booking_failed",
                }

            if (
                result.get(
                    "capability_result"
                )
                == "idempotent_existing"
            ):

                return {
                    "message": (
                        "You already have an "
                        "appointment at "
                        f"{format_time(start_time)}. "
                        "Please choose another slot."
                    ),
                    "capability_result": {
                        "type":
                            "already_booked",
                        "appointment_id":
                            result.get(
                                "appointment_id"
                            ),
                    },
                }

        # ====================================================
        # SUCCESS
        # ====================================================

        appointment_id = None

        if isinstance(result, dict):
            appointment_id = result.get(
                "appointment_id"
            )

        context.current_intent = (
            "appointment_booking"
        )

        context.selected_appointment_id = (
            appointment_id
        )

        context.context_data = str(
            {
                "last_booked_start":
                    start_time.isoformat(),
                "last_booked_end":
                    end_time.isoformat(),
            }
        )

        session.add(context)
        session.commit()

        return {
            "message": (
                "Your appointment has been "
                "successfully booked and "
                "confirmed for "
                f"{format_time(start_time)}."
            ),
            "capability_result":
                "booking_success",
            "appointment_id":
                appointment_id,
            "appointment":
                (
                    result.get("appointment")
                    if isinstance(
                        result,
                        dict,
                    )
                    else None
                ),
        }

    # ========================================================
    # DEFAULT
    # ========================================================

    return {
        "message": (
            "Hello! 👋 I can help you "
            "find a doctor, check available "
            "slots, and book an appointment."
        ),
        "capability_result": "general",
    }
