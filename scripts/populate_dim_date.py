"""Populate dim_date for a given range.

date_id uses the YYYYMMDD integer convention
(e.g. 2026-08-10 -> 20260810).

Usage:
    python -m scripts.populate_dim_date --start 2023-01-01 --end 2026-08-10
"""

import argparse
import datetime as dt

from vitalops.ingestion.db import get_conn


def date_id_of(d: dt.date) -> int:
    return d.year * 10000 + d.month * 100 + d.day


def daterange(start: dt.date, end: dt.date):
    current = start

    while current <= end:
        yield current
        current += dt.timedelta(days=1)


def build_rows(start: dt.date, end: dt.date):
    rows = []

    for d in daterange(start, end):
        iso_week = d.isocalendar().week

        rows.append(
            (
                date_id_of(d),
                d,
                d.day,
                d.isoweekday(),
                iso_week,
                d.month,
                d.year,
                d.isoweekday() in (6, 7),
            )
        )

    return rows


def upsert(rows):
    if not rows:
        return

    sql = """
        INSERT INTO dim_date (
            date_id,
            date,
            day,
            day_of_week,
            week,
            month,
            year,
            is_weekend
        )
        VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        ON CONFLICT (date_id) DO NOTHING
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, rows)

        conn.commit()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--start",
        default=None,
        help="YYYY-MM-DD, default 2 years back",
    )

    parser.add_argument(
        "--end",
        default=None,
        help="YYYY-MM-DD, default today",
    )

    args = parser.parse_args()

    end = dt.date.fromisoformat(args.end) if args.end else dt.date.today()

    start = (
        dt.date.fromisoformat(args.start)
        if args.start
        else end - dt.timedelta(days=730)
    )

    rows = build_rows(start, end)

    upsert(rows)

    print(f"dim_date: upserted {len(rows)} rows from {start} to {end}")


if __name__ == "__main__":
    main()
