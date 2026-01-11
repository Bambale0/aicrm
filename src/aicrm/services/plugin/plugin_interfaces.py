"""
Plugin system interfaces
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


@dataclass
class PluginInfo:
    """Plugin metadata"""

    name: str
    display_name: str
    version: str
    description: str
    author: str
    homepage: Optional[str] = None
    license: Optional[str] = None


@dataclass
class HookContext:
    """Context passed to hook handlers"""

    hook_type: str
    hook_event: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    user_id: Optional[int] = None
    data: Optional[Dict[str, Any]] = None
    db_session: Optional[Any] = None


@dataclass
class HookResult:
    """Result returned by hook handlers"""

    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    modified_data: Optional[Dict[str, Any]] = None
    should_continue: bool = True


class BasePlugin(ABC):
    """Base plugin interface - all plugins must implement this"""

    @property
    @abstractmethod
    def info(self) -> PluginInfo:
        """Plugin metadata"""
        pass

    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize plugin with configuration

        Args:
            config: Plugin configuration

        Returns:
            bool: True if initialization successful
        """
        pass

    @abstractmethod
    async def shutdown(self) -> bool:
        """
        Shutdown plugin gracefully

        Returns:
            bool: True if shutdown successful
        """
        pass

    @abstractmethod
    def get_settings_schema(self) -> Dict[str, Any]:
        """
        Return JSON Schema for plugin settings

        Returns:
            Dict: JSON Schema object
        """
        pass

    @abstractmethod
    def get_default_settings(self) -> Dict[str, Any]:
        """
        Return default settings

        Returns:
            Dict: Default configuration values
        """
        pass


