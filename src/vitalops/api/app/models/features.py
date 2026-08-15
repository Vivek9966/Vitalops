import uuid
from datetime import datetime
from sqlalchemy import (
    Float,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
    null,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from vitalops.api.app.models.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vitalops.api.app.models.user import User
    from vitalops.api.app.models.date import DateDimension


class DailyFeatures(Base):
    __table_args__ = (
        UniqueConstraint("user_id", "date_id", name="uq_features_user_date"),
    )
    __tablename__ = "daily_features"

    features_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dim_user.user_id"), nullable=False
    )
    date_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dim_date.date_id"), nullable=False
    )
    steps_7d_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    steps_28d_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    hrv_7d_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    hrv_28d_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    rhr_7d_avg: Mapped[float | None] = mapped_column(Float, nullable=True)

    sleep_7d_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    sleep_debt: Mapped[float | None] = mapped_column(Float, nullable=True)

    acute_training_load: Mapped[float | None] = mapped_column(Float, nullable=True)
    chronic_training_load: Mapped[float | None] = mapped_column(Float, nullable=True)

    acute_chronic_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)

    workout_days_7d: Mapped[int] = mapped_column(Integer)
    rest_days_7d: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="feature_rows")
    date_dimension: Mapped["DateDimension"] = relationship(
        back_populates="feature_rows"
    )
