"""launch.py — preflight checks and helpers."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import launch  # noqa: E402


def test_flask_check_passes():
    label, state, _detail, _fix = launch.check_flask()
    assert state == "ok"


def test_offline_services_warn_not_fatal():
    # VoxCPM/ComfyUI aren't running in CI → warn (graceful), never bad
    for fn in (launch.check_voxcpm, launch.check_comfyui):
        assert fn()[1] in ("ok", "warn")


def test_http_ok_false_for_dead_port():
    assert launch._http_ok("http://127.0.0.1:59999/nope", timeout=0.5) is False


def test_every_check_returns_four_fields():
    for fn in launch.CHECKS:
        label, state, detail, fix = fn()
        assert state in ("ok", "warn", "bad")
        assert isinstance(label, str) and isinstance(detail, str)


def test_preflight_ready_when_flask_present():
    assert launch.preflight() is True   # flask is installed in the test env
