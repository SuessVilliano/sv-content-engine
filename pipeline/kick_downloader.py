"""
SV Content Engine — Kick.com VOD Downloader
Downloads VODs and clips from kick.com using yt-dlp.

Kick.com is supported natively by yt-dlp.
VOD URLs: https://kick.com/video/{vod_id}
          https://kick.com/{channel}?vod={vod_id}
Clip URLs: https://kick.com/{channel}/clips/{clip_id}
"""
import re
import subprocess
import requests
from pathlib import Path
from utils.logger import get_logger

log = get_logger(__name__)

KICK_CHANNEL = "suessvillano"


# ─── Channel / VOD info ───────────────────────────────────────────

def get_channel_info(channel_slug: str = KICK_CHANNEL) -> dict:
    """Get Kick channel info including live status."""
    try:
        resp = requests.get(
            f"https://kick.com/api/v2/channels/{channel_slug}",
            headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        if e.response and e.response.status_code == 404:
            return {"error": "channel_not_found",
                    "message": f"No Kick account found for '{channel_slug}'. Create one at kick.com"}
        raise


def get_vods(channel_slug: str = KICK_CHANNEL, limit: int = 10) -> list:
    """
    Get list of VODs (past broadcasts) from Kick channel.
    Returns list of dicts: {id, title, source, duration, created_at}
    """
    try:
        resp = requests.get(
            f"https://kick.com/api/v2/channels/{channel_slug}/videos",
            params={"sort": "date", "limit": limit},
            headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", data) if isinstance(data, dict) else data
    except Exception as e:
        log.error("Could not fetch Kick VODs: %s", e)
        return []


def get_latest_vod(channel_slug: str = KICK_CHANNEL) -> dict | None:
    """Get the most recent VOD."""
    vods = get_vods(channel_slug, limit=1)
    return vods[0] if vods else None


def vod_url(vod_id: str) -> str:
    """Construct a Kick VOD URL from ID."""
    return f"https://kick.com/video/{vod_id}"


# ─── Download ─────────────────────────────────────────────────────

def download_vod(
    url: str,
    output_dir: Path,
    quality: str = "best",
    retries: int = 3,
) -> Path:
    """
    Download a Kick VOD or clip using yt-dlp.

    url:        Kick VOD/clip URL
    output_dir: Directory to save the video
    quality:    yt-dlp format string (default: best)
    retries:    Number of retry attempts on failure

    Returns Path to the downloaded file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_template = str(output_dir / "%(id)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "--no-warnings",
        "-f", quality,
        "-o", output_template,
        "--retries", str(retries),
        "--concurrent-fragments", "4",
        "--no-playlist",
        "--print", "after_move:filepath",
        url,
    ]

    log.info("Downloading Kick VOD: %s", url)
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed:\n{result.stderr[-1000:]}")

    # Get downloaded file path from stdout
    filepath = result.stdout.strip().split("\n")[-1]
    if filepath and Path(filepath).exists():
        log.info("Downloaded: %s", filepath)
        return Path(filepath)

    # Fallback: find newest file in output_dir
    files = sorted(output_dir.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True)
    mp4_files = [f for f in files if f.suffix in (".mp4", ".mkv", ".ts")]
    if mp4_files:
        return mp4_files[0]

    raise FileNotFoundError(f"Could not locate downloaded file in {output_dir}")


def parse_timestamps(ts_string: str) -> list[tuple[float, float]]:
    """
    Parse timestamp string into list of (start, end) float pairs.
    Same format as Twitch: "5:23-5:51,12:07-12:35"
    """
    pairs = []
    for segment in ts_string.split(","):
        segment = segment.strip()
        if "-" not in segment:
            continue
        start_str, end_str = segment.split("-", 1)

        def to_seconds(t: str) -> float:
            parts = t.strip().split(":")
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + float(parts[1])
            return float(parts[0])

        pairs.append((to_seconds(start_str), to_seconds(end_str)))
    return pairs


# ─── Clip posting (Kick does not have a public posting API yet) ────

def post_clip_to_kick(video_path: Path, title: str, description: str = "") -> dict:
    """
    Kick.com does not currently have a public API for posting clips.
    Clips on Kick are created through the dashboard or during live stream.

    This is a placeholder — check https://docs.kick.com for updates.
    When Kick releases a creator API, this will be wired up.
    """
    log.warning(
        "Kick clip posting API not yet available. "
        "Post manually at https://kick.com/dashboard or via OBS."
    )
    return {
        "platform": "kick",
        "success": False,
        "error": "Kick creator API not yet available for clip posting",
        "note": "You can create clips manually in your Kick dashboard during/after streams",
    }
