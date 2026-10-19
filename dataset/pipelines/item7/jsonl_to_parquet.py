"""Create Pandas-friendly Parquet mirrors of the validated JSONL outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    out = Path(args.output_dir)
    for stem in ("documents", "provisions", "retrieval_chunks"):
        rows = [json.loads(line) for line in (out / f"{stem}.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        # Nested/list values remain losslessly represented as JSON strings in this flat analytical mirror.
        flat = []
        for row in rows:
            flat.append({key: json.dumps(value, ensure_ascii=False, separators=(",", ":")) if isinstance(value, (list, dict)) else value for key, value in row.items()})
        pd.DataFrame(flat).to_parquet(out / f"{stem}.parquet", index=False)
        print(f"Wrote {stem}.parquet ({len(flat)} rows)")


if __name__ == "__main__":
    main()
