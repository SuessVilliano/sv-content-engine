"""
SV Content Engine — Telegram Review Bot
Sends clip previews to Jamaur for approval. Handles edit commands via chat.
"""
import asyncio
import json
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)

import clip_config as config
from utils.logger import get_logger
from utils.storage import (
    ClipRecord, load_clip, move_clip, save_clip,
    list_clips, queue_stats,
    STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED, STATUS_PUBLISHED,
)

log = get_logger(__name__)

_app: Application = None


def _keyboard(clip_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approve", callback_data=f"approve:{clip_id}"),
        InlineKeyboardButton("❌ Reject",  callback_data=f"reject:{clip_id}"),
        InlineKeyboardButton("✏️ Edit",    callback_data=f"edit:{clip_id}"),
    ]])


async def send_clip_for_review(record: ClipRecord):
    """Send a clip preview to Jamaur's Telegram for approval."""
    if not _app:
        log.error("Telegram app not initialized")
        return

    video_path = Path(record.video_path)
    if not video_path.exists():
        log.error("Video file not found: %s", video_path)
        return

    caption = (
        f"🎬 *New clip ready for review*\n\n"
        f"*{record.clip_title}*\n\n"
        f"📌 Hook: _{record.hook}_\n\n"
        f"⏱ Duration: {record.end_time - record.start_time:.0f}s\n"
        f"🎯 Why: {record.reason}\n\n"
        f"ID: `{record.clip_id}`"
    )

    try:
        with open(video_path, "rb") as f:
            msg = await _app.bot.send_video(
                chat_id=config.TELEGRAM_CHAT_ID,
                video=f,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=_keyboard(record.clip_id),
            )
        # Store Telegram message ID for later reference
        record.telegram_message_id = msg.message_id
        save_clip(record)
        log.info("Clip sent to Telegram for review: %s", record.clip_id)
    except Exception as e:
        log.error("Failed to send clip to Telegram: %s", e)


# ─── Callback handlers ────────────────────────────────────────────────────────

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Approve/Reject/Edit button taps."""
    query = update.callback_query
    await query.answer()

    data = query.data
    action, clip_id = data.split(":", 1)

    record = load_clip(clip_id)
    if not record:
        await query.edit_message_caption(caption=f"⚠️ Clip `{clip_id}` not found.")
        return

    if action == "approve":
        move_clip(clip_id, STATUS_APPROVED)
        await query.edit_message_caption(
            caption=f"✅ *Approved* — {record.clip_title}\n`{clip_id}`\n\nReady to publish. Use /publish to post now.",
            parse_mode="Markdown",
        )
        log.info("Clip approved via Telegram: %s", clip_id)

        # Auto-publish if REVIEW_MODE is auto
        if config.REVIEW_MODE == "auto":
            await _publish_clip_async(clip_id, context)

    elif action == "reject":
        move_clip(clip_id, STATUS_REJECTED)
        await query.edit_message_caption(
            caption=f"❌ *Rejected* — {record.clip_title}\n`{clip_id}`",
            parse_mode="Markdown",
        )

    elif action == "edit":
        await query.edit_message_caption(
            caption=(
                f"✏️ *Edit mode* — `{clip_id}`\n\n"
                f"Send me a command:\n"
                f"• `trim 3s start` — trim 3 seconds from beginning\n"
                f"• `trim 2s end` — trim from end\n"
                f"• `caption: your new caption text`\n"
                f"• `music 2` — use music track #2\n"
                f"• `title: new title`\n\n"
                f"Current clip: *{record.clip_title}*"
            ),
            parse_mode="Markdown",
        )
        context.user_data["editing_clip_id"] = clip_id


# ─── Command handlers ─────────────────────────────────────────────────────────

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = queue_stats()
    text = (
        f"📊 *SV Content Engine Status*\n\n"
        f"⏳ Pending review: {stats['pending']}\n"
        f"✅ Approved (ready): {stats['approved']}\n"
        f"🚀 Published: {stats['published']}\n"
        f"❌ Rejected: {stats['rejected']}\n\n"
        f"Mode: {'🤖 AUTO' if config.REVIEW_MODE == 'auto' else '👁️ REVIEW'}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_clips(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending = list_clips(STATUS_PENDING)[:5]
    approved = list_clips(STATUS_APPROVED)[:3]

    if not pending and not approved:
        await update.message.reply_text("No clips in queue right now.")
        return

    lines = ["*Clip Queue*\n"]
    if pending:
        lines.append("⏳ *Pending Review:*")
        for c in pending:
            dur = c.end_time - c.start_time
            lines.append(f"  • `{c.clip_id}` — {c.clip_title} ({dur:.0f}s)")

    if approved:
        lines.append("\n✅ *Approved (ready to publish):*")
        for c in approved:
            lines.append(f"  • `{c.clip_id}` — {c.clip_title}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    approved = list_clips(STATUS_APPROVED)
    if not approved:
        await update.message.reply_text("No approved clips to publish.")
        return

    await update.message.reply_text(f"🚀 Publishing {len(approved)} clip(s)...")

    for record in approved:
        await _publish_clip_async(record.clip_id, context)


async def cmd_auto_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config.REVIEW_MODE = "auto"
    await update.message.reply_text(
        "🤖 *Auto mode ON* — clips will be published immediately after rendering without review.",
        parse_mode="Markdown"
    )


async def cmd_auto_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config.REVIEW_MODE = "review"
    await update.message.reply_text(
        "👁️ *Review mode ON* — clips will be sent to you for approval before posting.",
        parse_mode="Markdown"
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*SV Content Engine Commands*\n\n"
        "/status — show queue stats\n"
        "/clips — list recent clips\n"
        "/publish — publish all approved clips\n"
        "/auto_on — switch to fully hands-off mode\n"
        "/auto_off — switch to review mode (default)\n"
        "/help — show this message\n\n"
        "*Edit commands* (reply after tapping ✏️ Edit):\n"
        "`trim 3s start` — trim beginning\n"
        "`caption: new caption` — update caption\n"
        "`music 2` — use music track 2\n"
        "`title: new title` — update title",
        parse_mode="Markdown"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle free-text edit commands."""
    clip_id = context.user_data.get("editing_clip_id")
    if not clip_id:
        await update.message.reply_text("No clip selected for editing. Tap ✏️ Edit on a clip first.")
        return

    command_text = update.message.text
    record = load_clip(clip_id)
    if not record:
        await update.message.reply_text(f"Clip {clip_id} not found.")
        context.user_data.pop("editing_clip_id", None)
        return

    # Parse with Claude
    from pipeline.ai_detector import parse_edit_command
    edits = parse_edit_command(command_text, {
        "clip_id": record.clip_id,
        "clip_title": record.clip_title,
        "caption": record.caption,
        "start_time": record.start_time,
        "end_time": record.end_time,
        "music_track": record.music_track,
    })

    if not edits:
        await update.message.reply_text("Couldn't parse that command. Try: `trim 3s start`, `caption: text`, `music 2`")
        return

    # Apply simple metadata edits immediately
    changed = []
    if "caption" in edits:
        record.caption = edits["caption"]
        changed.append("caption")
    if "clip_title" in edits:
        record.clip_title = edits["clip_title"]
        changed.append("title")
    if "music_track" in edits:
        record.music_track = int(edits["music_track"])
        changed.append("music track")

    needs_rerender = "trim_start" in edits or "trim_end" in edits or "music_track" in edits

    if needs_rerender:
        if "trim_start" in edits:
            record.start_time += float(edits["trim_start"])
            changed.append(f"trimmed {edits['trim_start']}s from start")
        if "trim_end" in edits:
            record.end_time -= float(edits["trim_end"])
            changed.append(f"trimmed {edits['trim_end']}s from end")

        save_clip(record)
        await update.message.reply_text(
            f"✏️ Updated: {', '.join(changed)}\n\nRe-rendering clip... (this takes ~30s)",
        )
        # Trigger re-render in background
        asyncio.create_task(_rerender_clip(record, update, context))
    else:
        save_clip(record)
        await update.message.reply_text(
            f"✅ Updated: {', '.join(changed)}\n\nClip `{clip_id}` is ready to approve.",
            parse_mode="Markdown"
        )

    context.user_data.pop("editing_clip_id", None)


