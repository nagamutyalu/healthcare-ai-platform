from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import select

from app.database.database import get_session
from app.models.ai_conversation import AIConversation
from app.models.ai_context import AIContext

from app.ai.agent import handle_request


router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


# ============================================================
# REQUEST BODY
# ============================================================

class ChatRequest(BaseModel):
    patient_id: int
    session_id: str
    message: str


# ============================================================
# CREATE CONVERSATION
# ============================================================

@router.post("/conversation")
def create_conversation(
    patient_id: int,
    session_id: str,
    message: str,
):

    session = next(get_session())

    try:

        conversation = AIConversation(
            patient_id=patient_id,
            session_id=session_id,
            role="user",
            message=message,
        )

        session.add(conversation)
        session.commit()
        session.refresh(conversation)

        return conversation

    finally:
        session.close()


# ============================================================
# GET CONVERSATION
# ============================================================

@router.get("/conversation/{session_id}")
def get_conversation(
    session_id: str,
):

    session = next(get_session())

    try:

        conversations = session.exec(
            select(AIConversation).where(
                AIConversation.session_id
                == session_id
            )
        ).all()

        return conversations

    finally:
        session.close()


# ============================================================
# GET CONTEXT
# ============================================================

@router.get("/context/{session_id}")
def get_context(
    session_id: str,
):

    session = next(get_session())

    try:

        context = session.exec(
            select(AIContext).where(
                AIContext.session_id
                == session_id
            )
        ).first()

        if not context:
            return {
                "message": "Context not found."
            }

        return context

    finally:
        session.close()


# ============================================================
# CHAT
# ============================================================

@router.post("/chat")
def chat(
    request: ChatRequest,
):

    session = next(get_session())

    try:

        # ---------------------------------------------
        # Save user message
        # ---------------------------------------------

        user_message = AIConversation(
            patient_id=request.patient_id,
            session_id=request.session_id,
            role="user",
            message=request.message,
        )

        session.add(user_message)
        session.commit()

        # ---------------------------------------------
        # AI agent
        # ---------------------------------------------

        result = handle_request(
            session=session,
            patient_id=request.patient_id,
            session_id=request.session_id,
            message=request.message,
        )

        # ---------------------------------------------
        # Save assistant response
        # ---------------------------------------------

        assistant_message = AIConversation(
            patient_id=request.patient_id,
            session_id=request.session_id,
            role="assistant",
            message=result.get(
                "message",
                "",
            ),
        )

        session.add(assistant_message)
        session.commit()

        return {
            "session_id":
                request.session_id,

            "patient_id":
                request.patient_id,

            "message":
                result.get(
                    "message",
                    "",
                ),

            "capability_result":
                result.get(
                    "capability_result"
                ),

            "doctor":
                result.get("doctor"),

            "appointment":
                result.get(
                    "appointment"
                ),

            "appointment_id":
                result.get(
                    "appointment_id"
                ),
        }

    except Exception as e:

        session.rollback()

        return {
            "session_id":
                request.session_id,

            "patient_id":
                request.patient_id,

            "message":
                "I couldn't process your request.",

            "capability_result": {
                "type":
                    "error",

                "error":
                    str(e),
            },
        }

    finally:
        session.close()
