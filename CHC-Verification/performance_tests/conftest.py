import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

def pytest_configure(config):
    csv_path = os.path.join(_THIS_DIR, "perf_results.csv")
    if os.path.exists(csv_path):
        os.remove(csv_path)
