#!/usr/bin/env python3
"""
SV Content Engine — Generation Cost Router
==========================================

One front door for every video/clip the engine generates. It reads the active
brand's "generation" block and decides, per request:

    free local model  (Wan / LTX in ComfyUI, $0)   ← default
    paid hero model   (Veo / Kling / Seedance)      ← only when hero=True

…then enforces a budget cap, dispatches to the right backend, and writes every
cent to a spend ledger. This is the module that converts the brand config into
actual savings: local-first by default, paid only for the rare flawless shot.

Safety by design:
  - Never silently spends. If the local backend is down, it raises instead of
    quietly escalating to a paid API.
  - A budget guard blocks paid calls that would exceed the brand's daily/monthly
    cap (override with hero=True + allow_over_budget, or raise the cap).
  - --dry-run prints the decision + estimated cost and touches no backend, so you
    can plan a batch's spend before running it for real.

CLI:
    python3 router.py gen --kind text_to_video --prompt "rain on glass" --seconds 5
    python3 router.py gen --kind image_to_video --image still.png --hero
    python3 router.py gen --kind music_video --audio song.wav --prompt "neon city"
    python3 router.py plan --kind text_to_video --seconds 5 --count 20   # estimate a batch
    python3 router.py spend [--brand <id>]                               # ledger totals
    python3 router.py prices                                             # show price table

Backends are pluggable. ComfyUI (local), fal.ai (Kling/Seedance), and Google Veo
adapters are included; each degrades gracefully to a clear error if its
server/key/SDK is unavailable.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

try:
    import brands as _brands
except Exception:  # noqa: BLE001
    _brands = None


# ──────────────────────────────────────────────────────────────────────────
# Pricing — USD. Local models are $0 (your own GPU). Paid rates are mid-2026
# list prices; tune freely. per_second applies to duration; per_clip is flat.
# ──────────────────────────────────────────────────────────────────────────
PRICING: Dict[str, Dict[str, Any]] = {
    # ---- free local (ComfyUI on your own GPU) ----
    "wan2.2":        {"tier": "local", "per_second": 0.0},
    "wan2.7":        {"tier": "local", "per_second": 0.0},
    "ltx-video":     {"tier": "local", "per_second": 0.0},
    "ltx-2.3-audio": {"tier": "local", "per_second": 0.0},
    "heygem":        {"tier": "local", "per_second": 0.0},

    # ---- paid hero APIs ----
    "veo-3.1":       {"tier": "api", "per_second": 0.03},   # native audio
    "veo-3.0":       {"tier": "api", "per_second": 0.05},
    "seedance-2.0":  {"tier": "api", "per_second": 0.09},
    "seedance-2.0-fast": {"tier": "api", "per_second": 0.022},
    "kling-1.6":     {"tier": "api", "per_second": 0.05},   # ~$0.25 / 5s
    "kling-2.0":     {"tier": "api", "per_second": 0.10},   # ~$0.50 / 5s
    "kling-3.0":     {"tier": "api", "per_second": 0.029},
    "freebeat":      {"tier": "api", "per_clip": 0.50},
    "heygen":        {"tier": "api", "per_clip": 0.30},
}


def estimate_cost(model: str, seconds: float = 5.0, clips: int = 1) -> float:
    p = PRICING.get(model)
    if not p:
        return 0.0
    if "per_clip" in p:
        return round(p["per_clip"] * clips, 4)
    return round(p["per_second"] * seconds * clips, 4)


def is_paid(model: str) -> bool:
    return PRICING.get(model, {}).get("tier") == "api"


# ──────────────────────────────────────────────────────────────────────────
# Request / result
# ──────────────────────────────────────────────────────────────────────────
@dataclass
class GenRequest:
    kind: str                       # text_to_video | image_to_video | music_video
    prompt: str = ""
    seconds: float = 5.0
    hero: bool = False
    image: Optional[str] = None     # source still for image_to_video
    audio: Optional[str] = None     # song for music_video
    out_path: Optional[str] = None
    seed: int = 0
    allow_over_budget: bool = False


@dataclass
class GenResult:
    ok: bool
    model: str
    backend: str
    cost: float
    out_path: Optional[str] = None
    dry_run: bool = False
    note: str = ""


class BackendUnavailable(RuntimeError):
    """Raised when a backend's server / key / SDK is not reachable."""


class BudgetExceeded(RuntimeError):
    """Raised when a paid request would push spend past the brand's cap."""


