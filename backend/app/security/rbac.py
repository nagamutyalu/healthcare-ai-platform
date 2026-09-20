from fastapi import Header, HTTPException


VALID_ROLES = {
    "PLATFORM_ADMIN",
    "HOSPITAL_ADMIN",
    "DOCTOR",
    "PATIENT",
}


def get_current_role(
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


def require_roles(*allowed_roles):
    allowed = {role.upper() for role in allowed_roles}

    def role_checker(
        current_role: str = None,
    ):
        if current_role not in allowed:
            raise HTTPException(
                status_code=403,
                detail="You are not authorized to perform this action.",
            )

        return current_role

    return role_checker


def check_role(
    current_role: str,
    allowed_roles: list[str],
):
    if current_role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action.",
        )

    return True
