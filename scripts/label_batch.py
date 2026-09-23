import argparse
import csv
import random
import time
from collections import Counter
from pathlib import Path

from reviews.label_store import pending_eval_reviews, pending_reviews, save_label
from reviews.labeling import (
    BATCH_PROMPT_VERSION,
    LabelParseError,
    build_batch_prompt,
    parse_batch,
)
from reviews.llm import DEFAULT_MODEL, DailyQuotaExceeded, complete


def read_eval_ids(path: str) -> list[str]:
    with Path(path).open(encoding="utf-8-sig") as f:
        return [row["review_id"] for row in csv.DictReader(f) if row.get("review_id")]


def main() -> None:
    parser = argparse.ArgumentParser(description="Yorumları gruplar halinde etiketle.")
    parser.add_argument("--batches", type=int, default=1, help="Gönderilecek istek sayısı")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--app-id", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--eval", action="store_true", help="Sadece değerlendirme setini etiketle")
    parser.add_argument("--eval-file", default="eval/eval_set.csv")
    parser.add_argument("--sleep", type=float, default=13.0, help="Gruplar arası bekleme (sn)")
    args = parser.parse_args()

    model = DEFAULT_MODEL
    version = BATCH_PROMPT_VERSION
    if args.eval:
        eval_ids = read_eval_ids(args.eval_file)
        items = pending_eval_reviews(eval_ids, version, model, args.batches * args.batch_size)
        print(f"Değerlendirme seti: {len(eval_ids)} yorum")
    else:
        items = pending_reviews(version, model, args.batches * args.batch_size, args.app_id)
    random.shuffle(items)
    print(f"Prompt sürümü: {version} | model: {model} | yorum: {len(items)}")
    if args.dry_run:
        return

    counts: Counter[str] = Counter()
    tokens = 0
    started = time.monotonic()

    for b, start in enumerate(range(0, len(items), args.batch_size), start=1):
        chunk = items[start : start + args.batch_size]
        numbered = list(enumerate(chunk, start=1))
        prompt = build_batch_prompt([(no, content) for no, (_, content) in numbered])

        try:
            response = complete(prompt, model=model)
        except DailyQuotaExceeded:
            print("Günlük kota doldu, duruyorum. Kalanlar sonraki çalıştırmada işlenecek.")
            break
        except Exception as exc:
            print(f"[grup {b}] çağrı hatası, tekrar denenecek: {exc}")
            counts["api_error"] += len(chunk)
            continue

        tokens += response.total_tokens or 0
        try:
            results = parse_batch(response.text, [no for no, _ in numbered])
        except LabelParseError as exc:
            print(f"[grup {b}] cevap kullanılamadı: {exc}")
            for _, (review_id, _) in numbered:
                save_label(
                    review_id,
                    version,
                    model,
                    "parse_error",
                    raw_response=response.text,
                    error=str(exc),
                )
            counts["parse_error"] += len(chunk)
            continue

        for no, (review_id, _) in numbered:
            result = results.get(no)
            if result is None:
                counts["missing"] += 1
            elif result.label is None:
                save_label(
                    review_id,
                    version,
                    model,
                    "parse_error",
                    raw_response=result.raw,
                    error=result.error,
                )
                counts["parse_error"] += 1
            else:
                save_label(
                    review_id,
                    version,
                    model,
                    "ok",
                    language=result.label.language,
                    raw_response=result.raw,
                    categories=result.label.categories,
                )
                counts["ok"] += 1
        print(f"[grup {b}] {len(chunk)} yorum, {response.total_tokens} token")
        time.sleep(args.sleep)
    elapsed = time.monotonic() - started
    print(f"\nSonuç: {dict(counts)}")
    print(f"Toplam token: {tokens} | süre: {elapsed:.0f} sn")


if __name__ == "__main__":
    main()
