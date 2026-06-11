"""
SV Content Engine — Kick.com Watcher
Polls Kick API for stream end events and triggers the pipeline.

Kick doesn't have webhooks/EventSub like Twitch, so we poll every 60s.
When a live stream ends, we wait 2 minutes for the VOD to be available,
then kick off the full pipeline.

Kick API: https://kick.com/api/v2/channels/{slug}
"""
import time
import threading
import requests
from utils.logger import get_logger

log = get_logger(__name__)

KICK_CHANNEL = "suessvillano"  # your Kick username
POLL_INTERVAL = 60             # seconds between checks


def get_channel_status(channel_slug: str) -> dict:
    """
    Fetch live status and latest VOD info from Kick public API.
    No auth required.
    """
    try:
        resp = requests.get(
            f"https://kick.com/api/v2/channels/{channel_slug}",
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0",
            },
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 404:
            log.warning("Kick channel not found: %s — create account at kick.com", channel_slug)
            return {}
        else:
            log.warning("Kick API returned %d", resp.status_code)
            return {}
    except Exception as e:
        log.error("Kick API error: %s", e)
        return {}


def get_latest_vod(channel_slug: str) -> dict | None:
    """
    Get the most recent VOD from a Kick channel.
    Returns VOD dict with id, title, url, duration, etc.
    """
    try:
        resp = requests.get(
            f"https://kick.com/api/v2/channels/{channel_slug}/videos",
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0",
            },
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            videos = data.get("data", data) if isinstance(data, dict) else data
            if videos:
                return videos[0] if isinstance(videos, list) else None
        return None
    except Exception as e:
        log.error("Kick VOD API error: %s", e)
        return None


def start_watcher(pipeline_fn, channel_slug: str = KICK_CHANNEL):
    """
    Poll Kick until the channel goes live, then wait for it to end,
    then trigger pipeline_fn(vod_url).

    Runs forever in the current thread.
    """
    log.info("Starting Kick watcher for channel: %s", channel_slug)

    was_live = False
    stream_end_time = None

    while True:
        try:
            channel = get_channel_status(channel_slug)

            if not channel:
                # Channel not found or API error — check if account exists
                log.debug("Kick channel unavailable, will retry...")
                time.sleep(POLL_INTERVAL)
                continue

            livestream = channel.get("livestream")
            is_live = livestream is not None and livestream.get("is_live", False)

            if is_live and not was_live:
                log.info("Kick stream STARTED: %s", channel_slug)
                was_live = True
                stream_end_time = None

            elif not is_live and was_live:
                log.info("Kick stream ENDED: %s — waiting 2 minutes for VOD...", channel_slug)
                was_live = False
                stream_end_time = time.time()

            elif stream_end_time and (time.time() - stream_end_time) >= 120:
                # 2 minutes have passed since stream ended — get the VOD
                stream_end_time = None
                log.info("Fetching latest Kick VOD...")

                vod = get_latest_vod(channel_slug)
                if vod:
                    vod_url = vod.get("source") or f"https://kick.com/{channel_slug}?vod={vod.get('id')}"
                    log.info("Kick VOD found: %s — triggering pipeline", vod_url)
                    # Run pipeline in background thread so watcher keeps polling
                    t = threading.Thread(target=pipeline_fn, args=(vod_url,), daemon=True)
                    t.start()
                else:
                    log.warning("No Kick VOD found after stream end")

        except Exception as e:
            log.error("Kick watcher error: %s", e)

        time.sleep(POLL_INTERVAL)
