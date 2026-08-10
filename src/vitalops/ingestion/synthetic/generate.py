"""Generate synthetic wearable data for VitalOps.

Usage:

    uv run python -m vitalops.ingestion.synthetic.generate \
        --start 2026-08-01 \
        --end 2026-08-01
"""

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

import numpy as np

from vitalops.ingestion.db import get_conn
from vitalops.ingestion.loaders import (
    upsert_daily_metrics,
    upsert_sleep,
    upsert_workouts,
)
from vitalops.ingestion.transforms import add_date_id
from vitalops.ingestion.synthetic.simulator import simulate_day


PROJECT_ROOT = Path(__file__).resolve().parents[4]

STATE_PATH = PROJECT_ROOT / "data" / "synthetic" / "seed_state.json"


def load_state() -> dict:
    if not STATE_PATH.exists():
        raise FileNotFoundError(
            f"Seed state not found: {STATE_PATH}\nRun the seed step first."
        )

    with STATE_PATH.open() as f:
        state = json.load(f)

    if not state.get("users"):
        raise ValueError(f"Seed state contains no users: {STATE_PATH}")

    return state


def save_state(state: dict) -> None:
    with STATE_PATH.open("w") as f:
        json.dump(
            state,
            f,
            indent=2,
            default=str,
        )


def daterange(
    start: dt.date,
    end: dt.date,
):
    current = start

    while current <= end:
        yield current
        current += dt.timedelta(days=1)


def make_rng(
    seed: int,
    user_id: str,
    date: dt.date,
) -> np.random.Generator:
    """Create deterministic RNG for one user/day."""

    seed_material = (f"{seed}:{user_id}:{date.isoformat()}").encode()

    digest = hashlib.sha256(seed_material).digest()

    rng_seed = int.from_bytes(
        digest[:8],
        byteorder="little",
    )

    return np.random.default_rng(rng_seed)


def generate_day(
    state: dict,
    date: dt.date,
) -> None:

    daily_rows = []
    sleep_rows = []
    workout_rows = []

    for user in state["users"]:
        user_id = user["user_id"]
        device_id = user["device_id"]

        baseline = user["baseline"]
        simulator_state = user["state"]

        rng = make_rng(
            seed=state["rng_seed"],
            user_id=user_id,
            date=date,
        )

        (
            daily_row,
            sleep_row,
            workouts,
            new_state,
        ) = simulate_day(
            date=date,
            baseline=baseline,
            state=simulator_state,
            user_id=user_id,
            device_id=device_id,
            rng=rng,
        )

        user["state"] = new_state

        if daily_row is not None:
            daily_row, sleep_row, workouts = add_date_id(
                daily_row,
                sleep_row,
                workouts,
            )

            daily_rows.append(daily_row)

            if sleep_row is not None:
                sleep_rows.append(sleep_row)

            workout_rows.extend(workouts)

    with get_conn() as conn:
        upsert_daily_metrics(
            conn,
            daily_rows,
        )

        upsert_sleep(
            conn,
            sleep_rows,
        )

        upsert_workouts(
            conn,
            workout_rows,
        )

        conn.commit()

    save_state(state)

    print(
        f"{date}: "
        f"{len(daily_rows)} daily, "
        f"{len(sleep_rows)} sleep, "
        f"{len(workout_rows)} workouts"
    )


def generate(
    start: dt.date,
    end: dt.date,
) -> None:

    if end < start:
        raise ValueError("End date cannot be before start date.")

    state = load_state()

    for date in daterange(start, end):
        generate_day(
            state,
            date,
        )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--start",
        required=True,
        help="YYYY-MM-DD",
    )

    parser.add_argument(
        "--end",
        required=True,
        help="YYYY-MM-DD",
    )

    args = parser.parse_args()

    start = dt.date.fromisoformat(args.start)

    end = dt.date.fromisoformat(args.end)

    generate(
        start,
        end,
    )


if __name__ == "__main__":
    main()
