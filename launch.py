#!/usr/bin/env python3
"""
SV Studio — one-command launcher.

    python3 launch.py            # preflight every service, then boot the Studio
    python3 launch.py --check    # just run the checks and exit
    python3 launch.py --port 5000

Boots the dashboard no matter what: the pipeline degrades gracefully, so a
missing local service (VoxCPM, ComfyUI, ffmpeg, librosa, whisper) only loses
that one capability. The preflight prints exactly what to start for full power.
"""
import argparse
import importlib.util
import os
import shutil
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
G, Y, R, B, DIM, END = "\033[32m", "\033[33m", "\033[31m", "\033[36m", "\033[2m", "\033[0m"
OK, WARN, BAD = f"{G}✅{END}", f"{Y}⚠️ {END}", f"{R}❌{END}"


def _http_ok(url: str, timeout: float = 2.0) -> bool:
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except urllib.error.HTTPError:
        return True   # responded (even 4xx) ⇒ the server is up
    except Exception:  # noqa: BLE001
        return False


def _have_pkg(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def _ffmpeg() -> str:
    for c in ("/opt/homebrew/bin/ffmpeg", "/usr/bin/ffmpeg", "ffmpeg"):
        if shutil.which(c) or os.path.exists(c):
            return c
    return ""


def _port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


# ── checks ──────────────────────────────────────────────────────────────────
# each returns (label, state, detail, fix)  where state ∈ {ok, warn, bad}
def check_flask():
    ok = _have_pkg("flask")
    return ("Flask (dashboard)", "ok" if ok else "bad",
            "installed" if ok else "missing — required to run the Studio",
            "pip install flask")


def check_voxcpm():
    url = os.environ.get("VOXCPM_URL", "http://localhost:8808")
    ok = _http_ok(url + "/api/health")
    return ("VoxCPM (voice)", "ok" if ok else "warn",
            f"live at {url}" if ok else f"offline at {url} — voice steps will skip",
            "start your VoxCPM server on :8808")


def check_comfyui():
    url = os.environ.get("COMFYUI_URL", "http://localhost:8188")
    ok = _http_ok(url + "/system_stats")
    return ("ComfyUI (free clips)", "ok" if ok else "warn",
            f"live at {url}" if ok else f"offline at {url} — clip steps will skip",
            "launch ComfyUI on :8188 (set COMFYUI_URL to override)")


def check_workflows():
    wf = sorted(p.stem for p in (ROOT / "workflows").glob("*.json"))
    if wf:
        return ("ComfyUI workflows", "ok", "found: " + ", ".join(wf), "")
    return ("ComfyUI workflows", "warn",
            "none exported yet — clips can't render locally",
            "export one workflow per model to workflows/<model>.json (see workflows/README.md)")


def check_ffmpeg():
    f = _ffmpeg()
    return ("ffmpeg (assembly)", "ok" if f else "warn",
            f"found: {f}" if f else "not found — assembly/re-render will skip",
            "brew install ffmpeg   (mac)  /  apt install ffmpeg  (linux)")


def check_song_analysis():
    lib, whi = _have_pkg("librosa"), _have_pkg("whisper")
    if lib and whi:
        return ("Song analysis", "ok", "librosa + whisper ready (beat + lyrics)", "")
    miss = [n for n, ok in (("librosa", lib), ("whisper", whi)) if not ok]
    return ("Song analysis", "warn",
            f"missing {', '.join(miss)} — drop-a-song won't auto-detect "
            + ("lyrics" if miss == ["whisper"] else "beat/lyrics"),
            "pip install librosa openai-whisper")


CHECKS = [check_flask, check_voxcpm, check_comfyui, check_workflows,
          check_ffmpeg, check_song_analysis]


def preflight() -> bool:
    print(f"\n{B}{'='*58}{END}")
    print(f"{B}  SV STUDIO — preflight{END}")
    print(f"{B}{'='*58}{END}\n")
    required_ok = True
    icon = {"ok": OK, "warn": WARN, "bad": BAD}
    for fn in CHECKS:
        label, state, detail, fix = fn()
        if state == "bad":
            required_ok = False
        print(f"  {icon[state]} {label:22s} {DIM}{detail}{END}")
        if state != "ok" and fix:
            print(f"       {DIM}↳ {fix}{END}")

    live = sum(1 for fn in CHECKS if fn()[1] == "ok")
    print(f"\n  {live}/{len(CHECKS)} services live.", end=" ")
    if required_ok:
        print(f"{G}Everything missing degrades gracefully — the Studio still runs.{END}")
    else:
        print(f"{R}Flask is required. Install it, then re-run.{END}")
    print()
    return required_ok


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="launch.py", description="Boot the SV Studio.")
    ap.add_argument("--check", action="store_true", help="run preflight only, don't boot")
    ap.add_argument("--port", type=int, default=4444, help="dashboard port (default 4444)")
    args = ap.parse_args(argv)

    ready = preflight()
    if args.check:
        return 0 if ready else 1
    if not ready:
        return 1

    if not _port_free(args.port):
        print(f"  {WARN} Port {args.port} is already in use — "
              f"is the Studio already running? Try --port <other>.\n")
        return 1

    os.chdir(ROOT)
    import dashboard
    url = f"http://localhost:{args.port}"
    print(f"  {OK} Booting Studio → {B}{url}{END}\n")
    try:
        dashboard.app.run(host="0.0.0.0", port=args.port, debug=False)
    except KeyboardInterrupt:
        print(f"\n  {DIM}Studio stopped.{END}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
