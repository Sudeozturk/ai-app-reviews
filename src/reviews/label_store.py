from collections.abc import Iterable

from reviews.db import get_connection
from reviews.labeling import CategoryLabel

PENDING_SQL = """
SELECT r.review_id, r.content
FROM reviews r
WHERE (%s::text IS NULL OR r.app_id = %s)
  AND NOT EXISTS (
      SELECT 1 FROM review_labels l
      WHERE l.review_id = r.review_id
        AND l.prompt_version = %s
        AND l.model = %s
  )
ORDER BY r.created_at DESC
LIMIT %s
"""

UPSERT_LABEL_SQL = """
INSERT INTO review_labels (
    review_id, prompt_version, model, status, language, raw_response, error
)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (review_id, prompt_version, model) DO UPDATE SET
    status       = EXCLUDED.status,
    language     = EXCLUDED.language,
    raw_response = EXCLUDED.raw_response,
    error        = EXCLUDED.error,
    labeled_at   = now()
"""

DELETE_CATEGORIES_SQL = """
DELETE FROM review_categories
WHERE review_id = %s AND prompt_version = %s AND model = %s
"""

INSERT_CATEGORY_SQL = """
INSERT INTO review_categories (review_id, prompt_version, model, category, sentiment)
VALUES (%s, %s, %s, %s, %s)
"""


def pending_reviews(
    prompt_version: str, model: str, limit: int, app_id: str | None = None
) -> list[tuple[str, str]]:
    with get_connection() as conn:
        rows = conn.execute(PENDING_SQL, (app_id, app_id, prompt_version, model, limit)).fetchall()
    return [(row[0], row[1]) for row in rows]


def save_label(
    review_id: str,
    prompt_version: str,
    model: str,
    status: str,
    *,
    language: str | None = None,
    raw_response: str | None = None,
    error: str | None = None,
    categories: Iterable[CategoryLabel] = (),
) -> None:
    key = (review_id, prompt_version, model)
    with get_connection() as conn:
        conn.execute(UPSERT_LABEL_SQL, (*key, status, language, raw_response, error))
        conn.execute(DELETE_CATEGORIES_SQL, key)
        for c in categories:
            conn.execute(INSERT_CATEGORY_SQL, (*key, c.name, c.sentiment))
