import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['TIDYCORE_DATA_DIR'] = tempfile.mkdtemp(prefix='tidycore-tests-state-')
os.environ['TIDYCORE_TEST_MODE'] = '1'
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
