"""
SV Content Engine — Twitch Watcher
Registers Twitch EventSub webhook for stream.offline events.
When stream ends, triggers the VOD download + processing pipeline.
"""
import hashlib
import hmac
import json
import time
import threading
from pathlib import Path

import requests
from flask import Flask, request, jsonify

import clip_config as config
from utils.logger import get_logger

log = get_logger(__name__)

app = Flask(__name__)
_pipeline_callback = None   # Set by main.py after import


def set_pipeline_callback(fn):
    """Register the function to call when a stream ends."""
    global _pipeline_callback
    _pipeline_callback = fn


# ─── Twitch EventSub ─────────────────────────────────────────────────────────

def get_app_token() -> str:
    r = requests.post("https://id.twitch.tv/oauth2/token", params={
        "client_id": config.TWITCH_CLIENT_ID,
        "client_secret": config.TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials",
    })
    r.raise_for_status()
    return r.json()["access_token"]


def get_broadcaster_id(token: str) -> str:
    r = requests.get(
        "https://api.twitch.tv/helix/users",
        params={"login": config.TWITCH_CHANNEL},
        headers={"Client-ID": config.TWITCH_CLIENT_ID, "Authorization": f"Bearer {token}"},
    )
    r.raise_for_status()
    data = r.json().get("data", [])
    if not data:
        raise ValueError(f"Channel '{config.TWITCH_CHANNEL}' not found on Twitch")
    return data[0]["id"]


def register_eventsub(token: str, broadcaster_id: str) -> str:
    """Subscribe to stream.offline EventSub. Returns subscription ID."""
    # Delete any existing subscriptions for this broadcaster first
    _cleanup_subscriptions(token, broadcaster_id)

    r = requests.post(
        "https://api.twitch.tv/helix/eventsub/subscriptions",
        headers={"Client-ID": config.TWITCH_CLIENT_ID, "Authorization": f"Bearer {token}"},
        json={
            "type": "stream.offline",
            "version": "1",
            "condition": {"broadcaster_user_id": broadcaster_id},
            "transport": {
                "method": "webhook",
                "callback": f"{config.TWITCH_WEBHOOK_URL}/twitch/webhook",
                "secret": config.TWITCH_WEBHOOK_SECRET,
            }
        }
    )
    if r.status_code not in (200, 202):
        raise RuntimeError(f"EventSub subscription failed: {r.status_code} {r.text}")

    sub_id = r.json()["data"][0]["id"]
    log.info("EventSub subscribed: stream.offline for %s (id: %s)", config.TWITCH_CHANNEL, sub_id)
    return sub_id


def _cleanup_subscriptions(token: str, broadcaster_id: str):
    """Remove existing stream.offline subscriptions to avoid duplicates."""
    r = requests.get(
        "https://api.twitch.tv/helix/eventsub/subscriptions",
        headers={"Client-ID": config.TWITCH_CLIENT_ID, "Authorization": f"Bearer {token}"},
        params={"type": "stream.offline"},
    )
    if r.ok:
        for sub in r.json().get("data", []):
            if sub.get("condition", {}).get("broadcaster_user_id") == broadcaster_id:
                requests.delete(
                    "https://api.twitch.tv/helix/eventsub/subscriptions",
                    headers={"Client-ID": config.TWITCH_CLIENT_ID, "Authorization": f"Bearer {token}"},
                    params={"id": sub["id"]}
                )
                log.info("Removed old EventSub subscription: %s", sub["id"])


# ─── Flask webhook handler ────────────────────────────────────────────────────

@app.route("/twitch/webhook", methods=["POST"])
def twitch_webhook():
    """Receive Twitch EventSub webhook callbacks."""
    body = request.get_data()
    headers = request.headers

    # Verify signature
    if not _verify_signature(headers, body):
        log.warning("Invalid webhook signature — rejected")
        return jsonify({"error": "Invalid signature"}), 403

    msg_type = headers.get("Twitch-Eventsub-Message-Type", "")

    # Verification challenge (Twitch sends this on first subscription)
    if msg_type == "webhook_callback_verification":
        challenge = request.json.get("challenge")
        log.info("EventSub verification challenge — responding")
        return challenge, 200

    # Handle actual events
    if msg_type == "notification":
        event_data = request.json
        sub_type = event_data.get("subscription", {}).get("type")

        if sub_type == "stream.offline":
            broadcaster = event_data.get("event", {}).get("broadcaster_user_login")
            log.info("Stream offline: %s — triggering pipeline", broadcaster)

            # Fire pipeline in background thread so we can respond to Twitch immediately
            if _pipeline_callback:
                thread = threading.Thread(
                    target=_delayed_pipeline_start,
                    daemon=True
                )
                thread.start()

    return "", 204


def _delayed_pipeline_start():
    """Wait 3 minutes after stream ends for VOD to be available, then trigger."""
    log.info("Waiting 3 minutes for VOD to be available...")
    time.sleep(180)
    if _pipeline_callback:
        _pipeline_callback()


def _verify_signature(headers, body: bytes) -> bool:
    """Verify Twitch EventSub HMAC signature."""
    msg_id        = headers.get("Twitch-Eventsub-Message-Id", "")
    msg_timestamp = headers.get("Twitch-Eventsub-Message-Timestamp", "")
    msg_signature = headers.get("Twitch-Eventsub-Message-Signature", "")

    hmac_message = (msg_id + msg_timestamp).encode() + body
    expected = "sha256=" + hmac.new(
        config.TWITCH_WEBHOOK_SECRET.encode(),
        hmac_message,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, msg_signature)


# ─── Entry point ─────────────────────────────────────────────────────────────

def start_watcher(pipeline_fn=None):
    """Start the Flask webhook server and register EventSub."""
    if pipeline_fn:
        set_pipeline_callback(pipeline_fn)

    if not all([config.TWITCH_CLIENT_ID, config.TWITCH_CLIENT_SECRET, config.TWITCH_WEBHOOK_URL]):
        raise RuntimeError("Twitch credentials not configured. Check .env file.")

    log.info("Registering Twitch EventSub...")
    token = get_app_token()
    broadcaster_id = get_broadcaster_id(token)
    register_eventsub(token, broadcaster_id)

    log.info("Starting webhook server on port %d...", config.TWITCH_WEBHOOK_PORT)
    log.info("Webhook URL: %s/twitch/webhook", config.TWITCH_WEBHOOK_URL)
    app.run(host="0.0.0.0", port=config.TWITCH_WEBHOOK_PORT)
