#!/usr/bin/env python3
"""
SV Content Engine — Main CLI
Twitch → AI clips → Social media. Fully automated.

Usage:
  python main.py watch                             Start Twitch stream watcher
  python main.py process <vod_url>                 Process a specific VOD
  python main.py process <vod_url> --ts "5:23-5:51,12:07-12:35"  Manual timestamps
  python main.py publish                           Publish all approved clips
  python main.py bot                               Start Telegram review bot
  python main.py generate-intro                    Generate branded intro/outro
  python main.py status                            Show pipeline status
"""
import sys
import json
import time
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich import print as rprint

import clip_config as config
from utils.logger import get_logger
from utils.storage import list_clips, queue_stats, STATUS_APPROVED

log = get_logger("main")
console = Console()


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _run_full_pipeline(vod_url: str, manual_timestamps: str = None):
    """Core pipeline: download → transcribe → detect → edit → queue."""
    from pipeline.vod_downloader import download_vod, parse_timestamps, get_app_token, get_broadcaster_id, get_latest_vod
    from pipeline.ai_detector import transcribe_vod, detect_moments, ClipMoment
    from pipeline.clip_editor import render_clip
    from utils.storage import ClipRecord, new_clip_id, save_clip, STATUS_PENDING

    console.print(f"\n[bold gold1]SV Content Engine[/bold gold1] — Processing VOD: [cyan]{vod_url}[/cyan]\n")

    # 1. Download
    console.print("[bold]Step 1:[/bold] Downloading VOD...")
    vod_path = download_vod(vod_url, config.DOWNLOADS_DIR)
    console.print(f"  ✅ Downloaded: {vod_path.name}")

    # 2. Transcribe or use manual timestamps
    moments = []

    if manual_timestamps:
        console.print("[bold]Step 2:[/bold] Using manual timestamps...")
        from pipeline.vod_downloader import parse_timestamps
        ts_pairs = parse_timestamps(manual_timestamps)
        for i, (start, end) in enumerate(ts_pairs):
            moments.append(type('Moment', (), {
                'start_time': start,
                'end_time': min(end, start + config.MAX_CLIP_DURATION),
                'clip_title': f"Trading Moment {i+1}",
                'hook': "",
                'caption': f"Trading clip from @suessvillano #daytrading #futures #NQ",
                'reason': "Manual timestamp",
                'vod_url': vod_url,
            })())
        console.print(f"  ✅ {len(moments)} manual timestamps")
    else:
        console.print("[bold]Step 2:[/bold] Transcribing with Whisper...")
        segments = transcribe_vod(vod_path)
        console.print(f"  ✅ Transcribed {len(segments)} segments")

        console.print("[bold]Step 3:[/bold] Claude detecting best moments...")
        moments = detect_moments(segments, vod_url=vod_url)
        console.print(f"  ✅ Found {len(moments)} highlight moments")

    if not moments:
        console.print("[red]No moments detected. Exiting.[/red]")
        return

    # 3. Render clips
    console.print(f"\n[bold]Step 4:[/bold] Rendering {len(moments)} clips...")

    music_tracks = config.MUSIC_TRACKS
    default_music = Path(music_tracks[0]) if music_tracks else None

    clip_records = []
    for i, moment in enumerate(moments):
        clip_id = new_clip_id()
        console.print(f"  Rendering [{i+1}/{len(moments)}]: {moment.clip_title}")

        try:
            # Get whisper segments for this clip (if available)
            seg_list = segments if not manual_timestamps else None

            video_path = render_clip(
                vod_path=vod_path,
                start=moment.start_time,
                end=moment.end_time,
                output_dir=config.PENDING_DIR,
                clip_id=clip_id,
                segments=seg_list,
                music_path=default_music,
            )

            record = ClipRecord(
                clip_id=clip_id,
                status=STATUS_PENDING,
                vod_url=vod_url,
                start_time=moment.start_time,
                end_time=moment.end_time,
                clip_title=moment.clip_title,
                hook=moment.hook,
                caption=moment.caption,
                reason=moment.reason,
                video_path=str(video_path),
            )
            save_clip(record)
            clip_records.append(record)
            console.print(f"    ✅ {clip_id} ({moment.end_time - moment.start_time:.0f}s)")

        except Exception as e:
            console.print(f"    ❌ Failed: {e}")
            log.exception("Clip render failed for moment %d", i)

    console.print(f"\n[bold green]✅ {len(clip_records)} clips queued for review.[/bold green]")

    # 4. If review mode, send to Telegram
    if config.REVIEW_MODE == "review" and config.TELEGRAM_BOT_TOKEN:
        console.print("[bold]Step 5:[/bold] Sending to Telegram for review...")
        try:
            import asyncio
            from review.telegram_bot import send_clip_for_review, _app
            from telegram import Bot

            bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
            for record in clip_records:
                asyncio.run(_send_to_telegram(bot, record))
        except Exception as e:
            console.print(f"  ⚠️ Telegram send failed: {e}")
            console.print("  Clips are saved. Run `python main.py bot` to review them.")
    elif config.REVIEW_MODE == "auto":
        console.print("[bold]Step 5:[/bold] Auto-publishing...")
        _publish_approved()

    console.print(f"\nRun [cyan]python main.py status[/cyan] to check the queue.")


