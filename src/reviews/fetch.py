from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from google_play_scraper import Sort, reviews


@dataclass(frozen=True)
class Review:
    review_id: str
    app_id: str
    lang: str
    country: str
    score: int
    content: str
    app_version: str | None
    created_at: datetime
    thumbs_up: int


def normalize(raw: dict[str, Any], app_id: str, lang: str, country: str) -> Review:
    created = raw["at"]
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    return Review(
        review_id=raw["reviewId"],
        app_id=app_id,
        lang=lang,
        country=country,
        score=int(raw["score"]),
        content=(raw["content"] or "").strip(),
        app_version=raw.get("reviewCreatedVersion"),
        created_at=created,
        thumbs_up=int(raw.get("thumbsUpCount") or 0),
    )


def fetch_reviews(
    app_id: str,
    lang: str = "en",
    country: str = "us",
    count: int = 100,
) -> list[Review]:
    raw_items, _ = reviews(
        app_id,
        lang=lang,
        country=country,
        sort=Sort.NEWEST,
        count=count,
    )
    return [normalize(item, app_id, lang, country) for item in raw_items]
