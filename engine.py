#!/usr/bin/env python3
"""
SV Content Engine — Orchestrator ("type naturally → it builds")
===============================================================

The brain behind the command bar. One sentence in, a finished job out:

    "make me a 30s moody trading short about discipline, cinematic look"
        │
        ▼  parse()              natural language → JobSpec (free rules, or Claude)
        ▼  plan()               JobSpec → ordered pipeline steps + $ estimate
        ▼  run()                execute: script · voice · clips · assemble
        ▼  Job record           appears in the studio with a preview

It ties together everything already built:
    brands.py     who we're producing for (voice, avatar, pillars, folders)
    router.py     free-local-first generation + budget guard
    music_video.py  drop-a-song → beat-matched edit
    filters.py    one-click looks

parse() and plan() are pure and unit-tested here. run() drives the live
services (VoxCPM, ComfyUI, ffmpeg) and is best-effort with --dry-run.

CLI:
    python3 engine.py parse "30s ugc ad for my candle brand, warm look"
    python3 engine.py plan  "music video for song.mp3, neon, cut on the beat"
    python3 engine.py build "moody trading short about patience" --dry-run
    python3 engine.py jobs
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import brands as _brands
except Exception:  # noqa: BLE001
    _brands = None
try:
    import router as _router
except Exception:  # noqa: BLE001
    _router = None
try:
    import filters as _filters
except Exception:  # noqa: BLE001
    _filters = None
try:
    import music_video as _mv
except Exception:  # noqa: BLE001
    _mv = None


# ──────────────────────────────────────────────────────────────────────────
# JobSpec — the structured intent behind a natural-language request
# ──────────────────────────────────────────────────────────────────────────
KINDS = ("short", "music_video", "ugc_ad", "broll")

# kind synonyms people actually type
_KIND_HINTS = {
    "music_video": ["music video", "song", "track", "lyric", "beat", "mv", "visualizer"],
    "ugc_ad": ["ugc", "ad", "advert", "commercial", "promo", "product", "sell", "tiktok ad"],
    "broll": ["b-roll", "broll", "clip", "footage", "cutaway", "background video"],
    "short": ["short", "reel", "talking head", "post", "video"],  # default-ish
}

_PLATFORMS = {"tiktok": "TikTok", "reels": "IG", "instagram": "IG", "ig": "IG",
              "youtube": "YouTube", "shorts": "YouTube", "yt": "YouTube",
              "x": "X", "twitter": "X", "facebook": "FB", "fb": "FB"}


@dataclass
class JobSpec:
    prompt: str
    brand: str = ""
    kind: str = "short"
    topic: str = ""
    duration_s: int = 30
    looks: List[str] = field(default_factory=list)
    cut: str = "downbeat"           # music_video only
    song: str = ""                  # music_video only
    platform: str = ""
    hero: bool = False
    aspect: str = "1080x1920"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ──────────────────────────────────────────────────────────────────────────
# parse() — natural language → JobSpec
# ──────────────────────────────────────────────────────────────────────────
def _word(hint: str, text: str) -> bool:
    """Whole-word/phrase match so 'ad' does not fire inside 'trading'."""
    return re.search(rf"(?<![a-z]){re.escape(hint)}(?![a-z])", text) is not None


def _detect_kind(text: str) -> str:
    t = text.lower()
    best, best_kind = 0, "short"
    for kind, hints in _KIND_HINTS.items():
        score = sum(1 for h in hints if _word(h, t))
        # weight the strong signals so "music video" beats a stray "video"
        if kind == "music_video" and ("music video" in t or ".mp3" in t or ".wav" in t):
            score += 3
        if kind == "ugc_ad" and (_word("ugc", t) or _word("ad", t)):
            score += 2
        if score > best:
            best, best_kind = score, kind
    return best_kind


def _detect_duration(text: str) -> Optional[int]:
    t = text.lower()
    m = re.search(r"(\d+)\s*(?:s|sec|secs|seconds)\b", t)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\s*(?:m|min|mins|minute|minutes)\b", t)
    if m:
        return int(m.group(1)) * 60
    if "minute" in t or "1 min" in t:
        return 60
    return None


def _detect_looks(text: str) -> List[str]:
    if _filters is None:
        return []
    t = text.lower()
    found: List[str] = []
    vocab = list(_filters.LOOKS.keys()) + list(_filters.ALIASES.keys())
    for name in vocab:
        if re.search(rf"\b{re.escape(name)}\b", t):
            resolved = _filters.resolve(name)
            if resolved not in found:
                found.append(resolved)
    return found


def _detect_song(text: str) -> str:
    m = re.search(r"([^\s'\"]+\.(?:mp3|wav|m4a|flac))", text, re.I)
    return m.group(1) if m else ""


def _detect_platform(text: str) -> str:
    t = text.lower()
    for k, v in _PLATFORMS.items():
        if re.search(rf"\b{k}\b", t):
            return v
    return ""


def _strip_topic(text: str) -> str:
    """Best-effort topic = the meat after removing control words."""
    t = text
    t = re.sub(r"\b(make|create|build|generate|give me|i want|please)\b", "", t, flags=re.I)
    t = re.sub(r"\b\d+\s*(?:s|sec|secs|seconds|m|min|mins|minute|minutes)\b", "", t, flags=re.I)
    for w in ("music video", "ugc ad", "ugc", "short", "reel", "b-roll", "broll", "video", "ad"):
        t = re.sub(rf"\b{re.escape(w)}\b", "", t, flags=re.I)
    t = re.sub(r"\b(look|style|vibe|aesthetic)\b", "", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip(" ,.-")
    # drop leading filler ("me a moody trading about X" -> "moody trading about X")
    t = re.sub(r"^(?:me|a|an|the|some|of|for|about)\b\s*", "", t, flags=re.I).strip(" ,.-")
    t = re.sub(r"^(?:me|a|an|the|some|of|for|about)\b\s*", "", t, flags=re.I).strip(" ,.-")
    return t


def _parse_rules(prompt: str, brand_id: str) -> JobSpec:
    kind = _detect_kind(prompt)
    spec = JobSpec(prompt=prompt, brand=brand_id, kind=kind)
    dur = _detect_duration(prompt)
    if dur:
        spec.duration_s = dur
    elif kind == "music_video":
        spec.duration_s = 0  # full song length, resolved at run time
    spec.looks = _detect_looks(prompt)
    spec.platform = _detect_platform(prompt)
    spec.hero = bool(re.search(r"\b(hero|best quality|flawless|premium|4k|cinematic hero)\b",
                               prompt, re.I))
    if kind == "music_video":
        spec.song = _detect_song(prompt)
        if re.search(r"\bbar(s)?\b", prompt, re.I):
            spec.cut = "bars"
        elif re.search(r"\bevery beat\b|\bon every beat\b", prompt, re.I):
            spec.cut = "beat"
    spec.topic = _strip_topic(prompt)
    return spec


def _parse_llm(prompt: str, brand_id: str) -> Optional[JobSpec]:
    """Use Claude to parse free-form requests when ANTHROPIC_API_KEY is set.
    Pennies per call. Returns None if the SDK/key is unavailable so the caller
    falls back to rules."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        import anthropic  # type: ignore
    except ImportError:
        return None
    looks_vocab = ", ".join(_filters.LOOKS.keys()) if _filters else ""
    schema = (
        "Return ONLY JSON with keys: kind (short|music_video|ugc_ad|broll), "
        "topic (string), duration_s (int seconds; 0 = full song), "
        f"looks (array from: {looks_vocab}), cut (downbeat|beat|bars), "
        "song (filename or ''), platform (TikTok|IG|YouTube|X|FB|''), hero (bool)."
    )
    try:
        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            system="You convert a creator's request into a video JobSpec. " + schema,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        data = json.loads(re.search(r"\{.*\}", text, re.S).group(0))
    except Exception:  # noqa: BLE001 — any failure → fall back to rules
        return None
    spec = JobSpec(prompt=prompt, brand=brand_id)
    for f in ("kind", "topic", "cut", "song", "platform"):
        if data.get(f):
            setattr(spec, f, data[f])
    spec.duration_s = int(data.get("duration_s", spec.duration_s))
    spec.looks = [l for l in data.get("looks", []) if _filters and l in _filters.LOOKS]
    spec.hero = bool(data.get("hero", False))
    if spec.kind not in KINDS:
        spec.kind = "short"
    return spec


