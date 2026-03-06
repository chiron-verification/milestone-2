#!/usr/bin/env python3
"""
Test runner for the CHC verification test suite.

Usage:
    python run_all.py                      # run everything
    python run_all.py -v                   # verbose
    python run_all.py -k trig              # only trig tests  (Python 3.12+)
    python run_all.py default.test_default # run one module
"""

import sys
import os
import unittest

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=os.path.dirname(os.path.abspath(__file__)),
        pattern="test_*.py",
    )
    runner = unittest.TextTestRunner(verbosity=2 if "-v" in sys.argv else 1)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
