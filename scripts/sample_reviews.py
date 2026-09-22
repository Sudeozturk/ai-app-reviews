import argparse

from reviews.db import get_connection

SQL = """
SELECT app_id, score, app_version, length(content) AS uzunluk, content
FROM reviews
WHERE length(content) >= %s
ORDER BY random()
LIMIT %s
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Rastgele yorum örneği yazdır.")
    parser.add_argument("--count", type=int, default=120)
    parser.add_argument("--min-length", type=int, default=0)
    parser.add_argument("--out", default="sample.txt")
    args = parser.parse_args()

    with get_connection() as conn:
        rows = conn.execute(SQL, (args.min_length, args.count)).fetchall()

    with open(args.out, "w", encoding="utf-8") as f:
        for i, (app_id, score, version, uzunluk, content) in enumerate(rows, start=1):
            f.write(f"--- {i} | {app_id} | {score}★ | v{version} | {uzunluk} karakter\n")
            f.write(f"{content}\n\n")

    print(f"{len(rows)} yorum {args.out} dosyasına yazıldı.")


if __name__ == "__main__":
    main()
