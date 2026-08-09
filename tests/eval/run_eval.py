import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from domain.services.anonymizer_service import AnonymizerService
from infrastructure.detectors.bank_account_detector import BankAccountDetector
from infrastructure.detectors.date_detector import DateDetector
from infrastructure.detectors.email_detector import EmailDetector
from infrastructure.detectors.pesel_detector import PeselDetector
from infrastructure.detectors.phone_detector import PhoneDetector
from infrastructure.detectors.spacy.detector import SpacyPIIDetector

DEFAULT_DATASET = Path(__file__).parent / "dataset.json"


def build_service() -> AnonymizerService:
    detectors = [
        SpacyPIIDetector(),
        EmailDetector(),
        PhoneDetector(),
        PeselDetector(),
        BankAccountDetector(),
        DateDetector(),
    ]
    return AnonymizerService(detectors)


def load_dataset(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate(service: AnonymizerService, examples: list[dict], category: str | None):
    per_type = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    failures = []

    for ex in examples:
        if category and ex.get("category") != category:
            continue

        gold = {(e["type"], e["value"]) for e in ex["entities"]}
        _, mapping = service.anonymize(ex["text"])
        predicted = {(t.type.name, t.original_value) for t in mapping.values()}

        tp, fp, fn = gold & predicted, predicted - gold, gold - predicted

        for t, _ in tp:
            per_type[t]["tp"] += 1
        for t, _ in fp:
            per_type[t]["fp"] += 1
        for t, _ in fn:
            per_type[t]["fn"] += 1

        if fp or fn:
            failures.append(
                {
                    "id": ex.get("id"),
                    "category": ex.get("category"),
                    "text": ex["text"],
                    "missed": sorted(fn),
                    "spurious": sorted(fp),
                }
            )

    return per_type, failures


def _prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f1


def print_report(per_type: dict, failures: list[dict], verbose: bool) -> None:
    total_tp = total_fp = total_fn = 0
    print(f"{'TYPE':<14}{'P':>8}{'R':>8}{'F1':>8}{'TP':>6}{'FP':>6}{'FN':>6}")
    for t in sorted(per_type):
        s = per_type[t]
        tp, fp, fn = s["tp"], s["fp"], s["fn"]
        total_tp += tp
        total_fp += fp
        total_fn += fn
        p, r, f1 = _prf(tp, fp, fn)
        print(f"{t:<14}{p:>8.2%}{r:>8.2%}{f1:>8.2%}{tp:>6}{fp:>6}{fn:>6}")

    p, r, f1 = _prf(total_tp, total_fp, total_fn)
    print("-" * 56)
    print(f"{'OVERALL':<14}{p:>8.2%}{r:>8.2%}{f1:>8.2%}{total_tp:>6}{total_fp:>6}{total_fn:>6}")

    if verbose and failures:
        print("\nFailures:")
        for f in failures:
            print(f"\n[{f['id']}] ({f['category']}) {f['text']!r}")
            if f["missed"]:
                print(f"  missed:   {f['missed']}")
            if f["spurious"]:
                print(f"  spurious: {f['spurious']}")


def main() -> None:
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET, help="Path to the eval dataset JSON file.")
    parser.add_argument("--category", type=str, default=None, help="Only run examples with this category.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print per-example misses/false positives.")
    args = parser.parse_args()

    examples = load_dataset(args.dataset)
    service = build_service()
    per_type, failures = evaluate(service, examples, args.category)
    print_report(per_type, failures, args.verbose)


if __name__ == "__main__":
    main()
