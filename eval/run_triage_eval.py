"""Triage eval: real API, cached. Run: uv run python -m eval.run_triage_eval [data/triage_set.jsonl]"""
import json
import sys
from pathlib import Path

from core.triage import triage


def metrics(gold: list[dict], pred: list[dict]) -> dict:
    cats = sorted({g["category"] for g in gold} | {p["category"] for p in pred})
    per = {}
    for c in cats:
        tp = sum(g["category"] == c and p["category"] == c for g, p in zip(gold, pred))
        fp = sum(g["category"] != c and p["category"] == c for g, p in zip(gold, pred))
        fn = sum(g["category"] == c and p["category"] != c for g, p in zip(gold, pred))
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        per[c] = {"precision": prec, "recall": rec, "f1": f1, "support": tp + fn}
    emerg = [(g, p) for g, p in zip(gold, pred) if g["urgency"] == "emergency"]
    supported = [v for v in per.values() if v["support"]]
    return {
        "per_category": per,
        "macro_f1": sum(v["f1"] for v in supported) / max(1, len(supported)),
        "urgency_accuracy": sum(g["urgency"] == p["urgency"] for g, p in zip(gold, pred)) / len(gold),
        "emergency_recall": (sum(p["urgency"] == "emergency" for _, p in emerg) / len(emerg)) if emerg else None,
    }


def main(path="data/triage_set.jsonl"):
    items = [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
    preds = []
    for it in items:
        img = Path(it["image"]).read_bytes() if it.get("image") else None
        r = triage(it["text"], img)
        preds.append({"category": r.category, "urgency": r.urgency})
        flag = "" if (r.category, r.urgency) == (it["category"], it["urgency"]) else f"  <-- gold {it['category']}/{it['urgency']}"
        print(f"{r.category:12} {r.urgency:10} {it['text'][:60]}{flag}")
    mt = metrics(items, preds)
    print("\nper category (P / R / F1 / n)")
    for c, v in mt["per_category"].items():
        print(f"  {c:12} {v['precision']:.2f} {v['recall']:.2f} {v['f1']:.2f} {v['support']}")
    print(f"\nmacro-F1 {mt['macro_f1']:.3f}  (target >= 0.85)")
    print(f"urgency accuracy {mt['urgency_accuracy']:.3f}")
    print(f"emergency recall {mt['emergency_recall']}  (target = 1.0)")


if __name__ == "__main__":
    main(*sys.argv[1:])
