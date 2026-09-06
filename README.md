# AI Production CRM

> **AI-assisted CRM and production workflow backend** · FastAPI · SQLAlchemy · PostgreSQL/SQLite · JWT · Docker
>
> Repository codename: `aicrm`.

AI Production CRM is a backend-focused CRM for companies that manage customer communication, orders and multi-step production workflows. The project adds AI-assisted intent analysis and response generation on top of conventional CRM domain logic rather than treating the LLM as the entire application.

## What this project demonstrates

- FastAPI REST backend.
- SQLAlchemy 2 domain models and repositories.
- JWT authentication and protected API routes.
- Customer and order management.
- Multi-stage production workflows.
- Task and deadline tracking.
- AI provider abstraction for OpenAI/OpenRouter-compatible services.
- Structured logging and health checks.
- Docker-based deployment.

## Domain model

```text
Customer
   |
   +--> Orders
          |
          +--> Production steps
          |      |-- design
          |      |-- materials
          |      |-- production
          |      |-- post-processing
          |      +-- quality control
          |
          +--> Tasks / deadlines

Customer + Order context
          |
          v
     AI services
          |-- intent analysis
          +-- response assistance
```

The AI layer is isolated in services so business workflows remain testable and understandable without depending on one specific model provider.

## Main modules

```text
src/aicrm/
├── api/          # FastAPI routers and schemas
├── core/         # config, database and dependencies
├── models/       # users, customers, orders, production, communication
├── services/     # business logic, auth and AI integrations
└── utils/        # logging and helpers
```

## Stack

| Area | Technology |
| --- | --- |
| Backend | Python 3.11+, FastAPI |
| ORM | SQLAlchemy 2 |
| Database | PostgreSQL / SQLite for development |
| Validation | Pydantic 2 |
| Authentication | JWT |
| AI | OpenAI/OpenRouter-compatible APIs |
| Delivery | Docker |

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Create a local environment file from the example configuration and run the application with Uvicorn.

```bash
uvicorn aicrm.main:app --reload
```

The repository intentionally does **not** track local `.env` files. Runtime credentials belong in environment variables or a secret manager.

## Example API areas

```text
/auth/*
/customers/*
/orders/*
/ai/*
/health
```

Typical AI-assisted flows include:

- classify a customer request;
- generate a suggested response using CRM context;
- identify whether human intervention is needed;
- suggest the next business action without bypassing the normal order workflow.

## Portfolio note

This project is included to show backend/domain work outside Telegram media generation: conventional CRM entities, auth, production processes and AI-assisted business automation in one service-oriented backend.