async def _rerender_clip(record: ClipRecord, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Re-render a clip with updated parameters."""
    try:
        from pipeline.clip_editor import render_clip

        music_tracks = config.MUSIC_TRACKS
        music_path = Path(music_tracks[record.music_track]) if music_tracks and record.music_track < len(music_tracks) else None

        new_path = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: render_clip(
                vod_path=Path(record.vod_url) if Path(record.vod_url).exists() else None,
                start=record.start_time,
                end=record.end_time,
                output_dir=config.PENDING_DIR,
                clip_id=record.clip_id + "_v2",
                music_path=music_path,
            )
        )
        record.video_path = str(new_path)
        save_clip(record)
        await send_clip_for_review(record)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Re-render failed: {e}")


async def _publish_clip_async(clip_id: str, context: ContextTypes.DEFAULT_TYPE):
    """Publish a single clip and report results via Telegram."""
    from pipeline.publisher import publish_clip

    record = load_clip(clip_id)
    if not record:
        return

    video_path = Path(record.video_path)
    cdn_url = config.INSTAGRAM_VIDEO_CDN_BASE_URL + video_path.name if config.INSTAGRAM_VIDEO_CDN_BASE_URL else ""

    results = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: publish_clip(
            video_path=video_path,
            clip_id=clip_id,
            title=record.clip_title,
            caption=record.caption,
            cdn_url=cdn_url,
        )
    )

    move_clip(clip_id, STATUS_PUBLISHED)

    # Send results summary to Telegram
    lines = [f"🚀 *Published:* {record.clip_title}\n"]
    for r in results:
        status = "✅" if r.success else "❌"
        lines.append(f"{status} {r.platform.upper()}: {r.url or r.error}")

    await _app.bot.send_message(
        chat_id=config.TELEGRAM_CHAT_ID,
        text="\n".join(lines),
        parse_mode="Markdown",
    )


# ─── Entry point ─────────────────────────────────────────────────────────────

def run_bot():
    """Start the Telegram bot (blocking)."""
    global _app

    if not config.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set in .env")

    _app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    _app.add_handler(CommandHandler("start",    cmd_help))
    _app.add_handler(CommandHandler("help",     cmd_help))
    _app.add_handler(CommandHandler("status",   cmd_status))
    _app.add_handler(CommandHandler("clips",    cmd_clips))
    _app.add_handler(CommandHandler("publish",  cmd_publish))
    _app.add_handler(CommandHandler("auto_on",  cmd_auto_on))
    _app.add_handler(CommandHandler("auto_off", cmd_auto_off))
    _app.add_handler(CallbackQueryHandler(button_callback))
    _app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    log.info("Telegram bot started — waiting for commands")
    _app.run_polling()