# ──────────────────────────────────────────────────────────────────────────
# Spend ledger — append-only JSONL under the brand's base_dir
# ──────────────────────────────────────────────────────────────────────────
class Ledger:
    def __init__(self, base_dir: Path):
        self.path = Path(base_dir) / ".spend_ledger.jsonl"

    def record(self, brand_id: str, model: str, cost: float, kind: str,
               dry_run: bool = False) -> None:
        if dry_run:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "brand": brand_id, "model": model, "kind": kind,
            "cost": round(cost, 4), "tier": PRICING.get(model, {}).get("tier", "?"),
        }
        with open(self.path, "a") as f:
            f.write(json.dumps(row) + "\n")

    def _rows(self):
        if not self.path.exists():
            return []
        rows = []
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return rows

    def spent(self, period: str = "day") -> float:
        """Total USD spent today ('day') or this month ('month')."""
        now = datetime.now(timezone.utc)
        total = 0.0
        for r in self._rows():
            try:
                ts = datetime.fromisoformat(r["ts"])
            except (ValueError, KeyError):
                continue
            if period == "day" and (ts.year, ts.month, ts.day) == (now.year, now.month, now.day):
                total += r.get("cost", 0.0)
            elif period == "month" and (ts.year, ts.month) == (now.year, now.month):
                total += r.get("cost", 0.0)
            elif period == "all":
                total += r.get("cost", 0.0)
        return round(total, 4)

    def summary(self) -> Dict[str, float]:
        return {"today": self.spent("day"), "month": self.spent("month"),
                "all_time": self.spent("all")}


# ──────────────────────────────────────────────────────────────────────────
# Backends
# ──────────────────────────────────────────────────────────────────────────
def _http_json(url: str, payload: dict, headers: dict, timeout: int = 600) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


class ComfyUIBackend:
    """Free local generation via ComfyUI's HTTP API.

    Loads a workflow template (JSON exported from ComfyUI) and substitutes
    placeholder tokens before submitting:
        {{PROMPT}} {{SECONDS}} {{IMAGE_PATH}} {{AUDIO_PATH}}
        {{OUTPUT_PREFIX}} {{SEED}}
    Workflow templates live in ./workflows/<model>.json (repo) or
    <brand.base_dir>/workflows/<model>.json (per-brand override).
    """
    name = "comfyui"

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.environ.get("COMFYUI_URL", "http://localhost:8188")).rstrip("/")

    def _workflow_path(self, model: str, brand) -> Optional[Path]:
        candidates = []
        if brand is not None:
            candidates.append(Path(brand.base_dir) / "workflows" / f"{model}.json")
        candidates.append(Path(__file__).resolve().parent / "workflows" / f"{model}.json")
        for c in candidates:
            if c.exists():
                return c
        return None

    def generate(self, req: GenRequest, model: str, brand) -> str:
        wf_path = self._workflow_path(model, brand)
        if wf_path is None:
            raise BackendUnavailable(
                f"No ComfyUI workflow for '{model}'. Export one from ComfyUI to "
                f"workflows/{model}.json (see workflows/README.md for tokens).")
        raw = wf_path.read_text()
        out_prefix = req.out_path or f"sv_{int(time.time())}"
        for token, value in {
            "{{PROMPT}}": req.prompt.replace('"', '\\"'),
            "{{SECONDS}}": str(req.seconds),
            "{{IMAGE_PATH}}": req.image or "",
            "{{AUDIO_PATH}}": req.audio or "",
            "{{OUTPUT_PREFIX}}": out_prefix,
            "{{SEED}}": str(req.seed or int(time.time())),
        }.items():
            raw = raw.replace(token, value)
        workflow = json.loads(raw)

        try:
            resp = _http_json(f"{self.base_url}/prompt", {"prompt": workflow},
                              {"Content-Type": "application/json"}, timeout=30)
        except (urllib.error.URLError, OSError) as e:
            raise BackendUnavailable(
                f"ComfyUI not reachable at {self.base_url} ({e}). Start ComfyUI first.")
        pid = resp.get("prompt_id")
        if not pid:
            raise BackendUnavailable(f"ComfyUI rejected the workflow: {resp}")

        # Poll history until the job shows up complete.
        deadline = time.time() + 1800
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(f"{self.base_url}/history/{pid}", timeout=30) as r:
                    hist = json.loads(r.read().decode())
            except (urllib.error.URLError, OSError):
                time.sleep(3)
                continue
            if pid in hist:
                return f"{out_prefix} (ComfyUI prompt_id={pid})"
            time.sleep(3)
        raise BackendUnavailable("ComfyUI job timed out after 30 min.")


