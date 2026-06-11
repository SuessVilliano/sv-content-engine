"""
SV Content Engine — Multi-Platform Publisher
Posts approved clips to TikTok, Instagram Reels, YouTube Shorts, Twitter/X, Facebook.
"""
import os
import json
import time
import mimetypes
from pathlib import Path
from dataclasses import dataclass

import requests

import clip_config as config
from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class PublishResult:
    platform: str
    success: bool
    url: str = ""
    error: str = ""
    post_id: str = ""


# ─── YouTube Shorts ──────────────────────────────────────────────────────────

def post_youtube_short(video_path: Path, title: str, description: str) -> PublishResult:
    """Upload to YouTube Shorts using Google API client."""
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request

        SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

        creds = None
        token_path = Path(config.YOUTUBE_TOKEN_PATH)
        secret_path = config.YOUTUBE_CLIENT_SECRET_PATH

        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not secret_path or not Path(secret_path).exists():
                    return PublishResult("youtube", False, error="YouTube client_secret.json not found")
                flow = InstalledAppFlow.from_client_secrets_file(str(secret_path), SCOPES)
                creds = flow.run_local_server(port=0)
            token_path.write_text(creds.to_json())

        youtube = build("youtube", "v3", credentials=creds)

        # Add #Shorts to title for YouTube Shorts detection
        shorts_title = f"{title} #Shorts"[:100]
        shorts_desc = f"{description}\n\n#Shorts #daytrading #futures #NQ #suessvillano"

        body = {
            "snippet": {
                "title": shorts_title,
                "description": shorts_desc,
                "tags": ["daytrading", "futures", "NQ", "nasdaq", "suessvillano", "shorts"],
                "categoryId": "22",  # People & Blogs
            },
            "status": {"privacyStatus": "public"},
        }

        media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)
        request_yt = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)

        response = None
        while response is None:
            status, response = request_yt.next_chunk()
            if status:
                log.info("YouTube upload: %.0f%%", status.progress() * 100)

        video_id = response["id"]
        url = f"https://www.youtube.com/shorts/{video_id}"
        log.info("YouTube Shorts posted: %s", url)
        return PublishResult("youtube", True, url=url, post_id=video_id)

    except Exception as e:
        log.error("YouTube publish failed: %s", e)
        return PublishResult("youtube", False, error=str(e))


# ─── TikTok ──────────────────────────────────────────────────────────────────

def post_tiktok(video_path: Path, caption: str) -> PublishResult:
    """Upload to TikTok using Content Posting API v2."""
    try:
        if not config.TIKTOK_ACCESS_TOKEN:
            return PublishResult("tiktok", False, error="TIKTOK_ACCESS_TOKEN not set")

        headers = {"Authorization": f"Bearer {config.TIKTOK_ACCESS_TOKEN}"}
        video_size = video_path.stat().st_size

        # Step 1: Initialize upload
        init_r = requests.post(
            "https://open.tiktokapis.com/v2/post/publish/video/init/",
            headers={**headers, "Content-Type": "application/json; charset=UTF-8"},
            json={
                "post_info": {
                    "title": caption[:2200],
                    "privacy_level": "PUBLIC_TO_EVERYONE",
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": video_size,
                    "chunk_size": video_size,
                    "total_chunk_count": 1,
                }
            }
        )
        init_r.raise_for_status()
        init_data = init_r.json().get("data", {})
        publish_id = init_data.get("publish_id")
        upload_url = init_data.get("upload_url")

        if not upload_url:
            return PublishResult("tiktok", False, error=f"No upload URL: {init_r.text}")

        # Step 2: Upload video
        with open(video_path, "rb") as f:
            upload_r = requests.put(
                upload_url,
                data=f,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Range": f"bytes 0-{video_size-1}/{video_size}",
                    "Content-Length": str(video_size),
                }
            )
        upload_r.raise_for_status()

        log.info("TikTok posted (publish_id: %s)", publish_id)
        return PublishResult("tiktok", True, post_id=publish_id,
                             url="https://www.tiktok.com/@suessvillano")

    except Exception as e:
        log.error("TikTok publish failed: %s", e)
        return PublishResult("tiktok", False, error=str(e))


# ─── Instagram Reels ─────────────────────────────────────────────────────────

def post_instagram_reel(video_url: str, caption: str) -> PublishResult:
    """
    Upload Instagram Reel via Meta Graph API (two-step).
    Requires a public CDN URL for the video (not local file path).
    """
    try:
        if not config.INSTAGRAM_ACCESS_TOKEN or not config.INSTAGRAM_USER_ID:
            return PublishResult("instagram", False, error="Instagram credentials not set")
        if not video_url:
            return PublishResult("instagram", False, error="No CDN video URL for Instagram")

        base = f"https://graph.facebook.com/v19.0/{config.INSTAGRAM_USER_ID}"
        token = config.INSTAGRAM_ACCESS_TOKEN

        # Step 1: Create media container
        create_r = requests.post(f"{base}/media", params={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": token,
        })
        create_r.raise_for_status()
        container_id = create_r.json().get("id")

        if not container_id:
            return PublishResult("instagram", False, error=f"No container ID: {create_r.text}")

        # Wait for processing (poll up to 2 minutes)
        for _ in range(24):
            time.sleep(5)
            status_r = requests.get(
                f"https://graph.facebook.com/v19.0/{container_id}",
                params={"fields": "status_code", "access_token": token}
            )
            status_code = status_r.json().get("status_code")
            if status_code == "FINISHED":
                break
            elif status_code == "ERROR":
                return PublishResult("instagram", False, error="Instagram processing error")

        # Step 2: Publish
        pub_r = requests.post(f"{base}/media_publish", params={
            "creation_id": container_id,
            "access_token": token,
        })
        pub_r.raise_for_status()
        media_id = pub_r.json().get("id")

        log.info("Instagram Reel posted: %s", media_id)
        return PublishResult("instagram", True, post_id=media_id,
                             url="https://www.instagram.com/suessvillano")

    except Exception as e:
        log.error("Instagram publish failed: %s", e)
        return PublishResult("instagram", False, error=str(e))


