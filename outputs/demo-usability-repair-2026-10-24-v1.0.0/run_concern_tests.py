import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
from test_concern_repairs import ConcernRepairTests
ConcernRepairTests.RUN=ROOT/(sys.argv[1] if len(sys.argv)>1 else 'outputs/item10-classifier-v1.5.56')
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ConcernRepairTests))
sys.exit(not result.wasSuccessful())
