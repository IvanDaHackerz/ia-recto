"""Validate future independent intake without opening a final model evaluation."""
import argparse
from pathlib import Path
from evaluation_common import ROOT, rows, save, sha
from validate_independent_gold import validate


def check(path):
    intake = rows(path)
    known = []
    for folder in [ROOT / 'dataset/processed/item9', ROOT / 'dataset/processed/item10']:
        for source in folder.rglob('*.jsonl'):
            if source.resolve() == Path(path).resolve(): continue
            known.extend(r['question_text'] for r in rows(source) if r.get('question_text'))
    from create_cases import create
    known.extend(c['question_text'] for c in create())
    result = validate(intake, known)
    result.update(input_sha256=sha(path), final_evaluation_executed=False,
        source_support_review_and_final_protocol_still_required=True)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists(): raise ValueError('Use a new intake report file')
    result = check(args.input); save(args.output, result)
    print(__import__('json').dumps({'passed': result['passed'], 'rows': result['rows'], 'final_evaluation_executed': False}))
    raise SystemExit(0 if result['passed'] else 1)
