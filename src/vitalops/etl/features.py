from vitalops.ingestion.db import get_conn


FEATURE_SQL = """
WITH user_dates AS (
    SELECT
        u.user_id,
        d.date_id,
        d.date,
        u.sleep_need_hours
    FROM dim_user u
    CROSS JOIN dim_date d
),

daily_metrics AS (
    SELECT
        user_id,
        date_id,
        AVG(steps) AS steps,
        AVG(hrv) AS hrv,
        AVG(resting_heart_rate) AS resting_heart_rate
    FROM fact_daily_metrics
    GROUP BY user_id, date_id
),

daily_sleep AS (
    SELECT
        user_id,
        date_id,
        SUM(duration_minutes) / 60.0 AS sleep_hours
    FROM fact_sleep
    GROUP BY user_id, date_id
),

daily_workouts AS (
    SELECT
        user_id,
        date_id,
        SUM(COALESCE(training_load, 0.0)) AS training_load,
        1 AS workout_day
    FROM fact_workouts
    GROUP BY user_id, date_id
),

daily AS (
    SELECT
        ud.user_id,
        ud.date_id,
        ud.date,
        ud.sleep_need_hours,

        dm.steps,
        dm.hrv,
        dm.resting_heart_rate,

         ds.sleep_hours AS sleep_hours,

        COALESCE(dw.training_load, 0.0) AS training_load,

        COALESCE(dw.workout_day, 0) AS workout_day

    FROM user_dates ud

    LEFT JOIN daily_metrics dm
        ON dm.user_id = ud.user_id
        AND dm.date_id = ud.date_id

    LEFT JOIN daily_sleep ds
        ON ds.user_id = ud.user_id
        AND ds.date_id = ud.date_id

    LEFT JOIN daily_workouts dw
        ON dw.user_id = ud.user_id
        AND dw.date_id = ud.date_id
),

rolling AS (
    SELECT
        *,

        AVG(steps) OVER (
            PARTITION BY user_id
            ORDER BY date
            RANGE BETWEEN INTERVAL '6 days' PRECEDING
            AND CURRENT ROW
        ) AS steps_7d_avg,

        AVG(steps) OVER (
            PARTITION BY user_id
            ORDER BY date
            RANGE BETWEEN INTERVAL '27 days' PRECEDING
            AND CURRENT ROW
        ) AS steps_28d_avg,

        AVG(hrv) OVER (
            PARTITION BY user_id
            ORDER BY date
            RANGE BETWEEN INTERVAL '6 days' PRECEDING
            AND CURRENT ROW
        ) AS hrv_7d_avg,

        AVG(hrv) OVER (
            PARTITION BY user_id
            ORDER BY date
            RANGE BETWEEN INTERVAL '27 days' PRECEDING
            AND CURRENT ROW
        ) AS hrv_28d_avg,

        AVG(resting_heart_rate) OVER (
            PARTITION BY user_id
            ORDER BY date
            RANGE BETWEEN INTERVAL '6 days' PRECEDING
            AND CURRENT ROW
        ) AS rhr_7d_avg,

        AVG(sleep_hours) OVER (
            PARTITION BY user_id
            ORDER BY date
            RANGE BETWEEN INTERVAL '6 days' PRECEDING
            AND CURRENT ROW
        ) AS sleep_7d_avg,

        SUM(training_load) OVER (
            PARTITION BY user_id
            ORDER BY date
            RANGE BETWEEN INTERVAL '6 days' PRECEDING
            AND CURRENT ROW
        ) AS acute_training_load,

        SUM(training_load) OVER (
            PARTITION BY user_id
            ORDER BY date
            RANGE BETWEEN INTERVAL '27 days' PRECEDING
            AND CURRENT ROW
        ) AS chronic_training_load,

        SUM(workout_day) OVER (
            PARTITION BY user_id
            ORDER BY date
            RANGE BETWEEN INTERVAL '6 days' PRECEDING
            AND CURRENT ROW
        ) AS workout_days_7d,

        SUM(
            CASE 
            WHEN sleep_hours IS NOT NULL
            THEN sleep_need_hours - sleep_hours
            ELSE 0.0
            END 
            ) OVER (
            PARTITION BY user_id
            ORDER BY date
            ROWS BETWEEN UNBOUNDED PRECEDING
            AND CURRENT ROW
        ) AS raw_sleep_debt

    FROM daily
)

SELECT
    user_id,
    date_id,

    steps_7d_avg,
    steps_28d_avg,

    hrv_7d_avg,
    hrv_28d_avg,

    rhr_7d_avg,

    sleep_7d_avg,

    GREATEST(
        0.0,
        raw_sleep_debt
    ) AS sleep_debt,

    acute_training_load,
    chronic_training_load,

    CASE
        WHEN chronic_training_load > 0
        THEN acute_training_load / chronic_training_load
        ELSE NULL
    END AS acute_chronic_ratio,

    workout_days_7d,
    7 - workout_days_7d AS rest_days_7d

FROM rolling
ORDER BY user_id, date_id
"""


UPSERT_SQL = """
INSERT INTO daily_features (
    features_id,
    user_id,
    date_id,
    steps_7d_avg,
    steps_28d_avg,
    hrv_7d_avg,
    hrv_28d_avg,
    rhr_7d_avg,
    sleep_7d_avg,
    sleep_debt,
    acute_training_load,
    chronic_training_load,
    acute_chronic_ratio,
    workout_days_7d,
    rest_days_7d
)
VALUES (
    gen_random_uuid(),
    %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (user_id, date_id)
DO UPDATE SET
    steps_7d_avg = EXCLUDED.steps_7d_avg,
    steps_28d_avg = EXCLUDED.steps_28d_avg,
    hrv_7d_avg = EXCLUDED.hrv_7d_avg,
    hrv_28d_avg = EXCLUDED.hrv_28d_avg,
    rhr_7d_avg = EXCLUDED.rhr_7d_avg,
    sleep_7d_avg = EXCLUDED.sleep_7d_avg,
    sleep_debt = EXCLUDED.sleep_debt,
    acute_training_load = EXCLUDED.acute_training_load,
    chronic_training_load = EXCLUDED.chronic_training_load,
    acute_chronic_ratio = EXCLUDED.acute_chronic_ratio,
    workout_days_7d = EXCLUDED.workout_days_7d,
    rest_days_7d = EXCLUDED.rest_days_7d
"""


def build_features() -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(FEATURE_SQL)
            rows = cur.fetchall()

            if not rows:
                print("No feature rows generated.")
                return

            cur.executemany(UPSERT_SQL, rows)

        conn.commit()

    print(f"Generated {len(rows)} daily feature rows.")


if __name__ == "__main__":
    build_features()
