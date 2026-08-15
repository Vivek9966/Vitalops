import json
from pathlib import Path
from vitalops.ingestion.db import get_conn

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = PROJECT_ROOT / "data" / "synthetic" / "seed_state.json"


def main():
    with STATE_PATH.open() as f:
        state = json.load(f)
    users = state["users"]
    with get_conn() as conn:
        with conn.cursor() as cur:
            for user in users:
                cur.execute(
                    """
                    UPDATE dim_user
                    SET sleep_need_hours = %s 
                    WHERE user_id = %s""",
                    (user["baseline"]["sleep_need_hours"], user["user_id"]),
                )
                if cur.rowcount != 1:
                    raise RuntimeError(
                        f"expected exactly for one user"
                        f"{user['user_id']},updated {cur.rowcount}"
                    )
        conn.commit()
    print(f"Backfilled sleep_need_hours {len(users)} users")


if __name__ == "__main__":
    main()