class FalBackend:
    """Paid hero generation via fal.ai (Kling / Seedance). Needs FAL_API_KEY."""
    name = "fal"
    ENDPOINTS = {
        "kling-1.6": "fal-ai/kling-video/v1.6/pro/text-to-video",
        "kling-2.0": "fal-ai/kling-video/v2.0/pro/text-to-video",
        "kling-3.0": "fal-ai/kling-video/v3.0/pro/text-to-video",
        "seedance-2.0": "fal-ai/bytedance/seedance-2.0",
        "seedance-2.0-fast": "fal-ai/bytedance/seedance-2.0/fast",
    }

    def generate(self, req: GenRequest, model: str, brand) -> str:
        key = os.environ.get("FAL_API_KEY", "")
        if not key:
            raise BackendUnavailable("FAL_API_KEY not set — cannot call fal.ai.")
        endpoint = self.ENDPOINTS.get(model)
        if not endpoint:
            raise BackendUnavailable(f"No fal.ai endpoint mapped for '{model}'.")
        payload: Dict[str, Any] = {"prompt": req.prompt,
                                   "duration": int(req.seconds)}
        if req.image:
            payload["image_url"] = req.image
        try:
            resp = _http_json(f"https://queue.fal.run/{endpoint}", payload,
                              {"Authorization": f"Key {key}",
                               "Content-Type": "application/json"}, timeout=600)
        except (urllib.error.URLError, OSError) as e:
            raise BackendUnavailable(f"fal.ai request failed: {e}")
        return resp.get("video", {}).get("url") or json.dumps(resp)[:200]


class VeoBackend:
    """Paid hero generation via Google Veo. Needs google-genai + GEMINI_API_KEY."""
    name = "veo"
    MODELS = {"veo-3.1": "veo-3.1-generate-preview", "veo-3.0": "veo-3.0-generate-001"}

    def generate(self, req: GenRequest, model: str, brand) -> str:
        key = os.environ.get("GEMINI_API_KEY", "")
        if not key:
            raise BackendUnavailable("GEMINI_API_KEY not set — cannot call Veo.")
        try:
            import google.genai as genai            # type: ignore
            import google.genai.types as gtypes      # type: ignore
        except ImportError:
            raise BackendUnavailable("google-genai not installed (pip install google-genai).")
        client = genai.Client(api_key=key)
        op = client.models.generate_videos(
            model=self.MODELS.get(model, "veo-3.1-generate-preview"),
            prompt=req.prompt,
            config=gtypes.GenerateVideosConfig(aspect_ratio="9:16", number_of_videos=1),
        )
        while not op.done:
            time.sleep(10)
            op = client.operations.get(op)
        vids = op.response.generated_videos
        return vids[0].video.uri if vids else "(veo returned no video)"


# model name -> backend instance factory
def _backend_for(model: str) -> Any:
    if PRICING.get(model, {}).get("tier") == "local":
        return ComfyUIBackend()
    if model.startswith("kling") or model.startswith("seedance"):
        return FalBackend()
    if model.startswith("veo"):
        return VeoBackend()
    # freebeat / heygen etc. — no auto adapter yet
    raise BackendUnavailable(f"No backend adapter wired for paid model '{model}'.")


# ──────────────────────────────────────────────────────────────────────────
# The router
# ──────────────────────────────────────────────────────────────────────────
def route(req: GenRequest, brand=None, dry_run: bool = False,
          backend_override: Optional[Callable] = None) -> GenResult:
    """Pick a model for the request, enforce budget, dispatch, and log spend."""
    if brand is None and _brands is not None:
        brand = _brands.active_brand()

    # 1. pick the model from the brand's generation block
    if brand is not None:
        model = brand.route_for(req.kind, hero=req.hero)
        gen_cfg = brand.generation
        brand_id = brand.id
        base_dir = brand.base_dir
    else:  # no brand layer: sane local-first defaults
        defaults = {"text_to_video": ("ltx-video", "veo-3.1"),
                    "image_to_video": ("wan2.2", "kling-2.0"),
                    "music_video": ("ltx-2.3-audio", "freebeat")}
        local, hero = defaults.get(req.kind, ("ltx-video", "veo-3.1"))
        model = hero if req.hero else local
        gen_cfg = {}
        brand_id = "default"
        base_dir = Path(".")

    if not model:
        return GenResult(False, "", "", 0.0, note=f"No model configured for kind '{req.kind}'.")

    cost = estimate_cost(model, seconds=req.seconds)
    ledger = Ledger(base_dir)

    # 2. budget guard — only paid calls can breach a cap
    if is_paid(model) and cost > 0:
        budget = gen_cfg.get("budget", {}) if isinstance(gen_cfg, dict) else {}
        day_cap = budget.get("daily_usd")
        month_cap = budget.get("monthly_usd")
        if not req.allow_over_budget:
            if day_cap is not None and ledger.spent("day") + cost > day_cap:
                raise BudgetExceeded(
                    f"${cost} for {model} would exceed daily cap ${day_cap} "
                    f"(spent ${ledger.spent('day')} today). "
                    f"Use a local model, raise the cap, or pass allow_over_budget=True.")
            if month_cap is not None and ledger.spent("month") + cost > month_cap:
                raise BudgetExceeded(
                    f"${cost} for {model} would exceed monthly cap ${month_cap} "
                    f"(spent ${ledger.spent('month')} this month).")

    # 3. dry run — decide + estimate, touch nothing
    if dry_run:
        return GenResult(True, model, _backend_name(model), cost, dry_run=True,
                         note=f"DRY RUN: would generate {req.kind} via {model} (~${cost}).")

    # 4. dispatch
    backend = backend_override() if backend_override else _backend_for(model)
    out = backend.generate(req, model, brand)
    ledger.record(brand_id, model, cost, req.kind)
    return GenResult(True, model, backend.name, cost, out_path=out,
                     note=f"{req.kind} via {model} (${cost})")


