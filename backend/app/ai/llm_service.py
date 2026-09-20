import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5.6-luna"
)


def mock_llm(user_message: str) -> str:
    message = user_message.lower()

    if "book" in message and "orthopedic" in message:
        return (
            "Sure. I can help you book an appointment with an "
            "orthopedic doctor. Which date would you prefer?"
        )

    if "orthopedic" in message:
        return (
            "I can help you find an orthopedic doctor. "
            "Would you like me to check available doctors and slots?"
        )

    if "appointment" in message:
        return (
            "I can help with your appointment. "
            "Would you like to book, reschedule, or cancel an appointment?"
        )

    if "cancel" in message:
        return (
            "I can help you cancel an appointment. "
            "Please provide the appointment details."
        )

    if "reschedule" in message:
        return (
            "I can help you reschedule your appointment. "
            "Which new date or time would you prefer?"
        )

    return (
        "I can help you with hospital discovery, doctor appointments, "
        "scheduling, cancellation, rescheduling, and pre-visit questionnaires."
    )


def ask_llm(user_message: str) -> str:

    try:
        response = client.responses.create(
            model=MODEL,
            instructions=(
                "You are an administrative healthcare access assistant. "
                "Help with hospitals, doctors, appointments, scheduling, "
                "questionnaires and administrative information. "
                "Do not diagnose, prescribe, recommend treatment, "
                "or change medications."
            ),
            input=user_message
        )

        return response.output_text

    except Exception as e:

        print(f"LLM unavailable. Using Mock LLM: {e}")

        return mock_llm(user_message)
