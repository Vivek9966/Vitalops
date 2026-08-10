from re import M
import uuid
from datetime import date, datetime
from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from vitalops.api.app.models.base import Base
from typing import TYPE_CHECKING

from vitalops.api.app.models.daily_metrics import FactDailyMetrics

if TYPE_CHECKING:
    from vitalops.api.app.models.device import Device
    from vitalops.api.app.models.sleep import FactSleep
    from vitalops.api.app.models.workout import FactWorkout


class User(Base):
    __tablename__ = "dim_user"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    dob: Mapped[date | None] = mapped_column(nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    devices: Mapped[list["Device"]] = relationship(
        back_populates="user", cascade="all,delete-orphan"
    )
    daily_metrics: Mapped[list["FactDailyMetrics"]] = relationship(
        back_populates="user"
    )
    sleep_records: Mapped[list["FactSleep"]] = relationship(back_populates="user")
    workouts: Mapped[list["FactWorkout"]] = relationship(back_populates="user")
