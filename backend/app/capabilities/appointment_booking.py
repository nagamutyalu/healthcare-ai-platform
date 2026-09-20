from datetime import datetime

from sqlmodel import Session, select

from app.models.appointment import Appointment
from app.models.availability import Availability
from app.models.doctor import Doctor
from app.models.hospital import Hospital
from app.models.patient import Patient

from app.integrations.mock_ehr import (
    create_external_appointment,
    verify_external_appointment,
)

from app.routers.workflows import trigger_appointment_confirmed_workflow


def create_appointment_capability(
    session: Session,
    hospital_id: int,
    doctor_id: int,
    patient_id: int,
    start_time: datetime,
    end_time: datetime,
    appointment_type: str = "IN_PERSON",
    idempotency_key: str | None = None,
    simulate_unknown_outcome: bool = False,
):

    # --------------------------------------------------
    # 1. VALIDATE HOSPITAL
    # --------------------------------------------------

    hospital = session.get(Hospital, hospital_id)

    if not hospital:
        return {
            "success": False,
            "message": "Hospital not found.",
            "error": "HOSPITAL_NOT_FOUND",
        }

    if getattr(hospital, "status", None) != "APPROVED":
        return {
            "success": False,
            "message": "Hospital is not approved for appointments.",
            "error": "HOSPITAL_NOT_APPROVED",
        }

    # --------------------------------------------------
    # 2. VALIDATE DOCTOR
    # --------------------------------------------------

    doctor = session.get(Doctor, doctor_id)

    if not doctor:
        return {
            "success": False,
            "message": "Doctor not found.",
            "error": "DOCTOR_NOT_FOUND",
        }

    if getattr(doctor, "status", None) != "ACTIVE":
        return {
            "success": False,
            "message": "Doctor is not active.",
            "error": "DOCTOR_NOT_ACTIVE",
        }

    if doctor.hospital_id != hospital_id:
        return {
            "success": False,
            "message": "Doctor does not belong to this hospital.",
            "error": "DOCTOR_HOSPITAL_MISMATCH",
        }

    # --------------------------------------------------
    # 3. VALIDATE PATIENT
    # --------------------------------------------------

    patient = session.get(Patient, patient_id)

    if not patient:
        return {
            "success": False,
            "message": "Patient not found.",
            "error": "PATIENT_NOT_FOUND",
        }

    # --------------------------------------------------
    # 4. VALIDATE APPOINTMENT TIME
    # --------------------------------------------------

    if start_time >= end_time:
        return {
            "success": False,
            "message": "Invalid appointment time.",
            "error": "INVALID_TIME_RANGE",
        }

    # --------------------------------------------------
    # 5. CHECK AVAILABILITY
    # --------------------------------------------------

    availability_statement = select(Availability).where(
        Availability.doctor_id == doctor_id,
        Availability.start_time <= start_time,
        Availability.end_time >= end_time,
        Availability.is_available == True,
    )

    availability = session.exec(
        availability_statement
    ).first()

    if not availability:
        return {
            "success": False,
            "message": "Selected time is not available.",
            "error": "TIME_NOT_AVAILABLE",
        }

    # --------------------------------------------------
    # 6. IDEMPOTENCY CHECK
    # --------------------------------------------------

    if idempotency_key:

        existing_by_key = session.exec(
            select(Appointment).where(
                Appointment.idempotency_key == idempotency_key
            )
        ).first()

        if existing_by_key:

            if existing_by_key.status == "CONFIRMED":
                return {
                    "success": True,
                    "message": (
                        "This appointment has already been booked."
                    ),
                    "appointment": existing_by_key,
                    "appointment_id": existing_by_key.id,
                    "external_appointment_id": (
                        existing_by_key.external_appointment_id
                    ),
                    "verified": True,
                    "idempotent_existing": True,
                    "capability_result": "already_booked",
                }

            return {
                "success": False,
                "message": (
                    "An appointment with this request "
                    "already exists."
                ),
                "error": "DUPLICATE_REQUEST",
                "appointment_id": existing_by_key.id,
            }

    # --------------------------------------------------
    # 6B. CHECK SLOT DOUBLE BOOKING
    # --------------------------------------------------

    overlapping_appointment = session.exec(
        select(Appointment).where(
            Appointment.doctor_id == doctor_id,
            Appointment.start_time < end_time,
            Appointment.end_time > start_time,
            Appointment.status.in_(
                [
                    "PENDING",
                    "CONFIRMED",
                    "RESCHEDULED",
                ]
            ),
        )
    ).first()

    if overlapping_appointment:
        return {
            "success": False,
            "message": "Selected slot is already booked.",
            "error": "SLOT_ALREADY_BOOKED",
        }

    # --------------------------------------------------
    # 7. CREATE INTERNAL APPOINTMENT
    # --------------------------------------------------

    appointment = Appointment(
        hospital_id=hospital_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        appointment_type=appointment_type,
        start_time=start_time,
        end_time=end_time,
        status="PENDING",
        idempotency_key=idempotency_key,
    )

    session.add(appointment)
    session.commit()
    session.refresh(appointment)

    # --------------------------------------------------
    # 8. CREATE APPOINTMENT IN MOCK EHR
    # --------------------------------------------------

    try:

        external_result = create_external_appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            hospital_id=hospital_id,
            start_time=start_time,
            end_time=end_time,
            appointment_type=appointment_type,
            simulate_unknown_outcome=simulate_unknown_outcome,
        )

    # --------------------------------------------------
    # 8A. UNKNOWN OUTCOME RECOVERY
    # --------------------------------------------------

    except TimeoutError as e:

        error_text = str(e)

        external_id = None

        marker = "External ID:"

        if marker in error_text:
            external_id = (
                error_text.split(marker, 1)[1].strip()
            )

        # --------------------------------------------------
        # QUERY EXTERNAL SYSTEM BEFORE CREATING AGAIN
        # --------------------------------------------------

        if external_id:

            try:

                verification = verify_external_appointment(
                    external_id
                )

            except Exception as verification_error:

                appointment.status = (
                    "RECONCILIATION_REQUIRED"
                )

                session.add(appointment)
                session.commit()
                session.refresh(appointment)

                return {
                    "success": False,
                    "message": (
                        "External booking outcome is unknown "
                        "and verification could not be completed."
                    ),
                    "error": "UNKNOWN_OUTCOME_VERIFICATION_FAILED",
                    "details": str(verification_error),
                    "appointment": appointment,
                    "appointment_id": appointment.id,
                    "external_appointment_id": external_id,
                    "verified": False,
                    "recovery": (
                        "RECONCILIATION_REQUIRED"
                    ),
                    "capability_result": (
                        "reconciliation_required"
                    ),
                }

            # --------------------------------------------------
            # EXTERNAL APPOINTMENT FOUND
            # --------------------------------------------------

            if verification.get("verified"):

                appointment.external_appointment_id = (
                    external_id
                )

                appointment.status = "CONFIRMED"

                session.add(appointment)
                session.commit()
                session.refresh(appointment)

                workflow_execution = (
                    trigger_appointment_confirmed_workflow(
                        session=session,
                        appointment_id=appointment.id,
                    )
                )

                return {
                    "success": True,
                    "message": (
                        "Appointment recovered after an "
                        "unknown external outcome. The "
                        "existing external appointment was "
                        "verified and synchronized without "
                        "creating a duplicate."
                    ),
                    "appointment": appointment,
                    "appointment_id": appointment.id,
                    "external_appointment_id": external_id,
                    "verified": True,
                    "recovery": (
                        "UNKNOWN_OUTCOME_RECOVERED"
                    ),
                    "duplicate_created": False,
                    "workflow_triggered": (
                        workflow_execution is not None
                    ),
                    "workflow_execution_id": (
                        workflow_execution.id
                        if workflow_execution
                        else None
                    ),
                    "capability_result": (
                        "booking_recovered"
                    ),
                }

        # --------------------------------------------------
        # EXTERNAL APPOINTMENT NOT FOUND
        # --------------------------------------------------

        appointment.status = (
            "RECONCILIATION_REQUIRED"
        )

        session.add(appointment)
        session.commit()
        session.refresh(appointment)

        return {
            "success": False,
            "message": (
                "External booking outcome is unknown. "
                "The appointment requires reconciliation."
            ),
            "error": "UNKNOWN_EXTERNAL_OUTCOME",
            "appointment": appointment,
            "appointment_id": appointment.id,
            "external_appointment_id": external_id,
            "verified": False,
            "recovery": "RECONCILIATION_REQUIRED",
            "capability_result": (
                "reconciliation_required"
            ),
        }

    # --------------------------------------------------
    # 8B. NORMAL EHR CREATE FAILURE
    # --------------------------------------------------

    except Exception as e:

        appointment.status = "FAILED"

        session.add(appointment)
        session.commit()
        session.refresh(appointment)

        return {
            "success": False,
            "message": (
                "External healthcare system "
                "booking failed."
            ),
            "error": "EHR_CREATE_FAILED",
            "details": str(e),
            "appointment_id": appointment.id,
        }

    # --------------------------------------------------
    # 9. STORE EXTERNAL APPOINTMENT ID
    # --------------------------------------------------

    external_id = None

    if isinstance(external_result, dict):

        external_id = (
            external_result.get(
                "external_appointment_id"
            )
            or external_result.get("id")
        )

    else:

        external_id = external_result

    appointment.external_appointment_id = external_id

    session.add(appointment)
    session.commit()
    session.refresh(appointment)

    # --------------------------------------------------
    # 10. VERIFY EXTERNAL APPOINTMENT
    # --------------------------------------------------

    try:

        verified = verify_external_appointment(
            external_id
        )

    except Exception as e:

        appointment.status = (
            "SYNCHRONIZATION_PENDING"
        )

        session.add(appointment)
        session.commit()
        session.refresh(appointment)

        return {
            "success": False,
            "message": (
                "Appointment was created externally, "
                "but verification could not be completed."
            ),
            "error": "EHR_VERIFICATION_FAILED",
            "details": str(e),
            "appointment": appointment,
            "appointment_id": appointment.id,
            "external_appointment_id": external_id,
            "verified": False,
            "capability_result": (
                "synchronization_pending"
            ),
        }

    # --------------------------------------------------
    # 11. CONFIRM AFTER SUCCESSFUL VERIFICATION
    # --------------------------------------------------

    if verified:

        appointment.status = "CONFIRMED"

        session.add(appointment)
        session.commit()
        session.refresh(appointment)

        # --------------------------------------------------
        # TRIGGER CONFIRMATION WORKFLOW
        # --------------------------------------------------

        workflow_execution = (
            trigger_appointment_confirmed_workflow(
                session=session,
                appointment_id=appointment.id,
            )
        )

        return {
            "success": True,
            "message": (
                "Appointment successfully booked "
                "and verified."
            ),
            "appointment": appointment,
            "appointment_id": appointment.id,
            "external_appointment_id": external_id,
            "verified": True,
            "workflow_triggered": (
                workflow_execution is not None
            ),
            "workflow_execution_id": (
                workflow_execution.id
                if workflow_execution
                else None
            ),
            "capability_result": (
                "booking_success"
            ),
        }

    # --------------------------------------------------
    # 12. VERIFICATION FAILED
    # --------------------------------------------------

    appointment.status = (
        "SYNCHRONIZATION_PENDING"
    )

    session.add(appointment)
    session.commit()
    session.refresh(appointment)

    return {
        "success": False,
        "message": (
            "Appointment was created, "
            "but external verification failed."
        ),
        "error": "VERIFICATION_FAILED",
        "appointment": appointment,
        "appointment_id": appointment.id,
        "external_appointment_id": external_id,
        "verified": False,
        "capability_result": (
            "synchronization_pending"
        ),
    }
