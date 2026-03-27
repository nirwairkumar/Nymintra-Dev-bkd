from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    
    # Using String for UUID to be compatible with SQLite in local dev
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(15), unique=True, index=True, nullable=False)
    password_hash = Column(String(255))
    auth_provider = Column(String(20), default="phone")
    avatar_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CardDesign(Base):
    __tablename__ = "card_designs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, index=True, nullable=False)
    category = Column(String(50), nullable=False, index=True)
    style = Column(String(50))
    description = Column(String)
    base_price = Column(Float, nullable=False)
    thumbnail_url = Column(String, nullable=False)
    preview_url = Column(String, nullable=False)
    print_url = Column(String, nullable=False)
    zones_json = Column(JSON, nullable=False)
    supported_langs = Column(JSON, default=["en"]) # JSON as array to support SQLite
    orientation = Column(String(20), default="portrait")
    is_active = Column(Boolean, default=True, index=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

