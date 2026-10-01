"""Wrapper pytest del selftest (la logica vive en src/imgops/selftest.py)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from imgops.selftest import CHECKS, run  # noqa: E402


def test_selftest_all_pass():
    rec = run()
    fails = [c for c in rec["checks"] if c["status"] != "PASS"]
    assert not fails, fails
    assert rec["passed"] == rec["total"] == len(CHECKS)
