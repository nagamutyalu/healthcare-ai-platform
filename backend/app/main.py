from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --------------------------------------------------
# DATABASE
# --------------------------------------------------

from app.database.database import create_db_and_tables

# --------------------------------------------------
# MODELS
# Import models so SQLModel knows about all tables
# --------------------------------------------------
from app.models.hospital import Hospital
from app. models.doctor import Doctor
from app.models.calendar import Calendar
from app.models.availability import Availability
from app.models.blocked_slot import BlockedSlot
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.mock_ehr_appointment import MockEHRAppointment
from app.models.questionnaire import Questionnaire
from app.models.question import Question
from app.models.questionnaire_response import QuestionnaireResponse
from app.models.notification import Notification
from app.models.workflow import Workflow
from app.models.workflow_execution import WorkflowExecution
from app.models.ai_conversation import AIConversation
from app.models.ai_context import AIContext
from app.models.audit_log import AuditLog

from app.routers.audit_logs import router as audit_logs_router
from app.routers.rbac import router as rbac_router
# --------------------------------------------------
# ROUTERS
# --------------------------------------------------

from app.routers.hospitals import router as hospital_router
from app.routers.doctors import router as doctor_router
from app.routers.calendars import router as calendar_router
from app.routers.availability import router as availability_router
from app.routers.patients import router as patient_router
from app.routers.appointments import router as appointment_router
from app.routers.questionnaires import router as questionnaire_router
from app.routers.questionnaire_responses import (
    router as questionnaire_response_router
)
from app.routers.notifications import router as notification_router
from app.routers.workflows import router as workflow_router
from app.routers.ai import router as ai_router
from app.routers.capabilities import router as capability_router

# --------------------------------------------------
# FASTAPI APPLICATION
# --------------------------------------------------

app = FastAPI(
    title="Healthcare AI Platform",
    description=(
        "AI-powered multi-hospital patient discovery, "
        "scheduling, intake and workflow platform."
    ),
    version="1.0.0",
)
app.router.routes.extend(rbac_router.routes)
app.router.routes.extend(audit_logs_router.routes)
# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# STARTUP
# --------------------------------------------------

@app.on_event("startup")
def startup_event():
    create_db_and_tables()


# --------------------------------------------------
# ROOT
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Healthcare AI Platform API is running",
        "status": "online",
        "version": "1.0.0",
    }


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# --------------------------------------------------
# REGISTER ROUTERS
# --------------------------------------------------

app.include_router(
    hospital_router
)

app.include_router(
    doctor_router
)

app.include_router(
    calendar_router
)

app.include_router(
    availability_router
)

app.include_router(
    patient_router
)

app.include_router(
    appointment_router
)

app.include_router(
    questionnaire_router
)

app.include_router(
    questionnaire_response_router
)

app.include_router(
    notification_router
)

app.include_router(
    workflow_router
)

app.include_router(
    ai_router
)

app.include_router(
    capability_router
)

# ============================================================
# DEMO DATA SEED
# ============================================================
try:
    from app.demo_seed import seed_demo_data
    seed_demo_data()
except Exception as e:
    print(f"DEMO SEED WARNING: {e}")
