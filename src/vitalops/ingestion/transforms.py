from datetime import datetime


def date_id_of(value):
    return value.year * 10000 + value.month * 100 + value.day


def add_date_id(daily_row, sleep_row, workout_rows):
    if daily_row is not None:
        metric_date = daily_row["date"]
        daily_row["date_id"] = date_id_of(metric_date)
    if sleep_row is not None:
        sleep_date = sleep_row["sleep_start"].date()
        sleep_row["date_id"] = date_id_of(sleep_date)

    for workout in workout_rows:
        workout["date_id"] = date_id_of(workout["start_time"].date())
    return daily_row, sleep_row, workout_rows
