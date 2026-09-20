from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database.database import get_session
from app.models.hospital import Hospital
from app.security.audit import create_audit_log


router = APIRouter(
    prefix="/hospitals",
    tags=["Hospitals"],
)


@router.post("/")
def create_hospital(
    hospital: Hospital,
    session: Session = Depends(get_session),
):
    hospital.status = "DRAFT"

    session.add(hospital)
    session.commit()
    session.refresh(hospital)

    create_audit_log(
        session=session,
        user_role="HOSPITAL_ADMIN",
        action="CREATE_HOSPITAL",
        resource_type="Hospital",
        resource_id=hospital.id,
        success=True,
        details=f"Hospital '{hospital.name}' created in DRAFT status.",
    )

    return hospital


@router.get("/")
def get_hospitals(
    session: Session = Depends(get_session),
):
    return session.exec(
        select(Hospital)
    ).all()


@router.get("/{hospital_id}")
def get_hospital(
    hospital_id: int,
    session: Session = Depends(get_session),
):
    hospital = session.get(Hospital, hospital_id)

    if not hospital:
        raise HTTPException(
            status_code=404,
            detail="Hospital not found.",
        )

    return hospital


@router.post("/{hospital_id}/submit")
def submit_hospital(
    hospital_id: int,
    session: Session = Depends(get_session),
):
    hospital = session.get(Hospital, hospital_id)

    if not hospital:
        raise HTTPException(
            status_code=404,
            detail="Hospital not found.",
        )

    if hospital.status != "DRAFT":
        raise HTTPException(
            status_code=400,
            detail="Only DRAFT hospitals can be submitted.",
        )

    hospital.status = "SUBMITTED"

    session.add(hospital)
    session.commit()
    session.refresh(hospital)

    create_audit_log(
        session=session,
        user_role="HOSPITAL_ADMIN",
        action="SUBMIT_HOSPITAL",
        resource_type="Hospital",
        resource_id=hospital.id,
        success=True,
        details="Hospital submitted for review.",
    )

    return {
        "success": True,
        "message": "Hospital submitted for review.",
        "hospital": hospital,
    }


@router.post("/{hospital_id}/review")
def review_hospital(
    hospital_id: int,
    session: Session = Depends(get_session),
):
    hospital = session.get(Hospital, hospital_id)

    if not hospital:
        raise HTTPException(
            status_code=404,
            detail="Hospital not found.",
        )

    if hospital.status != "SUBMITTED":
        raise HTTPException(
            status_code=400,
            detail="Only SUBMITTED hospitals can enter review.",
        )

    hospital.status = "UNDER_REVIEW"

    session.add(hospital)
    session.commit()
    session.refresh(hospital)

    create_audit_log(
        session=session,
        user_role="PLATFORM_ADMIN",
        action="REVIEW_HOSPITAL",
        resource_type="Hospital",
        resource_id=hospital.id,
        success=True,
        details="Hospital moved to UNDER_REVIEW.",
    )

    return {
        "success": True,
        "message": "Hospital moved to review.",
        "hospital": hospital,
    }


@router.post("/{hospital_id}/approve")
def approve_hospital(
    hospital_id: int,
    session: Session = Depends(get_session),
):
    hospital = session.get(Hospital, hospital_id)

    if not hospital:
        raise HTTPException(
            status_code=404,
            detail="Hospital not found.",
        )

    if hospital.status != "UNDER_REVIEW":
        raise HTTPException(
            status_code=400,
            detail="Only UNDER_REVIEW hospitals can be approved.",
        )

    hospital.status = "APPROVED"

    session.add(hospital)
    session.commit()
    session.refresh(hospital)

    create_audit_log(
        session=session,
        user_role="PLATFORM_ADMIN",
        action="APPROVE_HOSPITAL",
        resource_type="Hospital",
        resource_id=hospital.id,
        success=True,
        details=f"Hospital '{hospital.name}' approved.",
    )

    return {
        "success": True,
        "message": "Hospital approved successfully.",
        "hospital": hospital,
    }


@router.post("/{hospital_id}/reject")
def reject_hospital(
    hospital_id: int,
    session: Session = Depends(get_session),
):
    hospital = session.get(Hospital, hospital_id)

    if not hospital:
        raise HTTPException(
            status_code=404,
            detail="Hospital not found.",
        )

    if hospital.status != "UNDER_REVIEW":
        raise HTTPException(
            status_code=400,
            detail="Only UNDER_REVIEW hospitals can be rejected.",
        )

    hospital.status = "REJECTED"

    session.add(hospital)
    session.commit()
    session.refresh(hospital)

    create_audit_log(
        session=session,
        user_role="PLATFORM_ADMIN",
        action="REJECT_HOSPITAL",
        resource_type="Hospital",
        resource_id=hospital.id,
        success=True,
        details=f"Hospital '{hospital.name}' rejected.",
    )

    return {
        "success": True,
        "message": "Hospital rejected.",
        "hospital": hospital,
    }
