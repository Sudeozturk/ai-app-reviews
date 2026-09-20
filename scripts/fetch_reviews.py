import argparse

from reviews.fetch import fetch_reviews
from reviews.store import count_reviews, save_reviews


def main() -> None:
    parser = argparse.ArgumentParser(description="Google Play yorumlarını çek ve kaydet.")
    parser.add_argument("app_id", help="Uygulamanın paket adı, ör. com.scaleup.chatai")
    parser.add_argument("--lang", default="en")
    parser.add_argument("--country", default="us")
    parser.add_argument("--count", type=int, default=100)
    args = parser.parse_args()

    before = count_reviews(args.app_id)
    items = fetch_reviews(args.app_id, lang=args.lang, country=args.country, count=args.count)
    saved = save_reviews(items)
    after = count_reviews(args.app_id)

    print(f"Çekilen: {saved}")
    print(f"Yeni kayıt: {after - before}")
    print(f"Toplam ({args.app_id}): {after}")


if __name__ == "__main__":
    main()
