from datetime import datetime, timedelta
from sqlmodel import Session, select

from app.database.database import engine
from app.models.hospital import Hospital
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.calendar import Calendar
from app.models.availability import Availability
from app.models.appointment import Appointment


def seed_demo_data():
    with Session(engine) as session:

        # -----------------------------
        # HOSPITAL
        # -----------------------------
        hospital = session.exec(
            select(Hospital).where(Hospital.name == "Demo City Care Hospital")
        ).first()

        if not hospital:
            hospital = Hospital(
                name="Demo City Care Hospital",
                address="Main Road",
                city="Hyderabad",
                state="Telangana",
                phone="9876543210",
                status="APPROVED",
            )
            session.add(hospital)
            session.commit()
            session.refresh(hospital)
        else:
            hospital.status = "APPROVED"
            session.commit()

        # -----------------------------
        # DOCTOR
        # -----------------------------
        doctor = session.exec(
            select(Doctor).where(
                Doctor.name == "Dr. Rao",
                Doctor.hospital_id == hospital.id,
            )
        ).first()

        if not doctor:
            doctor = Doctor(
                hospital_id=hospital.id,
                name="Dr. Rao",
                specialty="Orthopedics",
                department="Orthopedics",
                qualifications="MBBS, MS Orthopedics",
                experience_years=10,
                languages="English, Telugu",
                consultation_type="IN_PERSON",
                consultation_duration=30,
                status="ACTIVE",
            )
            session.add(doctor)
            session.commit()
            session.refresh(doctor)

        # -----------------------------
        # PATIENT
        # -----------------------------
        patient = session.exec(
            select(Patient).where(
                Patient.email == "rahul.demo@example.com"
            )
        ).first()

        if not patient:
            patient = Patient(
                first_name="Rahul",
                last_name="Kumar",
                phone="9876501234",
                email="rahul.demo@example.com",
                date_of_birth="2000-01-15",
                preferred_language="English",
                communication_preference="SMS",
            )
            session.add(patient)
            session.commit()
            session.refresh(patient)

        # -----------------------------
        # CALENDAR
        # -----------------------------
        calendar = session.exec(
            select(Calendar).where(
                Calendar.doctor_id == doctor.id,
                Calendar.name == "Demo Calendar",
            )
        ).first()

        if not calendar:
            calendar = Calendar(
                doctor_id=doctor.id,
                name="Demo Calendar",
                is_active=True,
                timezone="Asia/Kolkata",
            )
            session.add(calendar)
            session.commit()
            session.refresh(calendar)

        # -----------------------------
        # AVAILABILITY
        # -----------------------------
        demo_slots = [
            "09:00",
            "09:30",
            "10:00",
            "10:30",
            "11:00",
            "14:00",
            "14:30",
            "15:00",
            "15:30",
        ]

        for t in demo_slots:
            start = datetime.fromisoformat(f"2026-09-21T{t}:00")
            end = start + timedelta(minutes=30)

            existing = session.exec(
                select(Availability).where(
                    Availability.doctor_id == doctor.id,
                    Availability.calendar_id == calendar.id,
                    Availability.start_time == start,
                )
            ).first()

            if not existing:
                session.add(
                    Availability(
                        doctor_id=doctor.id,
                        calendar_id=calendar.id,
                        start_time=start,
                        end_time=end,
                        appointment_type="IN_PERSON",
                        is_available=True,
                    )
                )

        session.commit()

        # -----------------------------
        # DEMO APPOINTMENT
        # -----------------------------
        appointment_start = datetime.fromisoformat(
            "2026-09-21T09:00:00"
        )
        appointment_end = datetime.fromisoformat(
            "2026-09-21T09:30:00"
        )

        appointment = session.exec(
            select(Appointment).where(
                Appointment.doctor_id == doctor.id,
                Appointment.patient_id == patient.id,
                Appointment.start_time == appointment_start,
            )
        ).first()

        if not appointment:
            appointment = Appointment(
                hospital_id=hospital.id,
                doctor_id=doctor.id,
                patient_id=patient.id,
                appointment_type="IN_PERSON",
                start_time=appointment_start,
                end_time=appointment_end,
                status="CONFIRMED",
                idempotency_key="demo-seed-appointment-001",
            )
            session.add(appointment)
            session.commit()
            session.refresh(appointment)

        print(
            f"DEMO DATA READY: hospital={hospital.id}, "
            f"doctor={doctor.id}, patient={patient.id}, "
            f"calendar={calendar.id}, appointment={appointment.id}"
        )
