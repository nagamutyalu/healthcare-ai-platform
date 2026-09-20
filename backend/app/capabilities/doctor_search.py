from sqlmodel import Session, select

from app.models.doctor import Doctor


def search_doctors(
    session: Session,
    specialty: str | None = None,
    hospital_id: int | None = None
):
    statement = select(Doctor).where(
        Doctor.status == "ACTIVE"
    )

    if specialty:
        statement = statement.where(
            Doctor.specialty.ilike(f"%{specialty}%")
        )

    if hospital_id:
        statement = statement.where(
            Doctor.hospital_id == hospital_id
        )

    return session.exec(statement).all()