def parse(prompt: str, brand_id: str = "", use_llm: bool = True) -> JobSpec:
    if not brand_id and _brands is not None:
        b = _brands.active_brand()
        brand_id = b.id if b else ""
    if use_llm:
        spec = _parse_llm(prompt, brand_id)
        if spec is not None:
            return spec
    return _parse_rules(prompt, brand_id)


# ──────────────────────────────────────────────────────────────────────────
# plan() — JobSpec → ordered steps + cost estimate
# ──────────────────────────────────────────────────────────────────────────
@dataclass
class Step:
    name: str
    detail: str = ""
    model: str = ""
    est_cost: float = 0.0


# how many distinct video clips each kind wants by default
_CLIP_COUNT = {"short": 4, "music_video": 8, "ugc_ad": 5, "broll": 1}


def plan(spec: JobSpec, brand=None) -> Dict[str, Any]:
    if brand is None and _brands is not None and spec.brand:
        try:
            brand = _brands.load_brand(spec.brand)
        except Exception:  # noqa: BLE001
            brand = None

    steps: List[Step] = []
    clip_kind = "image_to_video" if spec.kind in ("short", "ugc_ad") else "text_to_video"
    n_clips = _CLIP_COUNT.get(spec.kind, 4)
    seconds_each = 5

    def clip_model() -> str:
        if brand is not None:
            return brand.route_for(clip_kind, hero=spec.hero)
        return ("veo-3.1" if spec.hero else "ltx-video")

    def clip_cost(model: str) -> float:
        return _router.estimate_cost(model, seconds=seconds_each) if _router else 0.0

    if spec.kind == "music_video":
        steps.append(Step("ingest", f"transcribe lyrics + detect beat ({spec.song or 'song'})",
                          "whisper+librosa", 0.0))
        m = clip_model()
        steps.append(Step("clips", f"{n_clips} visuals to cut on the beat", m,
                          round(clip_cost(m) * n_clips, 4)))
        steps.append(Step("assemble",
                          f"beat-synced cut={spec.cut}" +
                          (f", look={'+'.join(spec.looks)}" if spec.looks else ""),
                          "ffmpeg", 0.0))
    elif spec.kind == "broll":
        m = clip_model()
        steps.append(Step("clips", f"{n_clips} clip(s) · {spec.topic or 'b-roll'}", m,
                          round(clip_cost(m) * n_clips, 4)))
    else:  # short / ugc_ad — talking head + b-roll + assembly
        steps.append(Step("script", f"write {spec.kind} script · {spec.topic or 'topic'}",
                          "claude/local", 0.0))
        steps.append(Step("voice", "VoxCPM voice (local)", "voxcpm", 0.0))
        avatar_model = (brand.avatar.get("engine") if brand else "heygem")
        steps.append(Step("talking_head", f"avatar ({avatar_model})", avatar_model,
                          _router.estimate_cost(avatar_model) if _router else 0.0))
        m = clip_model()
        steps.append(Step("broll", f"{n_clips} b-roll clips", m,
                          round(clip_cost(m) * n_clips, 4)))
        look = f", look={'+'.join(spec.looks)}" if spec.looks else ""
        steps.append(Step("assemble", f"talking head + b-roll + captions{look}", "ffmpeg", 0.0))

    total = round(sum(s.est_cost for s in steps), 4)
    return {
        "spec": spec.to_dict(),
        "steps": [asdict(s) for s in steps],
        "est_cost": total,
        "route": "hero/paid" if spec.hero else "local/free",
    }