async def _send_to_telegram(bot, record):
    from review.telegram_bot import send_clip_for_review
    await send_clip_for_review(record)


def _publish_approved():
    """Publish all approved clips."""
    from pipeline.publisher import publish_clip
    from utils.storage import move_clip, STATUS_PUBLISHED

    approved = list_clips(STATUS_APPROVED)
    if not approved:
        console.print("[yellow]No approved clips to publish.[/yellow]")
        return

    console.print(f"Publishing {len(approved)} approved clip(s)...\n")

    for record in approved:
        console.print(f"  📤 {record.clip_title}")
        cdn_url = (
            config.INSTAGRAM_VIDEO_CDN_BASE_URL + Path(record.video_path).name
            if config.INSTAGRAM_VIDEO_CDN_BASE_URL else ""
        )
        results = publish_clip(
            video_path=Path(record.video_path),
            clip_id=record.clip_id,
            title=record.clip_title,
            caption=record.caption,
            cdn_url=cdn_url,
        )
        record.publish_results = [
            {"platform": r.platform, "success": r.success, "url": r.url, "error": r.error}
            for r in results
        ]
        move_clip(record.clip_id, STATUS_PUBLISHED)

        for r in results:
            icon = "✅" if r.success else "❌"
            console.print(f"    {icon} {r.platform}: {r.url or r.error}")


# ─── CLI commands ─────────────────────────────────────────────────────────────

@click.group()
def cli():
    """SV Content Engine — suessvillano Twitch Clip Pipeline"""
    pass


@cli.command()
@click.option("--platform", default="twitch", type=click.Choice(["twitch", "kick", "both"]),
              help="Which platform to watch (default: twitch)")
def watch(platform):
    """Start stream watcher — auto-process VOD when stream ends."""

    def _on_stream_end(vod_url_override=None):
        """Called when a stream ends on any platform."""
        if vod_url_override:
            console.print(f"\n[bold gold1]Stream ended! VOD: {vod_url_override}[/bold gold1]")
            _run_full_pipeline(vod_url_override)
            return

        from pipeline.vod_downloader import get_app_token, get_broadcaster_id, get_latest_vod
        console.print("\n[bold gold1]Twitch stream ended! Fetching latest VOD...[/bold gold1]")
        try:
            token = get_app_token()
            broadcaster_id = get_broadcaster_id(token)
            vod = get_latest_vod(broadcaster_id, token)
            if vod:
                vod_url = vod.get("url", f"https://www.twitch.tv/videos/{vod['id']}")
                console.print(f"VOD found: {vod_url}")
                _run_full_pipeline(vod_url)
            else:
                console.print("[red]No VOD found after stream.[/red]")
        except Exception as e:
            log.exception("Twitch pipeline failed: %s", e)

    import threading

    if platform in ("twitch", "both"):
        from pipeline.twitch_watcher import start_watcher as twitch_watcher
        if platform == "both":
            t = threading.Thread(target=twitch_watcher, args=(_on_stream_end,), daemon=True)
            t.start()
            console.print("[bold]Twitch watcher started in background[/bold]")
        else:
            twitch_watcher(_on_stream_end)

    if platform in ("kick", "both"):
        from pipeline.kick_watcher import start_watcher as kick_watcher

        def on_kick_end(vod_url):
            _on_stream_end(vod_url)

        console.print("[bold]Starting Kick.com watcher...[/bold]")
        console.print("[dim](Create your Kick account at kick.com/signup to enable this)[/dim]")
        kick_watcher(on_kick_end)


