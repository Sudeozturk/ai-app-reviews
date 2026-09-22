import argparse
import csv
import re
from pathlib import Path

from reviews.db import get_connection

HEADER = re.compile(r"^--- (\d+) \| (\S+) \| (\d)★ \|")

FIND_SQL = """
SELECT review_id FROM reviews
WHERE app_id = %s AND score = %s AND content = %s
  AND NOT (review_id = ANY(%s::text[]))
LIMIT 1
"""

COLUMNS = [
    "no",
    "review_id",
    "app_id",
    "score",
    "content",
    "kategori_1",
    "duygu_1",
    "kategori_2",
    "duygu_2",
    "kategori_3",
    "duygu_3",
    "not",
]


def parse_sample(path: Path) -> list[tuple[int, str, int, str]]:
    entries: list[tuple[int, str, int, str]] = []
    current: tuple[int, str, int] | None = None
    lines: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = HEADER.match(line)
        if match:
            if current:
                entries.append((*current, "\n".join(lines).strip()))
            current = (int(match.group(1)), match.group(2), int(match.group(3)))
            lines = []
        else:
            lines.append(line)
    if current:
        entries.append((*current, "\n".join(lines).strip()))
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description="Okunan örneklemden değerlendirme seti oluştur.")
    parser.add_argument("--sample", default="sample.txt")
    parser.add_argument("--out", default="eval/eval_set.csv")
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists():
        raise SystemExit(f"{out} zaten var, elle etiketlerin kaybolmasın diye üzerine yazmıyorum.")

    entries = parse_sample(Path(args.sample))
    used: list[str] = []
    rows: list[dict] = []
    with get_connection() as conn:
        for no, app_id, score, content in entries:
            row = conn.execute(FIND_SQL, (app_id, score, content, used)).fetchone()
            if row is None:
                print(f"Eşleşmedi: {no}")
                continue
            used.append(row[0])
            rows.append(
                {
                    "no": no,
                    "review_id": row[0],
                    "app_id": app_id,
                    "score": score,
                    "content": content,
                }
            )

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} / {len(entries)} yorum eşleşti, {out} dosyasına yazıldı.")


if __name__ == "__main__":
    main()
