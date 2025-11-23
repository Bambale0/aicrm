-- Performance Optimization Indexes for AI CRM Database
-- Generated: 2025-11-23 09:57:43
-- Missing Foreign Key Indexes

-- Enable pg_stat_statements for query performance monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Automation indexes
CREATE INDEX IF NOT EXISTS idx_automation_errors_automation_execution_id ON automation_errors(automation_execution_id);
CREATE INDEX IF NOT EXISTS idx_automation_errors_robot_id ON automation_errors(robot_id);
CREATE INDEX IF NOT EXISTS idx_automation_errors_trigger_id ON automation_errors(trigger_id);

-- Execution workflow indexes
CREATE INDEX IF NOT EXISTS idx_automation_executions_trigger_id ON automation_executions(trigger_id);
CREATE INDEX IF NOT EXISTS idx_automation_executions_robot_id ON automation_executions(robot_id);
CREATE INDEX IF NOT EXISTS idx_automation_executions_stage_id ON automation_executions(stage_id);

-- Customer relationship indexes
CREATE INDEX IF NOT EXISTS idx_avito_chat_settings_customer_id ON avito_chat_settings(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);

-- Product and category indexes
CREATE INDEX IF NOT EXISTS idx_product_tags_product_id ON product_tags(product_id);
CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_service_tags_service_id ON service_tags(service_id);
CREATE INDEX IF NOT EXISTS idx_services_category_id ON services(category_id);

-- Production workflow indexes
CREATE INDEX IF NOT EXISTS idx_production_steps_order_id ON production_steps(order_id);
CREATE INDEX IF NOT EXISTS idx_production_steps_assigned_user_id ON production_steps(assigned_user_id);

-- Robot and automation indexes
CREATE INDEX IF NOT EXISTS idx_robot_actions_config_robot_id ON robot_actions_config(robot_id);
CREATE INDEX IF NOT EXISTS idx_robots_stage_id ON robots(stage_id);

-- Workflow management indexes
CREATE INDEX IF NOT EXISTS idx_stages_process_id ON stages(process_id);
CREATE INDEX IF NOT EXISTS idx_triggers_target_stage_id ON triggers(target_stage_id);

-- Task management indexes
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_created_by ON tasks(created_by);
CREATE INDEX IF NOT EXISTS idx_tasks_related_order_id ON tasks(related_order_id);

-- Additional performance indexes for common queries

-- User performance indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Customer search indexes
CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
CREATE INDEX IF NOT EXISTS idx_customers_company ON customers(company);

-- Order query optimization indexes
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_deadline ON orders(deadline);

-- Communication indexes
CREATE INDEX IF NOT EXISTS idx_communications_customer_id ON communications(customer_id);
CREATE INDEX IF NOT EXISTS idx_communications_created_at ON communications(created_at);
CREATE INDEX IF NOT EXISTS idx_communications_type ON communications(type);

-- AI usage tracking indexes
CREATE INDEX IF NOT EXISTS idx_ai_usage_user_id ON ai_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_usage_created_at ON ai_usage(created_at);
CREATE INDEX IF NOT EXISTS idx_ai_usage_model ON ai_usage(model);

-- Campaign performance indexes
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_created_at ON campaigns(created_at);
CREATE INDEX IF NOT EXISTS idx_campaigns_end_date ON campaigns(end_date);
