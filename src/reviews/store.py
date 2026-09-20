from collections.abc import Iterable

from reviews.db import get_connection
from reviews.fetch import Review

UPSERT_SQL = """
INSERT INTO reviews (
    review_id, app_id, lang, country, score,
    content, app_version, created_at, thumbs_up
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (review_id) DO UPDATE SET
    score       = EXCLUDED.score,
    content     = EXCLUDED.content,
    thumbs_up   = EXCLUDED.thumbs_up,
    fetched_at  = now()
"""


def save_reviews(items: Iterable[Review]) -> int:
    rows = [
        (
            r.review_id,
            r.app_id,
            r.lang,
            r.country,
            r.score,
            r.content,
            r.app_version,
            r.created_at,
            r.thumbs_up,
        )
        for r in items
    ]
    if not rows:
        return 0
    with get_connection() as conn, conn.cursor() as cur:
        cur.executemany(UPSERT_SQL, rows)
    return len(rows)


def count_reviews(app_id: str | None = None) -> int:
    with get_connection() as conn:
        if app_id is None:
            row = conn.execute("SELECT count(*) FROM reviews").fetchone()
        else:
            row = conn.execute(
                "SELECT count(*) FROM reviews WHERE app_id = %s", (app_id,)
            ).fetchone()
    return int(row[0])