"""
Example plugins for demonstration
"""

from typing import Any, Dict, List

from .plugin_interfaces import (
    ActionPlugin,
    AutomationPlugin,
    BasePlugin,
    HookContext,
    HookPlugin,
    HookResult,
    PluginInfo,
    create_plugin_info,
)


class ExampleActionPlugin(ActionPlugin):
    """
    Example plugin that provides custom actions
    """

    def __init__(self):
        self._is_initialized = False
        super().__init__()

    @property
    def info(self) -> PluginInfo:
        return create_plugin_info(
            name="example-action-plugin",
            display_name="Пример плагина действий",
            version="1.0.0",
            description="Демонстрационный плагин с примерами действий",
            author="AICRM Team",
            homepage="https://github.com/aicrm/plugins",
        )

    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize plugin"""
        try:
            self._config = config
            self._is_initialized = True
            print(f"[ExampleActionPlugin] Initialized with config: {config}")
            return True
        except Exception as e:
            print(f"[ExampleActionPlugin] Initialization failed: {e}")
            return False

    async def shutdown(self) -> bool:
        """Shutdown plugin"""
        print("[ExampleActionPlugin] Shutting down")
        self._is_initialized = False
        return True

    def get_settings_schema(self) -> Dict[str, Any]:
        """Return JSON Schema for settings"""
        return {
            "type": "object",
            "properties": {
                "api_key": {
                    "type": "string",
                    "title": "API Key",
                    "description": "API key for external service",
                },
                "timeout": {
                    "type": "integer",
                    "title": "Timeout",
                    "description": "Request timeout in seconds",
                    "default": 30,
                    "minimum": 1,
                    "maximum": 300,
                },
            },
            "required": ["api_key"],
        }

    def get_default_settings(self) -> Dict[str, Any]:
        """Return default settings"""
        return {"api_key": "", "timeout": 30}

    async def execute_action(
        self,
        action_name: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Execute plugin action"""
        print(
            f"[ExampleActionPlugin] Executing action: {action_name} with params: {parameters}"
        )

        if action_name == "send_greeting":
            name = parameters.get("name", "World")
            message = f"Hello, {name}!"
            return {
                "success": True,
                "message": message,
                "timestamp": "2025-11-23T11:10:00Z",
            }

        elif action_name == "calculate_sum":
            numbers = parameters.get("numbers", [])
            result = sum(numbers)
            return {"success": True, "sum": result, "count": len(numbers)}

        else:
            return {"success": False, "error": f"Unknown action: {action_name}"}

    def get_available_actions(self) -> List[str]:
        """Return available actions"""
        return ["send_greeting", "calculate_sum"]

    def get_action_schema(self, action_name: str) -> Dict[str, Any]:
        """Return JSON Schema for action parameters"""
        schemas = {
            "send_greeting": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "title": "Name",
                        "description": "Name to greet",
                        "default": "World",
                    }
                },
            },
            "calculate_sum": {
                "type": "object",
                "properties": {
                    "numbers": {
                        "type": "array",
                        "title": "Numbers",
                        "description": "List of numbers to sum",
                        "items": {"type": "number"},
                        "minItems": 1,
                    }
                },
                "required": ["numbers"],
            },
        }

        return schemas.get(action_name, {"type": "object", "properties": {}})


