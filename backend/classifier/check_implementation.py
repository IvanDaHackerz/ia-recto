"""Save API software checks without running a performance evaluation."""
from __future__ import annotations
import argparse
import io
import json
from pathlib import Path
import unittest


def check(output):
    output=Path(output)
    log=output/'api_software_tests.log'
    summary=output/'api_software_tests.json'
    if log.exists() or summary.exists():raise ValueError('Use a new check directory')
    output.mkdir(parents=True,exist_ok=True)
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromName('backend.classifier.test_service'))
    log.write_text(stream.getvalue(),encoding='utf-8')
    value={'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'skipped':len(result.skipped),'passed':result.wasSuccessful(),
        'loopback_http_exercised':True,'formal_evaluation':False,'accuracy_f1_calibration_metrics_produced':False}
    summary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(value,indent=2))
    return result.wasSuccessful()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    raise SystemExit(0 if check(args.output) else 1)