# ──────────────────────────────────────────────────────────────────────────
# Jobs — records the studio reads
# ──────────────────────────────────────────────────────────────────────────
def _jobs_dir(brand) -> Path:
    base = brand.base_dir if brand else Path(".")
    d = Path(base) / "jobs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _new_job_id() -> str:
    return time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:4]


def record_job(brand, job: Dict[str, Any]) -> None:
    d = _jobs_dir(brand)
    (d / f"{job['id']}.json").write_text(json.dumps(job, indent=2))
    with open(d / "jobs.jsonl", "a") as f:
        f.write(json.dumps({"id": job["id"], "ts": job["ts"],
                            "kind": job["spec"]["kind"], "status": job["status"],
                            "prompt": job["spec"]["prompt"]}) + "\n")


def _save_job(brand, job: Dict[str, Any]) -> None:
    """Rewrite a job's JSON in place (live progress updates, no jsonl append)."""
    (_jobs_dir(brand) / f"{job['id']}.json").write_text(json.dumps(job, indent=2))


def get_job(brand, job_id: str) -> Optional[Dict[str, Any]]:
    p = _jobs_dir(brand) / f"{job_id}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return None


def list_jobs(brand) -> List[Dict[str, Any]]:
    d = Path((brand.base_dir if brand else Path("."))) / "jobs"
    if not d.exists():
        return []
    out = []
    for p in sorted(d.glob("*.json")):
        if p.name == "jobs.jsonl":
            continue
        try:
            out.append(json.loads(p.read_text()))
        except json.JSONDecodeError:
            continue
    return sorted(out, key=lambda j: j.get("ts", ""), reverse=True)


