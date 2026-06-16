from datetime import datetime
from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String, Integer, Float, BigInteger, Boolean, DateTime, Text, TIMESTAMP, Date
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

__all__ = [
    "User",
    "Goals",
    "Injuries",
]

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    firstname: Mapped[str] = mapped_column(String(100))
    lastname: Mapped[str] = mapped_column(String(100))
    gender: Mapped[str] = mapped_column(String(20))
    age: Mapped[int] = mapped_column(Integer)
    height_cm: Mapped[float | int] = mapped_column(Float)
    weight_kg: Mapped[float | int] = mapped_column(Float)
    fitness_level: Mapped[int] = mapped_column(String(50))
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger)
    preferred_language: Mapped[str] = mapped_column(String(10))
    timezone: Mapped[str] = mapped_column(String(50))
    # preferred_message_time_morning: Mapped[time]
    # preferred_message_time_evening: Mapped[time]
    onboarding_completed: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, firstname={self.firstname!r}, lastname={self.lastname!r})"

class Goals(Base):
    __tablename__ = "goals"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    type: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    target_value: Mapped[float | int] = mapped_column(Float)
    current_value: Mapped[float | int] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20))
    deadline: Mapped[datetime] = mapped_column(Date)
    notes: Mapped[str] = mapped_column(Text)
    completed_at: Mapped[datetime] = mapped_column(TIMESTAMP)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP)

    def __repr__(self) -> str:
        return f"Goals(id={self.id!r}, user_id={self.user_id!r}, description={self.description!r})"

class Injuries(Base):
    __tablename__ = "injuries"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    description: Mapped[str] = mapped_column(Text)
    affected_area: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean)
    notes: Mapped[str] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(Date)
    resolved_at: Mapped[datetime] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP)

    def __repr__(self) -> str:
        return f"Injuries(id={self.id!r}, user_id={self.user_id!r}, description={self.description!r})"