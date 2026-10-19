"""Render the four image-only canonical PDFs into OCR-ready page images."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path

from PIL import Image
from pypdf import PdfReader


OCR_DOCUMENTS = {"DOLE_LA_06_20", "DOLE_LA_16_25", "DTI_DAO_02_1993", "DTI_DAO_20_02"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--pdftoppm", required=True)
    parser.add_argument("--work-dir", required=True)
    args = parser.parse_args()

    root = Path(args.project_root)
    work = Path(args.work_dir)
    images = work / "images"
    images.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "dataset/canonical_sources/manifests/canonical_documents.csv"
    rows = list(csv.DictReader(manifest_path.open(encoding="utf-8-sig", newline="")))
    jobs: list[dict] = []

    for row in rows:
        doc_id = row["document_id"]
        if doc_id not in OCR_DOCUMENTS:
            continue
        pdf = root / "dataset/canonical_sources" / row["local_path"]
        page_count = len(PdfReader(str(pdf)).pages)
        doc_dir = images / doc_id
        doc_dir.mkdir(exist_ok=True)
        for page_no in range(1, page_count + 1):
            prefix = doc_dir / f"pdf_{page_no:04d}"
            png = prefix.with_suffix(".png")
            subprocess.run(
                [args.pdftoppm, "-f", str(page_no), "-l", str(page_no), "-r", "200", "-png", "-singlefile", str(pdf), str(prefix)],
                check=True,
                stdout=subprocess.DEVNULL,
            )
            if doc_id == "DTI_DAO_02_1993":
                with Image.open(png) as source:
                    rotated = source.rotate(90, expand=True)
                    midpoint = rotated.width // 2
                    halves = [rotated.crop((0, 0, midpoint, rotated.height)), rotated.crop((midpoint, 0, rotated.width, rotated.height))]
                    for half_index, half in enumerate(halves, start=1):
                        out = doc_dir / f"pdf_{page_no:04d}_printed_{half_index}.png"
                        half.save(out, optimize=True)
                        jobs.append({
                            "document_id": doc_id,
                            "pdf_page": page_no,
                            "printed_page": (page_no - 1) * 2 + half_index + 1,
                            "image_path": str(out),
                            "rotation_degrees_clockwise": 270,
                            "page_segment": half_index,
                        })
                png.unlink()
            else:
                jobs.append({
                    "document_id": doc_id,
                    "pdf_page": page_no,
                    "printed_page": None,
                    "image_path": str(png),
                    "rotation_degrees_clockwise": 0,
                    "page_segment": 1,
                })

    output = work / "ocr_manifest.json"
    output.write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Prepared {len(jobs)} OCR images from {len(OCR_DOCUMENTS)} documents: {output}")


if __name__ == "__main__":
    main()