def _backend_name(model: str) -> str:
    tier = PRICING.get(model, {}).get("tier")
    if tier == "local":
        return "comfyui"
    if model.startswith(("kling", "seedance")):
        return "fal"
    if model.startswith("veo"):
        return "veo"
    return "?"


# ──────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────
def _cli(argv) -> int:
    ap = argparse.ArgumentParser(prog="router.py", description="Generation cost router")
    sub = ap.add_subparsers(dest="cmd")

    g = sub.add_parser("gen", help="route one generation request")
    g.add_argument("--kind", required=True,
                   choices=["text_to_video", "image_to_video", "music_video"])
    g.add_argument("--prompt", default="")
    g.add_argument("--seconds", type=float, default=5.0)
    g.add_argument("--hero", action="store_true", help="use the paid hero model")
    g.add_argument("--image"); g.add_argument("--audio"); g.add_argument("--out")
    g.add_argument("--brand")
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--allow-over-budget", action="store_true")

    p = sub.add_parser("plan", help="estimate cost of a batch (no calls)")
    p.add_argument("--kind", required=True,
                   choices=["text_to_video", "image_to_video", "music_video"])
    p.add_argument("--seconds", type=float, default=5.0)
    p.add_argument("--count", type=int, default=1)
    p.add_argument("--hero", action="store_true")
    p.add_argument("--brand")

    s = sub.add_parser("spend", help="show ledger totals")
    s.add_argument("--brand")

    sub.add_parser("prices", help="show the price table")

    args = ap.parse_args(argv)

    def _brand(bid):
        if _brands is None:
            return None
        return _brands.load_brand(bid) if bid else _brands.active_brand()

    if args.cmd == "prices":
        print(f"{'model':22s} {'tier':6s} rate")
        for m, p in PRICING.items():
            rate = (f"${p['per_second']}/s" if "per_second" in p else f"${p['per_clip']}/clip")
            print(f"{m:22s} {p['tier']:6s} {rate}")
        return 0

    if args.cmd == "spend":
        b = _brand(args.brand)
        base = b.base_dir if b else Path(".")
        led = Ledger(base)
        s = led.summary()
        print(f"Brand: {b.id if b else '(none)'}")
        print(f"  today    ${s['today']}")
        print(f"  month    ${s['month']}")
        print(f"  all-time ${s['all_time']}")
        return 0

    if args.cmd == "plan":
        b = _brand(args.brand)
        model = b.route_for(args.kind, hero=args.hero) if b else (
            "veo-3.1" if args.hero else "ltx-video")
        each = estimate_cost(model, seconds=args.seconds)
        total = round(each * args.count, 4)
        print(f"model:  {model}  ({'paid' if is_paid(model) else 'FREE local'})")
        print(f"each:   ${each}   x{args.count}   =   ${total}")
        if not is_paid(model):
            print("→ $0. This is the whole point: keep default_route=local for bulk.")
        return 0

    if args.cmd == "gen":
        b = _brand(args.brand)
        req = GenRequest(kind=args.kind, prompt=args.prompt, seconds=args.seconds,
                         hero=args.hero, image=args.image, audio=args.audio,
                         out_path=args.out, allow_over_budget=args.allow_over_budget)
        try:
            res = route(req, brand=b, dry_run=args.dry_run)
        except (BudgetExceeded, BackendUnavailable) as e:
            print(f"✗ {type(e).__name__}: {e}")
            return 1
        flag = "DRY" if res.dry_run else ("$" + str(res.cost))
        print(f"[{flag}] {res.note}")
        if res.out_path:
            print(f"  output: {res.out_path}")
        return 0 if res.ok else 1

    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
