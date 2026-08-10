def upsert_daily_metrics(conn, rows: list[dict]) -> None:
    if not rows:
        return

    sql = """
        INSERT INTO fact_daily_metrics (
            metric_id,
            user_id,
            date_id,
            device_id,
            steps,
            active_minutes,
            calories_burned,
            distance_km,
            avg_heart_rate,
            resting_heart_rate,
            max_heart_rate,
            hrv
        )
        VALUES (
            %(metric_id)s,
            %(user_id)s,
            %(date_id)s,
            %(device_id)s,
            %(steps)s,
            %(active_minutes)s,
            %(calories_burned)s,
            %(distance_km)s,
            %(avg_heart_rate)s,
            %(resting_heart_rate)s,
            %(max_heart_rate)s,
            %(hrv)s
        )
        ON CONFLICT (user_id, date_id, device_id)
        DO UPDATE SET
            steps = EXCLUDED.steps,
            active_minutes = EXCLUDED.active_minutes,
            calories_burned = EXCLUDED.calories_burned,
            distance_km = EXCLUDED.distance_km,
            avg_heart_rate = EXCLUDED.avg_heart_rate,
            resting_heart_rate = EXCLUDED.resting_heart_rate,
            max_heart_rate = EXCLUDED.max_heart_rate,
            hrv = EXCLUDED.hrv
    """

    with conn.cursor() as cur:
        cur.executemany(sql, rows)


def upsert_sleep(conn, rows: list[dict]) -> None:
    if not rows:
        return

    sql = """
        INSERT INTO fact_sleep (
            sleep_id,
            user_id,
            date_id,
            device_id,
            sleep_start,
            sleep_end,
            duration_minutes,
            deep_minutes,
            light_minutes,
            rem_minutes,
            awake_minutes,
            sleep_efficiency,
            avg_heart_rate,
            resting_heart_rate,
            hrv,
            awakenings
        )
        VALUES (
            %(sleep_id)s,
            %(user_id)s,
            %(date_id)s,
            %(device_id)s,
            %(sleep_start)s,
            %(sleep_end)s,
            %(duration_minutes)s,
            %(deep_minutes)s,
            %(light_minutes)s,
            %(rem_minutes)s,
            %(awake_minutes)s,
            %(sleep_efficiency)s,
            %(avg_heart_rate)s,
            %(resting_heart_rate)s,
            %(hrv)s,
            %(awakenings)s
        )
        ON CONFLICT (user_id, device_id, sleep_start)
        DO UPDATE SET
            sleep_end = EXCLUDED.sleep_end,
            duration_minutes = EXCLUDED.duration_minutes,
            deep_minutes = EXCLUDED.deep_minutes,
            light_minutes = EXCLUDED.light_minutes,
            rem_minutes = EXCLUDED.rem_minutes,
            awake_minutes = EXCLUDED.awake_minutes,
            sleep_efficiency = EXCLUDED.sleep_efficiency,
            avg_heart_rate = EXCLUDED.avg_heart_rate,
            resting_heart_rate = EXCLUDED.resting_heart_rate,
            hrv = EXCLUDED.hrv,
            awakenings = EXCLUDED.awakenings
    """

    with conn.cursor() as cur:
        cur.executemany(sql, rows)


def upsert_workouts(conn, rows: list[dict]) -> None:
    if not rows:
        return

    sql = """
        INSERT INTO fact_workouts (
            workout_id,
            user_id,
            date_id,
            device_id,
            workout_type,
            start_time,
            end_time,
            duration_minutes,
            distance_km,
            calories_burned,
            avg_heart_rate,
            max_heart_rate,
            training_load
        )
        VALUES (
            %(workout_id)s,
            %(user_id)s,
            %(date_id)s,
            %(device_id)s,
            %(workout_type)s,
            %(start_time)s,
            %(end_time)s,
            %(duration_minutes)s,
            %(distance_km)s,
            %(calories_burned)s,
            %(avg_heart_rate)s,
            %(max_heart_rate)s,
            %(training_load)s
        )
        ON CONFLICT (user_id, device_id, start_time)
        DO UPDATE SET
            end_time = EXCLUDED.end_time,
            duration_minutes = EXCLUDED.duration_minutes,
            distance_km = EXCLUDED.distance_km,
            calories_burned = EXCLUDED.calories_burned,
            avg_heart_rate = EXCLUDED.avg_heart_rate,
            max_heart_rate = EXCLUDED.max_heart_rate,
            training_load = EXCLUDED.training_load
    """

    with conn.cursor() as cur:
        cur.executemany(sql, rows)
