"""
Plugin API Router
Provides REST API endpoints for plugin management
"""

import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ...models import User
from ...schemas.plugin import (
    PluginActionRequest,
    PluginActionResponse,
    PluginCreate,
    PluginInstallRequest,
    PluginRegistryResponse,
    PluginResponse,
    PluginSandboxResponse,
    PluginSandboxTest,
    PluginUpdate,
)
from ..dependencies import get_current_user, get_db
from ..services.plugin.plugin_manager import PluginManager
from ..services.plugin.sandbox_executor import validate_plugin_sandbox

router = APIRouter(
    prefix="/api/v1/plugin",
    tags=["plugin"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)

# Global plugin manager instance
plugin_manager: Optional[PluginManager] = None


def get_plugin_manager(db: Session = Depends(get_db)) -> PluginManager:
    """Get or create plugin manager instance"""
    global plugin_manager
    if plugin_manager is None:
        plugin_manager = PluginManager(db)
        # Initialize plugin system
        import asyncio

        asyncio.create_task(plugin_manager.initialize())
    return plugin_manager


@router.get("/status", response_model=Dict[str, Any])
async def get_plugin_system_status(
    plugin_manager: PluginManager = Depends(get_plugin_manager),
) -> Dict[str, Any]:
    """Get plugin system status"""
    loaded_plugins = plugin_manager.get_loaded_plugins()
    return {
        "status": "active",
        "loaded_plugins_count": len(loaded_plugins),
        "loaded_plugins": loaded_plugins,
        "features": {
            "sandbox_enabled": True,
            "hook_system_enabled": True,
            "action_system_enabled": True,
        },
    }


@router.get("/list", response_model=List[PluginResponse])
async def list_plugins(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    plugin_manager: PluginManager = Depends(get_plugin_manager),
) -> List[PluginResponse]:
    """Get list of installed plugins"""
    from ...models.plugin import Plugin

    plugins = db.query(Plugin).all()
    loaded_plugins = {p["name"]: p for p in plugin_manager.get_loaded_plugins()}

    result = []
    for plugin in plugins:
        is_loaded = plugin.name in loaded_plugins
        result.append(
            PluginResponse(
                id=plugin.id,
                name=plugin.name,
                display_name=plugin.display_name,
                version=plugin.version,
                description=plugin.description,
                author=plugin.author,
                is_installed=plugin.is_installed,
                is_active=plugin.is_active,
                is_loaded=is_loaded,
                sandbox_enabled=getattr(plugin, "sandbox_enabled", True),
                installed_at=plugin.created_at,
                updated_at=plugin.updated_at,
                interfaces=loaded_plugins.get(plugin.name, {}).get("interfaces", []),
            )
        )

    return result


@router.get("/registry", response_model=List[PluginRegistryResponse])
async def get_plugin_registry(
    plugin_manager: PluginManager = Depends(get_plugin_manager),
    current_user: User = Depends(get_current_user),
) -> List[PluginRegistryResponse]:
    """Get available plugins from registry"""
    registry_plugins = plugin_manager.get_plugin_registry()

    result = []
    for plugin in registry_plugins:
        result.append(
            PluginRegistryResponse(
                name=plugin["name"],
                display_name=plugin["display_name"],
                description=plugin["description"],
                version=plugin["version"],
                category=plugin["category"],
                author=plugin["author"],
                repository_url=plugin["repository_url"],
                download_count=plugin["download_count"],
                rating=plugin.get("rating", 0.0),
            )
        )

    return result


@router.post("/install", response_model=Dict[str, Any])
async def install_plugin(
    request: PluginInstallRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    plugin_manager: PluginManager = Depends(get_plugin_manager),
) -> Dict[str, Any]:
    """Install a new plugin from registry"""
    try:
        # Import plugin class (simplified - in real app would download from registry)
        plugin_class = await _get_plugin_class_from_registry(request.plugin_name)

        if not plugin_class:
            raise HTTPException(status_code=404, detail="Plugin not found in registry")

        result = await plugin_manager.install_plugin(
            request.plugin_name, plugin_class, current_user.id
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    except Exception as e:
        logger.error(f"Error installing plugin {request.plugin_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Installation failed: {str(e)}")


@router.post("/upload", response_model=Dict[str, Any])
async def upload_plugin(
    file: UploadFile = File(...),
    plugin_name: str = Form(...),
    sandbox_enabled: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    plugin_manager: PluginManager = Depends(get_plugin_manager),
) -> Dict[str, Any]:
    """Upload and install plugin from file"""
    try:
        # Validate file type
        if not file.filename.endswith(".py"):
            raise HTTPException(
                status_code=400, detail="Only Python files are supported"
            )

        # Read plugin code
        plugin_code = await file.read()
        plugin_code_str = plugin_code.decode("utf-8")

        # Validate plugin code
        validation_result = await validate_plugin_sandbox(plugin_code_str)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Plugin validation failed: {validation_result['error']}",
            )

        # Create plugin record
        from ...models.plugin import Plugin

        plugin_record = Plugin(
            name=plugin_name,
            display_name=plugin_name,  # Will be updated from plugin info
            version="1.0.0",  # Will be updated from plugin info
            source_code=plugin_code_str,
            sandbox_enabled=sandbox_enabled,
            is_installed=True,
            is_active=False,
            installed_by=current_user.id,
        )

        # Extract plugin info from code (simplified)
        try:
            plugin_info = _extract_plugin_info_from_code(plugin_code_str)
            plugin_record.display_name = plugin_info.get("display_name", plugin_name)
            plugin_record.version = plugin_info.get("version", "1.0.0")
            plugin_record.description = plugin_info.get("description", "")
            plugin_record.author = plugin_info.get("author", "Unknown")
        except Exception as e:
            logger.warning(f"Could not extract plugin info: {e}")

        db.add(plugin_record)
        db.commit()

        return {
            "success": True,
            "message": f"Plugin '{plugin_name}' uploaded and installed",
            "plugin_id": plugin_record.id,
            "validation": validation_result,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading plugin: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.put("/{plugin_name}/activate", response_model=Dict[str, Any])
async def activate_plugin(
    plugin_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    plugin_manager: PluginManager = Depends(get_plugin_manager),
) -> Dict[str, Any]:
    """Activate a plugin"""
    try:
        # Get plugin record
        from ...models.plugin import Plugin

        plugin_record = db.query(Plugin).filter(Plugin.name == plugin_name).first()

        if not plugin_record:
            raise HTTPException(status_code=404, detail="Plugin not found")

        if not plugin_record.is_installed:
            raise HTTPException(status_code=400, detail="Plugin is not installed")

        if plugin_record.is_active:
            return {"success": True, "message": "Plugin is already active"}

        # Load plugin
        success = await plugin_manager.load_plugin(plugin_record)

        if success:
            plugin_record.is_active = True
            db.commit()
            return {"success": True, "message": f"Plugin '{plugin_name}' activated"}
        else:
            raise HTTPException(status_code=500, detail="Failed to load plugin")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error activating plugin {plugin_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Activation failed: {str(e)}")


@router.put("/{plugin_name}/deactivate", response_model=Dict[str, Any])
async def deactivate_plugin(
    plugin_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    plugin_manager: PluginManager = Depends(get_plugin_manager),
) -> Dict[str, Any]:
    """Deactivate a plugin"""
    try:
        # Get plugin record
        from ...models.plugin import Plugin

        plugin_record = db.query(Plugin).filter(Plugin.name == plugin_name).first()

        if not plugin_record:
            raise HTTPException(status_code=404, detail="Plugin not found")

        if not plugin_record.is_active:
            return {"success": True, "message": "Plugin is already inactive"}

        # Unload plugin
        success = await plugin_manager.unload_plugin(plugin_name)

        if success:
            plugin_record.is_active = False
            db.commit()
            return {"success": True, "message": f"Plugin '{plugin_name}' deactivated"}
        else:
            raise HTTPException(status_code=500, detail="Failed to unload plugin")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deactivating plugin {plugin_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Deactivation failed: {str(e)}")


@router.delete("/{plugin_name}", response_model=Dict[str, Any])
async def uninstall_plugin(
    plugin_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    plugin_manager: PluginManager = Depends(get_plugin_manager),
) -> Dict[str, Any]:
    """Uninstall a plugin"""
    try:
        result = await plugin_manager.uninstall_plugin(plugin_name, current_user.id)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uninstalling plugin {plugin_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Uninstallation failed: {str(e)}")


@router.post("/{plugin_name}/action/{action_name}", response_model=PluginActionResponse)
async def execute_plugin_action(
    plugin_name: str,
    action_name: str,
    request: PluginActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    plugin_manager: PluginManager = Depends(get_plugin_manager),
) -> PluginActionResponse:
    """Execute a plugin action"""
    try:
        result = await plugin_manager.execute_plugin_action(
            plugin_name=plugin_name,
            action_name=action_name,
            parameters=request.parameters,
            context={
                "user_id": current_user.id,
                "entity_type": request.entity_type,
                "entity_id": request.entity_id,
            },
            use_sandbox=request.use_sandbox,
        )

        return PluginActionResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            data=result.get("result", {}),
            error=result.get("error"),
            execution_time=result.get("execution_time"),
            memory_used=result.get("memory_used"),
        )

    except Exception as e:
        logger.error(f"Error executing plugin action {plugin_name}.{action_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Action execution failed: {str(e)}"
        )


@router.post("/sandbox/test", response_model=PluginSandboxResponse)
async def test_plugin_in_sandbox(
    request: PluginSandboxTest, current_user: User = Depends(get_current_user)
) -> PluginSandboxResponse:
    """Test plugin code in sandbox"""
    try:
        validation_result = await validate_plugin_sandbox(request.code)

        if request.execute and validation_result["valid"]:
            # Execute test action if provided
            if request.test_action:
                execution_result = await plugin_manager.execute_plugin_action(
                    plugin_name=f"test-plugin-{uuid.uuid4().hex[:8]}",
                    action_name=request.test_action,
                    parameters=request.test_parameters or {},
                    context={"user_id": current_user.id},
                    use_sandbox=True,
                )

                return PluginSandboxResponse(
                    valid=True,
                    validation_message=validation_result.get("message", "Valid"),
                    execution_success=execution_result.get("success", False),
                    execution_result=execution_result,
                    execution_time=execution_result.get("execution_time"),
                )
            else:
                return PluginSandboxResponse(
                    valid=True,
                    validation_message=validation_result.get("message", "Valid"),
                )
        else:
            return PluginSandboxResponse(
                valid=validation_result["valid"],
                validation_message=validation_result.get("error", "Unknown error"),
                error_type=validation_result.get("error_type", "validation"),
            )

    except Exception as e:
        logger.error(f"Error testing plugin in sandbox: {e}")
        return PluginSandboxResponse(
            valid=False,
            validation_message=f"Test failed: {str(e)}",
            error_type="execution",
        )


@router.get("/{plugin_name}/actions", response_model=List[Dict[str, Any]])
async def get_plugin_actions(
    plugin_name: str,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get available actions for a plugin"""
    if plugin_name not in plugin_manager.plugin_actions:
        raise HTTPException(
            status_code=404, detail="Plugin not found or has no actions"
        )

    actions = []
    for action_name, action_info in plugin_manager.plugin_actions[plugin_name].items():
        actions.append({"name": action_name, "schema": action_info["schema"]})

    return actions


@router.get("/{plugin_name}/hooks", response_model=List[Dict[str, Any]])
async def get_plugin_hooks(
    plugin_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get registered hooks for a plugin"""
    from ...models.plugin import Plugin, PluginHook

    plugin = db.query(Plugin).filter(Plugin.name == plugin_name).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    hooks = db.query(PluginHook).filter(PluginHook.plugin_id == plugin.id).all()

    return [
        {
            "id": hook.id,
            "hook_type": hook.hook_type,
            "hook_event": hook.hook_event,
            "priority": hook.priority,
            "conditions": hook.conditions,
            "settings": hook.settings,
            "created_at": hook.created_at,
        }
        for hook in hooks
    ]


@router.get("/{plugin_name}/logs", response_model=List[Dict[str, Any]])
async def get_plugin_logs(
    plugin_name: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get execution logs for a plugin"""
    from ...models.plugin import Plugin, PluginAction

    plugin = db.query(Plugin).filter(Plugin.name == plugin_name).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    logs = (
        db.query(PluginAction)
        .filter(PluginAction.plugin_id == plugin.id)
        .order_by(PluginAction.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": log.id,
            "action_name": log.action_name,
            "execution_status": log.execution_status,
            "parameters": log.parameters,
            "result": log.result,
            "error_message": log.error_message,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "user_id": log.user_id,
            "executed_at": log.created_at,
        }
        for log in logs
    ]


# Helper functions


async def _get_plugin_class_from_registry(plugin_name: str):
    """Get plugin class from registry (simplified implementation)"""
    # In real implementation, this would download and import from registry
    from ..services.plugin.example_plugins import EXAMPLE_PLUGINS

    return EXAMPLE_PLUGINS.get(plugin_name)


def _extract_plugin_info_from_code(plugin_code: str) -> Dict[str, Any]:
    """Extract plugin info from plugin code"""
    info = {}

    # Simple regex-based extraction (simplified)
    import re

    # Extract name
    name_match = re.search(r'"name":\s*"([^"]+)"', plugin_code)
    if name_match:
        info["name"] = name_match.group(1)

    # Extract display_name
    display_match = re.search(r'"display_name":\s*"([^"]+)"', plugin_code)
    if display_match:
        info["display_name"] = display_match.group(1)

    # Extract version
    version_match = re.search(r'"version":\s*"([^"]+)"', plugin_code)
    if version_match:
        info["version"] = version_match.group(1)

    # Extract description
    desc_match = re.search(r'"description":\s*"([^"]+)"', plugin_code)
    if desc_match:
        info["description"] = desc_match.group(1)

    # Extract author
    author_match = re.search(r'"author":\s*"([^"]+)"', plugin_code)
    if author_match:
        info["author"] = author_match.group(1)

    return info
