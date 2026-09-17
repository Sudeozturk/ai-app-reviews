import psycopg

from reviews.config import get_database_url


def get_connection() -> psycopg.Connection:
    return psycopg.connect(get_database_url())


def get_pgvector_version() -> str:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
        ).fetchone()
    if row is None:
        raise RuntimeError("pgvector uzantısı yüklü değil.")
    return row[0]
