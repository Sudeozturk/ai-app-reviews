import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from reviews.db import get_connection

MODEL_LABELS_SQL = """
SELECT review_id, category, sentiment
FROM review_categories
WHERE prompt_version = %s AND model = %s
"""

Labels = dict[str, dict[str, str]]


@dataclass(frozen=True)
class CategoryScore:
    category: str
    gold: int
    pred: int
    hit: int

    @property
    def precision(self) -> float:
        return self.hit / self.pred if self.pred else 0.0

    @property
    def recall(self) -> float:
        return self.hit / self.gold if self.gold else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0


def read_gold(path: str) -> Labels:
    gold: Labels = {}
    with Path(path).open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            pairs = {}
            for i in (1, 2, 3):
                name = (row.get(f"kategori_{i}") or "").strip()
                sentiment = (row.get(f"duygu_{i}") or "").strip()
                if name:
                    pairs[name] = sentiment
            if pairs:
                gold[row["review_id"]] = pairs
    return gold


def read_predictions(prompt_version: str, model: str) -> Labels:
    pred: Labels = defaultdict(dict)
    with get_connection() as conn:
        rows = conn.execute(MODEL_LABELS_SQL, (prompt_version, model)).fetchall()
    for review_id, category, sentiment in rows:
        pred[review_id][category] = sentiment
    return dict(pred)


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def category_scores(gold: Labels, pred: Labels) -> list[CategoryScore]:
    names = {c for pairs in gold.values() for c in pairs}
    names |= {c for pairs in pred.values() for c in pairs}
    scores = []
    for name in sorted(names):
        g = sum(1 for rid in gold if name in gold[rid])
        p = sum(1 for rid in gold if name in pred.get(rid, {}))
        hit = sum(1 for rid in gold if name in gold[rid] and name in pred.get(rid, {}))
        scores.append(CategoryScore(name, g, p, hit))
    return scores


def agreement(gold: Labels, pred: Labels) -> dict[str, float]:
    shared = [rid for rid in gold if rid in pred]
    if not shared:
        return {"kapsam": 0.0}

    exact = sum(1 for rid in shared if set(gold[rid]) == set(pred[rid]))
    jac = sum(jaccard(set(gold[rid]), set(pred[rid])) for rid in shared) / len(shared)

    icerikli = [rid for rid in shared if "siniflandirilamaz" not in gold[rid]]
    jac_icerikli = (
        sum(jaccard(set(gold[rid]), set(pred[rid])) for rid in icerikli) / len(icerikli)
        if icerikli
        else 0.0
    )

    ortak = [(rid, c) for rid in shared for c in set(gold[rid]) & set(pred[rid])]
    duygu = (
        sum(1 for rid, c in ortak if gold[rid][c] == pred[rid][c]) / len(ortak) if ortak else 0.0
    )

    return {
        "kapsam": len(shared) / len(gold),
        "tam_eslesme": exact / len(shared),
        "jaccard": jac,
        "jaccard_icerikli": jac_icerikli,
        "duygu_uyumu": duygu,
        "karsilastirilan": float(len(shared)),
        "icerikli": float(len(icerikli)),
    }


CONTENT_SQL = "SELECT review_id, content FROM reviews WHERE review_id = ANY(%s::text[])"


def read_contents(review_ids: list[str]) -> dict[str, str]:
    if not review_ids:
        return {}
    with get_connection() as conn:
        rows = conn.execute(CONTENT_SQL, (review_ids,)).fetchall()
    return {row[0]: row[1] for row in rows}


def disagreements(gold: Labels, pred: Labels) -> list[tuple[str, set[str], set[str], str]]:
    ids = [rid for rid in gold if rid in pred and set(gold[rid]) != set(pred[rid])]
    contents = read_contents(ids)
    return [(rid, set(gold[rid]), set(pred[rid]), contents.get(rid, "")) for rid in ids]
