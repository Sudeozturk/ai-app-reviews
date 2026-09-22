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

    CREATE TABLE IF NOT EXISTS llm_calls (
    id            BIGSERIAL PRIMARY KEY,
    model         TEXT        NOT NULL,
    prompt_sha    TEXT        NOT NULL,
    prompt_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens  INTEGER,
    duration_ms   INTEGER     NOT NULL,
    ok            BOOLEAN     NOT NULL,
    error         TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS llm_calls_created_idx
    ON llm_calls (created_at DESC);

    
    CREATE TABLE IF NOT EXISTS review_labels (
    review_id      TEXT        NOT NULL REFERENCES reviews (review_id) ON DELETE CASCADE,
    prompt_version TEXT        NOT NULL,
    model          TEXT        NOT NULL,
    status         TEXT        NOT NULL,
    language       TEXT,
    raw_response   TEXT,
    error          TEXT,
    labeled_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (review_id, prompt_version, model)
);

CREATE TABLE IF NOT EXISTS review_categories (
    review_id      TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    model          TEXT NOT NULL,
    category       TEXT NOT NULL,
    sentiment      TEXT NOT NULL,
    PRIMARY KEY (review_id, prompt_version, model, category),
    FOREIGN KEY (review_id, prompt_version, model)
        REFERENCES review_labels (review_id, prompt_version, model) ON DELETE CASCADE
);
"""


def main() -> None:
    with get_connection() as conn:
        conn.execute(SCHEMA_SQL)
    print("Şema hazır.")


if __name__ == "__main__":
    main()