# ──────────────────────────────────────────────────────────────────────────
# build() — parse → plan → (run) → job record
# ──────────────────────────────────────────────────────────────────────────
def build(prompt: str, brand_id: str = "", dry_run: bool = True,
          use_llm: bool = True) -> Dict[str, Any]:
    spec = parse(prompt, brand_id, use_llm=use_llm)
    brand = None
    if _brands is not None and spec.brand:
        try:
            brand = _brands.load_brand(spec.brand)
        except Exception:  # noqa: BLE001
            brand = None
    p = plan(spec, brand)
    job = {
        "id": _new_job_id(),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "spec": spec.to_dict(),
        "plan": p,
        "status": "planned" if dry_run else "queued",
        "output": None,
    }
    job["step_status"] = {s["name"]: "pending" for s in p["steps"]}
    record_job(brand, job)
    if not dry_run:
        # Run live in the background so the command bar returns instantly and the
        # Studio can poll progress. Tests call execute() directly (synchronous).
        t = threading.Thread(target=_execute_safe, args=(job["id"], brand), daemon=True)
        t.start()
        job["status"] = "running"
    return job


# ──────────────────────────────────────────────────────────────────────────
# Live execution
# ──────────────────────────────────────────────────────────────────────────
class Skip(RuntimeError):
    """A step could not run (service offline / missing input). Not fatal —
    the job continues and the step is marked skipped with the reason."""


def _workdir(brand, job_id: str) -> Path:
    d = _jobs_dir(brand) / job_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _ffmpeg() -> str:
    for cand in ("/opt/homebrew/bin/ffmpeg", "/usr/bin/ffmpeg", "ffmpeg"):
        if shutil.which(cand) or os.path.exists(cand):
            return cand
    return "ffmpeg"


# ---- individual steps. Each returns a short note; raises Skip if it can't run.
def _step_script(job, spec, brand, ctx) -> str:
    """Write a script for the topic in the brand voice. Best-effort template;
    a fuller writer can swap in later."""
    topic = spec.topic or "today"
    signoff = (brand.signoff if brand else "") or ""
    text = (f"Pay attention.\n\n{topic.capitalize()}.\n\n"
            f"This is where most people get it wrong.\n\n"
            f"Slow down. Control what you can control.\n\n{signoff}").strip()
    path = ctx["dir"] / "script.txt"
    path.write_text(text)
    ctx["script"] = str(path)
    ctx["script_text"] = text
    return f"script.txt ({len(text)} chars)"


def _step_voice(job, spec, brand, ctx) -> str:
    if brand is None:
        raise Skip("no brand voice configured")
    text = ctx.get("script_text", spec.topic or "")
    api = brand.voice.get("api_url", "")
    ref = brand.voice_reference()
    out = ctx["dir"] / "voice.wav"
    try:
        payload = json.dumps({"text": text, "reference_audio": ref}).encode()
        req = urllib.request.Request(api, data=payload,
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=600) as r:
            out.write_bytes(r.read())
    except (urllib.error.URLError, OSError) as e:
        raise Skip(f"VoxCPM offline ({e})")
    ctx["voice"] = str(out)
    return f"voice.wav ({out.stat().st_size // 1024}KB)"


