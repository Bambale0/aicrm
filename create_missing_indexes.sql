-- Missing Performance Indexes for AI CRM Database
-- Generated: 2025-11-23 after analysis
-- Only truly missing indexes

-- Enable pg_stat_statements for query performance monitoring
-- This should be run by a superuser once per database
-- CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Additional missing FK indexes identified by analysis

-- Users table - email index should exist but adding role index
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Add any missing indexes that weren't created due to IF NOT EXISTS

-- Compound indexes for common query patterns

-- Orders by status and creation date (for sorting)
CREATE INDEX IF NOT EXISTS idx_orders_status_created_at ON orders(status, created_at);

-- Communications by customer and created_at (for timeline views)
CREATE INDEX IF NOT EXISTS idx_communications_customer_created ON communications(customer_id, created_at DESC);

-- AI usage by user and month (for usage reporting)
CREATE INDEX IF NOT EXISTS idx_ai_usage_user_month ON ai_usage(user_id, month_year);

-- Production steps by order and status (workflow optimization)
CREATE INDEX IF NOT EXISTS idx_production_steps_order_id ON production_steps(order_id);

-- Tasks by assigned user and created date
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_created ON tasks(assigned_to, created_at DESC);

-- Automation executions by trigger and start time (for performance analysis)
CREATE INDEX IF NOT EXISTS idx_automation_executions_trigger_started ON automation_executions(trigger_id, started_at DESC);

-- Partial indexes for performance optimization

-- Active customers (not deleted)
CREATE INDEX IF NOT EXISTS idx_customers_active ON customers(id) WHERE is_deleted = false;

-- Open orders (not cancelled or delivered - using actual enum values)
CREATE INDEX IF NOT EXISTS idx_orders_open ON orders(id) WHERE status NOT IN ('CANCELLED', 'DELIVERED');

-- Recent communications (last 30 days - using constant date)
-- Note: Using CURRENT_DATE - INTERVAL '30 days' for immutability
CREATE INDEX IF NOT EXISTS idx_communications_recent ON communications(created_at DESC) WHERE created_at >= CURRENT_DATE - 30;

-- Recent AI usage (for monitoring - last 7 days)
CREATE INDEX IF NOT EXISTS idx_ai_usage_recent ON ai_usage(created_at DESC) WHERE created_at >= CURRENT_DATE - 7;
