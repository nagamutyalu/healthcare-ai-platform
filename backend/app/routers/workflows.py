from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database.database import get_session
from app.models.workflow import Workflow
from app.models.workflow_execution import WorkflowExecution
from app.models.appointment import Appointment
from app.models.notification import Notification


router = APIRouter(
    prefix="/workflows",
    tags=["Workflows"]
)


@router.post("/")
def create_workflow(
    workflow: Workflow,
    session: Session = Depends(get_session)
):
    session.add(workflow)
    session.commit()
    session.refresh(workflow)

    return workflow


@router.get("/")
def get_workflows(
    session: Session = Depends(get_session)
):
    return session.exec(select(Workflow)).all()


@router.get("/{workflow_id}")
def get_workflow(
    workflow_id: int,
    session: Session = Depends(get_session)
):
    workflow = session.get(Workflow, workflow_id)

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found"
        )

    return workflow


@router.post("/{workflow_id}/execute")
def execute_workflow(
    workflow_id: int,
    trigger_data: str | None = None,
    session: Session = Depends(get_session)
):
    workflow = session.get(Workflow, workflow_id)

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found"
        )

    if not workflow.is_active:
        raise HTTPException(
            status_code=400,
            detail="Workflow is inactive"
        )

    execution = WorkflowExecution(
        workflow_id=workflow_id,
        status="RUNNING",
        trigger_data=trigger_data
    )

    session.add(execution)
    session.commit()
    session.refresh(execution)

    # Appointment confirmation workflow
    if workflow.event_type == "APPOINTMENT_CONFIRMED":

        if not trigger_data:
            execution.status = "FAILED"
            execution.error_message = "Appointment ID is required"
            execution.completed_at = datetime.utcnow()

            session.commit()
            session.refresh(execution)

            return execution

        try:
            appointment_id = int(
                trigger_data.split("=")[1]
            )

            appointment = session.get(
                Appointment,
                appointment_id
            )

            if not appointment:
                raise ValueError(
                    "Appointment not found"
                )

            notification = Notification(
                recipient_type="PATIENT",
                recipient_id=appointment.patient_id,
                notification_type="APPOINTMENT_CONFIRMED",
                title="Appointment Confirmed",
                message=(
                    f"Your appointment with Doctor ID "
                    f"{appointment.doctor_id} has been confirmed."
                ),
                status="PENDING"
            )

            session.add(notification)

            execution.status = "COMPLETED"
            execution.result = (
                "Appointment confirmation notification created"
            )
            execution.completed_at = datetime.utcnow()

            session.commit()
            session.refresh(execution)

            return execution

        except Exception as e:

            execution.status = "FAILED"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()

            session.commit()
            session.refresh(execution)

            return execution

    # Default workflow
    execution.status = "COMPLETED"
    execution.result = "Workflow executed successfully"
    execution.completed_at = datetime.utcnow()

    session.commit()
    session.refresh(execution)

    return execution


@router.get("/{workflow_id}/executions")
def get_workflow_executions(
    workflow_id: int,
    session: Session = Depends(get_session)
):
    workflow = session.get(
        Workflow,
        workflow_id
    )

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found"
        )

    statement = select(WorkflowExecution).where(
        WorkflowExecution.workflow_id == workflow_id
    )

    return session.exec(statement).all()
def trigger_appointment_confirmed_workflow(
    session: Session,
    appointment_id: int
):
    workflow = session.exec(
        select(Workflow).where(
            Workflow.event_type == "APPOINTMENT_CONFIRMED",
            Workflow.is_active == True
        )
    ).first()

    if not workflow:
        return None

    execution = WorkflowExecution(
        workflow_id=workflow.id,
        status="RUNNING",
        trigger_data=f"appointment_id={appointment_id}"
    )

    session.add(execution)
    session.commit()
    session.refresh(execution)

    try:
        appointment = session.get(
            Appointment,
            appointment_id
        )

        if not appointment:
            raise ValueError("Appointment not found")

        notification = Notification(
            recipient_type="PATIENT",
            recipient_id=appointment.patient_id,
            notification_type="APPOINTMENT_CONFIRMED",
            title="Appointment Confirmed",
            message=(
                f"Your appointment with Doctor ID "
                f"{appointment.doctor_id} has been confirmed."
            ),
            status="PENDING"
        )

        session.add(notification)

        execution.status = "COMPLETED"
        execution.result = (
            "Appointment confirmation notification created"
        )
        execution.completed_at = datetime.utcnow()

        session.commit()
        session.refresh(execution)

        return execution

    except Exception as e:

        execution.status = "FAILED"
        execution.error_message = str(e)
        execution.completed_at = datetime.utcnow()

        session.commit()
        session.refresh(execution)

        return execution
