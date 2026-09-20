from datetime import datetime, timedelta
import re

from sqlmodel import select

from app.capabilities.doctor_search import search_doctors
from app.capabilities.availability_search import check_availability
from app.capabilities.appointment_booking import create_appointment_capability

from app.models.ai_context import AIContext


# ============================================================
# Helpers
# ============================================================

def get_or_create_context(
    session,
    patient_id: int,
    session_id: str,
):
    statement = select(AIContext).where(
        AIContext.session_id == session_id
    )

    context = session.exec(statement).first()

    if context:
        return context

    context = AIContext(
        patient_id=patient_id,
        session_id=session_id,
    )

    session.add(context)
    session.commit()
    session.refresh(context)

    return context


def extract_requested_time(message: str):
    """
    Extract times such as:
    10:00
    10:30
    10 am
    10am
    4 pm
    4pm
    """

    message_lower = message.lower()

    # 10:00 / 10:30 / 16:00
    match = re.search(
        r"\b(\d{1,2}):(\d{2})\s*(am|pm)?\b",
        message_lower,
    )

    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        meridiem = match.group(3)

        if meridiem == "pm" and hour < 12:
            hour += 12

        if meridiem == "am" and hour == 12:
            hour = 0

        return hour, minute

    # 10am / 10 am / 4pm / 4 pm
    match = re.search(
        r"\b(\d{1,2})\s*(am|pm)\b",
        message_lower,
    )

    if match:
        hour = int(match.group(1))
        meridiem = match.group(2)

        if meridiem == "pm" and hour < 12:
            hour += 12

        if meridiem == "am" and hour == 12:
            hour = 0

        return hour, 0

    return None


def slot_value(slot, key):
    """
    Supports both dictionary slots and SQLModel objects.
    """

    if isinstance(slot, dict):
        return slot.get(key)

    return getattr(slot, key, None)


def format_time(value):
    if not value:
        return ""

    if isinstance(value, datetime):
        return value.strftime("%I:%M %p").lstrip("0")

    return str(value)


def normalize_slots(slots):
    """
    Convert availability results into a consistent
    dictionary format for the frontend.
    """

    result = []

    for slot in slots or []:

        start_time = slot_value(
            slot,
            "start_time",
        )

        end_time = slot_value(
            slot,
            "end_time",
        )

        slot_id = slot_value(
            slot,
            "id",
        )

        doctor_id = slot_value(
            slot,
            "doctor_id",
        )

        appointment_type = slot_value(
            slot,
            "appointment_type",
        )

        result.append(
            {
                "id": slot_id,
                "doctor_id": doctor_id,
                "start_time": start_time,
                "end_time": end_time,
                "appointment_type": appointment_type,
            }
        )

    return result


# ============================================================
# Doctor search
# ============================================================

def find_orthopedic_doctor(
    session,
):
    doctors = search_doctors(
        session=session,
        specialty="Orthopedics",
    )

    if not doctors:
        return None

    return doctors[0]


# ============================================================
# Main AI handler
# ============================================================

