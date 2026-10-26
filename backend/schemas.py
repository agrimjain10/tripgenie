import json
from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class TokenOut(BaseModel):
    token: str
    user: UserOut


class TripCreate(BaseModel):
    destination: str = Field(min_length=2, max_length=120)
    origin: Optional[str] = Field(default=None, max_length=120)
    start_date: date
    end_date: date
    travelers: int = Field(default=1, ge=1, le=20)
    budget: Optional[float] = Field(default=None, ge=0, le=100000000)
    interests: str = Field(default="", max_length=500)
    trip_brief: str = Field(default="", max_length=1500)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("End date must be on or after the start date")
        return self

    @field_validator("destination", "origin")
    @classmethod
    def trim_places(cls, value):
        return value.strip() if value else value


class TripOut(BaseModel):
    id: int
    user_id: int
    destination: str
    origin: Optional[str]
    start_date: str
    end_date: str
    travelers: int
    budget: Optional[float]
    interests: str
    trip_brief: str
    plan_json: Optional[str]
    created_at: str
    status: str = "draft"
    workspace: dict = Field(default_factory=dict)
    public_slug: Optional[str] = None

    @classmethod
    def from_trip(cls, trip):
        return cls(id=trip.id, user_id=trip.user_id, destination=trip.destination,
                   origin=trip.origin, start_date=trip.start_date, end_date=trip.end_date,
                   travelers=trip.travelers or 1, budget=trip.budget,
                   interests=trip.interests or "", trip_brief=trip.trip_brief or "",
                   plan_json=trip.plan_json,
                   status=trip.status or "draft", workspace={key: value for key, value in json.loads(trip.workspace_json or '{}').items() if not key.startswith('_')},
                   public_slug=trip.public_slug,
                   created_at=trip.created_at.isoformat() if trip.created_at else "")


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
