"""Rerun legacy validators while redirecting their reports out of frozen data."""
import contextlib
import importlib.util
import io
import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'dataset/pipelines/item7/vendor'))
original_write = Path.write_text
results = {}
for item in (7, 8, 9):
    source = ROOT / f'dataset/pipelines/item{item}/validate_item{item}.py'
    spec = importlib.util.spec_from_file_location(f'foundation_item{item}', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    frozen_report = ROOT / f'dataset/processed/item{item}/validation_report.json'
    report = OUT / f'item{item}_validation.json'

    def redirect(path, value, *args, **kwargs):
        if path.resolve() != frozen_report.resolve():
            raise ValueError('Unexpected validator write: ' + str(path))
        return original_write(report, value, *args, **kwargs)

    argv = [str(source)]
    if item == 7:
        argv += ['--project-root', str(ROOT), '--output-dir', str(ROOT / 'dataset/processed/item7')]
    if item == 8:
        argv += ['--dataset-root', str(ROOT / 'dataset')]
    stream = io.StringIO()
    with patch.object(sys, 'argv', argv), patch.object(Path, 'write_text', redirect), contextlib.redirect_stdout(stream):
        try:
            code = module.main() or 0
        except SystemExit as error:
            code = error.code
    original_write(OUT / f'item{item}_validation.log', stream.getvalue(), encoding='utf-8')
    value = json.loads(report.read_text(encoding='utf-8'))
    results[str(item)] = {'exit_code': code, 'passed': code == 0 and not value.get('errors'),
                          'errors': value.get('errors', []), 'report': report.name}
original_write(OUT / 'foundation_checks.json', json.dumps(results, indent=2) + '\n', encoding='utf-8')
print(json.dumps(results, indent=2))
raise SystemExit(0 if all(r['passed'] for r in results.values()) else 1)