def _step_ingest(job, spec, brand, ctx) -> str:
    if _mv is None:
        raise Skip("music_video module unavailable")
    song = spec.song
    if song and not os.path.isabs(song) and brand is not None:
        cand = Path(brand.folder("beats")) / song
        if cand.exists():
            song = str(cand)
    if not song or not os.path.exists(song):
        raise Skip(f"song not found: {spec.song or '(none)'}")
    try:
        out_json = str(ctx["dir"] / "song.json")
        ctx["song"] = _mv.ingest(song, out_json)
        ctx["song_path"] = song
    except _mv.MissingDependency as e:
        raise Skip(str(e))
    return (f"{len(ctx['song'].get('beats', []))} beats, "
            f"{len(ctx['song'].get('lyrics', []))} lyric lines")


def _step_clips(job, spec, brand, ctx, kind="image_to_video") -> str:
    if _router is None:
        raise Skip("router unavailable")
    n = _CLIP_COUNT.get(spec.kind, 4)
    made: List[str] = []
    errs: List[str] = []
    for i in range(n):
        try:
            req = _router.GenRequest(kind=kind, prompt=spec.topic or spec.prompt,
                                     seconds=5, hero=spec.hero,
                                     out_path=str(ctx["dir"] / f"clip_{i}"))
            res = _router.route(req, brand=brand)
            if res.out_path:
                made.append(res.out_path)
        except (_router.BackendUnavailable, _router.BudgetExceeded) as e:
            errs.append(str(e))
            break
    ctx["clips"] = made
    if not made:
        raise Skip(errs[0] if errs else "no clips produced")
    return f"{len(made)} clip(s)"


def _step_talking_head(job, spec, brand, ctx) -> str:
    # Avatar adapters (heygen/heygem) plug in here. Until wired, skip cleanly so
    # the rest of the job (b-roll + assembly) still runs.
    engine_name = brand.avatar.get("engine") if brand else "heygem"
    raise Skip(f"avatar engine '{engine_name}' not yet wired (b-roll continues)")


def _step_assemble(job, spec, brand, ctx) -> str:
    ff = _ffmpeg()
    if not (shutil.which(ff) or os.path.exists(ff)):
        raise Skip("ffmpeg not found")
    out = ctx["dir"] / "final.mp4"
    look = spec.looks or None

    if spec.kind == "music_video":
        song = ctx.get("song")
        clips = ctx.get("clips") or []
        if not song or not clips:
            raise Skip("need song + clips to assemble")
        if _mv is None:
            raise Skip("music_video module unavailable")
        res = _mv.render(song, clips, ctx["song_path"], str(out),
                         cut=spec.cut, look=look, size=spec.aspect, run=True, ffmpeg=ff)
        if not res.get("ok"):
            raise Skip(f"ffmpeg failed: {res.get('error', '')[:200]}")
    else:
        clips = ctx.get("clips") or []
        if not clips:
            raise Skip("no clips to assemble")
        # concat clips, apply look, add voice audio if present
        w, h = spec.aspect.split("x")
        cmd = [ff, "-y"]
        for c in clips:
            cmd += ["-i", c]
        voice = ctx.get("voice")
        if voice:
            cmd += ["-i", voice]
        fg = []
        for i in range(len(clips)):
            fg.append(f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=increase,"
                      f"crop={w}:{h},fps=30[v{i}]")
        fg.append("".join(f"[v{i}]" for i in range(len(clips))) +
                  f"concat=n={len(clips)}:v=1:a=0[vc]")
        last = "vc"
        if look and _filters is not None:
            ch = _filters.chain(*look)
            if ch:
                fg.append(f"[vc]{ch}[vl]"); last = "vl"
        cmd += ["-filter_complex", ";".join(fg), "-map", f"[{last}]"]
        if voice:
            cmd += ["-map", f"{len(clips)}:a", "-shortest"]
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(out)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise Skip(f"ffmpeg failed: {proc.stderr[-200:]}")

    ctx["output"] = str(out)
    # surface into the brand's shorts folder so the Library/preview sees it
    if brand is not None:
        dest = Path(brand.folder("shorts")) / f"{job['id']}.mp4"
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(out, dest)
            ctx["output"] = str(dest)
        except OSError:
            pass
    return f"final.mp4 -> {Path(ctx['output']).name}"


_STEP_FUNCS = {
    "script": _step_script,
    "voice": _step_voice,
    "ingest": _step_ingest,
    "clips": lambda j, s, b, c: _step_clips(j, s, b, c, kind="text_to_video"),
    "broll": lambda j, s, b, c: _step_clips(j, s, b, c, kind="image_to_video"),
    "talking_head": _step_talking_head,
    "assemble": _step_assemble,
}


