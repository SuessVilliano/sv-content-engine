"""
SV Content Engine — Google Drive Uploader
Auto-uploads VODs and clips to the TRADE HYBRID STREAM Drive folder.

Setup (one-time):
  1. Go to console.cloud.google.com → APIs & Services → Credentials
  2. Create OAuth 2.0 Client ID (Desktop app)
  3. Download JSON → save as gdrive_credentials.json in the project root
  4. First run will open a browser for auth → creates gdrive_token.json

  Folder IDs are pre-configured in clip_config.py (set via env or use defaults).
"""
import json
import os
import mimetypes
from pathlib import Path

import clip_config as config
from utils.logger import get_logger

log = get_logger(__name__)

# Lazy imports — only loaded when Drive is actually used
_service = None


def _get_service():
    """Lazy-initialise the Drive API service (OAuth 2 user credentials)."""
    global _service
    if _service is not None:
        return _service

    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError:
        raise RuntimeError(
            "Google Drive libraries not installed. Run:\n"
            "  pip install google-api-python-client google-auth-oauthlib google-auth-httplib2 --break-system-packages"
        )

    SCOPES = ["https://www.googleapis.com/auth/drive.file"]
    creds = None
    token_path = Path(config.GDRIVE_TOKEN_PATH)
    creds_path = Path(config.GDRIVE_CREDENTIALS_PATH)

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                raise FileNotFoundError(
                    f"Google Drive credentials not found at {creds_path}.\n"
                    "See pipeline/drive_uploader.py for setup instructions."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)

        token_path.write_text(creds.to_json())
        log.info("Google Drive token saved to %s", token_path)

    _service = build("drive", "v3", credentials=creds, cache_discovery=False)
    return _service


def upload_file(
    local_path: Path,
    folder_id: str,
    filename: str | None = None,
    resumable: bool = True,
) -> dict:
    """
    Upload a file to a specific Google Drive folder.
    Returns the Drive file metadata dict with id and webViewLink.
    """
    from googleapiclient.http import MediaFileUpload

    local_path = Path(local_path)
    if not local_path.exists():
        raise FileNotFoundError(f"File not found: {local_path}")

    name = filename or local_path.name
    mime, _ = mimetypes.guess_type(str(local_path))
    mime = mime or "application/octet-stream"

    file_size_gb = local_path.stat().st_size / (1024 ** 3)
    log.info("Uploading %s (%.2f GB) to Drive folder %s …", name, file_size_gb, folder_id)

    media = MediaFileUpload(str(local_path), mimetype=mime, resumable=resumable)
    file_metadata = {"name": name, "parents": [folder_id]}

    service = _get_service()
    drive_file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id,name,webViewLink,size")
        .execute()
    )

    log.info(
        "Uploaded to Drive: %s  →  %s",
        drive_file["name"],
        drive_file.get("webViewLink", ""),
    )
    return drive_file


def upload_vod(local_path: Path, vod_title: str | None = None) -> dict | None:
    """
    Upload a raw VOD file to the Raw VODs Drive folder.
    Returns Drive file metadata, or None if Drive is disabled / creds missing.
    """
    if not config.GDRIVE_ENABLED:
        log.debug("Google Drive upload skipped (GDRIVE_ENABLED=false)")
        return None

    try:
        return upload_file(
            local_path=local_path,
            folder_id=config.GDRIVE_RAW_VODS_FOLDER_ID,
            filename=vod_title or local_path.name,
        )
    except FileNotFoundError as e:
        # Missing credentials — warn once, don't crash the pipeline
        log.warning("Drive upload skipped: %s", e)
        return None
    except Exception as e:
        log.error("Drive upload failed for %s: %s", local_path.name, e, exc_info=True)
        return None


def upload_clip(local_path: Path, clip_title: str | None = None) -> dict | None:
    """Upload a processed clip to the Processed Clips Drive folder."""
    if not config.GDRIVE_ENABLED:
        return None
    try:
        return upload_file(
            local_path=local_path,
            folder_id=config.GDRIVE_CLIPS_FOLDER_ID,
            filename=clip_title or local_path.name,
        )
    except Exception as e:
        log.error("Drive clip upload failed: %s", e, exc_info=True)
        return None


def upload_published(local_path: Path, clip_title: str | None = None) -> dict | None:
    """Upload a published clip to the Published Drive folder."""
    if not config.GDRIVE_ENABLED:
        return None
    try:
        return upload_file(
            local_path=local_path,
            folder_id=config.GDRIVE_PUBLISHED_FOLDER_ID,
            filename=clip_title or local_path.name,
        )
    except Exception as e:
        log.error("Drive published upload failed: %s", e, exc_info=True)
        return None
