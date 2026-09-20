from datetime import datetime, timedelta
from sqlmodel import Session, select

from app.database.database import engine
from app.models.hospital import Hospital
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.calendar import Calendar
from app.models.availability import Availability


def seed_demo_data():
    with Session(engine) as session:

        # -----------------------------
        # HOSPITAL
        # -----------------------------
        hospital = session.exec(
            select(Hospital).where(
                Hospital.name == "Demo City Care Hospital"
            )
        ).first()

        if not hospital:
            hospital = Hospital(
                name="Demo City Care Hospital",
                address="Main Road",
                city="Hyderabad",
                state="Telangana",
                phone="9999999999",
                status="APPROVED",
            )
            session.add(hospital)
            session.commit()
            session.refresh(hospital)
        else:
            hospital.status = "APPROVED"
            session.add(hospital)
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
        else:
            doctor.status = "ACTIVE"
            doctor.specialty = "Orthopedics"
            doctor.department = "Orthopedics"
            session.add(doctor)
            session.commit()

        # -----------------------------
        # PATIENT
        # -----------------------------
        patient = session.exec(
            select(Patient).where(
                Patient.phone == "9999999998"
            )
        ).first()

        if not patient:
            patient = Patient(
                first_name="Rahul",
                last_name="Kumar",
                phone="9999999998",
                email="rahul@example.com",
                preferred_language="English",
                communication_preference="SMS",
            )
            session.add(patient)
            session.commit()

        # -----------------------------
        # CALENDAR
        # -----------------------------
        calendar = session.exec(
            select(Calendar).where(
                Calendar.doctor_id == doctor.id
            )
        ).first()

        if not calendar:
            calendar = Calendar(
                doctor_id=doctor.id,
                name="Dr. Rao Calendar",
                active=True,
                timezone="Asia/Kolkata",
            )
            session.add(calendar)
            session.commit()
            session.refresh(calendar)

        # -----------------------------
        # AVAILABILITY
        # -----------------------------
        existing = session.exec(
            select(Availability).where(
                Availability.doctor_id == doctor.id
            )
        ).all()

        if not existing:
            slots = [
                ("09:00", "09:30"),
                ("09:30", "10:00"),
                ("10:00", "10:30"),
                ("10:30", "11:00"),
                ("11:00", "11:30"),
                ("14:00", "14:30"),
                ("14:30", "15:00"),
                ("15:00", "15:30"),
                ("15:30", "16:00"),
            ]

            for start, end in slots:
                session.add(
                    Availability(
                        doctor_id=doctor.id,
                        calendar_id=calendar.id,
                        start_time=datetime.fromisoformat(
                            f"2026-09-21T{start}:00"
                        ),
                        end_time=datetime.fromisoformat(
                            f"2026-09-21T{end}:00"
                        ),
                        appointment_type="IN_PERSON",
                        is_available=True,
                    )
                )

            session.commit()

        print(
            f"DEMO SEED OK | hospital={hospital.id} "
            f"doctor={doctor.id} patient={patient.id} "
            f"calendar={calendar.id}"
        )
