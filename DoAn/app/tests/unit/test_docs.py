"""Tài liệu (README, kịch bản demo, HANDOFF, CASSANDRA.MD §11) phải có đủ mục và khớp với mã thật."""
import re
from pathlib import Path

import pytest

from db import capabilities
from main import create_app

APP_DIR = Path(__file__).resolve().parents[2]  # DoAn/app
REPO_DIR = APP_DIR.parents[1]  # gốc repo
README = APP_DIR / "README.md"
DEMO = APP_DIR / "docs" / "kich_ban_demo.md"
HANDOFF = REPO_DIR / "HANDOFF.md"
CASSANDRA_MD = REPO_DIR / "DoAn" / "CASSANDRA.MD"


def _read(path: Path) -> str:
    assert path.is_file(), f"Thiếu file {path}"
    return path.read_text(encoding="utf-8")


def _section(text: str, start_heading: str, end_heading: str | None = None) -> str:
    """Nội dung từ start_heading đến end_heading (hoặc tiêu đề `## ` kế tiếp, hoặc hết file)."""
    start = text.index(start_heading)
    if end_heading is None:
        nxt = text.find("\n## ", start + len(start_heading))
        return text[start:] if nxt == -1 else text[start:nxt]
    return text[start:text.index(end_heading, start)]


def test_readme_has_required_headings():
    text = _read(README)
    for heading in ("## Cài đặt", "## Chuẩn bị CSDL", "## Tài khoản đăng nhập thử", "## Chạy test tự động",
                    "## Đối chiếu barem chấm điểm", "## Khác biệt so với 05_transactions.cql",
                    "## Thay đổi schema: 06_app_migration.cql", "## Giới hạn đã biết"):
        assert re.search(rf"^{re.escape(heading)}\s*$", text, re.M), heading


def test_readme_has_demo_accounts_plates_test_keyspace_and_markers():
    text = _read(README)
    for needle in ("drv551", "51K-567.89", "ride_booking_test", "dieuphoi", "cust010"):
        assert needle in text, needle
    for marker in ("auth", "crud", "business", "backup", "nosql"):
        assert f"-m {marker}" in text, marker


def test_readme_documents_environment_and_primary_install_path():
    text = _read(README)
    for var in ("CASSANDRA_HOSTS", "CASSANDRA_PORT", "CASSANDRA_KEYSPACE", "CASSANDRA_LOCAL_DC", "$env:CASSANDRA_KEYSPACE"):
        assert var in text, var
    for needle in ("3.11.4", "python -m tools.check_env", "python -m tools.setup_db --keyspace ride_booking --seed --yes",
                   "python -m tools.migrate --keyspace ride_booking", "uvicorn main:app"):
        assert needle in text, needle


def test_readme_lists_known_limitations_recorded_across_tasks():
    text = _read(README)
    limits = _section(text, "## Giới hạn đã biết")
    for needle in ("không nguyên tử", "BUSY", "WriteTimeout", "admin cuối", "biển số", "phi chuẩn hóa", "rated_at",
                   "quét toàn bảng", "bộ nhớ", "password_hash", "_prerestore.json", "CSRF", "SameSite", "2026-12-31",
                   "SHA-256", "PBKDF2", "release_version", "Bootstrap"):
        assert needle in limits, needle


def test_readme_documents_app_debug_and_hidden_500_page():
    text = _read(README)
    assert "APP_DEBUG" in text.split("## Chạy test tự động")[0]  # có trong bảng biến môi trường
    security = _section(text, "**Bảo mật**", "**Dữ liệu mẫu và môi trường**")
    assert "APP_DEBUG" in security and "log" in security
    assert "vẫn in loại lỗi" not in text  # giới hạn cũ đã được sửa


def test_handoff_no_longer_lists_fixed_500_leak():
    assert "Trang lỗi 500 vẫn in" not in _read(HANDOFF)


def test_demo_script_covers_scenarios():
    text = _read(DEMO)
    for needle in ("T05", "9.4", "9.1", "9.2", "9.3", "[applied]", "DbSchema", "ALLOW FILTERING",
                   "might involve data filtering", "Backup", "partition key"):
        assert needle in text, needle


def test_handoff_is_at_repo_root_and_records_probe():
    text = _read(HANDOFF)
    assert "capabilities" in text
    assert capabilities.PROBED_ON in text
    for flag in ("TRUNCATE_CLEARS_MV", "LWT_IF_IN_SUPPORTED", "LWT_ON_MV_BASE_OK", "JSON_ROUNDTRIP_OK"):
        assert flag in text, flag


def test_cassandra_md_section_11_matches_real_app():
    text = _read(CASSANDRA_MD)
    assert "tools.setup_db" in text
    s11 = _section(text, "## 11. Kết nối từ ứng dụng", "## 12.")
    for needle in ("DoAn/app", "tools.check_env", "JSON"):
        assert needle in s11, needle
    assert "backup_snapshot.sh" not in s11  # không còn gợi ý docker exec làm cách backup chính


@pytest.mark.parametrize("path", [README, HANDOFF, CASSANDRA_MD], ids=lambda p: p.name)
def test_every_tools_command_in_docs_exists(path):
    modules = set(re.findall(r"python -m tools\.(\w+)", _read(path)))
    for m in modules:
        assert (APP_DIR / "tools" / f"{m}.py").is_file(), f"{path.name}: tools.{m} không tồn tại"


def _real_routes():
    """Regex của mọi route thật (lấy từ OpenAPI vì FastAPI mới bọc router con nên app.routes không liệt kê phẳng)."""
    app = create_app(db=object())  # không chạy lifespan nên không kết nối Cassandra
    out = []
    for template in app.openapi()["paths"]:
        parts = re.split(r"\{[^}]+\}", template)
        out.append(re.compile("^" + "[^/]+".join(re.escape(x) for x in parts) + "$"))
    return out


@pytest.mark.parametrize("path", [README, DEMO, HANDOFF], ids=lambda p: p.name)
def test_every_route_path_in_docs_is_real(path):
    routes = _real_routes()
    paths = set(re.findall(r"`(/[a-z][A-Za-z0-9_\-./{}]*)(?:\?[^`]*)?`", _read(path)))
    assert paths, f"{path.name} không nhắc route nào"
    for p in paths:
        probe = re.sub(r"\{[^}]+\}", "x", p)
        assert any(r.match(probe) for r in routes), f"{path.name}: route không có thật: {p}"
