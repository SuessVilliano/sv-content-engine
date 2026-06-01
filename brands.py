#!/usr/bin/env python3
"""
SV Content Engine — Multi-Brand / Multi-Persona Config Layer
============================================================

One engine, many brands. Each brand is a JSON file in ./brands/ that holds
everything that used to be hardcoded for the single "Source Vessel" persona:
its folders, its voice, its avatar, its content pillars, its hashtags, its
distribution accounts, and its generation routing (free-local vs paid-hero).

This means the SAME engine (generate_90days.py + dashboard.py) can drive:
  - your music     -> brand type "music"     (songs -> beat-synced videos)
  - each business  -> brand type "business"  (UGC ads, talking head + product)
  - each avatar    -> brand type "persona"   (a consistent face that posts daily)

Design goals:
  - Stdlib only. No pip installs. Runs anywhere Python 3.8+ runs.
  - Backward compatible. If ./brands/ is missing, callers fall back to their
    old hardcoded defaults, so nothing that works today breaks.
  - Secrets stay in env vars, never in the committed JSON. A config value of
    "env:FAL_API_KEY" is resolved from os.environ at load time.

CLI:
    python3 brands.py list           # list configured brands
    python3 brands.py show <id>      # print one brand, fully resolved
    python3 brands.py active         # print the currently active brand id
    python3 brands.py validate       # check every brand file for problems
    python3 brands.py paths <id>     # print resolved folder paths for a brand
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# Directory that holds the per-brand JSON files (next to this module).
BRANDS_DIR = Path(__file__).resolve().parent / "brands"

# A pointer file lets you set the active brand without env vars:
#   brands/_active.json  ->  {"active": "source_vessel"}
ACTIVE_POINTER = BRANDS_DIR / "_active.json"

# Env var wins over the pointer file when both are present.
ACTIVE_ENV = "SV_BRAND"


# ──────────────────────────────────────────────────────────────────────────
# Secret resolution
# ──────────────────────────────────────────────────────────────────────────
def _resolve_secret(value: Any) -> Any:
    """Resolve "env:NAME" references against the environment.

    Keeps API keys OUT of committed JSON. A missing env var resolves to "" so
    the engine can detect "not configured" without crashing.
    """
    if isinstance(value, str) and value.startswith("env:"):
        return os.environ.get(value[4:], "")
    if isinstance(value, dict):
        return {k: _resolve_secret(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_secret(v) for v in value]
    return value


# ──────────────────────────────────────────────────────────────────────────
# Brand model
# ──────────────────────────────────────────────────────────────────────────
@dataclass
class Brand:
    """A single brand / persona / channel the engine can produce for."""

    id: str
    raw: Dict[str, Any]

    # ---- identity --------------------------------------------------------
    @property
    def name(self) -> str:
        return self.raw.get("name", self.id)

    @property
    def type(self) -> str:
        # persona | music | business
        return self.raw.get("type", "persona")

    @property
    def goal(self) -> str:
        # following | music_videos | ugc_ads
        return self.raw.get("goal", "following")

    # ---- filesystem ------------------------------------------------------
    @property
    def base_dir(self) -> Path:
        return Path(os.path.expanduser(self.raw.get("base_dir", "."))).resolve()

    def folder(self, key: str) -> Path:
        """Resolve a named output folder, with sensible defaults.

        Override any of these per-brand under "folders": {...} in the JSON.
        """
        defaults = {
            "scripts": "scripts",
            "voice": "voice",
            "beats": "assets/music",
            "drafts": "drafts",
            "broll": "broll_library",
            "masters": "masters",
            "shorts": "shorts_reels",
            "approved": "approved",
            "scheduled": "scheduled",
            "posted": "posted",
            "assets": "assets",
        }
        rel = self.raw.get("folders", {}).get(key, defaults.get(key, key))
        return self.base_dir / rel

    def ensure_folders(self) -> None:
        for key in ("scripts", "voice", "drafts", "broll", "masters",
                    "shorts", "approved", "scheduled", "posted"):
            self.folder(key).mkdir(parents=True, exist_ok=True)

    # ---- voice -----------------------------------------------------------
    @property
    def voice(self) -> Dict[str, Any]:
        v = dict(self.raw.get("voice", {}))
        v.setdefault("engine", "voxcpm")
        v.setdefault("api_url", "http://localhost:8808/api/clone")
        return _resolve_secret(v)

    def voice_reference(self) -> str:
        """Best available reference audio, falling back if the primary is gone."""
        v = self.voice
        primary = os.path.expanduser(v.get("reference_audio", ""))
        fallback = os.path.expanduser(v.get("fallback_reference", ""))
        if primary and os.path.exists(primary):
            return primary
        return fallback or primary

    @property
    def voice_style_rules(self) -> List[str]:
        return self.raw.get("voice", {}).get("style_rules", [])

    # ---- avatar ----------------------------------------------------------
    @property
    def avatar(self) -> Dict[str, Any]:
        a = dict(self.raw.get("avatar", {}))
        # heygem (free/local) | hedra | heygen
        a.setdefault("engine", "heygem")
        return _resolve_secret(a)

    # ---- content ---------------------------------------------------------
    @property
    def pillars(self) -> List[Dict[str, Any]]:
        return self.raw.get("pillars", [])

    @property
    def hashtags(self) -> str:
        return self.raw.get("hashtags", "")

    @property
    def signoff(self) -> str:
        return self.raw.get("signoff", "")

    @property
    def brand_voice(self) -> Dict[str, Any]:
        return self.raw.get("brand_voice", {})

    # ---- generation routing (sets up the cost router) --------------------
    @property
    def generation(self) -> Dict[str, Any]:
        g = dict(self.raw.get("generation", {}))
        # local-first by default; this is the knob that controls spend.
        g.setdefault("default_route", "local")
        g.setdefault("text_to_video", {"local": "ltx-video", "hero": "veo-3.1"})
        g.setdefault("image_to_video", {"local": "wan2.2", "hero": "kling-2.0"})
        g.setdefault("music_video", {"local": "ltx-2.3-audio", "hero": "freebeat"})
        return g

    def route_for(self, kind: str, hero: bool = False) -> str:
        """Pick the model for a generation request.

        kind: text_to_video | image_to_video | music_video
        hero: True for the rare flawless shot that justifies a paid API.
        """
        spec = self.generation.get(kind, {})
        if hero or self.generation.get("default_route") == "api":
            return spec.get("hero", spec.get("local", ""))
        return spec.get("local", spec.get("hero", ""))

    # ---- distribution ----------------------------------------------------
    @property
    def distribution(self) -> Dict[str, Any]:
        return _resolve_secret(self.raw.get("distribution", {}))

    # ---- serialization ---------------------------------------------------
    def resolved(self) -> Dict[str, Any]:
        """Full brand dict with secrets resolved — for debugging/inspection."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "goal": self.goal,
            "base_dir": str(self.base_dir),
            "voice": self.voice,
            "avatar": self.avatar,
            "pillars": self.pillars,
            "hashtags": self.hashtags,
            "signoff": self.signoff,
            "brand_voice": self.brand_voice,
            "generation": self.generation,
            "distribution": self.distribution,
            "folders": {k: str(self.folder(k)) for k in (
                "scripts", "voice", "beats", "drafts", "broll",
                "masters", "shorts", "approved", "scheduled", "posted")},
        }