class ActionPlugin(BasePlugin):
    """Plugin that can execute actions"""

    @abstractmethod
    async def execute_action(
        self,
        action_name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a plugin action

        Args:
            action_name: Name of action to execute
            parameters: Action parameters
            context: Execution context (entity_type, entity_id, user_id, etc.)

        Returns:
            Dict: Action result
        """
        pass

    @abstractmethod
    def get_available_actions(self) -> List[str]:
        """
        Return list of available actions

        Returns:
            List[str]: Available action names
        """
        pass

    @abstractmethod
    def get_action_schema(self, action_name: str) -> Dict[str, Any]:
        """
        Return JSON Schema for action parameters

        Args:
            action_name: Name of action

        Returns:
            Dict: JSON Schema for action parameters
        """
        pass


class HookPlugin(BasePlugin):
    """Plugin that can register hooks"""

    @abstractmethod
    def get_registered_hooks(self) -> List[Dict[str, Any]]:
        """
        Return list of hooks this plugin registers for

        Returns:
            List[Dict]: Hook configurations
            [
                {
                    'hook_type': 'before_save',
                    'hook_event': 'order_created',
                    'priority': 10,
                    'conditions': {...}
                }
            ]
        """
        pass

    @abstractmethod
    async def handle_hook(self, hook_context: HookContext) -> HookResult:
        """
        Handle a hook execution

        Args:
            hook_context: Hook execution context

        Returns:
            HookResult: Hook execution result
        """
        pass


class IntegrationPlugin(BasePlugin):
    """Plugin that integrates with external services"""

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to external service

        Returns:
            Dict: Connection test result
            {
                'success': bool,
                'message': str,
                'details': {...}
            }
        """
        pass

    @abstractmethod
    async def sync_data(self, sync_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronize data with external service

        Args:
            sync_config: Synchronization configuration

        Returns:
            Dict: Synchronization result
        """
        pass

    @abstractmethod
    def get_integration_info(self) -> Dict[str, Any]:
        """
        Return integration information

        Returns:
            Dict: Integration metadata
            {
                'service_name': 'External Service',
                'service_url': 'https://api.service.com',
                'supported_operations': ['read', 'write', 'sync'],
                'webhook_url': 'https://aicrm.com/api/webhooks/service'
            }
        """
        pass


class AnalyticsPlugin(BasePlugin):
    """Plugin that provides analytics capabilities"""

    @abstractmethod
    async def collect_metrics(
        self, entity_type: str, entity_id: int, metrics_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Collect and calculate metrics

        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            metrics_config: Metrics configuration

        Returns:
            Dict: Collected metrics
        """
        pass

    @abstractmethod
    async def generate_report(
        self, report_config: Dict[str, Any], filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate analytics report

        Args:
            report_config: Report configuration
            filters: Report filters

        Returns:
            Dict: Report data
        """
        pass

    @abstractmethod
    def get_available_metrics(self) -> List[Dict[str, Any]]:
        """
        Return list of available metrics

        Returns:
            List[Dict]: Available metrics
            [
                {
                    'name': 'conversion_rate',
                    'display_name': 'Conversion Rate',
                    'type': 'percentage',
                    'entity_types': ['order'],
                    'description': 'Order to customer conversion rate'
                }
            ]
        """
        pass


class AutomationPlugin(BasePlugin):
    """Plugin that extends automation capabilities"""

    @abstractmethod
    def get_custom_actions(self) -> List[Dict[str, Any]]:
        """
        Return custom automation actions provided by this plugin

        Returns:
            List[Dict]: Custom actions
            [
                {
                    'action_type': 'CUSTOM_SEND_SMS',
                    'display_name': 'Send SMS via Custom Provider',
                    'description': 'Send SMS using configured SMS provider',
                    'parameters_schema': {...},
                    'handler': 'send_sms'  # Method name in plugin
                }
            ]
        """
        pass

    @abstractmethod
    def get_custom_triggers(self) -> List[Dict[str, Any]]:
        """
        Return custom automation triggers provided by this plugin

        Returns:
            List[Dict]: Custom triggers
            [
                {
                    'trigger_event': 'CUSTOM_API_WEBHOOK',
                    'display_name': 'Custom API Webhook',
                    'description': 'Triggered by custom API webhook',
                    'conditions_schema': {...}
                }
            ]
        """
        pass

    @abstractmethod
    async def execute_custom_action(
        self,
        action_type: str,
        action_config: Dict[str, Any],
        entity_type: str,
        entity_id: int,
    ) -> Dict[str, Any]:
        """
        Execute custom automation action

        Args:
            action_type: Type of action to execute
            action_config: Action configuration
            entity_type: Entity type
            entity_id: Entity ID

        Returns:
            Dict: Action execution result
        """
        pass


# Utility functions for plugin validation


def validate_plugin_implementation(plugin_class: type) -> Dict[str, Any]:
    """
    Validate that a plugin class properly implements required interfaces

    Args:
        plugin_class: Plugin class to validate

    Returns:
        Dict: Validation result
    """
    result = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "implemented_interfaces": [],
    }

    # Check base implementation
    required_methods = [
        "info",
        "initialize",
        "shutdown",
        "get_settings_schema",
        "get_default_settings",
    ]

    for method in required_methods:
        if not hasattr(plugin_class, method) or not callable(
            getattr(plugin_class, method)
        ):
            result["errors"].append(f"Missing required method: {method}")
            result["is_valid"] = False

    # Check for abstract methods
    try:
        plugin_instance = plugin_class()
        # If we can create instance, it's not properly abstract
        result["warnings"].append(
            "Plugin class should not be instantiable without configuration"
        )
    except Exception:
        pass  # Expected for proper abstract implementations

    # Determine implemented interfaces
    interfaces = [
        ("ActionPlugin", ActionPlugin),
        ("HookPlugin", HookPlugin),
        ("IntegrationPlugin", IntegrationPlugin),
        ("AnalyticsPlugin", AnalyticsPlugin),
        ("AutomationPlugin", AutomationPlugin),
    ]

    for interface_name, interface_class in interfaces:
        required_methods = [
            m
            for m in dir(interface_class)
            if not m.startswith("_") and callable(getattr(interface_class, m))
        ]
        implements_all = True

        for method in required_methods:
            if not hasattr(plugin_class, method) or not callable(
                getattr(plugin_class, method)
            ):
                implements_all = False
                break

        if implements_all:
            result["implemented_interfaces"].append(interface_name)

    return result


def create_plugin_info(**kwargs) -> PluginInfo:
    """
    Utility function to create PluginInfo dataclass

    Args:
        **kwargs: Plugin info fields

    Returns:
        PluginInfo: Plugin info instance
    """
    return PluginInfo(**kwargs)
