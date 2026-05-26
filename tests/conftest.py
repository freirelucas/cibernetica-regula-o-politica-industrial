import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))


@pytest.fixture(scope="session")
def root():
    return ROOT


@pytest.fixture(scope="session")
def results():
    with open(os.path.join(ROOT, "data", "scisci_results.json"), encoding="utf-8") as f:
        return json.load(f)
