import argparse
import time
from collections import Counter

from reviews.label_store import pending_reviews, save_label
from reviews.labeling import PROMPT_VERSION, LabelParseError, build_prompt, parse_label
from reviews.llm import DEFAULT_MODEL, complete


def main() -> None:
    parser = argparse.ArgumentParser(description="Yorumları LLM ile etiketle.")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--min-length", type=int, default=0)
    parser.add_argument("--app-id", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    model = DEFAULT_MODEL
    items = pending_reviews(PROMPT_VERSION, model, args.limit, args.app_id)
    print(f"Prompt sürümü: {PROMPT_VERSION} | model: {model} | işlenecek: {len(items)}")
    if args.dry_run:
        return

    counts: Counter[str] = Counter()
    tokens = 0
    started = time.monotonic()

    for i, (review_id, content) in enumerate(items, start=1):
        if len(content) < args.min_length:
            save_label(review_id, PROMPT_VERSION, model, "skipped")
            counts["skipped"] += 1
            continue

        try:
            response = complete(build_prompt(content), model=model)
        except Exception as exc:
            print(f"[{i}] çağrı hatası, sonraki çalıştırmada tekrar denenecek: {exc}")
            counts["api_error"] += 1
            continue

        tokens += response.total_tokens or 0
        try:
            result = parse_label(response.text)
        except LabelParseError as exc:
            save_label(
                review_id,
                PROMPT_VERSION,
                model,
                "parse_error",
                raw_response=response.text,
                error=str(exc),
            )
            counts["parse_error"] += 1
            continue

        save_label(
            review_id,
            PROMPT_VERSION,
            model,
            "ok",
            language=result.language,
            raw_response=response.text,
            categories=result.categories,
        )
        counts["ok"] += 1
        print(f"[{i}/{len(items)}] " + ", ".join(c.name for c in result.categories))

    elapsed = time.monotonic() - started
    print(f"\nSonuç: {dict(counts)}")
    print(f"Toplam token: {tokens} | süre: {elapsed:.0f} sn")


if __name__ == "__main__":
    main()
