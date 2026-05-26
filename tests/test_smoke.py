"""Smoke headless do site (pula se Playwright/Chromium ausente)."""
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_headless_render():
    pytest.importorskip("playwright", reason="Playwright não instalado")
    driver = os.path.join(ROOT, ".claude", "skills", "run-scisci-ipea", "driver.py")
    r = subprocess.run([sys.executable, driver, "--build", "--shot", "/tmp/pytest_site.png"],
                       capture_output=True, text=True, timeout=180)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "STATUS: OK" in r.stdout, r.stdout + r.stderr
