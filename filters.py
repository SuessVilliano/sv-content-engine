#!/usr/bin/env python3
"""
SV Content Engine — Filters / Looks Library
===========================================

One-click cinematic "looks" — each is an ffmpeg filter chain you can stack on
any clip or final video. The studio exposes these as buttons; the engine applies
them during assembly. All free (ffmpeg), no per-use cost.

Two kinds of preset:
  - LOOKS:  linear, composable color/grain/contrast filters. Combine freely:
              filters.chain("cinematic", "grain", "vignette")
  - FRAMES: full filtergraphs for reframing/compositing (e.g. landscape -> 9:16
            with a blurred background pad). Use one at a time.

CLI:
    python3 filters.py list
    python3 filters.py chain cinematic grain vignette
    python3 filters.py vf cinematic grain        # just the -vf string
    python3 filters.py reframe vertical_blur_pad
"""
from __future__ import annotations

import sys
from typing import Dict, List

# ──────────────────────────────────────────────────────────────────────────
# Composable looks — each value is a linear ffmpeg filter chain (comma-joined).
# Tuned to be robust across modern ffmpeg builds (no exotic filters).
# ──────────────────────────────────────────────────────────────────────────
LOOKS: Dict[str, str] = {
    # teal shadows + warm highlights, the default "music video / ad" grade
    "cinematic":   "curves=preset=medium_contrast,"
                   "colorbalance=rs=-0.06:bs=0.06:rh=0.06:bh=-0.06,"
                   "eq=saturation=1.12:gamma=0.98",
    "warm":        "colorbalance=rh=0.10:gh=0.02:bh=-0.10,eq=saturation=1.05",
    "cold":        "colorbalance=rh=-0.10:bh=0.10,eq=saturation=1.05",
    "noir":        "hue=s=0,eq=contrast=1.35:brightness=-0.02",
    "vintage":     "curves=preset=vintage,eq=saturation=0.9",
    "faded":       "curves=preset=lighter,eq=saturation=0.82:contrast=0.95",
    "high_contrast": "eq=contrast=1.30:saturation=1.08",
    "neon":        "eq=saturation=1.65:contrast=1.10:brightness=0.02",
    "dreamy":      "gblur=sigma=1.4,eq=brightness=0.03:saturation=1.08",
    "moody":       "curves=preset=darker,colorbalance=bs=0.08:bh=-0.04,eq=saturation=0.95",
    "punch":       "unsharp=5:5:1.0,eq=saturation=1.2:contrast=1.12",
    # texture / finishing — stack these on top of a grade
    "grain":       "noise=alls=12:allf=t+u",
    "filmgrain":   "noise=alls=8:allf=t,eq=contrast=1.03",
    "vhs":         "rgbashift=rh=5:bh=-5,noise=alls=16:allf=t",
    "vignette":    "vignette=PI/4.5",
    "sharpen":     "unsharp=5:5:0.8",
    "soft":        "gblur=sigma=0.8",
}

# Aliases people will actually type
ALIASES = {
    "cinematic_teal": "cinematic", "bw": "noir", "blackwhite": "noir",
    "retro": "vintage", "glow": "dreamy", "crisp": "sharpen",
}


def resolve(name: str) -> str:
    name = name.strip().lower()
    name = ALIASES.get(name, name)
    if name not in LOOKS:
        raise KeyError(f"Unknown look '{name}'. Try: {', '.join(sorted(LOOKS))}")
    return name


def chain(*looks: str) -> str:
    """Compose looks into one ffmpeg -vf chain string. Order = render order."""
    parts: List[str] = []
    for look in looks:
        if not look:
            continue
        parts.append(LOOKS[resolve(look)])
    return ",".join(parts)


def vf_args(*looks: str) -> List[str]:
    """Return ['-vf', '<chain>'] ready to splice into an ffmpeg argv."""
    c = chain(*looks)
    return ["-vf", c] if c else []


# ──────────────────────────────────────────────────────────────────────────
# Reframe / composite — full filtergraphs (use one at a time, not in chain()).
# ──────────────────────────────────────────────────────────────────────────
def vertical_blur_pad(w: int = 1080, h: int = 1920) -> str:
    """Fit any aspect into vertical w:h with a blurred fill background.

    The standard "looks pro on Reels/TikTok" treatment for landscape footage.
    """
    return (
        f"split[o][b];"
        f"[b]scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},gblur=sigma=24[bg];"
        f"[o]scale={w}:{h}:force_original_aspect_ratio=decrease[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2"
    )


def vertical_crop(w: int = 1080, h: int = 1920) -> str:
    """Center-crop hard to vertical (fills frame, loses the sides)."""
    return (f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}")


FRAMES = {
    "vertical_blur_pad": vertical_blur_pad,
    "vertical_crop": vertical_crop,
}


# ──────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────
def _cli(argv) -> int:
    cmd = argv[0] if argv else "list"
    if cmd == "list":
        print("LOOKS (composable):")
        for k in sorted(LOOKS):
            print(f"  {k:14s} {LOOKS[k]}")
        print("\nALIASES:")
        for a, t in sorted(ALIASES.items()):
            print(f"  {a:14s} -> {t}")
        print("\nFRAMES (use alone):")
        for k in FRAMES:
            print(f"  {k}")
        return 0
    if cmd == "chain":
        print(chain(*argv[1:]))
        return 0
    if cmd == "vf":
        print(" ".join(vf_args(*argv[1:])))
        return 0
    if cmd == "reframe":
        name = argv[1] if len(argv) > 1 else "vertical_blur_pad"
        if name not in FRAMES:
            print(f"Unknown frame '{name}'. Options: {', '.join(FRAMES)}")
            return 1
        print(FRAMES[name]())
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
