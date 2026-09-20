from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database.database import get_session
from app.models.notification import Notification

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


@router.post("/")
def create_notification(
    notification: Notification,
    session: Session = Depends(get_session)
):
    session.add(notification)
    session.commit()
    session.refresh(notification)

    return notification


@router.get("/{recipient_type}/{recipient_id}")
def get_notifications(
    recipient_type: str,
    recipient_id: int,
    session: Session = Depends(get_session)
):
    statement = select(Notification).where(
        Notification.recipient_type == recipient_type,
        Notification.recipient_id == recipient_id
    )

    return session.exec(statement).all()


@router.put("/{notification_id}/sent")
def mark_notification_sent(
    notification_id: int,
    session: Session = Depends(get_session)
):
    notification = session.get(Notification, notification_id)

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    notification.status = "SENT"
    notification.sent_at = datetime.utcnow()

    session.add(notification)
    session.commit()
    session.refresh(notification)

    return notification
