"""Admin API for the external AI connection."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...core.dependencies import get_current_admin_user, get_db
from ...models.user import User
from ...services.ai_connection import (
    AIConnectionError,
    fetch_models,
    get_ai_settings,
    get_ai_usage_and_balance,
    test_ai_connection,
    update_ai_settings,
)

router = APIRouter(prefix="/ai", tags=["ai"])


class AISettingsUpdate(BaseModel):
    api_key: str | None = Field(default=None, max_length=4096)
    selected_model: str | None = Field(default=None, max_length=255)


class AITestRequest(BaseModel):
    model: str | None = Field(default=None, max_length=255)


@router.get("/settings")
async def read_ai_settings(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    item = get_ai_settings(db)
    return {
        "api_key_configured": bool(item.encrypted_api_key),
        "selected_model": item.selected_model,
    }


@router.put("/settings")
async def save_ai_settings(
    payload: AISettingsUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    item = update_ai_settings(
        db,
        api_key=payload.api_key,
        selected_model=payload.selected_model,
    )
    return {
        "api_key_configured": bool(item.encrypted_api_key),
        "selected_model": item.selected_model,
    }


@router.get("/usage")
async def read_ai_usage(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    return await get_ai_usage_and_balance(db)


@router.get("/models")
async def list_ai_models(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    try:
        return {"data": await fetch_models(db)}
    except AIConnectionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/test")
async def test_ai(
    payload: AITestRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    try:
        return await test_ai_connection(db, model=payload.model)
    except AIConnectionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
