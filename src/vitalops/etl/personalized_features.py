from vitalops.ingestion.db import get_conn


PERSONALIZED_FEATURE_SQL = """
WITH daily AS (
    SELECT
        df.user_id,
        df.date_id,
        dd.date,

        dm.steps,
        dm.hrv,
        dm.resting_heart_rate,

        df.sleep_7d_avg,
        df.sleep_debt,
        df.acute_training_load,
        df.chronic_training_load,
        df.acute_chronic_ratio,

        -- Current-day sleep duration.
        sleep_data.sleep_hours AS sleep_hours

    FROM daily_features df

    JOIN dim_date dd
        ON dd.date_id = df.date_id

    LEFT JOIN fact_daily_metrics dm
        ON dm.user_id = df.user_id
        AND dm.date_id = df.date_id

    LEFT JOIN (
        SELECT
            user_id,
            date_id,
            SUM(duration_minutes) / 60.0 AS sleep_hours
        FROM fact_sleep
        GROUP BY user_id, date_id
    ) sleep_data
        ON sleep_data.user_id = df.user_id
        AND sleep_data.date_id = df.date_id
),

baselines AS (
    SELECT
        *,

        AVG(hrv) OVER (
            PARTITION BY user_id
            ORDER BY date
            RANGE BETWEEN INTERVAL '28 days' PRECEDING
            AND INTERVAL '1 day' PRECEDING
        ) AS hrv_baseline,

        STDDEV_SAMP(hrv) OVER (
            PARTITION BY user_id
            ORDER BY date
            RANGE BETWEEN INTERVAL '28 days' PRECEDING
            AND INTERVAL '1 day' PRECEDING
        ) AS hrv_baseline_std,

        AVG(resting_heart_rate) OVER (
            PARTITION BY user_id
            ORDER BY date
            RANGE BETWEEN INTERVAL '28 days' PRECEDING
            AND INTERVAL '1 day' PRECEDING
        ) AS rhr_baseline,

        STDDEV_SAMP(resting_heart_rate) OVER (
            PARTITION BY user_id
            ORDER BY date
            RANGE BETWEEN INTERVAL '28 days' PRECEDING
            AND INTERVAL '1 day' PRECEDING
        ) AS rhr_baseline_std,

        AVG(steps) OVER (
            PARTITION BY user_id
            ORDER BY date
            RANGE BETWEEN INTERVAL '28 days' PRECEDING
            AND INTERVAL '1 day' PRECEDING
        ) AS steps_baseline,

        STDDEV_SAMP(steps) OVER (
            PARTITION BY user_id
            ORDER BY date
            RANGE BETWEEN INTERVAL '28 days' PRECEDING
            AND INTERVAL '1 day' PRECEDING
        ) AS steps_baseline_std,

        AVG(sleep_hours) OVER (
            PARTITION BY user_id
            ORDER BY date
            RANGE BETWEEN INTERVAL '28 days' PRECEDING
            AND INTERVAL '1 day' PRECEDING
        ) AS sleep_baseline,

        STDDEV_SAMP(sleep_hours) OVER (
            PARTITION BY user_id
            ORDER BY date
            RANGE BETWEEN INTERVAL '28 days' PRECEDING
            AND INTERVAL '1 day' PRECEDING
        ) AS sleep_baseline_std

    FROM daily
)

SELECT
    user_id,
    date_id,
    date,

    steps,
    hrv,
    resting_heart_rate,
    sleep_hours,

    hrv_baseline,
    rhr_baseline,
    steps_baseline,
    sleep_baseline,

    CASE
        WHEN COUNT(hrv) OVER(
        PARTITION BY user_id
        ORDER BY date
        RANGE BETWEEN INTERVAL '28 days' PRECEDING
        AND INTERVAL '1 day' PRECEDING)>=7 
        AND hrv_baseline_std>0
        THEN (hrv- hrv_baseline) /hrv_baseline_std
        ELSE NULL
    END AS hrv_zscore,

    CASE
        WHEN COUNT(resting_heart_rate) OVER(
        PARTITION BY user_id
        ORDER BY date 
        RANGE BETWEEN INTERVAL'28 days' PRECEDING
        AND INTERVAL '1 day' PRECEDING)>=7 
        AND rhr_baseline_std>0
        THEN (resting_heart_rate - rhr_baseline) /rhr_baseline_std
        ELSE NULL
    END AS rhr_zscore,

    CASE
        WHEN COUNT(steps) OVER(
        PARTITION BY user_id 
        ORDER BY date 
        RANGE BETWEEN INTERVAL '28 days' PRECEDING
        AND INTERVAL '1 day' PRECEDING)>=7 
        AND steps_baseline>0
        THEN (steps - steps_baseline)
             / steps_baseline_std
        ELSE NULL
    END AS steps_zscore,

    CASE
        WHEN COUNT(sleep_hours) OVER(
        PARTITION BY user_id ORDER BY date
        RANGE BETWEEN INTERVAL '28 days' PRECEDING
        AND INTERVAL '1 day' PRECEDING) >=7 
        AND sleep_baseline_std > 0
        THEN (sleep_hours - sleep_baseline)
             / sleep_baseline_std
        ELSE NULL
    END AS sleep_zscore,

    sleep_7d_avg,
    sleep_debt,
    acute_training_load,
    chronic_training_load,
    acute_chronic_ratio

FROM baselines

ORDER BY user_id, date_id
"""


def build_personalized_features():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(PERSONALIZED_FEATURE_SQL)
            rows = cur.fetchall()

    print(f"Generated {len(rows)} personalized feature rows.")

    if rows:
        columns = [
            "user_id",
            "date_id",
            "date",
            "steps",
            "hrv",
            "resting_heart_rate",
            "sleep_hours",
            "hrv_baseline",
            "rhr_baseline",
            "steps_baseline",
            "sleep_baseline",
            "hrv_zscore",
            "rhr_zscore",
            "steps_zscore",
            "sleep_zscore",
            "sleep_7d_avg",
            "sleep_debt",
            "acute_training_load",
            "chronic_training_load",
            "acute_chronic_ratio",
        ]

        for row in rows[6:12]:
            print(dict(zip(columns, row)))


if __name__ == "__main__":
    build_personalized_features()
