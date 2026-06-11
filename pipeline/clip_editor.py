"""
SV Content Engine — Clip Editor
FFmpeg-based pipeline: cut → vertical 9:16 → captions → intro/outro → music
"""
import subprocess
import json
import tempfile
import shutil
from pathlib import Path
from typing import Optional

import clip_config as config
from utils.logger import get_logger

log = get_logger(__name__)

W, H = config.OUTPUT_WIDTH, config.OUTPUT_HEIGHT  # 1080x1920


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    log.debug("FFmpeg: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"FFmpeg error:\n{result.stderr[-2000:]}")
    return result


def cut_clip(
    source: Path,
    start: float,
    duration: float,
    output: Path,
) -> Path:
    """Step 1: Cut raw clip from VOD."""
    _run([
        "ffmpeg", "-y",
        "-ss", str(start),
        "-t", str(duration),
        "-i", str(source),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        str(output)
    ])
    log.info("Cut clip: %s (%.1fs)", output.name, duration)
    return output


def to_vertical(source: Path, output: Path) -> Path:
    """
    Step 2: Reformat to 9:16 vertical (1080x1920).
    Strategy for trading streams:
    - Top 60% of frame: chart area (crop center of original)
    - Bottom 40%: black padding with speaker overlay (if webcam in corner)
    This preserves the chart which is the key content.
    """
    # Get source dimensions
    probe = subprocess.run([
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", str(source)
    ], capture_output=True, text=True)
    info = json.loads(probe.stdout)
    vid = next(s for s in info["streams"] if s["codec_type"] == "video")
    src_w = int(vid["width"])
    src_h = int(vid["height"])

    # Target top portion height in source (60% of output = 1152px)
    chart_h_out = int(H * 0.60)   # 1152
    chart_w_out = W                # 1080
    bottom_h    = H - chart_h_out  # 768

    # Scale source to fill chart area (crop to 16:9 first, then scale)
    # Crop source to 16:9 centered, then scale to chart_w_out x chart_h_out
    src_aspect = src_w / src_h
    chart_aspect = chart_w_out / chart_h_out  # ~0.9375

    if src_aspect > chart_aspect:
        # Source is wider — crop width
        crop_h = src_h
        crop_w = int(src_h * chart_aspect)
    else:
        # Source is taller — crop height
        crop_w = src_w
        crop_h = int(src_w / chart_aspect)

    crop_x = (src_w - crop_w) // 2
    crop_y = 0  # Keep top of frame (where chart is)

    vf = (
        f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y},"
        f"scale={chart_w_out}:{chart_h_out},"
        f"pad=width={W}:height={H}:x=0:y=0:color=black"
    )

    _run([
        "ffmpeg", "-y", "-i", str(source),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        str(output)
    ])
    log.info("Vertical reformat: %s", output.name)
    return output


def add_captions(
    source: Path,
    output: Path,
    segments: list[dict] | None = None,
    static_text: str = "",
) -> Path:
    """
    Step 3: Burn captions into video.
    If Whisper segments provided → word-level captions timed to speech.
    If static_text provided → single caption overlay.
    """
    if not segments and not static_text:
        # No captions to add — just copy
        shutil.copy(source, output)
        return output

    if segments:
        # Create SRT subtitle file
        srt_path = source.with_suffix(".srt")
        _write_srt(segments, srt_path)

        _run([
            "ffmpeg", "-y", "-i", str(source),
            "-vf", (
                f"subtitles={srt_path}:force_style='"
                f"FontName=Arial,FontSize=18,Bold=1,"
                f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
                f"Outline=2,Shadow=1,"
                f"Alignment=2,MarginV=80'"
            ),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "copy",
            str(output)
        ])
        srt_path.unlink(missing_ok=True)

    elif static_text:
        escaped = static_text.replace("'", "\\'").replace(":", "\\:")
        _run([
            "ffmpeg", "-y", "-i", str(source),
            "-vf", (
                f"drawtext=text='{escaped}':"
                f"fontfile=/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf:"
                f"fontsize=36:fontcolor=white:bordercolor=black:borderw=2:"
                f"x=(w-text_w)/2:y=h-text_h-80"
            ),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "copy",
            str(output)
        ])

    log.info("Captions added: %s", output.name)
    return output