@cli.command(name="watch-kick")
def watch_kick():
    """Start Kick.com stream watcher specifically."""
    from pipeline.kick_watcher import start_watcher, get_channel_status
    from pipeline.kick_downloader import get_channel_info

    console.print("[bold gold1]Checking Kick.com channel...[/bold gold1]")
    info = get_channel_info()
    if "error" in info:
        console.print(f"[yellow]{info['message']}[/yellow]")
        console.print("  Once you create a Kick account, run this again to start watching.")
        return

    channel_name = info.get("slug", "suessvillano")
    console.print(f"[green]Kick channel found:[/green] {channel_name}")

    live = info.get("livestream")
    if live:
        console.print("[bold red]🔴 LIVE RIGHT NOW[/bold red]")
    else:
        console.print("[dim]Not currently live — watching for next stream...[/dim]")

    def on_stream_end(vod_url):
        _run_full_pipeline(vod_url)

    start_watcher(on_stream_end)


@cli.command()
@click.argument("vod_url")
@click.option("--ts", "--timestamps", default=None,
              help='Manual timestamps e.g. "5:23-5:51,12:07-12:35"')
def process(vod_url, ts):
    """Process a specific Twitch VOD URL."""
    _run_full_pipeline(vod_url, manual_timestamps=ts)


@cli.command()
def publish():
    """Publish all approved clips to social media."""
    _publish_approved()


@cli.command()
def bot():
    """Start the Telegram review bot."""
    from review.telegram_bot import run_bot
    console.print("[bold]Starting Telegram bot...[/bold]")
    run_bot()


@cli.command(name="generate-intro")
def generate_intro():
    """Generate branded intro and outro videos."""
    from pipeline.intro_generator import generate_both

    console.print("[bold gold1]Generating intro/outro...[/bold gold1]")

    logo = config.LOGO_PATH if config.LOGO_PATH.exists() else None
    if logo:
        console.print(f"  Logo found: {logo}")
    else:
        console.print("  [yellow]No logo.png found in assets/ — generating text-only intro[/yellow]")
        console.print("  [dim]Add assets/logo.png to include your logo[/dim]")

    try:
        intro, outro = generate_both(config.INTRO_PATH, config.OUTRO_PATH, logo)
        console.print(f"\n  ✅ Intro: {intro}")
        console.print(f"  ✅ Outro: {outro}")
        console.print("\n[green]Done! Run generate-intro again anytime to update branding.[/green]")
    except FileNotFoundError as e:
        console.print(f"\n[red]FFmpeg not found.[/red] Install it first:")
        console.print("  macOS:  brew install ffmpeg")
        console.print("  Ubuntu: sudo apt install ffmpeg")
        console.print("  Windows: https://ffmpeg.org/download.html")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
def status():
    """Show pipeline status and config health."""
    console.print("\n[bold gold1]═══ SV Content Engine Status ═══[/bold gold1]\n")

    # Queue stats
    stats = queue_stats()
    table = Table(title="Clip Queue", show_header=True)
    table.add_column("Status", style="bold")
    table.add_column("Count", justify="right")
    table.add_row("⏳ Pending review", str(stats["pending"]))
    table.add_row("✅ Approved",        str(stats["approved"]))
    table.add_row("🚀 Published",       str(stats["published"]))
    table.add_row("❌ Rejected",        str(stats["rejected"]))
    console.print(table)

    # Config health
    cfg = config.check_config()
    console.print("\n[bold]API Configuration:[/bold]")
    for key, ok in cfg.items():
        icon = "✅" if ok else "⚠️ "
        console.print(f"  {icon} {key.upper()}")

    console.print(f"\n[bold]Review Mode:[/bold] {'🤖 AUTO (hands-off)' if config.REVIEW_MODE == 'auto' else '👁️  REVIEW (Telegram approval)'}")
    console.print(f"[bold]Channel:[/bold] {config.TWITCH_CHANNEL}")
    console.print(f"[bold]Music tracks:[/bold] {len(config.MUSIC_TRACKS)}")
    console.print(f"[bold]Intro:[/bold] {'✅' if config.INTRO_PATH.exists() else '⚠️  Not generated — run: python main.py generate-intro'}")
    console.print()


if __name__ == "__main__":
    cli()
