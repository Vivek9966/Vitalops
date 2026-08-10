"""Stateful physiological simulator.

Design principles (this is what separates it from random.uniform() noise):

1. Fixed per-person baseline (drawn once at seed time, not here).
2. Autocorrelated noise, not i.i.d. — today's reading is close to
   yesterday's, drifting via an AR(1) process, layered on a slow-moving
   true physiological signal.
3. Training load is tracked as acute (7d) vs chronic (28d) exponentially
   weighted load, and their ratio (ACWR) suppresses HRV / raises RHR when
   elevated — this is a real sports-science mechanism, not decoration.
4. Sparse, causal anomalies: illness events that visibly move HRV/RHR/sleep
   for several consecutive days, then resolve — not point noise.
5. Missing-device days: sensors don't always sync. These become genuinely
   absent rows downstream, not zeros.

Nothing here computes a "recovery score" — that's left as a derived label
for the ML layer to learn from these raw signals.
"""

from __future__ import annotations
import datetime as dt
import uuid
import numpy as np

WORKOUT_TYPES = {
    "Run": dict(hr_frac=0.80, met=9.8, load_factor=1.0, dur_range=(25, 60)),
    "Strength": dict(hr_frac=0.65, met=6.0, load_factor=0.7, dur_range=(35, 70)),
    "Cycling": dict(hr_frac=0.75, met=8.0, load_factor=0.9, dur_range=(30, 90)),
    "HIIT": dict(hr_frac=0.88, met=10.5, load_factor=1.3, dur_range=(20, 40)),
    "Yoga": dict(hr_frac=0.55, met=3.0, load_factor=0.3, dur_range=(30, 60)),
    "Swim": dict(hr_frac=0.78, met=8.3, load_factor=1.0, dur_range=(25, 55)),
}

DEVICE_MISSING_PROB = 0.02
ILLNESS_START_PROB = 0.0035  # per day, gated by cooldown below
ILLNESS_COOLDOWN_DAYS = 20
AR_PHI = 0.7  # autocorrelation coefficient for daily noise


def _ar1_step(prev_noise: float, scale: float, rng: np.random.Generator) -> float:
    return AR_PHI * prev_noise + rng.normal(0, scale) * np.sqrt(1 - AR_PHI**2)


def _ewma_update(prev: float, value: float, span_days: int) -> float:
    alpha = 2 / (span_days + 1)
    return alpha * value + (1 - alpha) * prev


