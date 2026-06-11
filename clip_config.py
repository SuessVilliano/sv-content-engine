"""SV Content Engine — Configuration"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent

# ─── Twitch ──────────────────────────────────────────────────────────────────
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID", "")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET", "")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL", "suessvillano")
TWITCH_WEBHOOK_SECRET = os.getenv("TWITCH_WEBHOOK_SECRET", "")
TWITCH_WEBHOOK_URL = os.getenv("TWITCH_WEBHOOK_URL", "")
TWITCH_WEBHOOK_PORT = int(os.getenv("TWITCH_WEBHOOK_PORT", "8080"))

# ─── AI APIs ─────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ─── Telegram ────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ─── YouTube ─────────────────────────────────────────────────────────────────
YOUTUBE_CLIENT_SECRET_PATH = os.getenv("YOUTUBE_CLIENT_SECRET_PATH", "")
YOUTUBE_TOKEN_PATH = os.getenv("YOUTUBE_TOKEN_PATH", str(BASE_DIR / "youtube_token.json"))

# ─── TikTok ──────────────────────────────────────────────────────────────────
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN", "")
TIKTOK_OPEN_ID = os.getenv("TIKTOK_OPEN_ID", "")

# ─── Instagram ───────────────────────────────────────────────────────────────
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_USER_ID = os.getenv("INSTAGRAM_USER_ID", "")
INSTAGRAM_VIDEO_CDN_BASE_URL = os.getenv("INSTAGRAM_VIDEO_CDN_BASE_URL", "")

# ─── Twitter/X ───────────────────────────────────────────────────────────────
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET", "")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")

# ─── Facebook ────────────────────────────────────────────────────────────────
FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "")

# ─── Kick.com ────────────────────────────────────────────────────────────────
KICK_CHANNEL = os.getenv("KICK_CHANNEL", "suessvillano")

# ─── Viloud (Trade Hybrid TV) ─────────────────────────────────────────────────
VILOUD_API_KEY    = os.getenv("VILOUD_API_KEY", "")
VILOUD_CHANNEL_ID = os.getenv("VILOUD_CHANNEL_ID", "6b3e6d6696fb33d051c1ca4b341d21cf")
CDN_BASE_URL      = os.getenv("CDN_BASE_URL", "")

# ─── Opus Clip ───────────────────────────────────────────────────────────────
OPUS_CLIP_API_KEY = os.getenv("OPUS_CLIP_API_KEY", "sk-6DW-CjS1wZG7wozl4w0wRPxK9INhR8A8gGIa9LBA")

# ─── Google Drive (backup VOD storage) ───────────────────────────────────────
GDRIVE_ENABLED             = _bool("GDRIVE_ENABLED", "true")
GDRIVE_CREDENTIALS_PATH    = os.getenv("GDRIVE_CREDENTIALS_PATH", str(BASE_DIR / "gdrive_credentials.json"))
GDRIVE_TOKEN_PATH          = os.getenv("GDRIVE_TOKEN_PATH", str(BASE_DIR / "gdrive_token.json"))
GDRIVE_RAW_VODS_FOLDER_ID  = os.getenv("GDRIVE_RAW_VODS_FOLDER_ID", "1YtmLRteyfzvEdBLZBNESofZsMBbc3_y5")
GDRIVE_CLIPS_FOLDER_ID     = os.getenv("GDRIVE_CLIPS_FOLDER_ID", "1i7HCwhX5w-ZmKEgq08w30YtUhCKtEeaA")
GDRIVE_PUBLISHED_FOLDER_ID = os.getenv("GDRIVE_PUBLISHED_FOLDER_ID", "1xqGvEb-5XYvxUjisSFVmuD7Gn4rI105W")

# ─── Music ───────────────────────────────────────────────────────────────────
_music_raw = os.getenv("MUSIC_TRACKS", "")
MUSIC_TRACKS = [p.strip() for p in _music_raw.split(",") if p.strip()] if _music_raw else []
MUSIC_VOLUME_DB = float(os.getenv("MUSIC_VOLUME_DB", "-18"))

# ─── Pipeline ────────────────────────────────────────────────────────────────
REVIEW_MODE = os.getenv("REVIEW_MODE", "review")  # "review" | "auto"
MIN_CLIP_DURATION = int(os.getenv("MIN_CLIP_DURATION", "15"))
MAX_CLIP_DURATION = int(os.getenv("MAX_CLIP_DURATION", "30"))
MAX_CLIPS_PER_STREAM = int(os.getenv("MAX_CLIPS_PER_STREAM", "8"))

OUTPUT_WIDTH = int(os.getenv("OUTPUT_WIDTH", "1080"))
OUTPUT_HEIGHT = int(os.getenv("OUTPUT_HEIGHT", "1920"))

# ─── Platform toggles ────────────────────────────────────────────────────────
def _bool(key, default="true"):
    return os.getenv(key, default).lower() in ("true", "1", "yes")



PLATFORMS = {
    "tiktok":    _bool("PLATFORM_TIKTOK"),
    "instagram": _bool("PLATFORM_INSTAGRAM"),
    "youtube":   _bool("PLATFORM_YOUTUBE"),
    "twitter":   _bool("PLATFORM_TWITTER"),
    "facebook":  _bool("PLATFORM_FACEBOOK"),
    "kick":      _bool("PLATFORM_KICK"),
}

# ─── Paths ───────────────────────────────────────────────────────────────────
ASSETS_DIR    = BASE_DIR / "assets"
MUSIC_DIR     = ASSETS_DIR / "music"
OUTPUT_DIR    = BASE_DIR / "output"
PENDING_DIR   = OUTPUT_DIR / "pending"
APPROVED_DIR  = OUTPUT_DIR / "approved"
REJECTED_DIR  = OUTPUT_DIR / "rejected"
PUBLISHED_DIR = OUTPUT_DIR / "published"
DOWNLOADS_DIR = OUTPUT_DIR / "downloads"

LOGO_PATH  = ASSETS_DIR / "logo.png"
INTRO_PATH = ASSETS_DIR / "generated_intro.mp4"
OUTRO_PATH = ASSETS_DIR / "generated_outro.mp4"

for d in [ASSETS_DIR, MUSIC_DIR, OUTPUT_DIR, PENDING_DIR, APPROVED_DIR,
          REJECTED_DIR, PUBLISHED_DIR, DOWNLOADS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─── Validation helper ───────────────────────────────────────────────────────
def check_config():
    """Returns dict of which API groups are configured."""
    return {
        "twitch":    bool(TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET),
        "openai":    bool(OPENAI_API_KEY),
        "anthropic": bool(ANTHROPIC_API_KEY),
        "telegram":  bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID),
        "youtube":   bool(YOUTUBE_CLIENT_SECRET_PATH and Path(YOUTUBE_CLIENT_SECRET_PATH).exists()),
        "tiktok":    bool(TIKTOK_ACCESS_TOKEN),
        "instagram": bool(INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_USER_ID),
        "twitter":   bool(TWITTER_API_KEY and TWITTER_API_SECRET),
        "facebook":  bool(FACEBOOK_ACCESS_TOKEN and FACEBOOK_PAGE_ID),
        "music":     bool(MUSIC_TRACKS),
        "kick":      True,  # No keys needed — Kick is public
        "viloud":    bool(VILOUD_API_KEY),
        "gdrive":    bool(GDRIVE_ENABLED and Path(GDRIVE_CREDENTIALS_PATH).exists()),
    }
