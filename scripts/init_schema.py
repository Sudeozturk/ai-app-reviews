from reviews.db import get_connection

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS reviews (
    review_id     TEXT PRIMARY KEY,
    app_id        TEXT        NOT NULL,
    lang          TEXT        NOT NULL,
    country       TEXT        NOT NULL,
    score         INTEGER     NOT NULL,
    content       TEXT        NOT NULL,
    app_version   TEXT,
    created_at    TIMESTAMPTZ NOT NULL,
    thumbs_up     INTEGER     NOT NULL DEFAULT 0,
    fetched_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS reviews_app_created_idx
    ON reviews (app_id, created_at DESC);

CREATE INDEX IF NOT EXISTS reviews_app_version_idx
    ON reviews (app_id, app_version);
"""


def main() -> None:
    with get_connection() as conn:
        conn.execute(SCHEMA_SQL)
    print("Şema hazır.")


if __name__ == "__main__":
    main()