# ──────────────────────────────────────────────────────────────────────────
# Loading
# ──────────────────────────────────────────────────────────────────────────
def _brand_files() -> List[Path]:
    if not BRANDS_DIR.exists():
        return []
    out = []
    for p in sorted(BRANDS_DIR.glob("*.json")):
        # skip pointer files (_active.json) and templates (*.template.json)
        if p.name.startswith("_") or p.name.endswith(".template.json"):
            continue
        out.append(p)
    return out


def list_brand_ids() -> List[str]:
    return [p.stem for p in _brand_files()]


def load_brand(brand_id: str) -> Brand:
    path = BRANDS_DIR / f"{brand_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"No brand config: {path}")
    with open(path) as f:
        raw = json.load(f)
    raw.setdefault("id", brand_id)
    return Brand(id=brand_id, raw=raw)


def active_brand_id() -> Optional[str]:
    """Env var -> pointer file -> first brand on disk -> None."""
    env = os.environ.get(ACTIVE_ENV)
    if env:
        return env
    if ACTIVE_POINTER.exists():
        try:
            with open(ACTIVE_POINTER) as f:
                pid = json.load(f).get("active")
                if pid:
                    return pid
        except (json.JSONDecodeError, OSError):
            pass
    ids = list_brand_ids()
    return ids[0] if ids else None


