"""
Plugin API schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class PluginBase(BaseModel):
    """Base plugin schema"""

    name: str
    display_name: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None
    homepage: Optional[str] = None
    license: Optional[str] = None


class PluginResponse(PluginBase):
    """Plugin response schema"""

    id: int
    is_installed: bool = False
    is_active: bool = False
    is_loaded: bool = False
    sandbox_enabled: bool = True
    installed_at: datetime
    updated_at: datetime
    interfaces: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class PluginCreate(PluginBase):
    """Plugin create schema"""

    source_code: Optional[str] = None
    sandbox_enabled: bool = True


class PluginUpdate(BaseModel):
    """Plugin update schema"""

    display_name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    homepage: Optional[str] = None
    license: Optional[str] = None
    sandbox_enabled: Optional[bool] = None


class PluginActionRequest(BaseModel):
    """Plugin action request schema"""

    parameters: Dict[str, Any] = {}
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    use_sandbox: bool = True


class PluginActionResponse(BaseModel):
    """Plugin action response schema"""

    success: bool
    message: Optional[str] = None
    data: Dict[str, Any] = {}
    error: Optional[str] = None
    execution_time: Optional[float] = None
    memory_used: Optional[float] = None


class PluginRegistryResponse(BaseModel):
    """Plugin registry response schema"""

    name: str
    display_name: str
    description: Optional[str] = None
    version: str
    category: Optional[str] = None
    author: Optional[str] = None
    repository_url: Optional[str] = None
    download_count: int = 0
    rating: float = 0.0


class PluginInstallRequest(BaseModel):
    """Plugin install request schema"""

    plugin_name: str


class PluginSandboxTest(BaseModel):
    """Plugin sandbox test schema"""

    code: str
    test_action: Optional[str] = None
    test_parameters: Optional[Dict[str, Any]] = None
    execute: bool = False


class PluginSandboxResponse(BaseModel):
    """Plugin sandbox response schema"""

    valid: bool
    validation_message: Optional[str] = None
    execution_success: Optional[bool] = None
    execution_result: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    error_type: Optional[str] = None


class PluginLogResponse(BaseModel):
    """Plugin log response schema"""

    id: int
    action_name: str
    execution_status: str
    parameters: Dict[str, Any] = {}
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    user_id: Optional[int] = None
    executed_at: datetime


class PluginHookResponse(BaseModel):
    """Plugin hook response schema"""

    id: int
    hook_type: str
    hook_event: str
    priority: int
    conditions: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    created_at: datetime


class PluginActionInfo(BaseModel):
    """Plugin action info schema"""

    name: str
    action_schema: Dict[str, Any]
