"""
SV Content Engine — AI Moment Detector
Uses Whisper to transcribe the VOD, then Claude to pick the best trading moments.
"""
import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict

import openai
import anthropic

import clip_config as config
from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class ClipMoment:
    start_time: float       # seconds from stream start
    end_time: float         # seconds
    clip_title: str         # "I Just Made $2,400 in 3 Minutes"
    hook: str               # scroll-stopping first line
    caption: str            # full social media caption
    reason: str             # internal note
    vod_url: str = ""

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


CLAUDE_SYSTEM_PROMPT = """You are a trading content analyst for Twitch channel "suessvillano" — a day trading streamer focused on Nasdaq futures (NQ/MNQ), Solana, forex futures, and gold.

Your job: analyze this stream transcript and identify the 5-8 best moments for short-form social media clips (15-30 seconds each).

Look for:
- Big wins or losses ("I'm up $X", "I just took $X profit", significant PnL moments)
- Key trade setups being explained (order blocks, liquidity sweeps, key levels, ICT concepts)
- Emotional peaks (excitement, surprise, live reactions to big moves)
- Clear teaching moments (concise explanations of one concept)
- Strong hooks — the first 3 seconds must make someone stop scrolling

For each moment return a JSON object:
{
  "start_time": <float — seconds from stream start>,
  "end_time": <float — max 30 seconds after start_time, min 15 seconds>,
  "clip_title": "<punchy 5-8 word title — be specific, include $ amounts if relevant>",
  "hook": "<the scroll-stopping first sentence a viewer sees>",
  "caption": "<full social media caption, 2-3 sentences, 5 relevant hashtags: #daytrading #futures #NQ #forex #tradingsetup etc>",
  "reason": "<1 sentence internal note on why this moment is worth clipping>"
}

Return ONLY a JSON array. No markdown, no commentary, no explanation. Just the array."""


def transcribe_vod(vod_path: Path) -> list[dict]:
    """
    Transcribe VOD audio using OpenAI Whisper.
    Returns list of segments: [{start, end, text}, ...]
    """
    if not config.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set — needed for Whisper transcription")

    client = openai.OpenAI(api_key=config.OPENAI_API_KEY)

    log.info("Transcribing %s with Whisper...", vod_path.name)
    file_size_mb = vod_path.stat().st_size / (1024 * 1024)
    log.info("File size: %.1f MB", file_size_mb)

    with open(vod_path, "rb") as audio_file:
        # Whisper API limit is 25MB. For larger files, use chunked approach
        if file_size_mb > 24:
            log.warning("File >24MB — extracting audio first for Whisper")
            audio_path = _extract_audio(vod_path)
        else:
            audio_path = vod_path

        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=open(audio_path, "rb"),
            response_format="verbose_json",
            timestamp_granularities=["segment", "word"],
        )

    segments = [
        {"start": s.start, "end": s.end, "text": s.text}
        for s in transcript.segments
    ]
    log.info("Transcribed %d segments", len(segments))
    return segments


def _extract_audio(vod_path: Path) -> Path:
    """Extract audio track from video to mp3 for Whisper (handles large files)."""
    import subprocess
    audio_path = vod_path.with_suffix(".mp3")
    subprocess.run([
        "ffmpeg", "-y", "-i", str(vod_path),
        "-vn", "-acodec", "mp3", "-ab", "64k",
        str(audio_path)
    ], capture_output=True, check=True)
    return audio_path


def _transcript_to_text(segments: list[dict], max_chars: int = 80000) -> str:
    """Convert segments to timestamped text for Claude."""
    lines = []
    for seg in segments:
        ts = f"[{seg['start']:.1f}s]"
        lines.append(f"{ts} {seg['text'].strip()}")
    full = "\n".join(lines)
    if len(full) > max_chars:
        full = full[:max_chars] + "\n... [transcript truncated for length]"
    return full


def detect_moments(
    segments: list[dict],
    vod_url: str = "",
    max_clips: int = None,
) -> list[ClipMoment]:
    """
    Send transcript to Claude and get back a list of highlight moments.
    """
    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set — needed for moment detection")

    if max_clips is None:
        max_clips = config.MAX_CLIPS_PER_STREAM

    transcript_text = _transcript_to_text(segments)
    log.info("Sending %d chars to Claude for moment detection...", len(transcript_text))

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        system=CLAUDE_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Here is the stream transcript:\n\n{transcript_text}\n\nIdentify the best {max_clips} clips."
        }]
    )

    raw = message.content[0].text.strip()

    # Parse JSON
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Try extracting JSON array from response
        import re
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            raise RuntimeError(f"Claude returned non-JSON: {raw[:200]}")

    moments = []
    for item in data:
        # Clamp durations
        start = float(item["start_time"])
        end = float(item["end_time"])
        duration = end - start
        if duration < config.MIN_CLIP_DURATION:
            end = start + config.MIN_CLIP_DURATION
        elif duration > config.MAX_CLIP_DURATION:
            end = start + config.MAX_CLIP_DURATION

        moments.append(ClipMoment(
            start_time=start,
            end_time=end,
            clip_title=item.get("clip_title", "Trading Moment"),
            hook=item.get("hook", ""),
            caption=item.get("caption", ""),
            reason=item.get("reason", ""),
            vod_url=vod_url,
        ))

    log.info("Claude detected %d clip moments", len(moments))
    return moments


def parse_edit_command(command: str, clip_metadata: dict) -> dict:
    """
    Parse a natural language edit command from Telegram into structured edits.
    e.g. "trim 3 seconds from start" → {"trim_start": 3}
         "change caption to: New caption text" → {"caption": "New caption text"}
         "use music track 2" → {"music_track": 2}
    """
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    prompt = f"""You are parsing a clip editing command for the SV Content Engine.

Current clip metadata:
{json.dumps(clip_metadata, indent=2)}

User command: "{command}"

Return a JSON object with only the fields to change. Possible fields:
- trim_start: <float seconds to trim from beginning>
- trim_end: <float seconds to trim from end>
- caption: <new caption string>
- clip_title: <new title string>
- music_track: <int index 0-based, or null to remove music>
- hook: <new hook text>

Return ONLY the JSON object, no explanation."""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        log.warning("Could not parse edit command response: %s", raw)
        return {}