# ─── Twitter/X ───────────────────────────────────────────────────────────────

def post_twitter(video_path: Path, caption: str) -> PublishResult:
    """Post video to Twitter/X using tweepy v4."""
    try:
        import tweepy

        auth = tweepy.OAuth1UserHandler(
            config.TWITTER_API_KEY,
            config.TWITTER_API_SECRET,
            config.TWITTER_ACCESS_TOKEN,
            config.TWITTER_ACCESS_SECRET,
        )
        api_v1 = tweepy.API(auth)

        # Upload media (chunked upload for video)
        log.info("Uploading video to Twitter...")
        media = api_v1.media_upload(
            filename=str(video_path),
            media_category="tweet_video",
        )
        media_id = media.media_id

        # Wait for processing
        for _ in range(30):
            time.sleep(5)
            status = api_v1.get_media_upload_status(media_id)
            processing = status.processing_info
            if processing:
                state = processing.get("state")
                if state == "succeeded":
                    break
                elif state == "failed":
                    return PublishResult("twitter", False, error="Twitter media processing failed")

        # Post tweet
        client_v2 = tweepy.Client(
            bearer_token=config.TWITTER_BEARER_TOKEN,
            consumer_key=config.TWITTER_API_KEY,
            consumer_secret=config.TWITTER_API_SECRET,
            access_token=config.TWITTER_ACCESS_TOKEN,
            access_token_secret=config.TWITTER_ACCESS_SECRET,
        )

        tweet_text = caption[:280]
        tweet = client_v2.create_tweet(text=tweet_text, media_ids=[str(media_id)])
        tweet_id = tweet.data["id"]

        url = f"https://twitter.com/suessvillano/status/{tweet_id}"
        log.info("Twitter posted: %s", url)
        return PublishResult("twitter", True, url=url, post_id=tweet_id)

    except Exception as e:
        log.error("Twitter publish failed: %s", e)
        return PublishResult("twitter", False, error=str(e))


# ─── Facebook ────────────────────────────────────────────────────────────────

def post_facebook(video_path: Path, caption: str) -> PublishResult:
    """Post video to Facebook Page using Graph API."""
    try:
        if not config.FACEBOOK_ACCESS_TOKEN or not config.FACEBOOK_PAGE_ID:
            return PublishResult("facebook", False, error="Facebook credentials not set")

        url = f"https://graph-video.facebook.com/v19.0/{config.FACEBOOK_PAGE_ID}/videos"

        with open(video_path, "rb") as f:
            r = requests.post(url, data={
                "description": caption,
                "access_token": config.FACEBOOK_ACCESS_TOKEN,
            }, files={"source": f})

        r.raise_for_status()
        video_id = r.json().get("id")

        log.info("Facebook posted: %s", video_id)
        return PublishResult("facebook", True, post_id=video_id,
                             url=f"https://www.facebook.com/{config.FACEBOOK_PAGE_ID}")

    except Exception as e:
        log.error("Facebook publish failed: %s", e)
        return PublishResult("facebook", False, error=str(e))


# ─── Orchestrator ─────────────────────────────────────────────────────────────

def generate_captions(moment_caption: str, platform: str) -> str:
    """Adapt caption for each platform's style using Claude."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

        platform_guides = {
            "tiktok":    "TikTok: punchy, hook-first, casual, 3-5 hashtags max, under 220 chars",
            "instagram": "Instagram: 2-3 sentences, 10-15 hashtags, line breaks for readability",
            "youtube":   "YouTube Shorts: keyword-optimized, searchable, 2-3 hashtags",
            "twitter":   "Twitter/X: under 240 chars total with hashtags, 2-3 hashtags",
            "facebook":  "Facebook: conversational, minimal hashtags, full sentence",
        }

        guide = platform_guides.get(platform, "concise, 3-5 hashtags")

        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": (
                    f"Rewrite this trading clip caption for {platform.upper()}.\n"
                    f"Style guide: {guide}\n"
                    f"Always include @suessvillano and relevant trading hashtags.\n"
                    f"Original: {moment_caption}\n\n"
                    f"Return ONLY the rewritten caption."
                )
            }]
        )
        return msg.content[0].text.strip()
    except Exception:
        return moment_caption


def publish_clip(
    video_path: Path,
    clip_id: str,
    title: str,
    caption: str,
    cdn_url: str = "",
) -> list[PublishResult]:
    """Publish a clip to all enabled platforms."""
    results = []

    if config.PLATFORMS.get("youtube"):
        yt_cap = generate_captions(caption, "youtube")
        results.append(post_youtube_short(video_path, title, yt_cap))

    if config.PLATFORMS.get("tiktok"):
        tt_cap = generate_captions(caption, "tiktok")
        results.append(post_tiktok(video_path, tt_cap))

    if config.PLATFORMS.get("instagram"):
        ig_cap = generate_captions(caption, "instagram")
        results.append(post_instagram_reel(cdn_url, ig_cap))

    if config.PLATFORMS.get("twitter"):
        tw_cap = generate_captions(caption, "twitter")
        results.append(post_twitter(video_path, tw_cap))

    if config.PLATFORMS.get("facebook"):
        fb_cap = generate_captions(caption, "facebook")
        results.append(post_facebook(video_path, fb_cap))

    for r in results:
        status = "✅" if r.success else "❌"
        log.info("%s %s: %s", status, r.platform, r.url or r.error)

    return results
