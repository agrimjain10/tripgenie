from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    preferences_json = Column(Text, default="{}")
    trips = relationship("Trip", back_populates="owner", cascade="all, delete-orphan")


class Trip(Base):
    __tablename__ = "trips"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    destination = Column(String, nullable=False)
    origin = Column(String, nullable=True)
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    travelers = Column(Integer, nullable=False, default=1)
    budget = Column(Float, nullable=True)
    interests = Column(String, default="")
    trip_brief = Column(Text, default="")
    plan_json = Column(Text, nullable=True)
    status = Column(String, default="draft")
    workspace_json = Column(Text, default="{}")
    public_slug = Column(String, nullable=True, unique=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner = relationship("User", back_populates="trips")
