#!/usr/bin/env python3
"""
SV Content Engine — Music Video Brain
=====================================

Drop a song in, get a video out:

    mp3/wav ──► transcribe lyrics ──┐
            └─► detect beat/tempo ──┼─► song.json  ──► beat-synced edit map ──► ffmpeg ──► video
            └─► find sections    ──┘                     (cuts on the beat,
                                                          lyrics burned in)

Everything here is free/local:
  - lyrics:   faster-whisper / openai-whisper  (your GPU, $0)
  - beat:     librosa  (tempo, beats, downbeats, sections)
  - clips:    router.py (Wan/LTX local by default), or your own footage folder
  - assembly: ffmpeg (cut on beat + lyric subtitles + one-click look)

The heavy steps (transcribe/analyze) need their libs installed and raise a clear
hint if missing. The pure-logic steps — edit map, SRT, ffmpeg command — run
anywhere and are unit-testable without audio.

CLI:
    python3 music_video.py ingest song.mp3                  # -> song.json
    python3 music_video.py plan   song.json --clips ./clips # print beat-synced edit map
    python3 music_video.py srt    song.json                 # -> song.srt (lyrics)
    python3 music_video.py render song.json --clips ./clips --audio song.mp3 \
            --out video.mp4 --look cinematic,grain --cut downbeat
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import filters as _filters
except Exception:  # noqa: BLE001
    _filters = None


class MissingDependency(RuntimeError):
    """A local analysis library (whisper/librosa) is not installed."""


# ──────────────────────────────────────────────────────────────────────────
# 1. Lyrics — transcription with word/line timecodes
# ──────────────────────────────────────────────────────────────────────────
@dataclass
class LyricLine:
    start: float
    end: float
    text: str


def transcribe(audio: str, model_size: str = "base") -> List[LyricLine]:
    """Transcribe lyrics with timecodes. Prefers faster-whisper, falls back to
    openai-whisper. Both run locally for free."""
    audio = os.path.expanduser(audio)
    # faster-whisper (CTranslate2 — fastest local option)
    try:
        from faster_whisper import WhisperModel  # type: ignore
        model = WhisperModel(model_size, device="auto", compute_type="auto")
        segments, _ = model.transcribe(audio, vad_filter=True)
        return [LyricLine(round(s.start, 3), round(s.end, 3), s.text.strip())
                for s in segments if s.text.strip()]
    except ImportError:
        pass
    # openai-whisper fallback
    try:
        import whisper  # type: ignore
    except ImportError:
        raise MissingDependency(
            "Install one transcriber: `pip install faster-whisper` (recommended) "
            "or `pip install openai-whisper`.")
    model = whisper.load_model(model_size)
    result = model.transcribe(audio)
    return [LyricLine(round(s["start"], 3), round(s["end"], 3), s["text"].strip())
            for s in result.get("segments", []) if s.get("text", "").strip()]


# ──────────────────────────────────────────────────────────────────────────
# 2. Beat / tempo / sections
# ──────────────────────────────────────────────────────────────────────────
def analyze_beats(audio: str) -> Dict[str, Any]:
    """Tempo, beat times, estimated downbeats (every 4th beat), and structural
    sections via librosa. Free, local."""
    audio = os.path.expanduser(audio)
    try:
        import librosa  # type: ignore
        import numpy as np  # type: ignore
    except ImportError:
        raise MissingDependency("Install beat detection: `pip install librosa`.")

    y, sr = librosa.load(audio, mono=True)
    duration = float(librosa.get_duration(y=y, sr=sr))
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beats = [round(float(t), 3) for t in librosa.frames_to_time(beat_frames, sr=sr)]
    # downbeats: approximate as every 4th beat (4/4 assumption)
    downbeats = beats[::4]

    # structural sections via spectral-clustering of the chroma self-similarity
    sections: List[Dict[str, Any]] = []
    try:
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        bounds = librosa.segment.agglomerative(chroma, 8)
        bound_times = librosa.frames_to_time(bounds, sr=sr)
        labels = ["intro", "verse", "build", "chorus", "verse", "chorus", "bridge", "outro"]
        pts = [0.0] + [round(float(t), 3) for t in bound_times] + [duration]
        pts = sorted(set(pts))
        for i in range(len(pts) - 1):
            sections.append({
                "start": pts[i], "end": pts[i + 1],
                "label": labels[i % len(labels)],
            })
    except Exception:  # noqa: BLE001 — sectioning is best-effort
        sections = [{"start": 0.0, "end": duration, "label": "full"}]

    return {
        "duration": round(duration, 3),
        "tempo": round(float(tempo), 2),
        "beats": beats,
        "downbeats": downbeats,
        "sections": sections,
    }


# ──────────────────────────────────────────────────────────────────────────
# 3. Ingest — combine into one song.json
# ──────────────────────────────────────────────────────────────────────────
def ingest(audio: str, out_json: Optional[str] = None,
           model_size: str = "base") -> Dict[str, Any]:
    audio = os.path.expanduser(audio)
    beat = analyze_beats(audio)
    try:
        lyrics = [asdict(l) for l in transcribe(audio, model_size)]
    except MissingDependency as e:
        lyrics = []
        print(f"  (lyrics skipped: {e})", file=sys.stderr)
    song = {"audio": str(Path(audio).resolve()), "lyrics": lyrics, **beat}
    out_json = out_json or str(Path(audio).with_suffix(".song.json"))
    Path(out_json).write_text(json.dumps(song, indent=2))
    print(f"  song.json -> {out_json}")
    print(f"  tempo {song['tempo']} BPM · {len(song['beats'])} beats · "
          f"{len(song['sections'])} sections · {len(lyrics)} lyric lines")
    return song


# ──────────────────────────────────────────────────────────────────────────
# 4. Beat-synced edit map  (PURE PYTHON — testable without audio)
# ──────────────────────────────────────────────────────────────────────────
@dataclass
class Cut:
    index: int
    start: float
    end: float
    duration: float
    clip: str
    lyric: str = ""


def _cut_points(song: Dict[str, Any], cut: str, every: int) -> List[float]:
    """Where to switch clips. cut in {beat, downbeat, bars, seconds}."""
    duration = song.get("duration") or (song["beats"][-1] if song.get("beats") else 0)
    if cut == "downbeat":
        pts = list(song.get("downbeats") or song.get("beats", []))
    elif cut == "bars":
        beats = song.get("beats", [])
        pts = beats[::max(1, every * 4)]
    elif cut == "seconds":
        n = max(1, int(duration // max(1, every)))
        pts = [round(i * every, 3) for i in range(n + 1)]
    else:  # every Nth beat
        beats = song.get("beats", [])
        pts = beats[::max(1, every)]
    pts = sorted({0.0, *[p for p in pts if 0 <= p <= duration], duration})
    return pts


def _lyric_at(song: Dict[str, Any], t0: float, t1: float) -> str:
    for ln in song.get("lyrics", []):
        # a lyric line that overlaps this cut window
        if ln["start"] < t1 and ln["end"] > t0:
            return ln["text"]
    return ""


def build_edit_map(song: Dict[str, Any], clips: List[str],
                   cut: str = "downbeat", every: int = 1,
                   min_dur: float = 0.4) -> List[Cut]:
    """Assign clips to beat-defined windows. Clips cycle if there aren't enough.

    cut:   downbeat | beat | bars | seconds
    every: Nth beat (cut=beat) or N bars (cut=bars) or N seconds (cut=seconds)
    """
    if not clips:
        raise ValueError("No clips provided to build an edit map.")
    pts = _cut_points(song, cut, every)
    cuts: List[Cut] = []
    ci = 0
    idx = 0
    for a, b in zip(pts, pts[1:]):
        if b - a < min_dur:           # merge ultra-short windows into the last cut
            if cuts:
                cuts[-1].end = b
                cuts[-1].duration = round(cuts[-1].end - cuts[-1].start, 3)
            continue
        cuts.append(Cut(
            index=idx, start=round(a, 3), end=round(b, 3),
            duration=round(b - a, 3),
            clip=clips[ci % len(clips)],
            lyric=_lyric_at(song, a, b),
        ))
        ci += 1
        idx += 1
    return cuts


# ──────────────────────────────────────────────────────────────────────────
# 5. Lyrics -> SRT  (PURE PYTHON)
# ──────────────────────────────────────────────────────────────────────────
def _ts(t: float) -> str:
    h = int(t // 3600); m = int((t % 3600) // 60); s = int(t % 60)
    ms = int(round((t - int(t)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def generate_srt(song: Dict[str, Any], out_path: Optional[str] = None) -> str:
    lines = []
    for i, ln in enumerate(song.get("lyrics", []), start=1):
        lines.append(str(i))
        lines.append(f"{_ts(ln['start'])} --> {_ts(ln['end'])}")
        lines.append(ln["text"])
        lines.append("")
    srt = "\n".join(lines)
    if out_path:
        Path(out_path).write_text(srt)
    return srt


# ──────────────────────────────────────────────────────────────────────────
# 6. Render — build the ffmpeg command (cut on beat + lyrics + look + audio)
# ──────────────────────────────────────────────────────────────────────────
def render_command(cuts: List[Cut], audio: str, out: str,
                   look: Optional[List[str]] = None,
                   size: str = "1080x1920", fps: int = 30,
                   srt_path: Optional[str] = None,
                   ffmpeg: str = "ffmpeg") -> List[str]:
    """Construct an ffmpeg argv that:
       trims each clip to its beat window -> scales to `size` -> concats in order
       -> applies the look -> burns lyric subtitles -> muxes the original audio.
    Deterministic and testable; the caller runs it."""
    if not cuts:
        raise ValueError("No cuts to render.")
    w, h = size.split("x")

    # one -i per unique clip (reused across cuts)
    unique: List[str] = []
    for c in cuts:
        if c.clip not in unique:
            unique.append(c.clip)
    clip_input = {clip: i for i, clip in enumerate(unique)}

    cmd: List[str] = [ffmpeg, "-y"]
    for clip in unique:
        cmd += ["-i", clip]
    audio_idx = len(unique)
    cmd += ["-i", audio]

    # filtergraph: trim+scale each segment, then concat
    fg: List[str] = []
    seg_labels: List[str] = []
    for n, c in enumerate(cuts):
        src = clip_input[c.clip]
        lbl = f"v{n}"
        fg.append(
            f"[{src}:v]trim=duration={c.duration},setpts=PTS-STARTPTS,"
            f"scale={w}:{h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h},fps={fps}[{lbl}]"
        )
        seg_labels.append(f"[{lbl}]")
    fg.append("".join(seg_labels) + f"concat=n={len(cuts)}:v=1:a=0[vcat]")

    last = "vcat"
    if look and _filters is not None:
        look_chain = _filters.chain(*look)
        if look_chain:
            fg.append(f"[{last}]{look_chain}[vlook]")
            last = "vlook"
    if srt_path:
        esc = srt_path.replace(":", r"\:").replace("'", r"\'")
        fg.append(f"[{last}]subtitles='{esc}'[vout]")
        last = "vout"

    cmd += ["-filter_complex", ";".join(fg)]
    cmd += ["-map", f"[{last}]", "-map", f"{audio_idx}:a"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-shortest", out]
    return cmd


def render(song: Dict[str, Any], clips: List[str], audio: str, out: str,
           cut: str = "downbeat", every: int = 1,
           look: Optional[List[str]] = None, size: str = "1080x1920",
           run: bool = True, ffmpeg: str = "ffmpeg") -> Dict[str, Any]:
    cuts = build_edit_map(song, clips, cut=cut, every=every)
    srt_path = str(Path(out).with_suffix(".srt"))
    generate_srt(song, srt_path)
    command = render_command(cuts, audio, out, look=look, size=size,
                             srt_path=srt_path if song.get("lyrics") else None,
                             ffmpeg=ffmpeg)
    result = {"cuts": len(cuts), "out": out, "command": command}
    if run:
        print(f"  rendering {len(cuts)} beat cuts -> {out}")
        proc = subprocess.run(command, capture_output=True, text=True)
        result["ok"] = proc.returncode == 0
        if proc.returncode != 0:
            result["error"] = proc.stderr[-600:]
    return result


# ──────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────
def _load_song(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text())


def _find_clips(folder: str) -> List[str]:
    exts = (".mp4", ".mov", ".webm", ".mkv")
    p = Path(os.path.expanduser(folder))
    return sorted(str(f) for f in p.iterdir() if f.suffix.lower() in exts) if p.exists() else []


def _cli(argv) -> int:
    ap = argparse.ArgumentParser(prog="music_video.py")
    sub = ap.add_subparsers(dest="cmd")

    i = sub.add_parser("ingest", help="mp3 -> song.json (lyrics + beats)")
    i.add_argument("audio"); i.add_argument("--out"); i.add_argument("--model", default="base")

    p = sub.add_parser("plan", help="print the beat-synced edit map")
    p.add_argument("song"); p.add_argument("--clips", required=True)
    p.add_argument("--cut", default="downbeat"); p.add_argument("--every", type=int, default=1)

    s = sub.add_parser("srt", help="song.json -> .srt lyrics")
    s.add_argument("song"); s.add_argument("--out")

    r = sub.add_parser("render", help="render the beat-matched video")
    r.add_argument("song"); r.add_argument("--clips", required=True)
    r.add_argument("--audio", required=True); r.add_argument("--out", required=True)
    r.add_argument("--cut", default="downbeat"); r.add_argument("--every", type=int, default=1)
    r.add_argument("--look", default=""); r.add_argument("--size", default="1080x1920")
    r.add_argument("--dry-run", action="store_true")

    args = ap.parse_args(argv)

    if args.cmd == "ingest":
        try:
            ingest(args.audio, args.out, args.model)
        except MissingDependency as e:
            print(f"✗ {e}"); return 1
        return 0

    if args.cmd == "plan":
        cuts = build_edit_map(_load_song(args.song), _find_clips(args.clips),
                              cut=args.cut, every=args.every)
        print(f"{len(cuts)} cuts  (cut={args.cut}, every={args.every})")
        for c in cuts:
            ly = f"  ♪ {c.lyric}" if c.lyric else ""
            print(f"  [{c.index:3d}] {c.start:7.2f}-{c.end:7.2f}s ({c.duration:4.2f}s) "
                  f"{Path(c.clip).name}{ly}")
        return 0

    if args.cmd == "srt":
        out = args.out or str(Path(args.song).with_suffix(".srt"))
        generate_srt(_load_song(args.song), out)
        print(f"  -> {out}")
        return 0

    if args.cmd == "render":
        song = _load_song(args.song)
        clips = _find_clips(args.clips)
        if not clips:
            print(f"✗ no clips found in {args.clips}"); return 1
        look = [x for x in args.look.split(",") if x] or None
        res = render(song, clips, args.audio, args.out, cut=args.cut,
                     every=args.every, look=look, size=args.size, run=not args.dry_run)
        if args.dry_run:
            print(f"DRY RUN — {res['cuts']} cuts. ffmpeg command:")
            print("  " + " ".join(res["command"]))
            return 0
        print("✓ done" if res.get("ok") else f"✗ ffmpeg failed: {res.get('error','')}")
        return 0 if res.get("ok") else 1

    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
