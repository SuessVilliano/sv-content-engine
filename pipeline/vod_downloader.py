"""
SV Content Engine — VOD Downloader
Downloads Twitch VODs using yt-dlp.
"""
import subprocess
import json
import re
import time
from pathlib import Path

import requests

import clip_config as config
from utils.logger import get_logger

log = get_logger(__name__)


def get_twitch_token() -> str:
    """Get Twitch app access token."""
    r = requests.post("https://id.twitch.tv/oauth2/token", params={
        "client_id": config.TWITCH_CLIENT_ID,
        "client_secret": config.TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials",
    })
    r.raise_for_status()
    return r.json()["access_token"]


def get_broadcaster_id(channel: str, token: str) -> str:
    """Look up Twitch broadcaster ID by channel name."""
    r = requests.get(
        "https://api.twitch.tv/helix/users",
        params={"login": channel},
        headers={
            "Client-ID": config.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {token}",
        }
    )
    r.raise_for_status()
    data = r.json().get("data", [])
    if not data:
        raise ValueError(f"Twitch channel '{channel}' not found")
    return data[0]["id"]


def get_latest_vod(broadcaster_id: str, token: str) -> dict | None:
    """Get the most recent VOD for a broadcaster."""
    r = requests.get(
        "https://api.twitch.tv/helix/videos",
        params={"user_id": broadcaster_id, "type": "archive", "first": 1},
        headers={
            "Client-ID": config.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {token}",
        }
    )
    r.raise_for_status()
    data = r.json().get("data", [])
    return data[0] if data else None


def download_vod(
    vod_url: str,
    output_dir: Path,
    quality: str = "best[height<=1080]",
    retries: int = 3,
) -> Path:
    """
    Download a Twitch VOD using yt-dlp.
    Returns path to the downloaded file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract VOD ID from URL for filename
    vod_id = _extract_vod_id(vod_url)
    output_template = str(output_dir / f"vod_{vod_id}.%(ext)s")

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "-f", quality,
        "-o", output_template,
        "--no-warnings",
        "--progress",
        vod_url,
    ]

    log.info("Downloading VOD: %s", vod_url)

    for attempt in range(retries):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            log.info("Download complete")
            break
        except subprocess.CalledProcessError as e:
            if attempt < retries - 1:
                wait = (attempt + 1) * 30
                log.warning("Download failed (attempt %d/%d), retrying in %ds: %s",
                            attempt+1, retries, wait, e.stderr[-200:])
                time.sleep(wait)
            else:
                raise RuntimeError(f"VOD download failed after {retries} attempts:\n{e.stderr}")

    # Find the downloaded file
    for ext in ["mp4", "mkv", "ts", "webm"]:
        candidate = output_dir / f"vod_{vod_id}.{ext}"
        if candidate.exists():
            log.info("Downloaded: %s (%.1f GB)", candidate.name,
                     candidate.stat().st_size / (1024**3))
            return candidate

    # Fallback: find any new file
    files = sorted(output_dir.glob(f"vod_{vod_id}.*"), key=lambda f: f.stat().st_mtime)
    if files:
        return files[-1]

    raise FileNotFoundError(f"Could not find downloaded file for VOD {vod_id}")


def _extract_vod_id(url: str) -> str:
    """Extract numeric VOD ID from Twitch URL."""
    match = re.search(r'/videos?/(\d+)', url)
    if match:
        return match.group(1)
    # Try direct numeric
    match = re.search(r'(\d{8,})', url)
    if match:
        return match.group(1)
    raise ValueError(f"Could not extract VOD ID from URL: {url}")


def parse_timestamps(ts_string: str) -> list[tuple[float, float]]:
    """
    Parse manual timestamp string into (start, end) tuples in seconds.
    Format: "5:23-5:51,12:07-12:35" or "5:23-5:51" or "323-351" (raw seconds)
    """
    segments = []
    for part in ts_string.split(","):
        part = part.strip()
        if "-" not in part:
            continue
        start_str, end_str = part.split("-", 1)
        segments.append((_parse_time(start_str.strip()), _parse_time(end_str.strip())))
    return segments


def _parse_time(t: str) -> float:
    """Parse '5:23' → 323.0 or '323' → 323.0"""
    if ":" in t:
        parts = t.split(":")
        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    return float(t)