def handle_request(
    session,
    patient_id: int,
    session_id: str,
    message: str,
):

    message_lower = message.lower().strip()

    context = get_or_create_context(
        session=session,
        patient_id=patient_id,
        session_id=session_id,
    )

    # ========================================================
    # DOCTOR DISCOVERY
    # ========================================================

    orthopedic_keywords = [
        "orthopedic",
        "orthopaedic",
        "ortho",
        "bone doctor",
        "joint doctor",
    ]

    asks_for_doctor = any(
        keyword in message_lower
        for keyword in orthopedic_keywords
    )

    if asks_for_doctor:

        doctor = find_orthopedic_doctor(
            session=session,
        )

        if not doctor:

            return {
                "message": (
                    "I couldn't find an active orthopedic "
                    "doctor right now."
                ),
                "capability_result": "doctor_not_found",
            }

        context.current_intent = "doctor_search"
        context.selected_doctor_id = doctor.id

        session.add(context)
        session.commit()

        doctor_name = doctor.name

        return {
            "message": (
                f"I found {doctor_name}, an orthopedic doctor. "
                "Would you like me to check the available slots?"
            ),
            "capability_result": "doctor_found",
        }

    # ========================================================
    # AVAILABILITY SEARCH
    # ========================================================

    availability_keywords = [
        "available slots",
        "availability",
        "available time",
        "available appointment",
        "show slots",
        "check slots",
        "slots",
        "appointments available",
    ]

    asks_for_availability = any(
        keyword in message_lower
        for keyword in availability_keywords
    )

    if asks_for_availability:

        doctor_id = context.selected_doctor_id

        if not doctor_id:

            doctor = find_orthopedic_doctor(
                session=session,
            )

            if not doctor:

                return {
                    "message": (
                        "I couldn't find an active "
                        "orthopedic doctor."
                    ),
                    "capability_result": "doctor_not_found",
                }

            doctor_id = doctor.id

            context.selected_doctor_id = doctor_id
            session.add(context)
            session.commit()

        slots = check_availability(
            session=session,
            doctor_id=doctor_id,
        )

        normalized_slots = normalize_slots(
            slots
        )

        if not normalized_slots:

            return {
                "message": (
                    "I couldn't find any available "
                    "appointment slots."
                ),
                "capability_result": {
                    "type": "availability",
                    "slots": [],
                },
            }

        # Save first available slot in context
        context.current_intent = "availability_search"

        context.context_data = str(
            {
                "available_slots":len( normalized_slots)
            }
        )

        session.add(context)
        session.commit()

        # Human-readable message
        time_list = []

        for slot in normalized_slots[:10]:

            time_text = format_time(
                slot["start_time"]
            )

            if time_text:
                time_list.append(
                    time_text
                )

        if time_list:

            message_text = (
                "Here are the available appointment "
                "slots: "
                + ", ".join(time_list)
                + ". Please choose a time to book."
            )

        else:

            message_text = (
                "Here are the available appointment "
                "slots. Please choose one to book."
            )

        return {
            "message": message_text,
            "capability_result": {
                "type": "availability",
                "doctor_id": doctor_id,
                "slots": normalized_slots,
            },
        }

    # ========================================================
    # BOOKING
    # ========================================================

    booking_keywords = [
        "book",
        "schedule",
        "appointment",
        "reserve",
    ]

    asks_for_booking = any(
        keyword in message_lower
        for keyword in booking_keywords
    )

    if asks_for_booking:

        doctor_id = context.selected_doctor_id

        if not doctor_id:

            doctor = find_orthopedic_doctor(
                session=session,
            )

            if not doctor:

                return {
                    "message": (
                        "I couldn't find a doctor "
                        "to book with."
                    ),
                    "capability_result": "doctor_not_found",
                }

            doctor_id = doctor.id

            context.selected_doctor_id = doctor_id
            session.add(context)
            session.commit()

        requested_time = extract_requested_time(
            message
        )

        slots = check_availability(
            session=session,
            doctor_id=doctor_id,
        )

        normalized_slots = normalize_slots(
            slots
        )

        if not normalized_slots:

            return {
                "message": (
                    "There are currently no available "
                    "slots for this doctor."
                ),
                "capability_result": {
                    "type": "availability",
                    "slots": [],
                },
            }

        selected_slot = None

        # ----------------------------------------------------
        # Match requested time
        # ----------------------------------------------------

        if requested_time:

            requested_hour, requested_minute = (
                requested_time
            )

            for slot in normalized_slots:

                start = slot["start_time"]

                if not start:
                    continue

                if isinstance(
                    start,
                    str,
                ):
                    try:
                        start_dt = datetime.fromisoformat(
                            start.replace(
                                "Z",
                                "+00:00",
                            )
                        )
                    except ValueError:
                        continue
                else:
                    start_dt = start

                if (
                    start_dt.hour
                    == requested_hour
                    and start_dt.minute
                    == requested_minute
                ):
                    selected_slot = slot
                    break

        # ----------------------------------------------------
        # If no specific time requested,
        # don't book automatically.
        # ----------------------------------------------------

        if not selected_slot:

            available_times = []

            for slot in normalized_slots[:10]:

                time_text = format_time(
                    slot["start_time"]
                )

                if time_text:
                    available_times.append(
                        time_text
                    )

            return {
                "message": (
                    "Please choose one of these available "
                    "times: "
                    + ", ".join(available_times)
                ),
                "capability_result": {
                    "type": "availability",
                    "doctor_id": doctor_id,
                    "slots": normalized_slots,
                },
            }

        # ----------------------------------------------------
        # Get start/end
        # ----------------------------------------------------

        start_time = selected_slot["start_time"]
        end_time = selected_slot["end_time"]

        if not start_time:
            return {
                "message": (
                    "I couldn't determine the selected "
                    "appointment time."
                ),
                "capability_result": "booking_failed",
            }

        if not end_time:

            # Default 30-minute consultation
            if isinstance(
                start_time,
                str,
            ):
                start_dt = datetime.fromisoformat(
                    start_time.replace(
                        "Z",
                        "+00:00",
                    )
                )
            else:
                start_dt = start_time

            end_time = (
                start_dt
                + timedelta(minutes=30)
            )

        # ----------------------------------------------------
        # Book appointment
        # ----------------------------------------------------

        try:

            booking_result = (
                create_appointment_capability(
                    session=session,
                    hospital_id=(
                        getattr(
                            context,
                            "selected_hospital_id",
                            None,
                        )
                    ),
                    doctor_id=doctor_id,
                    patient_id=patient_id,
                    appointment_type=(
                        selected_slot.get(
                            "appointment_type"
                        )
                        or "CONSULTATION"
                    ),
                    start_time=start_time,
                    end_time=end_time,
                    idempotency_key=(
                        f"patient-{patient_id}-"
                        f"doctor-{doctor_id}-"
                        f"slot-{start_time.isoformat()}"
                    ),
                )
            )

        except TypeError:

            # Fallback for capability implementations
            # using a different argument structure.
            booking_result = (
                create_appointment_capability(
                    session=session,
                    patient_id=patient_id,
                    doctor_id=doctor_id,
                    start_time=start_time,
                    end_time=end_time,
                )
            )

        except Exception as e:

            return {
                "message": (
                    "I couldn't complete the appointment "
                    f"booking: {str(e)}"
                ),
                "capability_result": {
                    "type": "booking_failed",
                    "error": str(e),
                },
            }

        # ----------------------------------------------------
        # Save selected appointment
        # ----------------------------------------------------

        appointment = None

        if isinstance(
            booking_result,
            dict,
        ):
            appointment = (
                booking_result.get(
                    "appointment"
                )
                or booking_result
            )

        if appointment:

            appointment_id = (
                appointment.get("id")
                if isinstance(
                    appointment,
                    dict,
                )
                else getattr(
                    appointment,
                    "id",
                    None,
                )
            )

            context.selected_appointment_id = (
                appointment_id
            )

            context.selected_slot = str(
                selected_slot
            )

            context.current_intent = (
                "appointment_booked"
            )

            session.add(context)
            session.commit()

        return {
            "message": (
                "Your appointment has been "
                "successfully booked and confirmed."
            ),
            "capability_result": {
                "type": "booking_success",
                "appointment": appointment,
                "workflow_triggered": (
                    booking_result.get(
                        "workflow_triggered"
                    )
                    if isinstance(
                        booking_result,
                        dict,
                    )
                    else None
                ),
                "workflow_execution_id": (
                    booking_result.get(
                        "workflow_execution_id"
                    )
                    if isinstance(
                        booking_result,
                        dict,
                    )
                    else None
                ),
            },
        }

    # ========================================================
    # DEFAULT RESPONSE
    # ========================================================

    return {
        "message": (
            "I can help you find a doctor, "
            "check available appointment slots, "
            "and book an appointment. "
            "For example, you can say "
            "'I need an orthopedic doctor'."
        ),
        "capability_result": None,
    }
