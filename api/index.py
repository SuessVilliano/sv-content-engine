"""
Vercel serverless entrypoint for the SV Content Engine dashboard.

Vercel's Python runtime serves any module-level WSGI application named `app`,
so we just import the Flask app from the repo root. Heavy generation (VoxCPM,
ComfyUI, ffmpeg) lives on local services and is unavailable in serverless —
the dashboard degrades gracefully and still serves the full UI + read APIs.
"""
import os
import sys

# Make the repo-root modules (dashboard, brands, engine, …) importable, and
# point every data folder at the bundled repo instead of a machine-specific
# absolute path so the hosted dashboard shows the real scripts/content.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("SV_BASE_DIR", ROOT)

from dashboard import app  # noqa: E402  (WSGI app Vercel serves)