def execute(job: Dict[str, Any], brand, hooks: Optional[Dict] = None) -> Dict[str, Any]:
    """Run a job's steps in order. Each step is best-effort: failures become
    'skipped: <reason>' so partial progress is preserved and visible."""
    funcs = dict(_STEP_FUNCS)
    if hooks:
        funcs.update(hooks)
    job["status"] = "running"
    job.setdefault("step_status", {})
    job.setdefault("step_notes", {})
    ctx: Dict[str, Any] = {"dir": _workdir(brand, job["id"])}
    produced_output = False
    for step in job["plan"]["steps"]:
        name = step["name"]
        fn = funcs.get(name)
        if fn is None:
            job["step_status"][name] = "skipped: no executor"
            continue
        job["step_status"][name] = "running"
        _save_job(brand, job)
        try:
            note = fn(job, _spec_from(job), brand, ctx)
            job["step_status"][name] = "done"
            job["step_notes"][name] = note
        except Skip as e:
            job["step_status"][name] = f"skipped: {e}"
        except Exception as e:  # noqa: BLE001 — a bad step shouldn't kill the job
            job["step_status"][name] = f"error: {e}"
        _save_job(brand, job)

    if ctx.get("output"):
        job["output"] = ctx["output"]
        produced_output = True
    # persist artifacts so the in-platform editor can re-cut/re-render later
    job["artifacts"] = {
        "clips": ctx.get("clips") or [],
        "song_json": str(ctx["dir"] / "song.json") if ctx.get("song") else None,
        "song_path": ctx.get("song_path"),
        "voice": ctx.get("voice"),
        "output": ctx.get("output"),
    }
    done = [v for v in job["step_status"].values() if v == "done"]
    if produced_output:
        job["status"] = "done"
    elif done:
        job["status"] = "partial"
    else:
        job["status"] = "skipped"
    _save_job(brand, job)
    return job


def _spec_from(job) -> "JobSpec":
    d = job["spec"]
    return JobSpec(**{k: d[k] for k in JobSpec.__dataclass_fields__ if k in d})


def _execute_safe(job_id: str, brand) -> None:
    job = get_job(brand, job_id)
    if job is None:
        return
    try:
        execute(job, brand)
    except Exception as e:  # noqa: BLE001
        job["status"] = "error"
        job["error"] = str(e)
        _save_job(brand, job)


def process_queue(brand) -> int:
    """Run every queued job for a brand (for a cron/worker). Returns count run."""
    n = 0
    for job in list_jobs(brand):
        if job.get("status") == "queued":
            _execute_safe(job["id"], brand)
            n += 1
    return n


# ──────────────────────────────────────────────────────────────────────────
# Drop-a-song upload  &  in-platform editor (re-cut / re-order / re-look)
# ──────────────────────────────────────────────────────────────────────────
LOOK_NAMES = sorted(_filters.LOOKS.keys()) if _filters else []
CUT_MODES = ["downbeat", "beat", "bars", "seconds"]


def ingest_song(brand, audio_path: str) -> Dict[str, Any]:
    """Analyse an uploaded song (beat + lyrics) and stash song.json beside it in
    the brand's beats folder. Returns a summary the Studio renders immediately.
    Degrades gracefully when librosa/whisper aren't installed."""
    if _mv is None:
        return {"ok": False, "error": "music_video module unavailable"}
    name = os.path.basename(audio_path)
    out_json = str(Path(audio_path).with_suffix(".song.json"))
    try:
        song = _mv.ingest(audio_path, out_json)
    except _mv.MissingDependency as e:
        return {"ok": False, "name": name, "error": str(e),
                "hint": "pip install librosa openai-whisper"}
    lyrics = song.get("lyrics", [])
    return {
        "ok": True, "name": name, "song_json": out_json,
        "tempo": song.get("tempo"), "beats": len(song.get("beats", [])),
        "sections": len(song.get("sections", [])), "lyrics": len(lyrics),
        "lyric_preview": " / ".join(l["text"] for l in lyrics[:3]),
    }