def _write_srt(segments: list[dict], srt_path: Path):
    """Write Whisper segments to SRT subtitle file."""
    def fmt_time(t: float) -> str:
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines = []
    for i, seg in enumerate(segments, 1):
        lines.append(str(i))
        lines.append(f"{fmt_time(seg['start'])} --> {fmt_time(seg['end'])}")
        lines.append(seg["text"].strip())
        lines.append("")

    srt_path.write_text("\n".join(lines))


def prepend_intro(source: Path, intro: Path, output: Path) -> Path:
    """Step 4a: Concatenate intro before main clip."""
    if not intro.exists():
        log.warning("Intro not found at %s — skipping", intro)
        shutil.copy(source, output)
        return output

    return _concat_videos([intro, source], output)


def append_outro(source: Path, outro: Path, output: Path) -> Path:
    """Step 4b: Concatenate outro after main clip."""
    if not outro.exists():
        log.warning("Outro not found at %s — skipping", outro)
        shutil.copy(source, output)
        return output

    return _concat_videos([source, outro], output)


def _concat_videos(videos: list[Path], output: Path) -> Path:
    """Concatenate multiple video files using ffmpeg concat filter."""
    # Write concat list file
    list_file = output.parent / f"_concat_{output.stem}.txt"
    with open(list_file, "w") as f:
        for v in videos:
            f.write(f"file '{v.absolute()}'\n")

    _run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        str(output)
    ])
    list_file.unlink(missing_ok=True)
    return output


def mix_music(
    source: Path,
    music_path: Path,
    output: Path,
    volume_db: float = None,
) -> Path:
    """
    Step 5: Mix background music at low volume under the speech audio.
    Music loops if shorter than the clip.
    """
    if volume_db is None:
        volume_db = config.MUSIC_VOLUME_DB

    if not music_path.exists():
        log.warning("Music file not found: %s — skipping", music_path)
        shutil.copy(source, output)
        return output

    _run([
        "ffmpeg", "-y",
        "-i", str(source),
        "-stream_loop", "-1", "-i", str(music_path),
        "-filter_complex", (
            f"[1:a]volume={volume_db}dB[bg];"
            f"[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        ),
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        str(output)
    ])
    log.info("Music mixed at %sdB: %s", volume_db, output.name)
    return output


def render_clip(
    vod_path: Path,
    start: float,
    end: float,
    output_dir: Path,
    clip_id: str,
    segments: list[dict] | None = None,
    intro_path: Path | None = None,
    outro_path: Path | None = None,
    music_path: Path | None = None,
    music_volume_db: float = None,
) -> Path:
    """
    Full pipeline: cut → vertical → captions → intro → outro → music → final
    Returns path to final rendered clip.
    """
    if intro_path is None:
        intro_path = config.INTRO_PATH
    if outro_path is None:
        outro_path = config.OUTRO_PATH
    if music_volume_db is None:
        music_volume_db = config.MUSIC_VOLUME_DB

    tmp = output_dir / f"_tmp_{clip_id}"
    tmp.mkdir(exist_ok=True)
    duration = end - start

    try:
        # Step 1: Cut
        step1 = tmp / "01_cut.mp4"
        cut_clip(vod_path, start, duration, step1)

        # Step 2: Vertical
        step2 = tmp / "02_vertical.mp4"
        to_vertical(step1, step2)

        # Step 3: Captions
        step3 = tmp / "03_captions.mp4"
        # Adjust segment timestamps to be relative to clip start
        if segments:
            rel_segs = [
                {**s, "start": max(0, s["start"] - start), "end": max(0, s["end"] - start)}
                for s in segments
                if s["start"] >= start and s["start"] < end
            ]
        else:
            rel_segs = None
        add_captions(step2, step3, segments=rel_segs)

        # Step 4a: Prepend intro
        step4a = tmp / "04a_intro.mp4"
        prepend_intro(step3, Path(intro_path), step4a)

        # Step 4b: Append outro
        step4b = tmp / "04b_outro.mp4"
        append_outro(step4a, Path(outro_path), step4b)

        # Step 5: Mix music
        final = output_dir / f"{clip_id}.mp4"
        if music_path and Path(music_path).exists():
            mix_music(step4b, Path(music_path), final, music_volume_db)
        else:
            shutil.copy(step4b, final)

        log.info("Clip rendered: %s", final)
        return final

    finally:
        # Clean up temp files
        shutil.rmtree(tmp, ignore_errors=True)
