from datetime import UTC, datetime

import pytest

from reviews.db import get_connection
from reviews.fetch import Review
from reviews.store import count_reviews, save_reviews

pytestmark = pytest.mark.integration

TEST_APP_ID = "test.app.fake"


def make_review(review_id: str, score: int = 5, content: str = "harika 👍") -> Review:
    return Review(
        review_id=review_id,
        app_id=TEST_APP_ID,
        lang="tr",
        country="tr",
        score=score,
        content=content,
        app_version=None,
        created_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        thumbs_up=0,
    )


@pytest.fixture(autouse=True)
def temiz_tablo():
    yield
    with get_connection() as conn:
        conn.execute("DELETE FROM reviews WHERE app_id = %s", (TEST_APP_ID,))


def test_ayni_yorum_iki_kez_kaydedilince_tek_satir_olur():
    items = [make_review("r1"), make_review("r2")]

    save_reviews(items)
    assert count_reviews(TEST_APP_ID) == 2

    save_reviews(items)
    assert count_reviews(TEST_APP_ID) == 2


def test_tekrar_kayitta_degisen_alanlar_guncellenir():
    save_reviews([make_review("r1", score=1, content="berbat")])
    save_reviews([make_review("r1", score=5, content="düzeldi")])

    with get_connection() as conn:
        row = conn.execute(
            "SELECT score, content FROM reviews WHERE review_id = %s", ("r1",)
        ).fetchone()

    assert row[0] == 5
    assert row[1] == "düzeldi"


def test_bos_liste_hata_vermez():
    assert save_reviews([]) == 0