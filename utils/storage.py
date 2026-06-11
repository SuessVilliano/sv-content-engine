"""
Clip queue state machine.
pending → approved → published
pending → rejected
"""
import json
import shutil
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path

import clip_config as config
from utils.logger import get_logger

log = get_logger(__name__)

STATUS_PENDING   = "pending"
STATUS_APPROVED  = "approved"
STATUS_REJECTED  = "rejected"
STATUS_PUBLISHED = "published"


@dataclass
class ClipRecord:
    clip_id: str
    status: str
    vod_url: str
    start_time: float
    end_time: float
    clip_title: str
    hook: str
    caption: str
    reason: str
    video_path: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    published_at: str = ""
    publish_results: list = field(default_factory=list)
    music_track: int = 0
    telegram_message_id: int = 0


def new_clip_id() -> str:
    return f"clip_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"


def save_clip(record: ClipRecord):
    """Save clip metadata JSON to its status folder."""
    folder = _folder_for(record.status)
    path = folder / f"{record.clip_id}.json"
    path.write_text(json.dumps(asdict(record), indent=2))


def load_clip(clip_id: str) -> ClipRecord | None:
    """Load clip record by ID (searches all status folders)."""
    for folder in [config.PENDING_DIR, config.APPROVED_DIR,
                   config.REJECTED_DIR, config.PUBLISHED_DIR]:
        path = folder / f"{clip_id}.json"
        if path.exists():
            data = json.loads(path.read_text())
            return ClipRecord(**data)
    return None


def list_clips(status: str = None) -> list[ClipRecord]:
    """List all clips, optionally filtered by status."""
    folders = {
        STATUS_PENDING:   config.PENDING_DIR,
        STATUS_APPROVED:  config.APPROVED_DIR,
        STATUS_REJECTED:  config.REJECTED_DIR,
        STATUS_PUBLISHED: config.PUBLISHED_DIR,
    }
    if status:
        folders = {status: folders[status]}

    records = []
    for _, folder in folders.items():
        for json_file in sorted(folder.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True):
            try:
                data = json.loads(json_file.read_text())
                records.append(ClipRecord(**data))
            except Exception as e:
                log.warning("Could not load clip %s: %s", json_file, e)
    return records


def move_clip(clip_id: str, new_status: str) -> ClipRecord | None:
    """Move a clip to a new status."""
    record = load_clip(clip_id)
    if not record:
        log.warning("Clip not found: %s", clip_id)
        return None

    old_folder = _folder_for(record.status)
    new_folder = _folder_for(new_status)

    # Move JSON
    old_json = old_folder / f"{clip_id}.json"
    new_json = new_folder / f"{clip_id}.json"

    record.status = new_status
    if new_status == STATUS_PUBLISHED:
        record.published_at = datetime.now().isoformat()

    new_json.write_text(json.dumps(asdict(record), indent=2))
    old_json.unlink(missing_ok=True)

    # Move video file
    video = Path(record.video_path)
    if video.exists() and video.parent != new_folder:
        new_video = new_folder / video.name
        shutil.move(str(video), str(new_video))
        record.video_path = str(new_video)
        new_json.write_text(json.dumps(asdict(record), indent=2))

    log.info("Clip %s → %s", clip_id, new_status)
    return record


def queue_stats() -> dict:
    return {
        "pending":   len(list(config.PENDING_DIR.glob("*.json"))),
        "approved":  len(list(config.APPROVED_DIR.glob("*.json"))),
        "rejected":  len(list(config.REJECTED_DIR.glob("*.json"))),
        "published": len(list(config.PUBLISHED_DIR.glob("*.json"))),
    }


def _folder_for(status: str) -> Path:
    return {
        STATUS_PENDING:   config.PENDING_DIR,
        STATUS_APPROVED:  config.APPROVED_DIR,
        STATUS_REJECTED:  config.REJECTED_DIR,
        STATUS_PUBLISHED: config.PUBLISHED_DIR,
    }[status]
