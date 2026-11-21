import os
import subprocess
import sys

import pytest

from config import APP_DIR

# Mỗi lệnh đều in tiếng Việt ra stdout/stderr mà không cần kết nối Cassandra thật
CASES = [
    ["-m", "tools.check_env"],
    ["-m", "tools.seed", "--keyspace", "ride_booking_test"],  # thiếu --yes: in "Từ chối" ra stderr
    ["-m", "tools.setup_db", "--keyspace", "ride_booking_test", "--seed"],  # thiếu --yes
]


@pytest.mark.parametrize("args", CASES, ids=["check_env", "seed", "setup_db"])
def test_cli_prints_vietnamese_on_cp1252_console(args):
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONUTF8", "PYTHONIOENCODING")}
    env.update(PYTHONIOENCODING="cp1252", CASSANDRA_HOSTS="127.0.0.1", CASSANDRA_PORT="1")
    p = subprocess.run(
        [sys.executable, *args], cwd=APP_DIR, env=env, capture_output=True, timeout=60
    )
    err = p.stderr.decode("utf-8", errors="replace")
    assert "UnicodeEncodeError" not in err, err
    assert p.returncode in (1, 2), (p.returncode, err)
    # ký tự tiếng Việt phải ra được dưới dạng UTF-8
    assert "ừ".encode("utf-8") in (p.stdout + p.stderr) or "á".encode("utf-8") in (p.stdout + p.stderr)
