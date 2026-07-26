from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import threading

from app.core.database import get_db
from app.models.execution import Execution, ExecutionLog
from app.models.workflow import Workflow
from app.models.user import User
from app.schemas.execution import ExecutionOut
from app.api.v1.auth import get_current_user
from app.services.execution_engine import run_workflow

router = APIRouter(prefix="/executions", tags=["Executions"])


@router.post("/run/{workflow_id}", response_model=ExecutionOut, status_code=201)
def start_execution(
    workflow_id:      int,
    user_input:       str = "",
    background_tasks: BackgroundTasks = None,
    db:               Session = Depends(get_db),
    current_user:     User    = Depends(get_current_user),
):
    """
    POST /executions/run/{workflow_id}?user_input=...
    
    Creates an execution record and starts the workflow in a background thread.
    Returns the execution ID immediately so the frontend can start polling.
    
    The actual execution runs in the background via run_workflow().
    The frontend polls GET /executions/{id} every 2 seconds to see progress.
    """
    # Verify workflow exists and belongs to user
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.user_id == current_user.id
    ).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Create the execution record
    execution = Execution(
        user_id       = current_user.id,
        workflow_id   = workflow_id,
        workflow_name = workflow.name,
        user_input    = user_input,
        status        = "pending",
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    exec_id = execution.id
    print(f"[API] Created execution {exec_id} for workflow '{workflow.name}'")

    # Start execution in a separate thread
    # We use threading.Thread instead of BackgroundTasks because
    # run_workflow opens its own DB session and runs long-running LLM calls
    thread = threading.Thread(
        target = run_workflow,
        args   = (exec_id, workflow_id, user_input),
        daemon = True,   # daemon=True: thread stops if main process stops
    )
    thread.start()

    # Return the execution immediately — frontend will poll for updates
    execution.logs = []
    return execution


@router.get("/", response_model=List[ExecutionOut])
def list_executions(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
    limit:        int     = 20,
):
    """
    GET /executions/
    Returns recent executions for the dashboard Action Zone.
    """
    executions = (
        db.query(Execution)
        .filter(Execution.user_id == current_user.id)
        .order_by(Execution.started_at.desc())
        .limit(limit)
        .all()
    )
    for exe in executions:
        exe.logs = db.query(ExecutionLog).filter(
            ExecutionLog.execution_id == exe.id
        ).all()
    return executions


@router.get("/{execution_id}", response_model=ExecutionOut)
def get_execution(
    execution_id: int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """
    GET /executions/{id}
    Returns execution status + all agent logs.
    Called by the frontend every 2 seconds while status = 'running'.
    """
    execution = db.query(Execution).filter(
        Execution.id      == execution_id,
        Execution.user_id == current_user.id,
    ).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    execution.logs = db.query(ExecutionLog).filter(
        ExecutionLog.execution_id == execution_id
    ).order_by(ExecutionLog.id.asc()).all()

    return execution


@router.get("/workflow/{workflow_id}", response_model=List[ExecutionOut])
def get_workflow_executions(
    workflow_id:  int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """GET /executions/workflow/{id} — all runs for a specific workflow."""
    executions = (
        db.query(Execution)
        .filter(
            Execution.workflow_id == workflow_id,
            Execution.user_id     == current_user.id,
        )
        .order_by(Execution.started_at.desc())
        .limit(10)
        .all()
    )
    for exe in executions:
        exe.logs = db.query(ExecutionLog).filter(
            ExecutionLog.execution_id == exe.id
        ).all()
    return executions