from datetime import datetime
from re import M, U
import uuid

from sqlalchemy import (
    INT,
    Integer,
    Float,
    Date,
    DateTime,
    ForeignKey,
    func,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from vitalops.api.app.models import device
from vitalops.api.app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vitalops.api.app.models.date import DateDimension
    from vitalops.api.app.models.daily_metrics import FactDailyMetrics
    from vitalops.api.app.models.device import Device
    from vitalops.api.app.models.user import User


class FactSleep(Base):
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "device_id",
            "sleep_start",
            name="uq_sleep_user_device_start",
        ),
    )
    __tablename__ = "fact_sleep"

    sleep_id: Mapped[uuid.UUID] = mapped_column(
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
    sleep_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    sleep_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deep_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    light_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rem_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    awake_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sleep_efficiency: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_heart_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resting_heart_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hrv: Mapped[float | None] = mapped_column(Float, nullable=True)
    awakenings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    user: Mapped["User"] = relationship(back_populates="sleep_records")
    device: Mapped["Device"] = relationship(back_populates="sleep_records")
    date_dimension: Mapped["DateDimension"] = relationship(
        back_populates="sleep_records"
    )