def active_brand() -> Optional[Brand]:
    """The brand the engine should produce for right now, or None if unconfigured.

    Callers should treat None as 'use my legacy hardcoded defaults' so the
    engine keeps working before any brand files exist.
    """
    bid = active_brand_id()
    if not bid:
        return None
    try:
        return load_brand(bid)
    except FileNotFoundError:
        return None


def set_active(brand_id: str) -> None:
    BRANDS_DIR.mkdir(parents=True, exist_ok=True)
    with open(ACTIVE_POINTER, "w") as f:
        json.dump({"active": brand_id}, f, indent=2)


# ──────────────────────────────────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────────────────────────────────
def validate_brand(b: Brand) -> List[str]:
    problems: List[str] = []
    if not b.raw.get("name"):
        problems.append("missing 'name'")
    if b.type not in ("persona", "music", "business"):
        problems.append(f"unknown type '{b.type}' (expected persona|music|business)")
    if not b.raw.get("base_dir"):
        problems.append("missing 'base_dir'")
    if b.type in ("persona", "business"):
        if not b.voice.get("reference_audio") and not b.voice.get("fallback_reference"):
            problems.append("voice has no reference_audio/fallback_reference")
    if b.type == "music":
        if not b.raw.get("music"):
            problems.append("music brand missing 'music' block (songs_dir / lyrics)")
    if not b.pillars and b.type != "music":
        problems.append("no content pillars defined")
    return problems


# ──────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────
def _cli(argv: List[str]) -> int:
    cmd = argv[0] if argv else "list"

    if cmd == "list":
        ids = list_brand_ids()
        if not ids:
            print("No brands configured. Add JSON files to ./brands/")
            print("Templates available: " + ", ".join(
                p.name for p in BRANDS_DIR.glob("*.template.json")) if BRANDS_DIR.exists() else "")
            return 0
        act = active_brand_id()
        for bid in ids:
            try:
                b = load_brand(bid)
                star = "* " if bid == act else "  "
                print(f"{star}{bid:22s} {b.type:9s} goal={b.goal:13s} {b.name}")
            except Exception as e:  # noqa: BLE001
                print(f"  {bid:22s} ERROR: {e}")
        return 0

    if cmd == "active":
        print(active_brand_id() or "(none)")
        return 0

    if cmd == "show":
        if len(argv) < 2:
            print("usage: brands.py show <id>")
            return 1
        print(json.dumps(load_brand(argv[1]).resolved(), indent=2))
        return 0

    if cmd == "paths":
        if len(argv) < 2:
            print("usage: brands.py paths <id>")
            return 1
        b = load_brand(argv[1])
        for k in ("scripts", "voice", "beats", "drafts", "broll",
                  "masters", "shorts", "approved", "scheduled", "posted"):
            print(f"{k:10s} {b.folder(k)}")
        return 0

    if cmd == "validate":
        ids = list_brand_ids()
        if not ids:
            print("No brands to validate.")
            return 0
        any_bad = False
        for bid in ids:
            b = load_brand(bid)
            probs = validate_brand(b)
            if probs:
                any_bad = True
                print(f"✗ {bid}")
                for p in probs:
                    print(f"    - {p}")
            else:
                print(f"✓ {bid}")
        return 1 if any_bad else 0

    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
