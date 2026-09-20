from fastapi import APIRouter, Depends, Header, HTTPException

router = APIRouter(prefix="/rbac", tags=["RBAC"])


VALID_ROLES = {
    "PLATFORM_ADMIN",
    "HOSPITAL_ADMIN",
    "DOCTOR",
    "PATIENT",
}


def get_role(
    x_user_role: str | None = Header(default=None),
):
    if not x_user_role:
        raise HTTPException(
            status_code=401,
            detail="Missing X-User-Role header.",
        )

    role = x_user_role.upper()

    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Invalid user role.",
        )

    return role


@router.get("/me")
def get_current_user_role(
    role: str = Depends(get_role),
):
    return {
        "authenticated": True,
        "role": role,
    }


@router.get("/platform-admin")
def platform_admin_only(
    role: str = Depends(get_role),
):
    if role != "PLATFORM_ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Platform Admin access required.",
        )

    return {
        "success": True,
        "message": "Platform Admin access granted.",
    }


@router.get("/hospital-admin")
def hospital_admin_only(
    role: str = Depends(get_role),
):
    if role not in {"PLATFORM_ADMIN", "HOSPITAL_ADMIN"}:
        raise HTTPException(
            status_code=403,
            detail="Hospital Admin access required.",
        )

    return {
        "success": True,
        "message": "Hospital Admin access granted.",
    }


@router.get("/doctor")
def doctor_only(
    role: str = Depends(get_role),
):
    if role not in {
        "PLATFORM_ADMIN",
        "HOSPITAL_ADMIN",
        "DOCTOR",
    }:
        raise HTTPException(
            status_code=403,
            detail="Doctor access required.",
        )

    return {
        "success": True,
        "message": "Doctor access granted.",
    }


@router.get("/patient")
def patient_only(
    role: str = Depends(get_role),
):
    if role not in {
        "PLATFORM_ADMIN",
        "HOSPITAL_ADMIN",
        "PATIENT",
    }:
        raise HTTPException(
            status_code=403,
            detail="Patient access required.",
        )

    return {
        "success": True,
        "message": "Patient access granted.",
    }
