"""dashboard.py — security-critical routes: path traversal, auth, uploads."""
import importlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import dashboard  # noqa: E402


def test_safe_path_blocks_traversal(tmp_path):
    (tmp_path / "ok.mp4").write_text("x")
    assert dashboard._safe_path(str(tmp_path), "ok.mp4")
    assert dashboard._safe_path(str(tmp_path), "../../etc/passwd") is None
    assert dashboard._safe_path(str(tmp_path), "a/../../b") is None


def test_safe_path_allows_nested(tmp_path):
    (tmp_path / "sub").mkdir()
    assert dashboard._safe_path(str(tmp_path), "sub", "f.mp4")


def test_broll_route_rejects_traversal():
    c = dashboard.app.test_client()
    r = c.get("/stream/broll/../../../../etc/passwd")
    assert r.status_code == 404


def test_upload_song_rejects_non_audio():
    c = dashboard.app.test_client()
    r = c.post("/api/upload-song",
               data={"song": (io.BytesIO(b"x"), "evil.txt")},
               content_type="multipart/form-data")
    assert r.get_json()["error"] == "not an audio file"


def test_looks_route():
    c = dashboard.app.test_client()
    d = c.get("/api/looks").get_json()
    assert "neon" in d["looks"] and "downbeat" in d["cuts"]


def test_auth_enforced_when_token_set(monkeypatch):
    # turn auth on, rebuild the test client
    monkeypatch.setattr(dashboard, "SV_TOKEN", "secret123")
    c = dashboard.app.test_client()
    assert c.get("/api/looks").status_code == 401
    assert c.get("/api/looks", headers={"X-SV-Token": "secret123"}).status_code == 200
    assert c.get("/api/looks?token=secret123").status_code == 200


def test_no_auth_when_token_absent(monkeypatch):
    monkeypatch.setattr(dashboard, "SV_TOKEN", "")
    c = dashboard.app.test_client()
    assert c.get("/api/looks").status_code == 200
