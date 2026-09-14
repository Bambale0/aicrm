from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aicrm.core.config import settings
from aicrm.core.dependencies import (
    create_access_token,
    get_current_active_user,
    get_current_admin_user,
    get_db,
)
from aicrm.models.base import Base
from aicrm.models.user import User


def _build_app(monkeypatch):
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    db = Session()
    admin = User(
        email="admin@example.test",
        hashed_password="unused",
        full_name="Admin",
        is_active=True,
        is_superuser=True,
        role="admin",
    )
    staff = User(
        email="staff@example.test",
        hashed_password="unused",
        full_name="Staff",
        is_active=True,
        is_superuser=False,
        role="employee",
    )
    db.add_all([admin, staff])
    db.commit()
    db.refresh(admin)
    db.refresh(staff)
    admin_email = admin.email
    staff_email = staff.email
    db.close()

    monkeypatch.setattr(settings, "auth_required", False)

    def override_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app = FastAPI()
    app.dependency_overrides[get_db] = override_db

    @app.get("/ordinary")
    async def ordinary(user: User = Depends(get_current_active_user)):
        return {"email": user.email}

    @app.get("/admin")
    async def admin_only(user: User = Depends(get_current_admin_user)):
        return {"email": user.email}

    return app, engine, admin_email, staff_email


def test_open_mode_does_not_bypass_admin_auth(monkeypatch):
    app, engine, admin_email, staff_email = _build_app(monkeypatch)
    client = TestClient(app)
    try:
        ordinary = client.get("/ordinary")
        assert ordinary.status_code == 200
        assert ordinary.json()["email"] == admin_email

        anonymous_admin = client.get("/admin")
        assert anonymous_admin.status_code == 401

        admin_token = create_access_token({"sub": admin_email})
        authenticated_admin = client.get(
            "/admin",
            headers={"Authorization": "Bearer " + admin_token},
        )
        assert authenticated_admin.status_code == 200
        assert authenticated_admin.json()["email"] == admin_email

        staff_token = create_access_token({"sub": staff_email})
        staff_admin = client.get(
            "/admin",
            headers={"Authorization": "Bearer " + staff_token},
        )
        assert staff_admin.status_code == 403
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