class ExampleHookPlugin(HookPlugin):
    """
    Example plugin that provides hooks
    """

    def __init__(self):
        self._is_initialized = False
        super().__init__()

    @property
    def info(self) -> PluginInfo:
        return create_plugin_info(
            name="example-hook-plugin",
            display_name="Пример плагина хуков",
            version="1.0.0",
            description="Демонстрационный плагин с примерами хуков",
            author="AICRM Team",
            homepage="https://github.com/aicrm/plugins",
        )

    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize plugin"""
        try:
            self._config = config
            self._is_initialized = True
            print(f"[ExampleHookPlugin] Initialized with config: {config}")
            return True
        except Exception as e:
            print(f"[ExampleHookPlugin] Initialization failed: {e}")
            return False

    async def shutdown(self) -> bool:
        """Shutdown plugin"""
        print("[ExampleHookPlugin] Shutting down")
        self._is_initialized = False
        return True

    def get_settings_schema(self) -> Dict[str, Any]:
        """Return JSON Schema for settings"""
        return {
            "type": "object",
            "properties": {
                "log_level": {
                    "type": "string",
                    "title": "Log Level",
                    "enum": ["DEBUG", "INFO", "WARNING", "ERROR"],
                    "default": "INFO",
                },
                "notify_admin": {
                    "type": "boolean",
                    "title": "Notify Admin",
                    "description": "Send notifications to admin",
                    "default": true,
                },
            },
        }

    def get_default_settings(self) -> Dict[str, Any]:
        """Return default settings"""
        return {"log_level": "INFO", "notify_admin": True}

    def get_registered_hooks(self) -> List[Dict[str, Any]]:
        """Return registered hooks"""
        return [
            {
                "hook_type": "after_create",
                "hook_event": "customer_created",
                "priority": 10,
                "conditions": {"customer_type": "business"},
            },
            {"hook_type": "before_save", "hook_event": "order_updated", "priority": 5},
        ]

    async def handle_hook(self, hook_context: HookContext) -> HookResult:
        """Handle hook execution"""
        print(
            f"[ExampleHookPlugin] Handling hook: {hook_context.hook_type}:{hook_context.hook_event}"
        )

        # Example: Log customer creation and send welcome email
        if hook_context.hook_event == "customer_created":
            print(f"New customer created: {hook_context.entity_id}")

            # Simulate sending welcome email
            return HookResult(
                success=True,
                message="Welcome email sent to new customer",
                data={"email_sent": True, "template": "welcome_business"},
            )

        # Example: Validate order before saving
        elif hook_context.hook_event == "order_updated":
            print(f"Order updated: {hook_context.entity_id}")

            # Simulate validation
            if hook_context.data and hook_context.data.get("total_amount", 0) < 0:
                return HookResult(
                    success=False,
                    message="Order total cannot be negative",
                    should_continue=False,
                )

        return HookResult(
            success=True,
            message=f"Hook {hook_context.hook_event} processed successfully",
        )


class ExampleAutomationPlugin(AutomationPlugin):
    """
    Example plugin that provides custom automation capabilities
    """

    def __init__(self):
        self._is_initialized = False
        super().__init__()

    @property
    def info(self) -> PluginInfo:
        return create_plugin_info(
            name="example-automation-plugin",
            display_name="Пример автоматизационного плагина",
            version="1.0.0",
            description="Демонстрационный плагин с кастомными действиями автоматизации",
            author="AICRM Team",
            homepage="https://github.com/aicrm/plugins",
        )

    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize plugin"""
        try:
            self._config = config
            self._is_initialized = True
            print(f"[ExampleAutomationPlugin] Initialized with config: {config}")
            return True
        except Exception as e:
            print(f"[ExampleAutomationPlugin] Initialization failed: {e}")
            return False

    async def shutdown(self) -> bool:
        """Shutdown plugin"""
        print("[ExampleAutomationPlugin] Shutting down")
        self._is_initialized = False
        return True

    def get_settings_schema(self) -> Dict[str, Any]:
        """Return JSON Schema for settings"""
        return {
            "type": "object",
            "properties": {
                "custom_sms_provider": {
                    "type": "string",
                    "title": "SMS Provider",
                    "enum": ["provider_a", "provider_b", "custom"],
                    "default": "provider_a",
                },
                "custom_sms_api_key": {
                    "type": "string",
                    "title": "SMS API Key",
                    "description": "API key for SMS provider",
                },
            },
        }

    def get_default_settings(self) -> Dict[str, Any]:
        """Return default settings"""
        return {"custom_sms_provider": "provider_a", "custom_sms_api_key": ""}

    def get_custom_actions(self) -> List[Dict[str, Any]]:
        """Return custom automation actions"""
        return [
            {
                "action_type": "CUSTOM_SEND_SMS",
                "display_name": "Отправить SMS через кастомного провайдера",
                "description": "Отправка SMS через настроенного провайдера",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "phone": {"type": "string", "title": "Phone number"},
                        "message": {"type": "string", "title": "Message text"},
                    },
                    "required": ["phone", "message"],
                },
                "handler": "send_custom_sms",
            },
            {
                "action_type": "CUSTOM_NOTIFY_TEAM",
                "display_name": "Уведомить команду в Slack",
                "description": "Отправка уведомления в Slack канал",
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "channel": {
                            "type": "string",
                            "title": "Slack channel",
                            "default": "#general",
                        },
                        "message": {"type": "string", "title": "Notification message"},
                    },
                    "required": ["message"],
                },
                "handler": "notify_slack_team",
            },
        ]

    def get_custom_triggers(self) -> List[Dict[str, Any]]:
        """Return custom automation triggers"""
        return [
            {
                "trigger_event": "CUSTOM_EXTERNAL_API_CALL",
                "display_name": "Вызов внешнего API",
                "description": "Срабатывает при вызове внешнего webhook API",
                "conditions_schema": {
                    "type": "object",
                    "properties": {
                        "api_endpoint": {"type": "string", "title": "API Endpoint URL"},
                        "http_method": {
                            "type": "string",
                            "enum": ["GET", "POST", "PUT", "DELETE"],
                            "default": "POST",
                        },
                    },
                    "required": ["api_endpoint"],
                },
            }
        ]

    async def execute_custom_action(
        self,
        action_type: str,
        action_config: Dict[str, Any],
        entity_type: str,
        entity_id: int,
    ) -> Dict[str, Any]:
        """Execute custom automation action"""
        print(f"[ExampleAutomationPlugin] Executing custom action: {action_type}")

        if action_type == "CUSTOM_SEND_SMS":
            # Simulate SMS sending
            return {
                "success": True,
                "message": f"SMS sent to {action_config.get('phone')}",
                "provider": self._config.get("custom_sms_provider"),
            }

        elif action_type == "CUSTOM_NOTIFY_TEAM":
            # Simulate Slack notification
            return {
                "success": True,
                "message": f"Notification sent to Slack channel {action_config.get('channel')}",
                "timestamp": "2025-11-23T11:10:00Z",
            }

        else:
            return {"success": False, "error": f"Unknown action type: {action_type}"}


# Registry of example plugins
EXAMPLE_PLUGINS = {
    "example-action-plugin": ExampleActionPlugin,
    "example-hook-plugin": ExampleHookPlugin,
    "example-automation-plugin": ExampleAutomationPlugin,
}


def get_example_plugin(name: str):
    """Get example plugin class by name"""
    return EXAMPLE_PLUGINS.get(name)


def list_example_plugins():
    """List all available example plugins"""
    return [
        {
            "name": plugin_class().info.name,
            "display_name": plugin_class().info.display_name,
            "description": plugin_class().info.description,
            "version": plugin_class().info.version,
            "category": "example",
        }
        for plugin_class in EXAMPLE_PLUGINS.values()
    ]
