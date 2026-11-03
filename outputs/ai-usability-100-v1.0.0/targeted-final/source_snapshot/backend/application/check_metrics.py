"""Export the public synthetic evaluation projection for the frontend reconciliation test."""
import json
from .performance import ROOT, performance_report


def main():
    target = ROOT / "tmp/website-integration-performance.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(performance_report(), ensure_ascii=False), encoding="utf-8")
    print("Saved synthetic development metrics projection for the frontend reconciliation check.")


if __name__ == "__main__":
    main()
