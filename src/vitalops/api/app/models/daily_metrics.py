from re import I
import uuid
from sqlalchemy import DateTime, Float, Integer, String, ForeignKey, func, null
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.operators import not_endswith_op
from vitalops.api.app.models.base import Base
from sqlalchemy import UniqueConstraint

if TYPE_CHECKING:
    from vitalops.api.app.models.user import User
    from vitalops.api.app.models.date import DateDimension
    from vitalops.api.app.models.device import Device


class FactDailyMetrics(Base):
    __tablename__ = "fact_daily_metrics"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "date_id", "device_id", name="uq_daily_metrics_user_date_device"
        ),
    )
    metric_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dim_user.user_id"), nullable=False
    )
    date_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dim_date.date_id"), nullable=False
    )
    device_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dim_device.device_id"), nullable=True
    )

    steps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    calories_burned: Mapped[float | None] = mapped_column(Float, nullable=True)
    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_heart_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resting_heart_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_heart_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hrv: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    user: Mapped["User"] = relationship(back_populates="daily_metrics")
    date_dimension: Mapped["DateDimension"] = relationship(
        back_populates="daily_metrics"
    )
    devices: Mapped["Device | None"] = relationship(back_populates="daily_metrics")
