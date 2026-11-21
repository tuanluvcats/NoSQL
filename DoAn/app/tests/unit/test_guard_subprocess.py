import os
import subprocess
import sys

from config import APP_DIR


def test_integration_refuses_non_test_keyspace():
    p = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/integration/test_fixture_smoke.py", "-q", "-p", "no:cacheprovider"],
        cwd=APP_DIR,
        env={**os.environ, "CASSANDRA_TEST_KEYSPACE": "ride_booking"},
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = p.stdout + p.stderr
    assert p.returncode == 4, out
    assert "ride_booking" in out and "_test" in out
