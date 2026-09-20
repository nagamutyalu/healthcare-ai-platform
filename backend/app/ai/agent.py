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
    from datetime import datetime

    text = message.lower().strip()

    # DATE + TIME: 23 Sep 10:00, Sep 23 10:00 AM,
    # 2026-09-23 10:00, etc.
    date_match = re.search(
        r"\\b(20\\d{2})[-/](\\d{1,2})[-/](\\d{1,2})\\b",
        text,
    )

    month_match = re.search(
        r"\\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|"
        r"may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|"
        r"oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\\s+(\\d{1,2})\\b",
        text,
        re.IGNORECASE,
    )

    time_match = re.search(
        r"\\b(\\d{1,2})(?::(\\d{2}))?\\s*(am|pm)\\b",
        text,
        re.IGNORECASE,
    )

    if not time_match:
        time_match = re.search(
            r"\\b([01]?\\d|2[0-3]):([0-5]\\d)\\b",
            text,
        )

    if not time_match:
        return None

    hour = int(time_match.group(1))
    minute = int(time_match.group(2) or 0)
    period = time_match.group(3) if len(time_match.groups()) >= 3 else None

    if period:
        period = period.lower()
        if period == "am" and hour == 12:
            hour = 0
        elif period == "pm" and hour != 12:
            hour += 12

    # Return time tuple for backward compatibility.
    # Date selection is handled from the user's explicit date below.
    if date_match:
        return (
            hour,
            minute,
            datetime(
                int(date_match.group(1)),
                int(date_match.group(2)),
                int(date_match.group(3)),
            ).date(),
        )

    if month_match:
        months = {
            "jan":1,"january":1,"feb":2,"february":2,
            "mar":3,"march":3,"apr":4,"april":4,"may":5,
            "jun":6,"june":6,"jul":7,"july":7,
            "aug":8,"august":8,"sep":9,"september":9,
            "oct":10,"october":10,"nov":11,"november":11,
            "dec":12,"december":12,
        }
        month_text = re.search(
            r"[A-Za-z]+", month_match.group(0)
        ).group(0).lower()
        month = months[month_text]
        year = datetime.now().year
        return (
            hour,
            minute,
            datetime(year, month, int(month_match.group(1))).date(),
        )

    return (hour, minute, None)

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
    doctors = session.exec(
        select(Doctor)
    ).all()

    for doctor in doctors:
        status = (doctor.status or "").strip().upper()
        specialty = (doctor.specialty or "").strip().lower()
        department = (doctor.department or "").strip().lower()

        if status != "ACTIVE":
            continue

        if (
            "orthopedic" in specialty
            or "orthopaedic" in specialty
            or "orthopedic" in department
            or "orthopaedic" in department
        ):
            return doctor

    return None

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
    patient_id,
    doctor_id,
    start_time,
):
    from app.models.appointment import Appointment

    appointments = session.exec(
        select(Appointment).where(
            Appointment.patient_id == patient_id,
            Appointment.doctor_id == doctor_id,
        )
    ).all()

    for appointment in appointments:
        if appointment.status not in (
            "CONFIRMED",
            "PENDING",
            "RESCHEDULED",
        ):
            continue

        # EXACT DATETIME — date AND time must match.
        existing_start = appointment.start_time

        if existing_start == start_time:
            return appointment

    return None

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

        requested_hour = requested_time[0]
        requested_minute = requested_time[1]
        requested_date = (
            requested_time[2]
            if len(requested_time) > 2
            else None
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
                and (
                    requested_date is None
                    or start.date() == requested_date
                )
            ):
                selected_slot = slot
                break

        # ====================================================
        # IDEMPOTENT RETRY CHECK — BEFORE SLOT AVAILABILITY
        # ====================================================

        requested_start = None

        for existing_candidate in session.exec(
            select(Appointment).where(
                Appointment.patient_id == patient_id,
                Appointment.doctor_id == doctor_id,
            )
        ).all():
            if existing_candidate.status in ["CONFIRMED", "PENDING", "RESCHEDULED"]:
                if (
                    existing_candidate.start_time.hour == requested_hour
                    and existing_candidate.start_time.minute == requested_minute
                ):
                    requested_start = existing_candidate.start_time
                    break

        if requested_start is not None:
            existing = find_existing_booking(
                session,
                patient_id,
                doctor_id,
                requested_start,
            )

            if existing:
                return {
                    "message": (
                        "Your appointment is already confirmed for "
                        f"{format_time(existing.start_time)}."
                    ),
                    "capability_result": "already_booked",
                    "appointment": {
                        "id": existing.id,
                        "patient_id": existing.patient_id,
                        "doctor_id": existing.doctor_id,
                        "start_time": existing.start_time.isoformat(),
                        "end_time": existing.end_time.isoformat(),
                        "status": existing.status,
                        "external_appointment_id": existing.external_appointment_id,
                    },
                    "appointment_id": existing.id,
                    "idempotent_existing": True,
                }

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
