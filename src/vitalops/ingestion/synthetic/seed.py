"""Seed synthetic users and devices.

Creates dim_user and dim_device once and persists each synthetic
user's physiological baseline and rolling simulator state.

Usage:
    uv run python -m vitalops.ingestion.synthetic.seed --users 4
"""

import argparse
import datetime as dt
import json
import uuid
from pathlib import Path

import numpy as np
from faker import Faker

from vitalops.ingestion.db import get_conn


PROJECT_ROOT = Path(__file__).resolve().parents[4]
STATE_PATH = PROJECT_ROOT / "data" / "synthetic" / "seed_state.json"


DEVICES = [
    ("Garmin", "Forerunner 265", "smartwatch"),
    ("Apple", "Watch Series 9", "smartwatch"),
    ("Fitbit", "Charge 6", "band"),
    ("Oura", "Ring Gen3", "ring"),
    ("Whoop", "4.0", "band"),
]


fake = Faker()


def make_user_baseline(rng: np.random.Generator) -> dict:
    """Create a fixed physiological baseline for one synthetic user."""

    age = int(rng.integers(22, 52))

    activity_bias = rng.choice([0.95, 1.0, 1.05])

    return {
        "age": age,
        "height_cm": float(np.clip(rng.normal(170, 9), 150, 200)),
        "weight_kg": float(np.clip(rng.normal(72, 12), 45, 120)),
        "resting_hr_base": float(np.clip(rng.normal(60, 7), 45, 82)),
        "hrv_base": float(np.clip(rng.normal(55, 15), 20, 120)),
        "sleep_need_hours": float(np.clip(rng.normal(7.5, 0.5), 6.0, 9.0)),
        "chronotype_offset_min": float(rng.normal(0, 45)),
        "fitness_activity_bias": float(activity_bias),
        "fitness_trend_rate": float(rng.normal(0.0008, 0.0004)),
        "workout_days_pref": sorted(
            rng.choice(
                range(7),
                size=int(rng.integers(3, 6)),
                replace=False,
            ).tolist()
        ),
    }


def seed(
    n_users: int,
    seed_val: int = 42,
) -> None:

    if STATE_PATH.exists():
        try:
            with STATE_PATH.open() as f:
                state = json.load(f)
            if state.get("users"):
                print(f"Seed state already exists: {STATE_PATH}")
                print("Skipping seed.")
                return
        except json.JSONDecodeError, OSError:
            print("Existing seed state is invalid. Recreating it.")

    STATE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    rng = np.random.default_rng(seed_val)

    users = []

    with get_conn() as conn:
        with conn.cursor() as cur:
            for _ in range(n_users):
                user_id = str(uuid.uuid4())

                name = fake.name()

                baseline = make_user_baseline(rng)

                dob = dt.date.today() - dt.timedelta(days=baseline["age"] * 365)

                cur.execute(
                    """
                    INSERT INTO dim_user (
                        user_id,
                        name,
                        dob,
                        height_cm,
                        weight_kg
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        name,
                        dob,
                        baseline["height_cm"],
                        baseline["weight_kg"],
                    ),
                )

                manufacturer, model, device_type = DEVICES[
                    rng.integers(0, len(DEVICES))
                ]

                device_id = str(uuid.uuid4())

                cur.execute(
                    """
                    INSERT INTO dim_device (
                        device_id,
                        user_id,
                        manufacturer,
                        model,
                        device_type
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        device_id,
                        user_id,
                        manufacturer,
                        model,
                        device_type,
                    ),
                )

                users.append(
                    {
                        "user_id": user_id,
                        "name": name,
                        "device_id": device_id,
                        "baseline": baseline,
                        "state": {
                            "last_date": None,
                            "acute_load": 0.0,
                            "chronic_load": 0.0,
                            "sleep_debt_hours": 0.0,
                            "hrv_noise_prev": 0.0,
                            "rhr_noise_prev": 0.0,
                            "illness_days_left": 0,
                            "days_since_illness": 999,
                            "fitness_trend": 0.0,
                        },
                    }
                )

        conn.commit()

    with STATE_PATH.open("w") as f:
        json.dump(
            {
                "rng_seed": seed_val,
                "users": users,
            },
            f,
            indent=2,
            default=str,
        )

    print(f"Seeded {n_users} users + devices.")

    print(f"State written to {STATE_PATH}")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--users",
        type=int,
        default=3,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    args = parser.parse_args()

    if args.users < 1:
        parser.error("--users must be >= 1")

    seed(
        args.users,
        args.seed,
    )


if __name__ == "__main__":
    main()
