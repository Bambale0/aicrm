"""
Plugin Manager Service
"""

import importlib
import logging
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Type

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...models.plugin import (
    Plugin,
    PluginAction,
    PluginHook,
    PluginPermission,
    PluginRegistry,
)
from .plugin_interfaces import (
    ActionPlugin,
    BasePlugin,
    HookContext,
    HookPlugin,
    validate_plugin_implementation,
)
from .sandbox_executor import execute_plugin_in_sandbox

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Main plugin management service
    """

    def __init__(self, db: Session):
        self.db = db
        self.loaded_plugins: Dict[str, BasePlugin] = {}
        self.plugin_hooks: Dict[str, List[Dict[str, Any]]] = {}
        self.plugin_actions: Dict[str, Dict[str, Any]] = {}

    async def initialize(self) -> bool:
        """
        Initialize plugin system - load all installed and active plugins

        Returns:
            bool: True if initialization successful
        """
        try:
            logger.info("Initializing plugin system...")

            # Load all installed and active plugins
            plugins_query = (
                self.db.query(Plugin)
                .filter(Plugin.is_installed == True, Plugin.is_active == True)
                .all()
            )

            loaded_count = 0
            failed_count = 0

            for plugin_record in plugins_query:
                try:
                    success = await self.load_plugin(plugin_record)
                    if success:
                        loaded_count += 1
                        logger.info(
                            f"Plugin '{plugin_record.name}' loaded successfully"
                        )
                    else:
                        failed_count += 1
                        logger.error(f"Failed to load plugin '{plugin_record.name}'")
                except Exception as e:
                    logger.error(f"Error loading plugin '{plugin_record.name}': {e}")
                    failed_count += 1

            logger.info(
                f"Plugin system initialized: {loaded_count} loaded, {failed_count} failed"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize plugin system: {e}")
            return False

    async def shutdown(self) -> bool:
        """
        Shutdown plugin system - gracefully shutdown all loaded plugins

        Returns:
            bool: True if shutdown successful
        """
        try:
            logger.info("Shutting down plugin system...")

            shutdown_count = 0
            failed_count = 0

            for plugin_name, plugin_instance in self.loaded_plugins.items():
                try:
                    success = await plugin_instance.shutdown()
                    if success:
                        shutdown_count += 1
                        logger.info(f"Plugin '{plugin_name}' shut down successfully")
                    else:
                        failed_count += 1
                        logger.error(f"Failed to shut down plugin '{plugin_name}'")
                except Exception as e:
                    logger.error(f"Error shutting down plugin '{plugin_name}': {e}")
                    failed_count += 1

            # Clear loaded plugins and hooks
            self.loaded_plugins.clear()
            self.plugin_hooks.clear()
            self.plugin_actions.clear()

            logger.info(
                f"Plugin system shut down: {shutdown_count} shut down, {failed_count} failed"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to shutdown plugin system: {e}")
            return False

    async def load_plugin(self, plugin_record: Plugin) -> bool:
        """
        Load a plugin by its database record

        Args:
            plugin_record: Plugin database record

        Returns:
            bool: True if loading successful
        """
        try:
            plugin_name = plugin_record.name

            # Check if plugin is already loaded
            if plugin_name in self.loaded_plugins:
                logger.warning(f"Plugin '{plugin_name}' is already loaded")
                return False

            # Import plugin class
            plugin_class = self._import_plugin_class(plugin_record)
            if not plugin_class:
                logger.error(f"Failed to import plugin class for '{plugin_name}'")
                return False

            # Validate plugin implementation
            validation = validate_plugin_implementation(plugin_class)
            if not validation["is_valid"]:
                logger.error(
                    f"Plugin '{plugin_name}' validation failed: {validation['errors']}"
                )
                return False

            # Create plugin instance
            plugin_instance = plugin_class()
            self.loaded_plugins[plugin_name] = plugin_instance

            # Initialize plugin with its configuration
            config = self._merge_plugin_config(plugin_record)
            init_success = await plugin_instance.initialize(config)

            if not init_success:
                logger.error(f"Plugin '{plugin_name}' initialization failed")
                del self.loaded_plugins[plugin_name]
                return False

            # Register plugin hooks (if it's a HookPlugin)
            if isinstance(plugin_instance, HookPlugin):
                await self._register_plugin_hooks(plugin_record.id, plugin_instance)

            # Register plugin actions (if it's an ActionPlugin)
            if isinstance(plugin_instance, ActionPlugin):
                await self._register_plugin_actions(plugin_record.id, plugin_instance)

            logger.info(f"Plugin '{plugin_name}' loaded and initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Error loading plugin '{plugin_record.name}': {e}")
            # Cleanup on failure
            if plugin_record.name in self.loaded_plugins:
                del self.loaded_plugins[plugin_record.name]
            return False

    async def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin

        Args:
            plugin_name: Name of plugin to unload

        Returns:
            bool: True if unloading successful
        """
        try:
            if plugin_name not in self.loaded_plugins:
                logger.warning(f"Plugin '{plugin_name}' is not loaded")
                return False

            plugin_instance = self.loaded_plugins[plugin_name]

            # Shutdown plugin
            shutdown_success = await plugin_instance.shutdown()
            if not shutdown_success:
                logger.warning(
                    f"Plugin '{plugin_name}' shutdown may not have completed properly"
                )

            # Unregister hooks and actions
            await self._unregister_plugin_hooks(plugin_name)
            await self._unregister_plugin_actions(plugin_name)

            # Remove from loaded plugins
            del self.loaded_plugins[plugin_name]

            # Update database record
            plugin_record = (
                self.db.query(Plugin).filter(Plugin.name == plugin_name).first()
            )
            if plugin_record:
                plugin_record.is_active = False
                self.db.commit()

            logger.info(f"Plugin '{plugin_name}' unloaded successfully")
            return True

        except Exception as e:
            logger.error(f"Error unloading plugin '{plugin_name}': {e}")
            return False

    async def execute_plugin_action(
        self,
        plugin_name: str,
        action_name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        use_sandbox: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute a plugin action

        Args:
            plugin_name: Name of plugin
            action_name: Name of action to execute
            parameters: Action parameters
            context: Execution context
            use_sandbox: Whether to use sandbox execution

        Returns:
            Dict: Action execution result
        """
        plugin_action = None
        try:
            # Get plugin record
            plugin_record = (
                self.db.query(Plugin).filter(Plugin.name == plugin_name).first()
            )
            if not plugin_record:
                return {"success": False, "error": f'Plugin "{plugin_name}" not found'}

            # Choose execution method
            if use_sandbox and plugin_record.sandbox_enabled:
                # Execute in sandbox
                result = await self._execute_plugin_action_in_sandbox(
                    plugin_record, action_name, parameters, context
                )
            else:
                # Execute directly
                result = await self._execute_plugin_action_direct(
                    plugin_name, action_name, parameters, context
                )

            # Log action execution
            if result.get("success", False):
                execution_status = "success"
                error_message = None
            else:
                execution_status = "error"
                error_message = result.get("error", "Unknown error")

            plugin_action = PluginAction(
                plugin_id=plugin_record.id,
                action_name=action_name,
                execution_status=execution_status,
                parameters=parameters,
                result=result,
                error_message=error_message,
                entity_type=context.get("entity_type") if context else None,
                entity_id=context.get("entity_id") if context else None,
                user_id=context.get("user_id") if context else None,
            )

            return result

        except Exception as e:
            logger.error(
                f"Error executing plugin action {plugin_name}.{action_name}: {e}"
            )

            # Log failed action execution
            if plugin_action:
                plugin_action.execution_status = "error"
                plugin_action.error_message = str(e)
                plugin_action.error_details = {"exception": str(e)}

            return {"success": False, "error": str(e)}

        finally:
            # Save action log to database
            if plugin_action:
                try:
                    self.db.add(plugin_action)
                    self.db.commit()
                except Exception as e:
                    logger.error(f"Failed to log plugin action: {e}")

    async def _execute_plugin_action_direct(
        self,
        plugin_name: str,
        action_name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute plugin action directly"""
        # Get plugin instance
        plugin_instance = self.loaded_plugins.get(plugin_name)
        if not plugin_instance or not isinstance(plugin_instance, ActionPlugin):
            return {
                "success": False,
                "error": f'Plugin "{plugin_name}" not found or not an action plugin',
            }

        # Execute action
        result = await plugin_instance.execute_action(action_name, parameters, context)
        return result

    async def _execute_plugin_action_in_sandbox(
        self,
        plugin_record: Plugin,
        action_name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute plugin action in sandbox"""
        # Get plugin source code
        plugin_code = plugin_record.source_code
        if not plugin_code:
            return {
                "success": False,
                "error": "Plugin source code not available for sandbox execution",
            }

        # Execute in sandbox
        return await execute_plugin_in_sandbox(
            plugin_code, action_name, parameters, context
        )

    async def install_plugin(
        self,
        plugin_name: str,
        plugin_class: Type[BasePlugin],
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Install a new plugin

        Args:
            plugin_name: Name of plugin to install
            plugin_class: Plugin class
            user_id: ID of user installing the plugin

        Returns:
            Dict: Installation result
        """
        try:
            # Validate plugin implementation
            validation = validate_plugin_implementation(plugin_class)
            if not validation["is_valid"]:
                return {
                    "success": False,
                    "error": f'Plugin validation failed: {", ".join(validation["errors"])}',
                }

            # Create plugin record
            plugin_info = (
                plugin_class().info if hasattr(plugin_class(), "info") else None
            )
            if not plugin_info:
                return {"success": False, "error": "Plugin must provide info property"}

            plugin_record = Plugin(
                name=plugin_name,
                display_name=plugin_info.display_name,
                version=plugin_info.version,
                description=plugin_info.description,
                author=plugin_info.author,
                homepage=plugin_info.homepage,
                license=plugin_info.license,
                package_name=plugin_class.__module__,
                module_name=plugin_class.__module__,
                class_name=plugin_class.__name__,
                is_installed=True,
                is_active=False,  # Will be activated after successful loading
                installed_by=user_id,
            )

            # Get default settings
            if hasattr(plugin_class, "get_default_settings"):
                plugin_record.default_settings = plugin_class().get_default_settings()

            # Save to database
            self.db.add(plugin_record)
            self.db.commit()

            logger.info(f"Plugin '{plugin_name}' installed successfully")
            return {
                "success": True,
                "message": f'Plugin "{plugin_name}" installed successfully',
                "plugin_id": plugin_record.id,
            }

        except IntegrityError:
            self.db.rollback()
            return {"success": False, "error": "Plugin with this name already exists"}
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error installing plugin '{plugin_name}': {e}")
            return {"success": False, "error": f"Installation failed: {str(e)}"}

    async def uninstall_plugin(
        self, plugin_name: str, user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Uninstall a plugin

        Args:
            plugin_name: Name of plugin to uninstall
            user_id: ID of user uninstalling the plugin

        Returns:
            Dict: Uninstallation result
        """
        try:
            # Unload plugin first
            if plugin_name in self.loaded_plugins:
                await self.unload_plugin(plugin_name)

            # Remove from database
            plugin_record = (
                self.db.query(Plugin).filter(Plugin.name == plugin_name).first()
            )
            if not plugin_record:
                return {"success": False, "error": "Plugin not found"}

            # Don't allow uninstalling system plugins unless explicitly allowed
            if plugin_record.is_system:
                return {"success": False, "error": "Cannot uninstall system plugin"}

            # Remove all related records
            self.db.query(PluginAction).filter(
                PluginAction.plugin_id == plugin_record.id
            ).delete()
            self.db.query(PluginHook).filter(
                PluginHook.plugin_id == plugin_record.id
            ).delete()
            self.db.query(PluginPermission).filter(
                PluginPermission.plugin_id == plugin_record.id
            ).delete()

            # Remove plugin record
            self.db.delete(plugin_record)
            self.db.commit()

            logger.info(f"Plugin '{plugin_name}' uninstalled successfully")
            return {
                "success": True,
                "message": f'Plugin "{plugin_name}" uninstalled successfully',
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error uninstalling plugin '{plugin_name}': {e}")
            return {"success": False, "error": f"Uninstallation failed: {str(e)}"}

    def get_loaded_plugins(self) -> List[Dict[str, Any]]:
        """
        Get list of currently loaded plugins

        Returns:
            List[Dict]: List of loaded plugins info
        """
        plugins = []
        for plugin_name, plugin_instance in self.loaded_plugins.items():
            plugins.append(
                {
                    "name": plugin_name,
                    "info": asdict(plugin_instance.info),
                    "interfaces": self._get_plugin_interfaces(plugin_instance),
                }
            )
        return plugins

    def get_plugin_registry(self) -> List[Dict[str, Any]]:
        """
        Get available plugins from registry

        Returns:
            List[Dict]: List of available plugins
        """
        registry_plugins = (
            self.db.query(PluginRegistry)
            .filter(PluginRegistry.is_featured == True)
            .all()
        )

        return [
            {
                "name": p.name,
                "display_name": p.display_name,
                "description": p.description,
                "version": p.version,
                "category": p.category,
                "author": p.author,
                "repository_url": p.repository_url,
                "download_count": p.download_count,
                "rating": p.rating,
            }
            for p in registry_plugins
        ]

    # Private helper methods

    def _import_plugin_class(self, plugin_record: Plugin) -> Optional[Type[BasePlugin]]:
        """Import plugin class from module"""
        try:
            if plugin_record.package_name and plugin_record.class_name:
                # Import from package
                module = importlib.import_module(plugin_record.package_name)
                plugin_class = getattr(module, plugin_record.class_name)
                return plugin_class
            elif plugin_record.module_name and plugin_record.class_name:
                # Import from module
                module = importlib.import_module(plugin_record.module_name)
                plugin_class = getattr(module, plugin_record.class_name)
                return plugin_class
        except Exception as e:
            logger.error(f"Failed to import plugin class: {e}")

        return None

    def _merge_plugin_config(self, plugin_record: Plugin) -> Dict[str, Any]:
        """Merge default and current plugin configuration"""
        config = plugin_record.default_settings or {}
        if plugin_record.current_settings:
            config.update(plugin_record.current_settings)
        return config

    async def _register_plugin_hooks(self, plugin_id: int, plugin_instance: HookPlugin):
        """Register hooks for a HookPlugin"""
        hooks = plugin_instance.get_registered_hooks()

        for hook in hooks:
            hook_record = PluginHook(
                plugin_id=plugin_id,
                hook_type=hook["hook_type"],
                hook_event=hook["hook_event"],
                priority=hook.get("priority", 10),
                conditions=hook.get("conditions"),
                settings=hook.get("settings"),
            )

            try:
                self.db.add(hook_record)

                # Add to in-memory hooks registry
                hook_key = f"{hook['hook_type']}:{hook['hook_event']}"
                if hook_key not in self.plugin_hooks:
                    self.plugin_hooks[hook_key] = []

                self.plugin_hooks[hook_key].append(
                    {
                        "plugin_name": plugin_instance.info.name,
                        "plugin_id": plugin_id,
                        "priority": hook.get("priority", 10),
                        "conditions": hook.get("conditions"),
                        "settings": hook.get("settings"),
                    }
                )

            except Exception as e:
                logger.error(
                    f"Failed to register hook for plugin {plugin_instance.info.name}: {e}"
                )

        self.db.commit()

    async def _register_plugin_actions(
        self, plugin_id: int, plugin_instance: ActionPlugin
    ):
        """Register actions for an ActionPlugin"""
        actions = plugin_instance.get_available_actions()

        for action_name in actions:
            if plugin_instance.info.name not in self.plugin_actions:
                self.plugin_actions[plugin_instance.info.name] = {}

            self.plugin_actions[plugin_instance.info.name][action_name] = {
                "plugin_id": plugin_id,
                "schema": plugin_instance.get_action_schema(action_name),
            }

    async def _unregister_plugin_hooks(self, plugin_name: str):
        """Unregister hooks for a plugin"""
        # Remove from in-memory registry
        hooks_to_remove = []
        for hook_key, hooks in self.plugin_hooks.items():
            self.plugin_hooks[hook_key] = [
                h for h in hooks if h["plugin_name"] != plugin_name
            ]
            if not self.plugin_hooks[hook_key]:
                hooks_to_remove.append(hook_key)

        for hook_key in hooks_to_remove:
            del self.plugin_hooks[hook_key]

    async def _unregister_plugin_actions(self, plugin_name: str):
        """Unregister actions for a plugin"""
        if plugin_name in self.plugin_actions:
            del self.plugin_actions[plugin_name]

    def _check_hook_conditions(
        self, conditions: Optional[Dict[str, Any]], context: HookContext
    ) -> bool:
        """Check if hook conditions are met"""
        if not conditions:
            return True

        # Simple condition checking - can be extended
        for key, expected_value in conditions.items():
            if hasattr(context, key):
                actual_value = getattr(context, key)
                if actual_value != expected_value:
                    return False

        return True

    def _get_plugin_interfaces(self, plugin_instance: BasePlugin) -> List[str]:
        """Get list of interfaces implemented by plugin"""
        interfaces = []
        if isinstance(plugin_instance, ActionPlugin):
            interfaces.append("ActionPlugin")
        if isinstance(plugin_instance, HookPlugin):
            interfaces.append("HookPlugin")
        # Add other interfaces as they are implemented
