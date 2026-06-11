"""
SV Content Engine — Intro/Outro Generator
Generates branded 3-second 1080x1920 intro and outro using pure FFmpeg.
No After Effects, no external templates.
"""
import subprocess
import shutil
from pathlib import Path
from utils.logger import get_logger

log = get_logger(__name__)

GOLD   = "0xD4A017"
BLACK  = "0x000000"
WHITE  = "0xFFFFFF"
GRAY   = "0x1A1A1A"

W, H = 1080, 1920
FPS  = 30
DUR  = 3  # seconds


def _ffmpeg(*args, check=True):
    cmd = ["ffmpeg", "-y"] + list(args)
    log.debug("FFmpeg: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed:\n{result.stderr}")
    return result


def generate_intro(output_path: Path, logo_path: Path | None = None) -> Path:
    """
    Generate branded intro:
    - Black background
    - Gold accent bars (top + bottom)
    - SUESSVILLANO  white bold fade-in
    - DAY TRADING LIVE  gold subtitle fade-in
    - Logo overlay if logo_path provided
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    font_size_main = 72
    font_size_sub  = 38

    # Static gold bars at top and bottom — works on FFmpeg 4.4+
    bar_vf = (
        f"drawbox=x=0:y=0:w={W}:h=12:color={GOLD}:t=fill,"
        f"drawbox=x=0:y={H-12}:w={W}:h=12:color={GOLD}:t=fill"
    )
    text_vf = (
        f"drawtext=text='SUESSVILLANO':fontsize={font_size_main}:fontcolor=white:"
        f"x=(w-text_w)/2:y=(h-text_h)/2-60:"
        f"alpha='if(lt(t,0.3),0,if(lt(t,0.8),(t-0.3)/0.5,1))',"
        f"drawtext=text='DAY TRADING LIVE':fontsize={font_size_sub}:fontcolor={GOLD}:"
        f"x=(w-text_w)/2:y=(h-text_h)/2+40:"
        f"alpha='if(lt(t,0.6),0,if(lt(t,1.1),(t-0.6)/0.5,1))'"
    )

    if logo_path and Path(logo_path).exists():
        logo_y = H // 2 - 240
        _ffmpeg(
            "-f", "lavfi", "-i", f"color=c=black:size={W}x{H}:rate={FPS}:duration={DUR}",
            "-loop", "1", "-i", str(logo_path),
            "-filter_complex",
            f"[0:v]{bar_vf},{text_vf}[base];"
            f"[1:v]scale=200:200[logo];"
            f"[base][logo]overlay=(W-w)/2:{logo_y}:enable='gte(t,0.3)'[out]",
            "-map", "[out]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an",
            "-t", str(DUR),
            str(output_path)
        )
    else:
        _ffmpeg(
            "-f", "lavfi", "-i", f"color=c=black:size={W}x{H}:rate={FPS}:duration={DUR}",
            "-vf", f"{bar_vf},{text_vf}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an",
            "-t", str(DUR),
            str(output_path)
        )

    log.info("Intro generated: %s", output_path)
    return output_path


def generate_outro(output_path: Path) -> Path:
    """
    Generate branded outro:
    - Black background
    - Gold accent bars top + bottom
    - FOLLOW @suessvillano  large text
    - Platform list
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    _ffmpeg(
        "-f", "lavfi", "-i", f"color=c=black:size={W}x{H}:rate={FPS}:duration={DUR}",
        "-vf",
        f"drawbox=x=0:y=0:w={W}:h=12:color={GOLD}:t=fill,"
        f"drawbox=x=0:y={H-12}:w={W}:h=12:color={GOLD}:t=fill,"
        f"drawtext=text='FOLLOW':fontsize=60:fontcolor=white:"
        f"x=(w-text_w)/2:y=(h-text_h)/2-120:"
        f"alpha='if(lt(t,0.2),0,if(lt(t,0.7),(t-0.2)/0.5,1))',"
        f"drawtext=text='@suessvillano':fontsize=80:fontcolor={GOLD}:"
        f"x=(w-text_w)/2:y=(h-text_h)/2-50:"
        f"alpha='if(lt(t,0.4),0,if(lt(t,0.9),(t-0.4)/0.5,1))',"
        f"drawtext=text='LIVE EVERY TRADING DAY':fontsize=34:fontcolor=white:"
        f"x=(w-text_w)/2:y=(h-text_h)/2+60:"
        f"alpha='if(lt(t,0.6),0,if(lt(t,1.1),(t-0.6)/0.5,1))',"
        f"drawtext=text='TikTok  Instagram  YouTube  X':fontsize=28:fontcolor={GOLD}:"
        f"x=(w-text_w)/2:y=(h-text_h)/2+130:"
        f"alpha='if(lt(t,0.8),0,if(lt(t,1.3),(t-0.8)/0.5,1))'",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an",
        "-t", str(DUR),
        str(output_path)
    )

    log.info("Outro generated: %s", output_path)
    return output_path


def generate_both(intro_path: Path, outro_path: Path, logo_path: Path | None = None):
    """Generate both intro and outro. Called by main.py generate-intro command."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg not found. Install it: brew install ffmpeg  OR  apt install ffmpeg")

    log.info("Generating intro...")
    generate_intro(intro_path, logo_path)

    log.info("Generating outro...")
    generate_outro(outro_path)

    return intro_path, outro_path
