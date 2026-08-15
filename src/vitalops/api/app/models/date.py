from datetime import date
from re import M
from sqlalchemy import Boolean, Date, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.util import monkeypatch_proxied_specials
from typing import TYPE_CHECKING
from vitalops.api.app.models.base import Base

if TYPE_CHECKING:
    from vitalops.api.app.models.daily_metrics import FactDailyMetrics
    from vitalops.api.app.models.sleep import FactSleep
    from vitalops.api.app.models.workout import FactWorkout
    from vitalops.api.app.models.features import DailyFeatures
# test


class DateDimension(Base):
    __tablename__ = "dim_date"

    date_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)

    day: Mapped[int] = mapped_column(Integer, nullable=False)

    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    week: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    is_weekend: Mapped[bool] = mapped_column(Boolean, nullable=False)
    daily_metrics: Mapped[list["FactDailyMetrics"]] = relationship(
        back_populates="date_dimension"
    )
    sleep_records: Mapped[list["FactSleep"]] = relationship(
        back_populates="date_dimension"
    )
    workouts: Mapped[list["FactWorkout"]] = relationship(
        back_populates="date_dimension"
    )

    feature_rows: Mapped[list["DailyFeatures"]] = relationship(
        back_populates="date_dimension"
    )
