"""
Маршруты для Workflow Engine
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...core.dependencies import get_db
from ...models.automation import EntityType
from ...services.workflow_engine import get_workflow_engine
from ...utils.logging import get_logger
from ..schemas.workflow import (
    WorkflowExecution,
    WorkflowList,
    WorkflowStatus,
    WorkflowTrigger,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.post("/trigger", response_model=WorkflowExecution)
async def trigger_workflow(trigger: WorkflowTrigger, db: Session = Depends(get_db)):
    """Запустить workflow"""
    try:
        engine = get_workflow_engine(db)
        execution_id = await engine.trigger_workflow(
            workflow_id=trigger.workflow_id,
            entity_type=trigger.entity_type,
            entity_id=trigger.entity_id,
            trigger_data=trigger.trigger_data,
        )

        return WorkflowExecution(
            execution_id=execution_id,
            workflow_id=trigger.workflow_id,
            entity_type=trigger.entity_type,
            entity_id=trigger.entity_id,
            status="running",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to trigger workflow", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to trigger workflow")


@router.get("/status/{execution_id}", response_model=WorkflowStatus)
async def get_workflow_status(execution_id: str, db: Session = Depends(get_db)):
    """Получить статус выполнения workflow"""
    try:
        engine = get_workflow_engine(db)
        status_data = await engine.get_workflow_status(execution_id)

        if not status_data:
            raise HTTPException(status_code=404, detail="Workflow execution not found")

        return WorkflowStatus(**status_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get workflow status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get workflow status")


@router.delete("/cancel/{execution_id}")
async def cancel_workflow(execution_id: str, db: Session = Depends(get_db)):
    """Отменить выполнение workflow"""
    try:
        engine = get_workflow_engine(db)
        cancelled = await engine.cancel_workflow(execution_id)

        if not cancelled:
            raise HTTPException(status_code=404, detail="Workflow execution not found")

        return {"message": "Workflow cancelled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel workflow", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to cancel workflow")


@router.get("/workflows", response_model=WorkflowList)
async def list_workflows(db: Session = Depends(get_db)):
    """Получить список доступных workflow"""
    try:
        engine = get_workflow_engine(db)

        workflows = []
        for workflow_id, workflow in engine.workflows.items():
            workflows.append(
                {
                    "id": workflow_id,
                    "name": workflow.name,
                    "entity_type": workflow.entity_type.value,
                    "description": f"Автоматический workflow для {workflow.entity_type.value}",
                    "steps_count": len(workflow.steps),
                }
            )

        return WorkflowList(workflows=workflows)

    except Exception as e:
        logger.error("Failed to list workflows", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list workflows")


@router.post("/order/created/{order_id}")
async def trigger_order_creation_workflow(order_id: int, db: Session = Depends(get_db)):
    """Триггер workflow создания заказа"""
    try:
        engine = get_workflow_engine(db)
        execution_id = await engine.trigger_workflow(
            workflow_id="order_creation",
            entity_type=EntityType.ORDER,
            entity_id=order_id,
        )

        return {
            "message": "Order creation workflow triggered",
            "execution_id": execution_id,
            "order_id": order_id,
        }

    except Exception as e:
        logger.error("Failed to trigger order creation workflow", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to trigger workflow")


@router.post("/order/payment/{order_id}")
async def trigger_payment_workflow(
    order_id: int, payment_data: dict = None, db: Session = Depends(get_db)
):
    """Триггер workflow обработки платежа"""
    try:
        engine = get_workflow_engine(db)
        execution_id = await engine.trigger_workflow(
            workflow_id="payment_processing",
            entity_type=EntityType.ORDER,
            entity_id=order_id,
            trigger_data=payment_data,
        )

        return {
            "message": "Payment processing workflow triggered",
            "execution_id": execution_id,
            "order_id": order_id,
        }

    except Exception as e:
        logger.error("Failed to trigger payment workflow", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to trigger workflow")


@router.post("/order/completion/{order_id}")
async def trigger_completion_workflow(order_id: int, db: Session = Depends(get_db)):
    """Триггер workflow завершения производства"""
    try:
        engine = get_workflow_engine(db)
        execution_id = await engine.trigger_workflow(
            workflow_id="production_completion",
            entity_type=EntityType.ORDER,
            entity_id=order_id,
        )

        return {
            "message": "Production completion workflow triggered",
            "execution_id": execution_id,
            "order_id": order_id,
        }

    except Exception as e:
        logger.error("Failed to trigger completion workflow", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to trigger workflow")


@router.post("/customer/complaint/{customer_id}")
async def trigger_complaint_workflow(
    customer_id: int, complaint_data: dict = None, db: Session = Depends(get_db)
):
    """Триггер workflow обработки жалоб"""
    try:
        engine = get_workflow_engine(db)
        execution_id = await engine.trigger_workflow(
            workflow_id="complaint_handling",
            entity_type=EntityType.CUSTOMER,
            entity_id=customer_id,
            trigger_data=complaint_data,
        )

        return {
            "message": "Complaint handling workflow triggered",
            "execution_id": execution_id,
            "customer_id": customer_id,
        }

    except Exception as e:
        logger.error("Failed to trigger complaint workflow", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to trigger workflow")