def simulate_day(
    date: dt.date,
    baseline: dict,
    state: dict,
    user_id: str,
    device_id: str,
    rng: np.random.Generator,
):
    """Advance the simulator by exactly one day.

    Returns (daily_metrics_row | None, sleep_row | None, workout_rows: list, new_state).
    Rows are None when the device didn't sync that day (realistic gap).
    """
    state = dict(state)  # don't mutate caller's dict
    dow = date.isoweekday()  # 1=Mon .. 7=Sun
    is_weekend = dow in (6, 7)

    # --- illness state machine ---
    if state["illness_days_left"] > 0:
        state["illness_days_left"] -= 1
        state["days_since_illness"] = 0
        ill = True
    else:
        state["days_since_illness"] += 1
        ill = False
        if (
            state["days_since_illness"] > ILLNESS_COOLDOWN_DAYS
            and rng.random() < ILLNESS_START_PROB
        ):
            state["illness_days_left"] = int(rng.integers(3, 6)) - 1
            ill = True

    # --- device sync (missing-data realism) ---
    device_online = rng.random() > DEVICE_MISSING_PROB

    # --- slow fitness drift (VO2max-ish improvement/plateau) ---
    state["fitness_trend"] += baseline["fitness_trend_rate"] * rng.normal(1.0, 0.3)
    state["fitness_trend"] = float(np.clip(state["fitness_trend"], -3.0, 6.0))

    # --- ACWR (acute:chronic workload ratio) from yesterday's load, drives fatigue ---
    acwr = (
        state["acute_load"] / state["chronic_load"]
        if state["chronic_load"] > 1e-6
        else 1.0
    )
    fatigue_penalty = (
        max(0.0, acwr - 1.3) * 6.0
    )  # only bites once meaningfully overloaded

    # --- decide workout(s) for today ---
    workout_rows = []
    todays_load = 0.0
    wants_workout = (dow - 1) in baseline["workout_days_pref"]
    skip_for_fatigue = acwr > 1.6 and rng.random() < 0.6
    if wants_workout and not ill and not skip_for_fatigue and device_online:
        wtype = rng.choice(list(WORKOUT_TYPES.keys()), p=_workout_type_weights())
        spec = WORKOUT_TYPES[wtype]
        duration = int(rng.integers(*spec["dur_range"]))
        hr_peak_frac = spec["hr_frac"] * rng.normal(1.0, 0.05)
        max_hr_est = 208 - 0.7 * baseline["age"]  # Tanaka formula, common in wearables
        avg_hr = int(np.clip(max_hr_est * hr_peak_frac, 90, 195))
        max_hr = int(np.clip(avg_hr * rng.normal(1.12, 0.03), avg_hr, 205))
        calories = (
            spec["met"]
            * baseline["weight_kg"]
            * (duration / 60)
            * rng.normal(1.0, 0.08)
        )
        distance = (
            round(duration * rng.uniform(0.12, 0.19), 2)
            if wtype in ("Run", "Cycling", "Swim")
            else None
        )
        load = duration * spec["load_factor"] * (avg_hr / max_hr_est) * 10
        start_hour = rng.choice(
            [6, 7, 8, 12, 17, 18, 19], p=[0.18, 0.15, 0.07, 0.08, 0.17, 0.2, 0.15]
        )
        start_time = dt.datetime.combine(date, dt.time(hour=start_hour)) + dt.timedelta(
            minutes=int(rng.integers(0, 60))
        )
        end_time = start_time + dt.timedelta(minutes=duration)

        workout_rows.append(
            dict(
                workout_id=str(uuid.uuid4()),
                user_id=user_id,
                device_id=device_id,
                workout_type=wtype,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=duration,
                distance_km=distance,
                calories_burned=round(float(calories), 1),
                avg_heart_rate=avg_hr,
                max_heart_rate=max_hr,
                training_load=round(float(load), 1),
            )
        )
        todays_load = load

    state["acute_load"] = _ewma_update(state["acute_load"], todays_load, 7)
    state["chronic_load"] = _ewma_update(state["chronic_load"], todays_load, 28)

    if not device_online:
        # device didn't sync: no daily metrics, no sleep row, but workouts above are
        # forced off in that branch already since we gated on device_online.
        state["hrv_noise_prev"] = _ar1_step(state["hrv_noise_prev"], 3.0, rng)
        state["rhr_noise_prev"] = _ar1_step(state["rhr_noise_prev"], 2.0, rng)
        return None, None, [], state

    # --- HRV / RHR for the day (autocorrelated + mechanistic adjustments) ---
    state["hrv_noise_prev"] = _ar1_step(state["hrv_noise_prev"], 4.0, rng)
    state["rhr_noise_prev"] = _ar1_step(state["rhr_noise_prev"], 2.5, rng)

    hrv = (
        baseline["hrv_base"]
        + state["fitness_trend"] * 1.5
        - fatigue_penalty * 0.8
        - (18 if ill else 0)
        + state["hrv_noise_prev"]
    )
    hrv = float(np.clip(hrv, 12, 140))

    rhr = (
        baseline["resting_hr_base"]
        - state["fitness_trend"] * 0.4
        + fatigue_penalty * 0.5
        + (9 if ill else 0)
        + state["rhr_noise_prev"]
    )
    rhr = float(np.clip(rhr, 40, 100))

    # --- sleep ---
    weekend_bonus = 0.6 if is_weekend else 0.0
    debt_recovery = min(state["sleep_debt_hours"] * 0.3, 1.0)
    time_in_bed_h = np.clip(
        baseline["sleep_need_hours"]
        + weekend_bonus
        + debt_recovery
        + rng.normal(0, 0.4),
        4.5,
        10.5,
    )
    efficiency = np.clip(rng.normal(0.90 if not ill else 0.78, 0.04), 0.55, 0.99)
    time_in_bed_min = time_in_bed_h * 60
    awake_min = time_in_bed_min * (1 - efficiency)
    duration_min = time_in_bed_min - awake_min

    deep_frac = np.clip(rng.normal(0.18 if not ill else 0.11, 0.03), 0.05, 0.30)
    rem_frac = np.clip(rng.normal(0.22, 0.03), 0.08, 0.32)
    light_frac = max(0.0, 1 - deep_frac - rem_frac)
    deep_min = duration_min * deep_frac
    rem_min = duration_min * rem_frac
    light_min = duration_min * light_frac

    bedtime_hour = (
        23 + baseline["chronotype_offset_min"] / 60 + (0.7 if is_weekend else 0)
    )
    bedtime_hour = float(
        np.clip(bedtime_hour, 20.5, 26.5)
    )  # allow past-midnight via mod below
    # base_date = #date if bedtime_hour < 24 else date  # start is previous evening
    sleep_start = dt.datetime.combine(date, dt.time(0, 0)) + dt.timedelta(
        hours=bedtime_hour
    )
    sleep_end = sleep_start + dt.timedelta(minutes=time_in_bed_min)

    slept_enough = duration_min / 60 >= baseline["sleep_need_hours"] - 0.5
    state["sleep_debt_hours"] = max(
        0.0,
        state["sleep_debt_hours"]
        + (baseline["sleep_need_hours"] - duration_min / 60)
        * (0.0 if slept_enough else 1.0)
        * 0.5,
    )
    state["sleep_debt_hours"] = min(state["sleep_debt_hours"], 12.0)

    sleep_row = dict(
        sleep_id=str(uuid.uuid4()),
        user_id=user_id,
        device_id=device_id,
        sleep_start=sleep_start,
        sleep_end=sleep_end,
        duration_minutes=int(duration_min),
        deep_minutes=int(deep_min),
        light_minutes=int(light_min),
        rem_minutes=int(rem_min),
        awake_minutes=int(awake_min),
        sleep_efficiency=round(float(efficiency), 3),
        avg_heart_rate=int(np.clip(rhr + rng.normal(3, 2), 35, 90)),
        resting_heart_rate=int(round(rhr)),
        hrv=round(hrv, 1),
        awakenings=int(np.clip(rng.poisson(1.5 if not ill else 4), 0, 15)),
    )

    # --- daily aggregate metrics ---
    base_steps = 4500 + baseline["fitness_activity_bias"] * 2000
    workout_step_bonus = sum(w["duration_minutes"] * 90 for w in workout_rows)
    steps = int(
        np.clip(
            base_steps * (0.85 if is_weekend else 1.0) * rng.normal(1.0, 0.15)
            + workout_step_bonus
            - (2500 if ill else 0),
            500,
            30000,
        )
    )
    active_minutes = int(
        np.clip(sum(w["duration_minutes"] for w in workout_rows) + steps / 220, 0, 300)
    )
    calories = round(
        1600
        + baseline["weight_kg"] * 5
        + steps * 0.04
        + sum(w["calories_burned"] for w in workout_rows),
        1,
    )
    distance_km = round(steps * 0.0008, 2)
    max_hr_today = max(
        [w["max_heart_rate"] for w in workout_rows], default=int(rhr + 40)
    )

    daily_row = dict(
        metric_id=str(uuid.uuid4()),
        user_id=user_id,
        device_id=device_id,
        steps=steps,
        date=date,
        active_minutes=active_minutes,
        calories_burned=calories,
        distance_km=distance_km,
        avg_heart_rate=int(np.clip(rhr + rng.normal(12, 4), rhr, 130)),
        resting_heart_rate=int(round(rhr)),
        max_heart_rate=int(max_hr_today),
        hrv=round(hrv, 1),
    )

    return daily_row, sleep_row, workout_rows, state


def _workout_type_weights():
    # Run/Strength/Cycling most common, HIIT/Swim/Yoga less so
    return [0.30, 0.25, 0.18, 0.10, 0.10, 0.07]
