"""Domain models for housing-management CRM."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text

from .base import BaseModel


class Building(BaseModel):
    __tablename__ = "housing_buildings"

    address = Column(String(500), nullable=False, index=True)
    management_area = Column(String(255), nullable=True, index=True)
    entrances = Column(Integer, nullable=True)
    apartments_count = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class Premise(BaseModel):
    __tablename__ = "housing_premises"

    building_id = Column(Integer, ForeignKey("housing_buildings.id"), nullable=False, index=True)
    apartment = Column(String(50), nullable=False, index=True)
    entrance = Column(String(50), nullable=True)
    floor = Column(String(50), nullable=True)
    room = Column(String(50), nullable=True)
    is_residential = Column(Boolean, default=True, nullable=False)


class Resident(BaseModel):
    __tablename__ = "housing_residents"

    full_name = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    premise_id = Column(Integer, ForeignKey("housing_premises.id"), nullable=True, index=True)
    preferred_channel = Column(String(50), nullable=True)
    external_id = Column(String(255), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class ContractorCompany(BaseModel):
    __tablename__ = "housing_contractors"

    name = Column(String(255), nullable=False, index=True)
    legal_name = Column(String(500), nullable=True)
    inn = Column(String(20), nullable=True, index=True)
    kpp = Column(String(20), nullable=True)
    ogrn = Column(String(20), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    contact_person = Column(String(255), nullable=True)
    contract_number = Column(String(100), nullable=True)
    contract_start = Column(DateTime, nullable=True)
    contract_end = Column(DateTime, nullable=True)
    categories = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)


class Incident(BaseModel):
    __tablename__ = "housing_incidents"

    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    building_id = Column(Integer, ForeignKey("housing_buildings.id"), nullable=True, index=True)
    category = Column(String(100), nullable=True, index=True)
    priority = Column(String(50), default="normal", nullable=False, index=True)
    status = Column(String(50), default="active", nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)


class ServiceRequest(BaseModel):
    __tablename__ = "housing_requests"

    number = Column(String(64), unique=True, nullable=False, index=True)
    resident_id = Column(Integer, ForeignKey("housing_residents.id"), nullable=True, index=True)
    building_id = Column(Integer, ForeignKey("housing_buildings.id"), nullable=True, index=True)
    premise_id = Column(Integer, ForeignKey("housing_premises.id"), nullable=True, index=True)
    incident_id = Column(Integer, ForeignKey("housing_incidents.id"), nullable=True, index=True)

    source_channel = Column(String(50), default="operator", nullable=False, index=True)
    source_conversation_id = Column(String(255), nullable=True, index=True)

    category = Column(String(100), default="general", nullable=False, index=True)
    priority = Column(String(50), default="normal", nullable=False, index=True)
    status = Column(String(50), default="new", nullable=False, index=True)

    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)

    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    contractor_id = Column(Integer, ForeignKey("housing_contractors.id"), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    sla_deadline = Column(DateTime, nullable=True, index=True)
    resolved_at = Column(DateTime, nullable=True)
    extra_data = Column(JSON, nullable=True)


class RequestEvent(BaseModel):
    __tablename__ = "housing_request_events"

    request_id = Column(Integer, ForeignKey("housing_requests.id"), nullable=False, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    payload = Column(JSON, nullable=True)
