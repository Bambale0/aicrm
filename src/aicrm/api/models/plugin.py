"""
Plugin system models
"""

from sqlalchemy import JSON, Boolean, Column, DateTime, Index, Integer, String, Text
from sqlalchemy.sql import func

from .base import Base


class Plugin(Base):
    """
    Plugin model - stores plugin metadata and configuration
    """

    __tablename__ = "plugins"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)
    homepage = Column(String(500), nullable=True)
    license = Column(String(100), nullable=True)

    # Plugin location and status
    package_name = Column(String(255), nullable=True)
    module_name = Column(String(255), nullable=True)
    class_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=False, nullable=False, index=True)
    is_system = Column(Boolean, default=False, nullable=False)  # Built-in plugins
    is_installed = Column(Boolean, default=False, nullable=False, index=True)

    # Configuration
    settings_schema = Column(JSON, nullable=True)  # JSON Schema for plugin settings
    default_settings = Column(JSON, nullable=True)  # Default configuration values
    current_settings = Column(JSON, nullable=True)  # Current configuration values

    # Metadata
    requires_restart = Column(Boolean, default=False, nullable=False)
    dependencies = Column(JSON, nullable=True)  # List of required plugins
    compatibility = Column(JSON, nullable=True)  # Compatibility information

    # Installation info
    installed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    installed_by = Column(Integer, nullable=True)  # User ID who installed

    # Indexes
    __table_args__ = (
        Index("ix_plugins_name_active", "name", "is_active"),
        Index("ix_plugins_system_active", "is_system", "is_active"),
    )

    def __repr__(self):
        return f"<Plugin(name='{self.name}', version='{self.version}', active={self.is_active})>"


class PluginAction(Base):
    """
    Plugin action executions log
    """

    __tablename__ = "plugin_actions"

    id = Column(Integer, primary_key=True, index=True)
    plugin_id = Column(Integer, nullable=False, index=True)
    action_name = Column(String(255), nullable=False)
    execution_status = Column(
        String(50), nullable=False
    )  # 'success', 'error', 'running'
    started_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)  # Execution duration in milliseconds

    # Execution details
    parameters = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)

    # Context
    entity_type = Column(String(50), nullable=True)  # e.g., 'ORDER', 'CUSTOMER'
    entity_id = Column(Integer, nullable=True)
    user_id = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<PluginAction(plugin_id={self.plugin_id}, action='{self.action_name}', status='{self.execution_status}')>"


class PluginHook(Base):
    """
    Hook registrations - plugins can register for specific events
    """

    __tablename__ = "plugin_hooks"

    id = Column(Integer, primary_key=True, index=True)
    plugin_id = Column(Integer, nullable=False, index=True)
    hook_type = Column(
        String(100), nullable=False, index=True
    )  # e.g., 'before_save', 'after_create'
    hook_event = Column(
        String(100), nullable=False, index=True
    )  # e.g., 'order_created', 'customer_updated'
    priority = Column(
        Integer, default=10, nullable=False
    )  # Execution priority (lower = higher priority)

    # Hook configuration
    conditions = Column(JSON, nullable=True)  # Conditions for hook execution
    settings = Column(JSON, nullable=True)  # Additional hook settings

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<PluginHook(plugin_id={self.plugin_id}, type='{self.hook_type}', event='{self.hook_event}')>"


class PluginPermission(Base):
    """
    Plugin permissions and access control
    """

    __tablename__ = "plugin_permissions"

    id = Column(Integer, primary_key=True, index=True)
    plugin_id = Column(Integer, nullable=False, index=True)
    permission_name = Column(String(255), nullable=False, index=True)
    permission_type = Column(String(50), nullable=False)  # 'read', 'write', 'admin'
    resource_type = Column(
        String(100), nullable=False
    )  # e.g., 'order', 'customer', 'email'
    resource_id = Column(
        String(100), nullable=True
    )  # Specific resource ID or '*' for all
    conditions = Column(JSON, nullable=True)  # Additional conditions

    def __repr__(self):
        return f"<PluginPermission(plugin_id={self.plugin_id}, name='{self.permission_name}', type='{self.permission_type}')>"


class PluginRegistry(Base):
    """
    Available plugins registry (marketplace)
    """

    __tablename__ = "plugin_registry"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)
    version = Column(String(50), nullable=False)

    # Repository info
    repository_url = Column(String(500), nullable=True)
    homepage = Column(String(500), nullable=True)
    documentation_url = Column(String(500), nullable=True)

    # Classification
    category = Column(
        String(100), nullable=False, index=True
    )  # e.g., 'integration', 'automation', 'report'
    tags = Column(JSON, nullable=True)

    # Requirements
    min_version = Column(String(50), nullable=True)  # Minimum system version required
    dependencies = Column(JSON, nullable=True)  # Required dependencies
    compatibility = Column(JSON, nullable=True)  # Version compatibility

    # Status
    is_official = Column(
        Boolean, default=False, nullable=False
    )  # Official AI CRM plugin
    is_featured = Column(
        Boolean, default=False, nullable=False
    )  # Featured in marketplace
    download_count = Column(Integer, default=0, nullable=False)
    rating = Column(JSON, nullable=True)  # {average: float, count: int}

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<PluginRegistry(name='{self.name}', version='{self.version}', category='{self.category}')>"


class PluginTemplate(Base):
    """
    Plugin code templates for development
    """

    __tablename__ = "plugin_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, index=True)

    # Template files
    files = Column(JSON, nullable=False)  # {filename: content}
    dependencies = Column(JSON, nullable=True)
    configuration_schema = Column(JSON, nullable=True)

    # Usage
    usage_count = Column(Integer, default=0, nullable=False)
    is_official = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<PluginTemplate(name='{self.name}', category='{self.category}')>"