def rerender(brand, job_id: str, order: Optional[List[int]] = None,
             look: Optional[List[str]] = None, cut: Optional[str] = None,
             every: int = 1) -> Dict[str, Any]:
    """Re-cut an already-built music video: reorder clips, swap the look, change
    the beat-cut mode, and re-render. Returns the updated job (or an error)."""
    job = get_job(brand, job_id)
    if job is None:
        return {"ok": False, "error": "job not found"}
    if job.get("spec", {}).get("kind") != "music_video":
        return {"ok": False, "error": "editor only supports music videos"}
    art = job.get("artifacts") or {}
    clips, song_json, audio = art.get("clips"), art.get("song_json"), art.get("song_path")
    if not (clips and song_json and audio):
        return {"ok": False, "error": "this job has no clips/song to re-cut yet"}
    if _mv is None:
        return {"ok": False, "error": "music_video module unavailable"}

    if order:  # reorder / drop clips by index
        try:
            clips = [clips[i] for i in order if 0 <= i < len(clips)]
        except (TypeError, ValueError):
            return {"ok": False, "error": "bad clip order"}
    if not clips:
        return {"ok": False, "error": "no clips left after reorder"}

    spec = job["spec"]
    look = look if look is not None else spec.get("looks")
    cut = cut or spec.get("cut", "downbeat")
    try:
        song = json.loads(Path(song_json).read_text())
    except (OSError, json.JSONDecodeError) as e:
        return {"ok": False, "error": f"can't read song.json ({e})"}

    out = _workdir(brand, job_id) / f"edit_{int(time.time())}.mp4"
    ff = _ffmpeg()
    res = _mv.render(song, clips, audio, str(out), cut=cut, every=every,
                     look=look or None, size=spec.get("aspect", "1080x1920"),
                     run=True, ffmpeg=ff)
    if not res.get("ok"):
        return {"ok": False, "error": (res.get("error") or "ffmpeg failed")[:300]}

    final = str(out)
    if brand is not None:
        dest = Path(brand.folder("shorts")) / f"{job_id}.mp4"
        try:
            shutil.copy2(out, dest); final = str(dest)
        except OSError:
            pass
    job["output"] = final
    job["artifacts"]["output"] = final
    job["artifacts"]["clips"] = clips
    spec["looks"] = look or []
    spec["cut"] = cut
    job.setdefault("edits", []).append({
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "cut": cut, "every": every,
        "look": look or [], "clips": len(clips), "out": Path(final).name,
    })
    job["status"] = "done"
    _save_job(brand, job)
    return {"ok": True, "job": job}


# ──────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────
def _cli(argv) -> int:
    ap = argparse.ArgumentParser(prog="engine.py")
    sub = ap.add_subparsers(dest="cmd")
    for name in ("parse", "plan", "build"):
        s = sub.add_parser(name)
        s.add_argument("prompt")
        s.add_argument("--brand", default="")
        s.add_argument("--no-llm", action="store_true")
        if name == "build":
            s.add_argument("--dry-run", action="store_true")
    sub.add_parser("jobs").add_argument("--brand", default="")
    args = ap.parse_args(argv)

    if args.cmd == "parse":
        print(json.dumps(parse(args.prompt, args.brand, use_llm=not args.no_llm).to_dict(), indent=2))
        return 0
    if args.cmd == "plan":
        spec = parse(args.prompt, args.brand, use_llm=not args.no_llm)
        print(json.dumps(plan(spec), indent=2))
        return 0
    if args.cmd == "build":
        job = build(args.prompt, args.brand, dry_run=args.dry_run or True,
                    use_llm=not args.no_llm)
        print(f"job {job['id']}  [{job['status']}]  est ${job['plan']['est_cost']} "
              f"({job['plan']['route']})")
        for s in job["plan"]["steps"]:
            c = f" ${s['est_cost']}" if s["est_cost"] else ""
            print(f"  • {s['name']:13s} {s['detail']}  [{s['model']}{c}]")
        return 0
    if args.cmd == "jobs":
        b = _brands.load_brand(args.brand) if (_brands and args.brand) else (
            _brands.active_brand() if _brands else None)
        for j in list_jobs(b):
            print(f"{j['id']}  [{j['status']:8s}] {j['spec']['kind']:11s} "
                  f"{j['spec']['prompt'][:60]}")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
