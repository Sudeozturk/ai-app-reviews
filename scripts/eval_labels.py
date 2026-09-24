import argparse

from reviews.evaluation import (
    agreement,
    category_scores,
    disagreements,
    read_gold,
    read_predictions,
)
from reviews.labeling import BATCH_PROMPT_VERSION
from reviews.llm import DEFAULT_MODEL


def main() -> None:
    parser = argparse.ArgumentParser(description="Model etiketlerini elle etiketlerle karşılaştır.")
    parser.add_argument("--eval-file", default="eval/eval_set.csv")
    parser.add_argument("--prompt-version", default=BATCH_PROMPT_VERSION)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--show-diff", type=int, default=15)
    args = parser.parse_args()

    gold = read_gold(args.eval_file)
    pred = read_predictions(args.prompt_version, args.model)

    print(f"Prompt sürümü: {args.prompt_version} | model: {args.model}")
    print(f"Elle etiketli: {len(gold)} | model etiketli: {len(pred)}\n")

    metrics = agreement(gold, pred)
    if metrics.get("karsilastirilan", 0) == 0:
        print("Karşılaştırılacak ortak yorum yok.")
        return

    print("GENEL")
    print(f"  karşılaştırılan yorum : {int(metrics['karsilastirilan'])}")
    print(f"  kapsam                : {metrics['kapsam']:.0%}")
    print(f"  tam eşleşme           : {metrics['tam_eslesme']:.0%}")
    print(f"  jaccard               : {metrics['jaccard']:.2f}")
    print(f"  jaccard (içerikli {int(metrics['icerikli'])})  : {metrics['jaccard_icerikli']:.2f}")
    print(f"  duygu uyumu           : {metrics['duygu_uyumu']:.0%}\n")

    print("KATEGORİ BAZINDA")
    print(
        f"  {'kategori':<20} {'elle':>5} {'model':>6} {'ortak':>6} {'prec':>6} {'rec':>6} {'f1':>6}"
    )
    for s in sorted(category_scores(gold, pred), key=lambda x: -x.gold):
        print(
            f"  {s.category:<20} {s.gold:>5} {s.pred:>6} {s.hit:>6} "
            f"{s.precision:>6.2f} {s.recall:>6.2f} {s.f1:>6.2f}"
        )

    diffs = disagreements(gold, pred)
    print(f"\nAYRIŞMALAR ({len(diffs)} yorum, ilk {args.show_diff})")
    for _rid, g, p, content in diffs[: args.show_diff]:
        print(f"\n  {content[:160]}")
        print(f"    elle : {sorted(g)}")
        print(f"    model: {sorted(p)}")


if __name__ == "__main__":
    main()
