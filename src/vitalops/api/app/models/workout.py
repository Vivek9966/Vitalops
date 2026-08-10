from operator import le
from re import M
import re
import uuid

from sqlalchemy import (
    DateTime,
    UniqueConstraint,
    UUID,
    Date,
    Integer,
    Float,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

from sqlalchemy.sql.expression import null
from vitalops.api.app.models import device, user
from vitalops.api.app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vitalops.api.app.models.user import User
    from vitalops.api.app.models.date import DateDimension
    from vitalops.api.app.models.device import Device


class FactWorkout(Base):
    __table_args__ = (
        UniqueConstraint(
            "user_id", "device_id", "start_time", name="uq_workout_user_device_start"
        ),
    )
    __tablename__ = "fact_workouts"

    workout_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dim_user.user_id"), nullable=False
    )
    date_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dim_date.date_id"), nullable=False
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dim_device.device_id"), nullable=False
    )

    workout_type: Mapped[str | None] = mapped_column(String(length=100), nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)

    calories_burned: Mapped[float | None] = mapped_column(Float, nullable=True)

    avg_heart_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_heart_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)

    training_load: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    user: Mapped["User"] = relationship(back_populates="workouts")
    date_dimension: Mapped["DateDimension"] = relationship(back_populates="workouts")
    device: Mapped["Device"] = relationship(back_populates="workouts")
    # uq_workout_user_device_start
