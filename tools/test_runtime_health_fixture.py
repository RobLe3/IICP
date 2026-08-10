import subprocess
import sys
import unittest
from pathlib import Path


class RuntimeHealthFixtureTest(unittest.TestCase):
    def test_runtime_health_fixture(self) -> None:
        root = Path(__file__).resolve().parents[1]
        subprocess.run(
            [sys.executable, str(root / "tools/check_runtime_health_fixture.py")],
            cwd=root,
            check=True,
        )


if __name__ == "__main__":
    unittest.main()
