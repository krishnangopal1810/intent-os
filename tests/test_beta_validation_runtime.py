import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/product"))

from beta_validation.runtime import acquire_lock  # noqa: E402


class BetaValidationRuntimeTests(unittest.TestCase):
    def test_acquire_lock_replaces_corrupt_pid_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock_dir = Path(tmp) / "beta-validation.lock"
            lock_dir.mkdir()
            (lock_dir / "pid").write_text("not-a-pid\n", encoding="utf-8")

            acquire_lock(lock_dir)

            self.assertEqual((lock_dir / "pid").read_text(encoding="utf-8").strip(), str(os.getpid()))
