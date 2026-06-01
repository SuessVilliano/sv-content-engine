"""
SV CONTENT ENGINE — Dashboard v2
Mobile-first · Draft review workflow · Full content management
Run: python3 dashboard.py
Open: http://localhost:4444
"""
import os, json, subprocess, threading, urllib.request
from flask import Flask, send_file, jsonify, render_template_string, request, abort
from pathlib import Path
from datetime import datetime

# Generation status tracker
GEN_STATUS = {}  # day_num -> {"status": "generating|done|error", "message": "..."}

_MISSING_SECRETS = []
def _secret(name: str, default: str = "") -> str:
    """Read a credential from the environment. Never hardcode secrets in source —
    set them in the shell / .env. Missing ones are collected and warned about once
    at startup so a feature that needs them fails loudly, not silently."""
    val = os.environ.get(name, default)
    if not val:
        _MISSING_SECRETS.append(name)
    return val


# ── Multi-brand config layer ────────────────────────────────────────────
# The active brand (brands/_active.json or $SV_BRAND) drives all paths, voice,
# and routing. If the brand layer is absent we fall back to the original
# hardcoded Source Vessel defaults so this dashboard keeps working unchanged.
try:
    import brands as _brands
    BRAND = _brands.active_brand()
except Exception:  # noqa: BLE001 — never let config break the dashboard
    BRAND = None

if BRAND is not None:
    VOXCPM_API      = BRAND.voice.get("api_url", "http://localhost:8808/api/clone")
    SV_REF          = BRAND.voice.get("reference_audio", "")
    SV_REF_FALLBACK = BRAND.voice.get("fallback_reference", "")
else:
    VOXCPM_API = "http://localhost:8808/api/clone"
    # Use the clean Harrahs H1 reference (confirmed best quality)
    SV_REF     = "/Users/jamaurjohnson/Documents/SV_Content_Engine/assets/sv_voice_harrahs_clean.wav"
    SV_REF_FALLBACK = "/Users/jamaurjohnson/Documents/SV_Content_Engine/assets/sv_reference.wav"

def generate_voice_async(day_num, script_text):
    """Generate voice in background thread so approve is non-blocking"""
    key = f"day_{day_num:02d}"
    GEN_STATUS[key] = {"status": "generating", "message": f"Generating Day {day_num} voice..."}

    # Use best reference; fall back to generic if missing
    ref = SV_REF if os.path.exists(SV_REF) else SV_REF_FALLBACK
    out_path = f"/Users/jamaurjohnson/Documents/SV_Content_Engine/voice/day_{day_num:02d}_sv.wav"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    try:
        payload = json.dumps({
            "text": script_text,
            "reference_audio": ref,
        }).encode()
        req = urllib.request.Request(
            VOXCPM_API,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=600) as r:
            audio_data = r.read()

        with open(out_path, "wb") as f:
            f.write(audio_data)

        sz = os.path.getsize(out_path) // 1024
        GEN_STATUS[key] = {
            "status": "done",
            "message": f"Day {day_num} voice ready — {sz}KB saved",
            "file": out_path,
        }
        print(f"[Voice] Day {day_num} done: {sz}KB")
    except Exception as e:
        GEN_STATUS[key] = {"status": "error", "message": str(e)}
        print(f"[Voice] Day {day_num} error: {e}")

app = Flask(__name__)
# cap uploads (songs/videos) so a huge POST can't fill the disk
app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("SV_MAX_UPLOAD_MB", "300")) * 1024 * 1024

# ── Auth ────────────────────────────────────────────────────────────────
# If SV_DASHBOARD_TOKEN is set, every request must present it (header
# X-SV-Token or ?token=). Required when binding to a LAN; harmless on
# localhost. Without a token the dashboard can trigger paid generation and
# publish to socials, so set one before exposing it beyond 127.0.0.1.
SV_TOKEN = os.environ.get("SV_DASHBOARD_TOKEN", "")

@app.before_request
def _require_token():
    if not SV_TOKEN:
        return
    sent = request.headers.get("X-SV-Token") or request.args.get("token", "")
    if sent != SV_TOKEN:
        abort(401)

def _safe_path(base: str, *parts: str):
    """Join under `base` and confirm the result stays inside it. Returns the
    resolved path, or None on traversal (e.g. '../../etc/passwd')."""
    base_r = os.path.realpath(base)
    p = os.path.realpath(os.path.join(base_r, *parts))
    if p != base_r and not p.startswith(base_r + os.sep):
        return None
    return p

if BRAND is not None:
    BASE    = str(BRAND.base_dir)
    SHORTS  = str(BRAND.folder("shorts"))
    VOICE   = str(BRAND.folder("voice"))
    BEATS   = str(BRAND.folder("beats"))
    SCRIPTS = str(BRAND.folder("scripts"))
    DRAFTS  = str(BRAND.folder("drafts"))
else:
    BASE    = "/Users/jamaurjohnson/Documents/SV_Content_Engine"
    SHORTS  = f"{BASE}/shorts_reels"
    VOICE   = f"{BASE}/voice"
    BEATS   = f"{BASE}/assets/music"
    SCRIPTS = f"{BASE}/scripts"
    DRAFTS  = f"{BASE}/drafts"
THUMBS  = "/tmp/sv_dashboard_thumbs"

def _find_bin(name: str) -> str:
    import shutil as _sh
    for c in (os.environ.get(name.upper()), f"/opt/homebrew/bin/{name}",
              f"/usr/bin/{name}", name):
        if c and (_sh.which(c) or os.path.exists(c)):
            return c
    return name  # fall back to PATH lookup at call time

FFMPEG  = _find_bin("ffmpeg")
FFPROBE = _find_bin("ffprobe")

for d in [THUMBS, DRAFTS]:
    os.makedirs(d, exist_ok=True)

def list_files(folder, exts):
    if not os.path.exists(folder): return []
    out = []
    for f in sorted(os.listdir(folder)):
        if any(f.lower().endswith(e) for e in exts):
            p = os.path.join(folder, f)
            s = os.stat(p)
            out.append({"name": f, "size_mb": round(s.st_size/1024/1024, 1),
                        "modified": s.st_mtime, "path": p})
    return out

def make_thumb(video_path, thumb_path):
    if os.path.exists(thumb_path): return True
    try:
        subprocess.run([FFMPEG,"-y","-i",video_path,"-ss","0.5","-vframes","1",
                        "-vf","scale=360:-1",thumb_path], capture_output=True, timeout=10)
        return os.path.exists(thumb_path)
    except Exception: return False

def list_drafts():
    """List pending script drafts awaiting review"""
    drafts = []
    if os.path.exists(SCRIPTS):
        for f in sorted(os.listdir(SCRIPTS)):
            if f.endswith("_draft.txt") or f.endswith("_vox_ready.txt"):
                p = os.path.join(SCRIPTS, f)
                with open(p) as fp:
                    content = fp.read()
                day = None
                import re
                m = re.search(r"day_(\d+)", f)
                if m: day = int(m.group(1))
                # Check if video already exists for this day
                has_video = False
                if day:
                    vid = os.path.join(SHORTS, f"day{day:02d}_SV_FINAL.mp4")
                    has_video = os.path.exists(vid)
                drafts.append({
                    "name": f, "day": day,
                    "preview": content[:300],
                    "full": content,
                    "has_video": has_video,
                    "status": "produced" if has_video else "pending"
                })
    return drafts

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>SV Content Engine</title>
<script src="https://cdn.tailwindcss.com"></script>
<script>tailwind.config={theme:{extend:{colors:{gold:'#C9A84C',sv:'#00C851',panel:'#111118',border:'#1E1E2E'}}}}</script>
<style>
  *{box-sizing:border-box}
  body{background:#0A0A0A;color:#fff;font-family:system-ui,sans-serif;-webkit-font-smoothing:antialiased}
  .card{background:#111118;border:1px solid #1E1E2E}
  .pill{font-size:10px;font-weight:700;letter-spacing:.08em;padding:2px 8px;border-radius:9999px;text-transform:uppercase}
  ::-webkit-scrollbar{height:3px;width:3px}
  ::-webkit-scrollbar-track{background:#0A0A0A}
  ::-webkit-scrollbar-thumb{background:#2A2A3A;border-radius:3px}
  .tab-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none}
  .tab-scroll::-webkit-scrollbar{display:none}
  audio{accent-color:#C9A84C}
  @keyframes fadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
  .fade-up{animation:fadeUp .3s ease}
</style>
</head>
<body class="min-h-screen pb-24">

<!-- HEADER -->
<header class="border-b sticky top-0 z-50 px-4 md:px-8 py-3 flex items-center justify-between"
        style="background:rgba(10,10,10,.96);backdrop-filter:blur(16px);border-color:#1E1E2E">
  <div class="flex items-center gap-2.5">
    <div class="w-8 h-8 rounded-xl flex items-center justify-center font-black text-xs flex-shrink-0"
         style="background:linear-gradient(135deg,#C9A84C,#8B6914);color:#000">SV</div>
    <div>
      <p class="font-black text-white text-sm leading-tight">SV Content Engine</p>
      <p class="text-[10px] leading-tight" style="color:#555">Hybrid Funding · hybridfunding.co</p>
    </div>
  </div>
  <div class="flex items-center gap-2">
    <div class="w-1.5 h-1.5 rounded-full bg-sv animate-pulse"></div>
    <span class="text-[11px] hidden sm:block" style="color:#555" id="hdr-status">Loading…</span>
  </div>
</header>

<!-- STATS — 2 cols mobile, 4 cols desktop -->
<div class="px-4 md:px-8 pt-4 pb-2 grid grid-cols-2 md:grid-cols-4 gap-3">
  <div class="card rounded-xl p-3 md:p-4">
    <p class="text-2xl md:text-3xl font-black text-gold" id="stat-videos">—</p>
    <p class="text-[11px] mt-0.5" style="color:#555">Videos Ready</p>
  </div>
  <div class="card rounded-xl p-3 md:p-4">
    <p class="text-2xl md:text-3xl font-black text-sv" id="stat-voice">—</p>
    <p class="text-[11px] mt-0.5" style="color:#555">Voice Files</p>
  </div>
  <div class="card rounded-xl p-3 md:p-4">
    <p class="text-2xl md:text-3xl font-black" style="color:#A78BFA" id="stat-beats">—</p>
    <p class="text-[11px] mt-0.5" style="color:#555">Beats</p>
  </div>
  <div class="card rounded-xl p-3 md:p-4">
    <p class="text-2xl md:text-3xl font-black text-amber-400" id="stat-drafts">—</p>
    <p class="text-[11px] mt-0.5" style="color:#555">Drafts</p>
  </div>
</div>

<!-- TABS — horizontal scroll on mobile -->
<div class="tab-scroll px-4 md:px-8 pt-3 border-b" style="border-color:#1E1E2E">
  <div class="flex gap-0.5 min-w-max md:min-w-0">
    <button onclick="showTab('studio')"   id="tab-studio"   class="tab-btn active-tab  px-3 md:px-4 py-2.5 text-[13px] font-bold whitespace-nowrap rounded-t-lg border-b-2 transition-all">✨ Studio</button>
    <button onclick="showTab('videos')"   id="tab-videos"   class="tab-btn inactive-tab px-3 md:px-4 py-2.5 text-[13px] font-bold whitespace-nowrap rounded-t-lg border-b-2 transition-all">🎬 Videos</button>
    <button onclick="showTab('drafts')"   id="tab-drafts"   class="tab-btn inactive-tab px-3 md:px-4 py-2.5 text-[13px] font-bold whitespace-nowrap rounded-t-lg border-b-2 transition-all">📝 Drafts</button>
    <button onclick="showTab('voice')"    id="tab-voice"    class="tab-btn inactive-tab px-3 md:px-4 py-2.5 text-[13px] font-bold whitespace-nowrap rounded-t-lg border-b-2 transition-all">🎙️ Voice</button>
    <button onclick="showTab('beats')"    id="tab-beats"    class="tab-btn inactive-tab px-3 md:px-4 py-2.5 text-[13px] font-bold whitespace-nowrap rounded-t-lg border-b-2 transition-all">🎵 Beats</button>
    <button onclick="showTab('library')"  id="tab-library"  class="tab-btn inactive-tab px-3 md:px-4 py-2.5 text-[13px] font-bold whitespace-nowrap rounded-t-lg border-b-2 transition-all">📚 Library</button>
    <button onclick="showTab('pipeline')" id="tab-pipeline" class="tab-btn inactive-tab px-3 md:px-4 py-2.5 text-[13px] font-bold whitespace-nowrap rounded-t-lg border-b-2 transition-all">⚡ Pipeline</button>
    <button onclick="showTab('schedule')" id="tab-schedule" class="tab-btn inactive-tab px-3 md:px-4 py-2.5 text-[13px] font-bold whitespace-nowrap rounded-t-lg border-b-2 transition-all">📅 Schedule</button>
  </div>
</div>

<style>
  .active-tab{color:#C9A84C;border-color:#C9A84C}
  .inactive-tab{color:rgba(255,255,255,.3);border-color:transparent}
  .inactive-tab:hover{color:rgba(255,255,255,.6)}
</style>

<!-- CONTENT -->
<div class="px-4 md:px-8 py-4 md:py-6">

  <!-- STUDIO TAB — natural-language command bar -->
  <div id="tab-content-studio" class="tab-content">
    <div class="max-w-3xl mx-auto">
      <!-- drop-a-song -->
      <div id="dropzone" class="rounded-2xl p-5 mb-4 text-center cursor-pointer transition-all"
           style="border:1.5px dashed #2A2A3C;background:rgba(201,168,76,.03)"
           onclick="document.getElementById('song-file').click()">
        <p class="text-[13px] font-bold" style="color:#C9A84C">🎵 Drop a song to make a music video</p>
        <p class="text-[11px] mt-1" style="color:#555">MP3 / WAV — I'll find the beat & lyrics, then build to the beat</p>
        <input type="file" id="song-file" accept="audio/*" class="hidden" onchange="uploadSong(this.files[0])">
      </div>
      <div id="song-result" class="hidden card rounded-2xl p-4 mb-4"></div>

      <div class="card rounded-2xl p-4 md:p-5 mb-5">
        <p class="text-[11px] font-bold mb-2" style="color:#C9A84C;letter-spacing:.12em">✨ TYPE WHAT YOU WANT · IT BUILDS IT</p>
        <textarea id="cmd-input" rows="2"
          class="w-full rounded-xl px-4 py-3 text-sm bg-black/30 border outline-none resize-none"
          style="border-color:#2A2A3C;color:#eee"
          placeholder="e.g. make me a 30s moody trading short about discipline, cinematic look — or — music video for midnight_bloom.mp3, neon, cut on the beat"></textarea>
        <div class="flex items-center justify-between mt-3 gap-2">
          <p id="cmd-hint" class="text-[11px]" style="color:#555">Plan is free · I only build when you hit Build</p>
          <div class="flex gap-2">
            <button onclick="runCommand(true)"  id="cmd-plan-btn"
              class="px-4 py-2 rounded-xl text-[13px] font-bold border" style="border-color:#2A2A3C;color:#bbb">Plan</button>
            <button onclick="runCommand(false)" id="cmd-build-btn"
              class="px-5 py-2 rounded-xl text-[13px] font-black" style="background:#C9A84C;color:#0A0A0F">Build</button>
          </div>
        </div>
        <div id="cmd-plan" class="hidden mt-4 rounded-xl p-3 bg-black/20 border" style="border-color:#2A2A3C"></div>
      </div>

      <div class="flex items-center justify-between mb-3">
        <p class="text-[10px] font-bold" style="color:#555;letter-spacing:.1em">RECENT BUILDS</p>
        <button onclick="loadJobs()" class="text-[11px]" style="color:#666">↻ refresh</button>
      </div>
      <div id="jobs-list" class="space-y-3"></div>
      <p id="jobs-empty" class="hidden text-center py-16 text-sm" style="color:#444">
        Nothing built yet — type a request above and hit Build
      </p>
    </div>
  </div>

  <!-- VIDEOS TAB -->
  <div id="tab-content-videos" class="tab-content hidden">
    <p class="text-xs mb-4" style="color:#555">Tap any video to preview · Approve to send to YouTube</p>
    <div id="videos-grid"
         class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 md:gap-4"></div>
    <p id="videos-empty" class="hidden text-center py-20 text-sm" style="color:#444">
      No videos yet — add fal.ai credits and run the batch
    </p>
  </div>

  <!-- LIBRARY TAB — all created clips: finals, b-roll, masters -->
  <div id="tab-content-library" class="tab-content hidden">

    <!-- Finals / Reels -->
    <div class="mb-6">
      <p class="text-[10px] font-bold mb-3" style="color:#555;letter-spacing:.1em">🎬 FINAL REELS — READY TO POST</p>
      <div id="lib-finals-grid" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-2 md:gap-3"></div>
      <p id="lib-finals-empty" class="hidden text-sm py-4" style="color:#444">No final reels yet</p>
    </div>

    <!-- B-Roll Library -->
    <div class="mb-6">
      <p class="text-[10px] font-bold mb-3" style="color:#555;letter-spacing:.1em">🎥 B-ROLL LIBRARY — KLING GENERATED</p>
      <div id="lib-broll-grid" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-2 md:gap-3"></div>
      <p id="lib-broll-empty" class="hidden text-sm py-4" style="color:#444">No B-roll clips yet — run Kling generator</p>
    </div>

    <!-- Masters / Raw Recordings -->
    <div class="mb-6">
      <p class="text-[10px] font-bold mb-3" style="color:#555;letter-spacing:.1em">📼 MASTERS — RAW RECORDINGS</p>
      <div id="lib-masters-grid" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-2 md:gap-3"></div>
      <p id="lib-masters-empty" class="hidden text-sm py-4" style="color:#444">No master recordings yet</p>
    </div>

  </div>

  <!-- DRAFTS TAB -->
  <div id="tab-content-drafts" class="tab-content hidden">
    <div class="max-w-2xl">
      <div class="card rounded-xl p-4 mb-4">
        <p class="text-xs font-bold mb-1" style="color:#C9A84C;letter-spacing:.1em">HOW DRAFTS WORK</p>
        <p class="text-sm" style="color:rgba(255,255,255,.5)">
          Every morning Claude writes the day's script and presents it in conversation first.
          Review and approve or request changes. Once approved, voice + video generate automatically.
        </p>
      </div>
      <div id="drafts-list" class="space-y-3"></div>
      <p id="drafts-empty" class="hidden text-center py-20 text-sm" style="color:#444">
        No pending drafts — scripts approved and in production
      </p>
    </div>
  </div>

  <!-- VOICE TAB -->
  <div id="tab-content-voice" class="tab-content hidden">
    <div id="voice-list" class="space-y-2 max-w-2xl"></div>
    <p id="voice-empty" class="hidden text-center py-20 text-sm" style="color:#444">No voice files yet</p>
  </div>

  <!-- BEATS TAB -->
  <div id="tab-content-beats" class="tab-content hidden">
    <div id="beats-list" class="space-y-2 max-w-2xl"></div>
    <p id="beats-empty" class="hidden text-center py-20 text-sm" style="color:#444">Drop beats in beats/ folder</p>
  </div>

  <!-- PIPELINE TAB -->
  <div id="tab-content-pipeline" class="tab-content hidden">
    <div class="max-w-2xl space-y-3">
      <div class="card rounded-xl p-4">
        <p class="text-[10px] font-bold mb-3" style="color:#555;letter-spacing:.1em">CONTENT PROGRESS</p>
        <div id="pipeline-days" class="space-y-2"></div>
      </div>
      <div class="card rounded-xl p-4 space-y-2.5">
        <p class="text-[10px] font-bold mb-2" style="color:#555;letter-spacing:.1em">ENGINE STATUS</p>
        <div id="engine-status-list" class="space-y-2.5">
          <p class="text-xs" style="color:#555">Checking services...</p>
        </div>
      </div>
    </div>
  </div>

  <!-- SCHEDULE TAB -->
  <div id="tab-content-schedule" class="tab-content hidden">
    <div class="max-w-2xl space-y-6">

      <!-- Content Queue -->
      <div>
        <p class="text-[10px] font-bold mb-3" style="color:#555;letter-spacing:.1em">CONTENT QUEUE — READY TO SCHEDULE</p>
        <div id="schedule-queue" class="space-y-3">
          <p class="text-sm text-center py-8" style="color:#444">Loading queue...</p>
        </div>
      </div>

      <!-- Schedule Timeline -->
      <div>
        <p class="text-[10px] font-bold mb-3" style="color:#555;letter-spacing:.1em">SCHEDULED POSTS</p>
        <div id="schedule-timeline" class="space-y-2">
          <p class="text-sm text-center py-6" style="color:#444">No scheduled posts yet</p>
        </div>
      </div>

    </div>
  </div>

</div>

<!-- VIDEO PREVIEW MODAL — full screen on mobile -->
<div id="modal" class="fixed inset-0 z-50 hidden"
     style="background:rgba(0,0,0,.92);backdrop-filter:blur(12px)"
     onclick="closeModal(event)">
  <div class="flex flex-col h-full p-4 md:items-center md:justify-center" onclick="e=>e.stopPropagation()">
    <!-- Close button prominent on mobile -->
    <div class="flex items-center justify-between mb-3 md:hidden">
      <p id="modal-title-mobile" class="text-sm font-bold text-white truncate flex-1 mr-3"></p>
      <button onclick="closeModal()" class="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center text-white/60"
              style="background:#1E1E2E">✕</button>
    </div>
    <div class="w-full md:max-w-sm md:card md:rounded-2xl md:overflow-hidden flex-1 md:flex-none">
      <video id="modal-video" controls playsinline
             class="w-full rounded-xl md:rounded-none bg-black"
             style="max-height:calc(100vh - 200px);object-fit:contain"></video>
      <div class="mt-3 md:p-4 hidden md:flex items-center justify-between">
        <p id="modal-title" class="text-sm font-bold text-white/80 truncate"></p>
        <button onclick="closeModal()" class="text-white/30 hover:text-white/70 text-xs ml-4 flex-shrink-0">Close</button>
      </div>
    </div>
    <!-- Approve button on mobile -->
    <div class="mt-3 md:hidden" id="modal-approve-mobile">
      <button id="modal-approve-btn"
              class="w-full py-3.5 rounded-xl font-bold text-sm flex items-center justify-center gap-2"
              style="background:linear-gradient(135deg,#C9A84C,#8B6914);color:#000">
        ✅ Approve → Upload to YouTube
      </button>
    </div>
  </div>
</div>

<!-- APPROVAL FORM MODAL -->
<div id="approval-modal" class="fixed inset-0 z-60 hidden"
     style="background:rgba(0,0,0,.88);backdrop-filter:blur(12px);z-index:60"
     onclick="closeApproval(event)">
  <div class="flex items-end md:items-center justify-center min-h-full p-0 md:p-6"
       onclick="e=>e.stopPropagation()">
    <div class="w-full md:max-w-lg card rounded-t-2xl md:rounded-2xl p-5 md:p-6"
         style="max-height:90vh;overflow-y:auto">
      <div class="flex items-center justify-between mb-5">
        <div>
          <h2 class="text-lg font-black text-white">Upload to YouTube</h2>
          <p class="text-xs mt-0.5" style="color:#555" id="approval-filename"></p>
        </div>
        <button onclick="closeApproval()" class="w-8 h-8 rounded-lg flex items-center justify-center text-white/30 hover:text-white/70"
                style="background:#1E1E2E">✕</button>
      </div>
      <div class="space-y-4">
        <div>
          <label class="text-[10px] font-bold block mb-1.5" style="color:#555;letter-spacing:.1em">TITLE</label>
          <input id="yt-title" type="text" class="w-full rounded-xl px-3 py-3 text-sm text-white"
                 style="background:rgba(255,255,255,.05);border:1px solid #1E1E2E;outline:none;-webkit-appearance:none" />
        </div>
        <div>
          <label class="text-[10px] font-bold block mb-1.5" style="color:#555;letter-spacing:.1em">DESCRIPTION</label>
          <textarea id="yt-desc" rows="4" class="w-full rounded-xl px-3 py-3 text-sm text-white resize-none"
                    style="background:rgba(255,255,255,.05);border:1px solid #1E1E2E;outline:none;-webkit-appearance:none"></textarea>
        </div>
        <div>
          <label class="text-[10px] font-bold block mb-1.5" style="color:#555;letter-spacing:.1em">TAGS</label>
          <input id="yt-tags" type="text" class="w-full rounded-xl px-3 py-3 text-sm text-white"
                 style="background:rgba(255,255,255,.05);border:1px solid #1E1E2E;outline:none;-webkit-appearance:none"
                 placeholder="HybridFunding,PropTrading,FundedTrader" />
        </div>
        <div class="card rounded-xl p-3 text-xs" style="color:rgba(255,255,255,.4)">
          📱 Posted as <strong style="color:#C9A84C">Private</strong> first —
          review in YouTube Studio then make Public when ready
        </div>
        <div class="flex gap-3 pt-1">
          <button onclick="closeApproval()" class="flex-1 py-3 rounded-xl text-sm font-bold"
                  style="border:1px solid #1E1E2E;color:rgba(255,255,255,.4)">Cancel</button>
          <button onclick="submitApproval()" id="upload-btn"
                  class="flex-1 py-3 rounded-xl text-sm font-bold"
                  style="background:linear-gradient(135deg,#C9A84C,#8B6914);color:#000">
            Upload Now
          </button>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- IN-PLATFORM EDITOR -->
<div id="editor-modal" class="hidden fixed inset-0 z-50 flex items-center justify-center p-4" style="background:rgba(0,0,0,.7)">
  <div class="card rounded-2xl p-5 w-full max-w-lg" style="max-height:90vh;overflow-y:auto">
    <div class="flex items-center justify-between mb-3">
      <p class="text-[13px] font-black" style="color:#C9A84C">✂️ EDIT · re-cut to the beat</p>
      <button onclick="closeEditor()" class="text-sm" style="color:#666">✕</button>
    </div>
    <p class="text-[10px] font-bold mb-1" style="color:#555">CLIP ORDER — drag to reorder, ✕ to drop</p>
    <div id="editor-clips" class="space-y-1 mb-3"></div>
    <div class="grid grid-cols-2 gap-3 mb-3">
      <div>
        <p class="text-[10px] font-bold mb-1" style="color:#555">CUT</p>
        <select id="editor-cut" class="w-full rounded-lg px-2 py-2 text-[12px] bg-black/30 border" style="border-color:#2A2A3C;color:#ddd"></select>
      </div>
      <div>
        <p class="text-[10px] font-bold mb-1" style="color:#555">EVERY (n beats/bars)</p>
        <input id="editor-every" type="number" min="1" value="1" class="w-full rounded-lg px-2 py-2 text-[12px] bg-black/30 border" style="border-color:#2A2A3C;color:#ddd">
      </div>
    </div>
    <p class="text-[10px] font-bold mb-1" style="color:#555">LOOK — tap to toggle (stacks)</p>
    <div id="editor-looks" class="flex flex-wrap gap-1.5 mb-4"></div>
    <div class="flex gap-3">
      <button onclick="closeEditor()" class="flex-1 py-2.5 rounded-xl text-[13px] font-bold" style="border:1px solid #1E1E2E;color:rgba(255,255,255,.4)">Cancel</button>
      <button onclick="submitEdit()" id="editor-go" class="flex-1 py-2.5 rounded-xl text-[13px] font-black" style="background:#C9A84C;color:#0A0A0F">Re-render</button>
    </div>
    <p id="editor-msg" class="text-[11px] mt-2 text-center" style="color:#777"></p>
  </div>
</div>

<script>
let currentFile = null;
let allVideos = [], allVoice = [], allBeats = [], allDrafts = [];
let editorState = { job: null, clips: [], look: [], looks: [], cuts: [] };

// ── TABS ─────────────────────────────────────────────────────
function showTab(name) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('active-tab');
    btn.classList.add('inactive-tab');
  });
  document.getElementById('tab-content-' + name).classList.remove('hidden');
  const btn = document.getElementById('tab-' + name);
  btn.classList.remove('inactive-tab');
  btn.classList.add('active-tab');
  // Scroll tab into view on mobile
  btn.scrollIntoView({behavior:'smooth',block:'nearest',inline:'center'});
  if (name === 'schedule') loadSchedule();
  if (name === 'pipeline') loadEngineStatus();
  if (name === 'library')  loadLibrary();
}

// ── LIBRARY TAB ──────────────────────────────────────────────
async function loadLibrary() {
  const [finals, broll, masters] = await Promise.all([
    fetch('/api/videos').then(r=>r.json()).catch(()=>[]),
    fetch('/api/broll').then(r=>r.json()).catch(()=>[]),
    fetch('/api/masters').then(r=>r.json()).catch(()=>[]),
  ]);
  renderLibSection('lib-finals-grid',  'lib-finals-empty',  finals,
    f => `/stream/videos/${f.name}`,   f => `/thumb/${f.name}`,   f => f.name);
  renderLibSection('lib-broll-grid',   'lib-broll-empty',   broll,
    f => `/stream/broll/${f.rel_path}`, f => null,                f => f.name);
  renderLibSection('lib-masters-grid', 'lib-masters-empty', masters,
    f => `/stream/masters/${f.name}`,  f => null,                 f => f.name);
}

function renderLibSection(gridId, emptyId, items, streamFn, thumbFn, labelFn) {
  const grid  = document.getElementById(gridId);
  const empty = document.getElementById(emptyId);
  if (!items || !items.length) {
    grid.innerHTML = '';
    empty?.classList.remove('hidden');
    return;
  }
  empty?.classList.add('hidden');
  grid.innerHTML = items.map(f => {
    const src    = streamFn(f);
    const thumb  = thumbFn(f);
    const label  = labelFn(f).replace('.mp4','').replace('.mov','').replace(/_/g,' ');
    const folder = f.folder && f.folder !== 'root' ? `<span class="text-[9px] px-1 py-0.5 rounded" style="background:rgba(201,168,76,.15);color:#C9A84C">${f.folder.toUpperCase()}</span>` : '';
    return `
      <div class="card rounded-xl overflow-hidden cursor-pointer group"
           onclick="openVideo('${src}','${labelFn(f)}')">
        ${thumb
          ? `<div class="relative aspect-[9/16] bg-black overflow-hidden">
               <img src="${thumb}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    onerror="this.parentElement.innerHTML='<div style=\\'background:#111118;width:100%;height:100%;display:flex;align-items:center;justify-content:center\\'><span style=\\'font-size:28px\\'>🎬</span></div>'">
             </div>`
          : `<div class="aspect-[9/16] flex items-center justify-center" style="background:#111118">
               <span style="font-size:28px">🎬</span>
             </div>`
        }
        <div class="p-2">
          ${folder}
          <p class="text-[10px] font-bold text-white truncate mt-0.5">${label}</p>
          <p class="text-[10px]" style="color:#444">${f.size_mb}MB</p>
        </div>
      </div>`;
  }).join('');
}

// ── SCHEDULE TAB ─────────────────────────────────────────────
const DAY_META = {
  1: {label:'MINDSET — Mindset Shift',        time:'Thu Apr 16 · Posted'},
  2: {label:'DISCIPLINE — No Trade Is a Trade', time:'Fri Apr 17 · 12:00 PM EDT'},
  3: {label:'MINDSET — Fear as Information',   time:'Sat Apr 18 · 12:00 PM EDT'},
  4: {label:'PATIENCE — Quality Over Quantity',time:'Sun Apr 19 · 12:00 PM EDT'},
  5: {label:'PSYCHOLOGY — The Market as Lab',  time:'Mon Apr 20 · 12:00 PM EDT'},
};

async function loadSchedule() {
  const [queue, timeline] = await Promise.all([
    fetch('/api/queue').then(r=>r.json()).catch(()=>[]),
    fetch('/api/schedule').then(r=>r.json()).catch(()=>[]),
  ]);
  renderQueue(queue);
  renderTimeline(timeline);
}

function renderQueue(items) {
  const el = document.getElementById('schedule-queue');
  if (!items || !items.length) {
    el.innerHTML = '<p class="text-sm text-center py-8" style="color:#444">All content scheduled ✓</p>';
    return;
  }
  el.innerHTML = items.map(item => {
    const m = DAY_META[item.day] || {};
    const statusColor = item.status==='scheduled'?'#00C851':item.status==='posted'?'#555':'#C9A84C';
    const statusLabel = item.status==='scheduled'?'✓ Scheduled':item.status==='posted'?'✓ Posted':'⏳ Pending';
    const isPending   = item.status === 'pending';
    // Date/time picker row
    const pickerHtml = isPending ? `
      <div class="flex gap-2 mt-3">
        <input type="date" id="date-${item.day}"
               value="${(item.schedule_utc||'').substring(0,10)}"
               class="flex-1 rounded-lg px-2 py-2 text-xs text-white"
               style="background:rgba(255,255,255,.07);border:1px solid #1E1E2E;outline:none">
        <input type="time" id="time-${item.day}" value="12:00"
               class="w-24 rounded-lg px-2 py-2 text-xs text-white"
               style="background:rgba(255,255,255,.07);border:1px solid #1E1E2E;outline:none">
        <select id="tz-${item.day}"
                class="w-20 rounded-lg px-2 py-2 text-xs text-white"
                style="background:rgba(255,255,255,.07);border:1px solid #1E1E2E;outline:none">
          <option value="-4">EDT</option>
          <option value="-5">CDT</option>
          <option value="-7">PDT</option>
          <option value="0">UTC</option>
        </select>
      </div>
      <button onclick="scheduleDay(${item.day})" id="sched-btn-${item.day}"
              class="w-full py-3 rounded-xl text-sm font-bold mt-2 flex items-center justify-center gap-2"
              style="background:linear-gradient(135deg,#C9A84C,#8B6914);color:#000">
        📅 Schedule Post
      </button>` : '';
    return `
      <div class="card rounded-xl p-4">
        <div class="flex items-start gap-3">
          <img src="/thumb/${item.video_name}" class="w-12 h-20 object-cover rounded-lg flex-shrink-0 bg-black"
               onerror="this.style.background='#1E1E2E';this.removeAttribute('src')">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-[10px] font-black" style="color:#C9A84C">DAY ${item.day}</span>
              <span class="text-[10px] px-2 py-0.5 rounded-full font-bold"
                    style="background:rgba(255,255,255,.05);color:${statusColor}">${statusLabel}</span>
            </div>
            <p class="text-sm font-bold text-white mb-1">${m.label || item.label}</p>
            <p class="text-xs mb-2" style="color:#555">🕐 ${m.time || ''}</p>
            <p class="text-xs leading-relaxed line-clamp-2"
               style="color:rgba(255,255,255,.35)">${(item.caption_preview||'').substring(0,100)}...</p>
            ${pickerHtml}
            <div id="sched-msg-${item.day}" class="mt-2 text-xs" style="color:#00C851"></div>
          </div>
        </div>
      </div>`;
  }).join('');
}

function renderTimeline(items) {
  const el = document.getElementById('schedule-timeline');
  if (!items || !items.length) {
    el.innerHTML = '<p class="text-sm text-center py-6" style="color:#444">No scheduled posts yet</p>';
    return;
  }
  el.innerHTML = items.map(item => {
    const m = DAY_META[item.day] || {};
    const icon  = item.status==='posted'?'✅':item.status==='scheduled'?'📅':'❌';
    const color = item.status==='scheduled'?'#C9A84C':item.status==='posted'?'#00C851':'#ff4444';
    return `
      <div class="card rounded-xl p-3 flex items-center gap-3">
        <span class="text-lg flex-shrink-0">${icon}</span>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-bold text-white truncate">Day ${item.day} — ${m.label||item.label}</p>
          <p class="text-xs mt-0.5" style="color:${color}">${m.time||item.schedule_utc||''} · ${item.status}</p>
          ${item.error?`<p class="text-xs mt-0.5" style="color:#ff4444">${item.error.substring(0,100)}</p>`:''}
        </div>
      </div>`;
  }).join('');
}

async function scheduleDay(day) {
  const btn  = document.getElementById(`sched-btn-${day}`);
  const msg  = document.getElementById(`sched-msg-${day}`);
  const date = document.getElementById(`date-${day}`)?.value;
  const time = document.getElementById(`time-${day}`)?.value || '12:00';
  const tz   = parseInt(document.getElementById(`tz-${day}`)?.value || '-4');
  // Build UTC time from local inputs
  let schedUtc = null;
  if (date) {
    const [h,m2] = time.split(':').map(Number);
    const utcH = h - tz;  // convert offset to UTC
    schedUtc = `${date}T${String(utcH).padStart(2,'0')}:${String(m2).padStart(2,'0')}:00.000Z`;
  }
  if (btn) { btn.disabled=true; btn.textContent='⏳ Uploading & scheduling...'; }
  if (msg) { msg.textContent='Uploading video to GHL CDN...'; msg.style.color='#C9A84C'; }
  try {
    const res  = await fetch('/api/schedule-post', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({day, schedule_utc: schedUtc})
    });
    const data = await res.json();
    if (data.success) {
      if (msg) { msg.textContent='✓ '+(data.message||'Scheduled!'); msg.style.color='#00C851'; }
      if (btn) { btn.textContent='✓ Scheduled'; btn.style.background='#1E1E2E'; btn.style.color='#00C851'; }
      setTimeout(loadSchedule, 1500);
    } else {
      if (msg) { msg.textContent='✗ '+(data.error||data.message||'Failed'); msg.style.color='#ff4444'; }
      if (btn) { btn.disabled=false; btn.textContent='📅 Retry'; }
    }
  } catch(e) {
    if (msg) { msg.textContent='✗ '+e.message; msg.style.color='#ff4444'; }
    if (btn) { btn.disabled=false; btn.textContent='📅 Retry'; }
  }
}

// ── DATA LOADING ──────────────────────────────────────────────
async function loadAll() {
  try {
    const [vids, vc, beats, drafts] = await Promise.all([
      fetch('/api/videos').then(r=>r.json()).catch(()=>[]),
      fetch('/api/voice').then(r=>r.json()).catch(()=>[]),
      fetch('/api/beats').then(r=>r.json()).catch(()=>[]),
      fetch('/api/drafts').then(r=>r.json()).catch(()=>[]),
    ]);
    allVideos = vids; allVoice = vc; allBeats = beats; allDrafts = drafts;

    document.getElementById('stat-videos').textContent = vids.length;
    document.getElementById('stat-voice').textContent  = vc.length;
    document.getElementById('stat-beats').textContent  = beats.length;
    document.getElementById('stat-drafts').textContent = drafts.filter(d=>d.status==='pending').length || 0;
    document.getElementById('hdr-status').textContent  =
      vids.length + ' videos · ' + vc.length + ' voices · ' + beats.length + ' beats';

    renderVideos(vids);
    renderVoice(vc);
    renderBeats(beats);
    renderDrafts(drafts);
    renderPipeline(vids, vc);
  } catch(e) { console.error(e); }
}

// ── STUDIO (command bar) ──────────────────────────────────────
async function runCommand(planOnly) {
  const input = document.getElementById('cmd-input');
  const prompt = input.value.trim();
  if (!prompt) { input.focus(); return; }
  const planBox = document.getElementById('cmd-plan');
  const buildBtn = document.getElementById('cmd-build-btn');
  const planBtn  = document.getElementById('cmd-plan-btn');
  buildBtn.disabled = planBtn.disabled = true;
  planBox.classList.remove('hidden');
  planBox.innerHTML = '<p class="text-xs" style="color:#888">Thinking…</p>';
  try {
    const res = await fetch('/api/command', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ prompt, dry_run: planOnly })
    }).then(r=>r.json());
    if (res.error) { planBox.innerHTML = '<p class="text-xs text-red-400">'+res.error+'</p>'; return; }
    const p = res.plan, s = res.spec;
    const cost = p.est_cost > 0
      ? '<span class="text-amber-400 font-bold">~$'+p.est_cost+'</span> <span style="color:#666">('+p.route+')</span>'
      : '<span class="font-bold" style="color:#4ADE80">FREE</span> <span style="color:#666">(local)</span>';
    const steps = p.steps.map(st =>
      '<div class="flex items-center justify-between text-xs py-1">'
      + '<span style="color:#bbb">• '+st.name+' <span style="color:#666">'+st.detail+'</span></span>'
      + '<span style="color:#777">'+st.model+(st.est_cost? ' $'+st.est_cost:'')+'</span></div>'
    ).join('');
    planBox.innerHTML =
      '<div class="flex items-center justify-between mb-2">'
      + '<span class="text-[11px] font-bold" style="color:#C9A84C;letter-spacing:.1em">'
      +   s.kind.toUpperCase().replace("_"," ")+' · '+(s.duration_s? s.duration_s+'s':'full')
      +   (s.looks.length? ' · '+s.looks.join("+"):'')+'</span>'
      + '<span class="text-xs">'+cost+'</span></div>'
      + steps
      + (planOnly
          ? '<p class="text-[11px] mt-2" style="color:#555">Plan only — hit Build to produce it.</p>'
          : '<p class="text-[11px] mt-2" style="color:#4ADE80">Queued ✓ job '+res.id+'</p>');
    if (!planOnly) { input.value=''; loadJobs(); }
  } catch(e) {
    planBox.innerHTML = '<p class="text-xs text-red-400">'+e+'</p>';
  } finally {
    buildBtn.disabled = planBtn.disabled = false;
  }
}

async function loadJobs() {
  try {
    const jobs = await fetch('/api/jobs').then(r=>r.json()).catch(()=>[]);
    const list = document.getElementById('jobs-list');
    const empty = document.getElementById('jobs-empty');
    list.innerHTML = '';
    if (!jobs.length) { empty.classList.remove('hidden'); return; }
    empty.classList.add('hidden');
    const badge = { planned:'#888', queued:'#C9A84C', running:'#A78BFA',
                    done:'#4ADE80', partial:'#C9A84C', skipped:'#777', error:'#F87171' };
    let anyRunning = false;
    jobs.forEach(j => {
      const s = j.spec, c = (j.plan && j.plan.est_cost) || 0;
      if (j.status === 'running' || j.status === 'queued') anyRunning = true;
      const steps = (j.step_status && Object.keys(j.step_status).length)
        ? '<div class="flex flex-wrap gap-1 mt-2">' + Object.entries(j.step_status).map(([k,v]) => {
            const st = v.startsWith('done') ? '#4ADE80' : v.startsWith('running') ? '#A78BFA'
                     : v.startsWith('error') ? '#F87171' : '#666';
            const ic = v.startsWith('done') ? '✓' : v.startsWith('running') ? '…'
                     : v.startsWith('error') ? '✕' : '–';
            return '<span class="text-[10px] px-1.5 py-0.5 rounded" style="background:#00000033;color:'+st+'" title="'+v.replace(/"/g,'')+'">'+ic+' '+k+'</span>';
          }).join('') + '</div>'
        : '';
      const preview = (j.status === 'done' && j.output)
        ? '<video src="/stream/job/'+j.id+'?t='+(j.edits?j.edits.length:0)+'" controls preload="metadata" class="w-full rounded-lg mt-2" style="max-height:240px;background:#000"></video>'
        : '';
      const canEdit = s.kind === 'music_video' && j.artifacts
        && (j.artifacts.clips||[]).length && j.artifacts.song_json;
      const editBtn = canEdit
        ? '<button onclick=\'openEditor("'+j.id+'")\' class="text-[11px] font-bold px-2.5 py-1 rounded-lg mt-2" style="background:#1A1A28;color:#C9A84C">✂️ Edit · re-cut</button>'
        : '';
      const card = document.createElement('div');
      card.className = 'card rounded-xl p-3';
      card.innerHTML =
        '<div class="flex items-center justify-between mb-1">'
        + '<span class="text-[10px] font-bold" style="color:'+(badge[j.status]||'#888')+';letter-spacing:.08em">'
        +   (j.status||'').toUpperCase()+' · '+s.kind.replace("_"," ")+'</span>'
        + '<span class="text-[11px]" style="color:#666">'+(c>0?'$'+c:'free')+'</span></div>'
        + '<p class="text-sm" style="color:#ddd">'+(s.prompt||'').slice(0,120)+'</p>'
        + steps + preview + editBtn
        + '<p class="text-[10px] mt-1" style="color:#555">'+j.id+'</p>';
      list.appendChild(card);
    });
    // while anything is running, poll faster so progress feels live
    if (anyRunning) { clearTimeout(window._jobPoll); window._jobPoll = setTimeout(loadJobs, 4000); }
  } catch(e) { console.error(e); }
}

// ── DROP-A-SONG ───────────────────────────────────────────────
async function uploadSong(file) {
  if (!file) return;
  const box = document.getElementById('song-result');
  box.classList.remove('hidden');
  box.innerHTML = '<p class="text-xs" style="color:#888">Analysing '+file.name+' — finding beat & lyrics…</p>';
  try {
    const fd = new FormData(); fd.append('song', file);
    const r = await fetch('/api/upload-song', { method:'POST', body: fd }).then(x=>x.json());
    if (!r.ok) {
      box.innerHTML = '<p class="text-xs text-red-400">'+(r.error||'upload failed')+'</p>'
        + (r.hint? '<p class="text-[11px] mt-1" style="color:#666">Tip: '+r.hint+'</p>':'');
      return;
    }
    box.innerHTML =
      '<p class="text-[12px] font-bold" style="color:#4ADE80">✓ '+r.name+' analysed</p>'
      + '<div class="flex flex-wrap gap-3 mt-2 text-[12px]" style="color:#bbb">'
      +   '<span>🥁 '+(r.tempo||'?')+' BPM</span><span>· '+r.beats+' beats</span>'
      +   '<span>· '+r.sections+' sections</span><span>· '+r.lyrics+' lyric lines</span></div>'
      + (r.lyric_preview? '<p class="text-[11px] mt-2 italic" style="color:#888">"'+r.lyric_preview+'…"</p>':'')
      + '<button onclick=\'buildSong("'+r.name+'")\' class="mt-3 px-4 py-2 rounded-xl text-[13px] font-black" style="background:#C9A84C;color:#0A0A0F">🎬 Build music video to the beat</button>';
  } catch(e) { box.innerHTML = '<p class="text-xs text-red-400">'+e+'</p>'; }
}
function buildSong(name) {
  document.getElementById('cmd-input').value = 'music video for '+name+', cut on the beat';
  runCommand(false);
}
// dropzone drag styling
(function(){
  const dz = document.getElementById('dropzone'); if (!dz) return;
  ['dragover','dragenter'].forEach(ev => dz.addEventListener(ev, e => {
    e.preventDefault(); dz.style.borderColor = '#C9A84C'; dz.style.background = 'rgba(201,168,76,.08)';
  }));
  ['dragleave','drop'].forEach(ev => dz.addEventListener(ev, e => {
    e.preventDefault(); dz.style.borderColor = '#2A2A3C'; dz.style.background = 'rgba(201,168,76,.03)';
  }));
  dz.addEventListener('drop', e => { if (e.dataTransfer.files[0]) uploadSong(e.dataTransfer.files[0]); });
})();

// ── IN-PLATFORM EDITOR ────────────────────────────────────────
async function openEditor(jobId) {
  const job = await fetch('/api/job/'+jobId).then(r=>r.json());
  const opt = await fetch('/api/looks').then(r=>r.json());
  editorState.job = job;
  editorState.looks = opt.looks || []; editorState.cuts = opt.cuts || [];
  editorState.clips = (job.artifacts.clips||[]).map((c,i)=>({i, name:c.split('/').pop()}));
  editorState.look = (job.spec.looks||[]).slice();
  // cut select
  const cutSel = document.getElementById('editor-cut');
  cutSel.innerHTML = editorState.cuts.map(c=>'<option'+(c===job.spec.cut?' selected':'')+'>'+c+'</option>').join('');
  // looks toggles
  document.getElementById('editor-looks').innerHTML = editorState.looks.map(l=>{
    const on = editorState.look.includes(l);
    return '<button data-look="'+l+'" onclick="toggleLook(this)" class="text-[11px] px-2 py-1 rounded-lg" style="background:'+(on?'#C9A84C':'#1A1A28')+';color:'+(on?'#0A0A0F':'#999')+'">'+l+'</button>';
  }).join('');
  document.getElementById('editor-msg').textContent = '';
  renderEditorClips();
  document.getElementById('editor-modal').classList.remove('hidden');
}
function renderEditorClips() {
  const box = document.getElementById('editor-clips');
  box.innerHTML = editorState.clips.map((c,pos)=>
    '<div class="flex items-center gap-2 rounded-lg px-2 py-1.5" style="background:#1A1A28">'
    + '<span class="text-[11px] font-bold" style="color:#C9A84C">'+(pos+1)+'</span>'
    + '<span class="text-[11px] flex-1 truncate" style="color:#bbb">'+c.name+'</span>'
    + '<button onclick="moveClip('+pos+',-1)" class="text-[12px] px-1" style="color:#666">↑</button>'
    + '<button onclick="moveClip('+pos+',1)" class="text-[12px] px-1" style="color:#666">↓</button>'
    + '<button onclick="dropClip('+pos+')" class="text-[12px] px-1" style="color:#F87171">✕</button></div>'
  ).join('') || '<p class="text-[11px]" style="color:#F87171">No clips left — drop fewer.</p>';
}
function moveClip(pos, dir) {
  const t = pos + dir; if (t<0 || t>=editorState.clips.length) return;
  const a = editorState.clips;[a[pos],a[t]]=[a[t],a[pos]]; renderEditorClips();
}
function dropClip(pos) { editorState.clips.splice(pos,1); renderEditorClips(); }
function toggleLook(btn) {
  const l = btn.dataset.look, i = editorState.look.indexOf(l);
  if (i>=0) editorState.look.splice(i,1); else editorState.look.push(l);
  const on = editorState.look.includes(l);
  btn.style.background = on?'#C9A84C':'#1A1A28'; btn.style.color = on?'#0A0A0F':'#999';
}
function closeEditor() { document.getElementById('editor-modal').classList.add('hidden'); }
async function submitEdit() {
  const go = document.getElementById('editor-go'), msg = document.getElementById('editor-msg');
  if (!editorState.clips.length) { msg.textContent='Keep at least one clip.'; return; }
  go.disabled = true; msg.textContent = 'Re-rendering to the beat…';
  try {
    const r = await fetch('/api/edit', { method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        job_id: editorState.job.id,
        order: editorState.clips.map(c=>c.i),
        look: editorState.look,
        cut: document.getElementById('editor-cut').value,
        every: parseInt(document.getElementById('editor-every').value)||1,
      })}).then(x=>x.json());
    if (!r.ok) { msg.textContent = '✕ '+(r.error||'failed'); return; }
    msg.textContent = '✓ Re-rendered'; closeEditor(); loadJobs();
  } catch(e) { msg.textContent = '✕ '+e; } finally { go.disabled = false; }
}

// ── VIDEOS ────────────────────────────────────────────────────
function renderVideos(files) {
  const grid  = document.getElementById('videos-grid');
  const empty = document.getElementById('videos-empty');
  grid.innerHTML = '';
  if (!files.length) { empty.classList.remove('hidden'); return; }
  empty.classList.add('hidden');

  files.forEach((f, i) => {
    const day   = (f.name.match(/day(\d+)/) || [])[1] || '?';
    const card  = document.createElement('div');
    card.className = 'card rounded-2xl overflow-hidden cursor-pointer fade-up';
    card.style.animationDelay = (i * 0.04) + 's';
    card.innerHTML = `
      <div class="relative bg-black" style="aspect-ratio:9/16"
           onclick="openVideo('/stream/videos/${f.name}','${f.name}')">
        <img src="/thumb/${f.name}"
             class="w-full h-full object-cover transition-transform duration-500 hover:scale-105"
             onerror="this.parentElement.style.background='#111118';this.remove()">
        <div class="absolute inset-0 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity"
             style="background:rgba(0,0,0,.4)">
          <div class="w-14 h-14 rounded-full flex items-center justify-center"
               style="background:rgba(201,168,76,.9)">
            <span style="font-size:22px;color:#000;margin-left:3px">▶</span>
          </div>
        </div>
        <div class="absolute top-2.5 left-2.5">
          <span class="pill" style="background:rgba(0,0,0,.8);color:#C9A84C">DAY ${day}</span>
        </div>
        <div class="absolute bottom-2.5 right-2.5">
          <span class="pill" style="background:rgba(0,0,0,.8);color:#00C851">${f.size_mb}MB</span>
        </div>
      </div>
      <div class="p-3 space-y-2">
        <p class="text-xs font-semibold truncate" style="color:rgba(255,255,255,.7)">
          ${f.name.replace('.mp4','').replace(/_/g,' ')}
        </p>
        <div class="flex gap-2">
          <button onclick="openVideo('/stream/videos/${f.name}','${f.name}')"
                  class="flex-1 py-2 rounded-lg text-[11px] font-bold transition-all"
                  style="background:rgba(201,168,76,.12);color:#C9A84C">Preview</button>
          <button onclick="openApproval(${JSON.stringify(f).replace(/"/g,'&quot;')})"
                  class="flex-1 py-2 rounded-lg text-[11px] font-bold transition-all"
                  style="background:rgba(0,200,81,.12);color:#00C851">Post →</button>
        </div>
      </div>`;
    grid.appendChild(card);
  });
}

// ── VOICE ─────────────────────────────────────────────────────
function renderVoice(files) {
  const list  = document.getElementById('voice-list');
  const empty = document.getElementById('voice-empty');
  list.innerHTML = '';
  if (!files.length) { empty.classList.remove('hidden'); return; }
  empty.classList.add('hidden');
  files.filter(f => f.name.match(/^day_\d+_sv/)).forEach(f => {
    const day = (f.name.match(/day_(\d+)/) || [])[1] || '?';
    const el  = document.createElement('div');
    el.className = 'card rounded-xl p-3 md:p-4 flex items-center gap-3 md:gap-4 fade-up';
    el.innerHTML = `
      <div class="w-9 h-9 md:w-10 md:h-10 rounded-xl flex items-center justify-center font-black text-xs flex-shrink-0"
           style="background:#00C851;color:#000">D${day}</div>
      <div class="flex-1 min-w-0">
        <p class="text-xs font-semibold truncate mb-1" style="color:rgba(255,255,255,.7)">${f.name}</p>
        <audio src="/stream/voice/${f.name}" controls preload="none"
               class="w-full" style="height:28px"></audio>
      </div>
      <span class="text-[10px] flex-shrink-0" style="color:#555">${f.size_mb}MB</span>`;
    list.appendChild(el);
  });
}

// ── BEATS ─────────────────────────────────────────────────────
function renderBeats(files) {
  const list  = document.getElementById('beats-list');
  const empty = document.getElementById('beats-empty');
  list.innerHTML = '';
  if (!files.length) { empty.classList.remove('hidden'); return; }
  empty.classList.add('hidden');
  files.forEach(f => {
    const mood  = f.name.includes('dark') ? {l:'DARK',c:'#EF4444'}
                : f.name.includes('rise')||f.name.includes('motiv') ? {l:'RISE',c:'#F59E0B'}
                : {l:'FOCUS',c:'#8B5CF6'};
    const el = document.createElement('div');
    el.className = 'card rounded-xl p-3 md:p-4 flex items-center gap-3 md:gap-4 fade-up';
    el.innerHTML = `
      <div class="w-9 h-9 md:w-10 md:h-10 rounded-xl flex items-center justify-center text-base flex-shrink-0"
           style="background:${mood.c}22;border:1px solid ${mood.c}44">🎵</div>
      <div class="flex-1 min-w-0">
        <p class="text-xs font-semibold truncate mb-1" style="color:rgba(255,255,255,.7)">${f.name}</p>
        <audio src="/stream/beats/${f.name}" controls preload="none"
               class="w-full" style="height:28px"></audio>
      </div>
      <span class="pill flex-shrink-0" style="background:${mood.c}22;color:${mood.c}">${mood.l}</span>`;
    list.appendChild(el);
  });
}

// ── DRAFTS ────────────────────────────────────────────────────
function renderDrafts(drafts) {
  const list  = document.getElementById('drafts-list');
  const empty = document.getElementById('drafts-empty');
  list.innerHTML = '';
  if (!drafts.length) { empty.classList.remove('hidden'); return; }
  empty.classList.add('hidden');
  drafts.forEach(d => {
    const el = document.createElement('div');
    el.className = 'card rounded-xl p-4 fade-up';
    const statusColor = d.status === 'produced' ? '#00C851' : '#F59E0B';
    const statusLabel = d.status === 'produced' ? 'PRODUCED' : 'PENDING REVIEW';
    el.innerHTML = `
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-2">
          ${d.day ? `<span class="pill" style="background:rgba(201,168,76,.15);color:#C9A84C">DAY ${d.day}</span>` : ''}
          <span class="text-xs font-semibold" style="color:rgba(255,255,255,.6)">${d.name}</span>
        </div>
        <span class="pill" style="background:${statusColor}22;color:${statusColor}">${statusLabel}</span>
      </div>
      <div class="rounded-lg p-3 mb-3 text-xs leading-relaxed font-mono"
           style="background:rgba(255,255,255,.04);color:rgba(255,255,255,.5);max-height:120px;overflow-y:auto">
        ${d.preview.replace(/\n/g,'<br>')}
      </div>
      <div class="flex gap-2">
        <button onclick="viewDraft('${d.name}')"
                class="flex-1 py-2 rounded-lg text-[11px] font-bold"
                style="background:rgba(255,255,255,.06);color:rgba(255,255,255,.5)">
          Full Script
        </button>
        ${d.status !== 'produced' ? `
        <button onclick="approveDraft('${d.name}', this)"
                class="flex-1 py-2 rounded-lg text-[11px] font-bold transition-all"
                style="background:rgba(0,200,81,.15);color:#00C851;cursor:pointer">
          ✅ Approve → Generate
        </button>` : ''}
      </div>`;
    list.appendChild(el);
  });
}

// ── PIPELINE ─────────────────────────────────────────────────
function renderPipeline(videos, voice) {
  const el = document.getElementById('pipeline-days');
  // Show all days that have either voice or video (up to day 90 max, show first 14 + any with content)
  const totalDays = Math.max(14, videos.length ? parseInt((videos[videos.length-1]?.name.match(/\d+/)||[0])[0])||14 : 14);
  const showDays  = Math.min(totalDays, 90);
  el.innerHTML = Array.from({length:showDays},(_,i)=>i+1).map(d => {
    const pad = String(d).padStart(2,'0');
    const hv  = videos.some(v=>v.name.toLowerCase().includes('day'+pad)||v.name.toLowerCase().includes('day_'+pad));
    const hvc = voice.some(v=>v.name.includes('day_'+pad+'_sv'));
    return `<div class="flex items-center gap-3">
      <span class="text-[10px] w-10 font-bold flex-shrink-0" style="color:#555">DAY ${d}</span>
      <div class="flex gap-1.5">
        <span class="pill" style="background:${hvc?'#00C85122':'rgba(255,255,255,.04)'};color:${hvc?'#00C851':'#333'}">Voice</span>
        <span class="pill" style="background:${hv?'#C9A84C22':'rgba(255,255,255,.04)'};color:${hv?'#C9A84C':'#333'}">Video</span>
      </div>
      <div class="flex-1 h-1 rounded-full overflow-hidden" style="background:#1E1E2E">
        <div class="h-full rounded-full transition-all duration-700"
             style="background:${hv?'#C9A84C':hvc?'#00C851':'transparent'};width:${hv?'100%':hvc?'50%':'0%'}"></div>
      </div>
    </div>`;
  }).join('');
  // Load engine status dynamically
  loadEngineStatus();
}

async function loadEngineStatus() {
  const el = document.getElementById('engine-status-list');
  if (!el) return;
  try {
    const data = await fetch('/api/engine-status').then(r=>r.json());
    el.innerHTML = data.map(s => {
      const dot = s.status==='live'   ? '#00C851' :
                  s.status==='warn'   ? '#C9A84C' :
                  s.status==='error'  ? '#EF4444' : '#555';
      const badge = s.status==='live'   ? 'LIVE' :
                    s.status==='warn'   ? s.badge||'CHECK' :
                    s.status==='error'  ? s.badge||'KEY NEEDED' : '—';
      const badgeStyle = s.status==='live'
        ? 'background:rgba(0,200,81,.15);color:#00C851'
        : s.status==='warn'
          ? 'background:rgba(201,168,76,.15);color:#C9A84C'
          : 'background:rgba(239,68,68,.15);color:#EF4444';
      return `<div class="flex items-center justify-between gap-3">
        <div class="flex items-center gap-3 min-w-0">
          <div class="w-2 h-2 rounded-full flex-shrink-0" style="background:${dot}"></div>
          <div class="min-w-0">
            <p class="text-sm font-semibold text-white truncate">${s.name}</p>
            <p class="text-[11px] truncate" style="color:#555">${s.detail||''}</p>
          </div>
        </div>
        <span class="text-[10px] font-black px-2 py-1 rounded-full flex-shrink-0"
              style="${badgeStyle}">${badge}</span>
      </div>`;
    }).join('');
  } catch(e) {
    el.innerHTML = '<p class="text-xs" style="color:#555">Status unavailable</p>';
  }
}

// ── VIDEO MODAL ───────────────────────────────────────────────
function openVideo(src, name) {
  const modal = document.getElementById('modal');
  const vid   = document.getElementById('modal-video');
  const title = name.replace('.mp4','').replace(/_/g,' ');
  document.getElementById('modal-title').textContent       = title;
  document.getElementById('modal-title-mobile').textContent= title;
  vid.src = src;
  modal.classList.remove('hidden');
  vid.play().catch(()=>{});

  // Wire approve button on mobile
  const approveBtn = document.getElementById('modal-approve-btn');
  const fileObj = allVideos.find(v=>v.name===name);
  if (fileObj) {
    approveBtn.onclick = () => { closeModal(); setTimeout(()=>openApproval(fileObj),100); };
  }
  currentFile = name;
}

function closeModal(e) {
  if (e && e.target !== document.getElementById('modal')) return;
  document.getElementById('modal').classList.add('hidden');
  const vid = document.getElementById('modal-video');
  vid.pause(); vid.src = '';
}

// ── APPROVAL MODAL ────────────────────────────────────────────
function openApproval(file) {
  currentFile = file;
  const day   = (file.name.match(/day(\d+)/) || [])[1] || '?';
  document.getElementById('approval-filename').textContent = file.name;
  document.getElementById('yt-title').value =
    `Day ${day} — Trader Mindset | Hybrid Funding`;
  document.getElementById('yt-desc').value =
    `Trader mindset content from Source Vessel x Hybrid Funding.\n\nGet funded at hybridfunding.co\n\n#HybridFunding #PropTrading #TradingMindset #FundedTrader #FinancialFreedom`;
  document.getElementById('yt-tags').value =
    'HybridFunding,PropTrading,FundedTrader,TradingMindset,FinancialFreedom,ForexTrader';
  document.getElementById('approval-modal').classList.remove('hidden');
}

function closeApproval(e) {
  if (e && e.target !== document.getElementById('approval-modal')) return;
  document.getElementById('approval-modal').classList.add('hidden');
}

async function submitApproval() {
  if (!currentFile) return;
  const btn = document.getElementById('upload-btn');
  btn.textContent = 'Uploading…';
  btn.disabled = true;

  try {
    const res = await fetch('/api/approve', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        file: currentFile,
        title: document.getElementById('yt-title').value,
        description: document.getElementById('yt-desc').value,
        tags: document.getElementById('yt-tags').value,
      })
    });
    const data = await res.json();
    closeApproval();
    if (data.success) {
      alert('✅ ' + (data.message || 'Posted successfully!'));
    } else if (data.queued) {
      alert('⏳ Video staged.\n\n' + (data.message||'') + '\n\n' + (data.action||''));
    } else if (data.error) {
      alert('❌ Error: ' + data.error);
    } else {
      alert(data.message || 'Done.');
    }
  } catch(e) {
    alert('Error: ' + e.message);
  }
  btn.textContent = 'Upload Now';
  btn.disabled = false;
}

// ── DRAFTS ACTIONS ────────────────────────────────────────────
function viewDraft(name) {
  const draft = allDrafts.find(d=>d.name===name);
  if (!draft) return;
  const modal = document.createElement('div');
  modal.style.cssText = 'position:fixed;inset:0;z-index:100;background:rgba(0,0,0,.9);display:flex;align-items:center;justify-content:center;padding:16px';
  modal.innerHTML = `<div style="background:#111118;border:1px solid #1E1E2E;border-radius:16px;padding:20px;max-width:560px;width:100%;max-height:80vh;overflow-y:auto">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <p style="color:#C9A84C;font-weight:700;font-size:13px">${name}</p>
      <button onclick="this.closest('[style]').remove()" style="background:#1E1E2E;color:#fff;border:none;width:32px;height:32px;border-radius:8px;cursor:pointer;font-size:16px">✕</button>
    </div>
    <pre style="color:rgba(255,255,255,.7);font-size:13px;line-height:1.6;white-space:pre-wrap;font-family:system-ui">${(draft.full||'').replace(/</g,'&lt;')}</pre>
  </div>`;
  modal.onclick = e => { if(e.target===modal) modal.remove(); };
  document.body.appendChild(modal);
}

async function approveDraft(name, btn) {
  // Update button to loading state immediately
  const origText = btn ? btn.textContent : '';
  if (btn) { btn.textContent = '⏳ Starting…'; btn.disabled = true; }

  try {
    const res = await fetch('/api/approve-draft', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({name})
    });
    const data = await res.json();

    if (data.error) {
      if (btn) { btn.textContent = '❌ ' + data.error; btn.disabled = false; }
      return;
    }

    // Show inline status instead of alert
    if (btn) {
      btn.textContent = '🎙️ Generating voice…';
      btn.style.background = 'rgba(201,168,76,.2)';
      btn.style.color = '#C9A84C';

      // Poll for completion
      const pollInterval = setInterval(async () => {
        const statusRes = await fetch('/api/gen-status');
        const statuses = await statusRes.json();
        const dayKey = name.match(/day_(\d+)/)?.[1]?.padStart?.(2,'0');
        const status = dayKey ? statuses[`day_${dayKey}`] : null;

        if (status?.status === 'done') {
          clearInterval(pollInterval);
          btn.textContent = '✅ Voice ready — check Voice tab';
          btn.style.background = 'rgba(0,200,81,.15)';
          btn.style.color = '#00C851';
          btn.disabled = false;
          loadAll(); // Refresh all data
        } else if (status?.status === 'error') {
          clearInterval(pollInterval);
          btn.textContent = '❌ Error: ' + (status.message||'unknown');
          btn.style.background = 'rgba(239,68,68,.15)';
          btn.style.color = '#EF4444';
          btn.disabled = false;
        }
      }, 8000); // Poll every 8 seconds
    }
  } catch(e) {
    if (btn) { btn.textContent = '❌ Network error'; btn.disabled = false; }
  }
}

// ── INIT ──────────────────────────────────────────────────────
loadAll();
loadJobs();
setInterval(loadAll, 30000);
setInterval(loadJobs, 30000);
// Cmd/Ctrl+Enter in the command bar = Build
document.addEventListener('keydown', e => {
  if ((e.metaKey||e.ctrlKey) && e.key==='Enter'
      && document.activeElement && document.activeElement.id==='cmd-input') {
    e.preventDefault(); runCommand(false);
  }
});
</script>
</body>
</html>"""

@app.route("/")
def index():
    return render_template_string(HTML)

# ── Studio command bar ────────────────────────────────────────────────────
@app.route("/api/command", methods=["POST"])
def api_command():
    """Natural language -> JobSpec -> plan (and queue the job if not dry_run)."""
    try:
        import engine
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": f"engine unavailable: {e}"}), 500
    data = request.get_json(force=True, silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "empty prompt"}), 400
    brand_id = BRAND.id if BRAND is not None else ""
    try:
        job = engine.build(prompt, brand_id, dry_run=bool(data.get("dry_run", True)))
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 500
    return jsonify(job)

@app.route("/api/jobs")
def api_jobs():
    try:
        import engine
        return jsonify(engine.list_jobs(BRAND))
    except Exception:  # noqa: BLE001
        return jsonify([])

@app.route("/api/job/<job_id>")
def api_job(job_id):
    try:
        import engine
        job = engine.get_job(BRAND, job_id)
        return jsonify(job or {"error": "not found"}), (200 if job else 404)
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 500

@app.route("/stream/job/<job_id>")
def stream_job_file(job_id):
    """Stream a finished job's output video for in-Studio preview."""
    try:
        import engine
        job = engine.get_job(BRAND, job_id)
        out = job and job.get("output")
        if out and os.path.exists(out):
            return send_file(out, mimetype="video/mp4")
    except Exception:  # noqa: BLE001
        pass
    return ("not found", 404)

@app.route("/api/upload-song", methods=["POST"])
def api_upload_song():
    """Drag-drop an MP3 -> save into beats/ -> analyse beat + lyrics -> summary."""
    try:
        import engine
    except Exception as e:  # noqa: BLE001
        return jsonify({"ok": False, "error": f"engine unavailable: {e}"}), 500
    f = request.files.get("song")
    if f is None or not f.filename:
        return jsonify({"ok": False, "error": "no file"}), 400
    name = os.path.basename(f.filename)
    if not name.lower().endswith((".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg")):
        return jsonify({"ok": False, "error": "not an audio file"}), 400
    beats_dir = str(BRAND.folder("beats")) if BRAND is not None else "uploads"
    os.makedirs(beats_dir, exist_ok=True)
    dest = _safe_path(beats_dir, name)
    if not dest:
        return jsonify({"ok": False, "error": "bad filename"}), 400
    f.save(dest)
    res = engine.ingest_song(BRAND, dest)
    return jsonify(res), (200 if res.get("ok") else 422)

@app.route("/api/looks")
def api_looks():
    try:
        import engine
        return jsonify({"looks": engine.LOOK_NAMES, "cuts": engine.CUT_MODES})
    except Exception:  # noqa: BLE001
        return jsonify({"looks": [], "cuts": []})

@app.route("/api/edit", methods=["POST"])
def api_edit():
    """In-platform editor: reorder clips, swap look, re-cut to the beat, re-render."""
    try:
        import engine
    except Exception as e:  # noqa: BLE001
        return jsonify({"ok": False, "error": f"engine unavailable: {e}"}), 500
    d = request.get_json(force=True, silent=True) or {}
    job_id = d.get("job_id")
    if not job_id:
        return jsonify({"ok": False, "error": "no job_id"}), 400
    res = engine.rerender(BRAND, job_id, order=d.get("order"),
                          look=d.get("look"), cut=d.get("cut"),
                          every=int(d.get("every", 1)))
    return jsonify(res), (200 if res.get("ok") else 422)

@app.route("/api/videos")
def api_videos():
    return jsonify(list_files(SHORTS, [".mp4", ".mov"]))

@app.route("/api/voice")
def api_voice():
    return jsonify(list_files(VOICE, [".wav", ".mp3"]))

@app.route("/api/beats")
def api_beats():
    return jsonify(list_files(BEATS, [".mp3", ".wav"]))

@app.route("/api/drafts")
def api_drafts():
    return jsonify(list_drafts())

@app.route("/stream/videos/<name>")
def stream_video(name):
    p = _safe_path(SHORTS, name)
    if not p or not os.path.exists(p): return "Not found", 404
    return send_file(p, mimetype="video/mp4", conditional=True)

@app.route("/stream/voice/<name>")
def stream_voice(name):
    p = _safe_path(VOICE, name)
    if not p or not os.path.exists(p): return "Not found", 404
    return send_file(p, mimetype="audio/wav" if name.endswith(".wav") else "audio/mpeg", conditional=True)

@app.route("/stream/beats/<name>")
def stream_beat(name):
    p = _safe_path(BEATS, name)
    if not p or not os.path.exists(p): return "Not found", 404
    return send_file(p, mimetype="audio/mpeg", conditional=True)

@app.route("/thumb/<name>")
def thumb(name):
    vp = _safe_path(SHORTS, name)
    tp = _safe_path(THUMBS, name.replace(".mp4", ".jpg"))
    if not vp or not tp or not os.path.exists(vp): return "Not found", 404
    make_thumb(vp, tp)
    if os.path.exists(tp): return send_file(tp, mimetype="image/jpeg")
    return "No thumb", 404

GHL_LOCATION_ID = os.environ.get("GHL_LOCATION_ID", "alK3nxmaA2aXkCGUQlUT")
GHL_PIT_TOKEN   = _secret("GHL_PIT_TOKEN")
GHL_USER_ID     = os.environ.get("GHL_USER_ID", "69dfa1a7ac74e91e82eca6d6")
GHL_SOCIAL_API  = f"https://services.leadconnectorhq.com/social-media-posting/{GHL_LOCATION_ID}/posts"
GHL_UPLOAD_URL  = f"https://services.leadconnectorhq.com/medias/upload-file?locationId={GHL_LOCATION_ID}"

# Fixed account IDs for all four platforms
GHL_ACCOUNTS = [
    "69dfa1a7ac74e91e82eca6d6_alK3nxmaA2aXkCGUQlUT_618385581367963_page",    # Hybrid Funding FB
    "69dfa1a7ac74e91e82eca6d6_alK3nxmaA2aXkCGUQlUT_143722515643160_page",    # Suess Villiano FB
    "69dfa1c6583d3ccbfa0e5869_alK3nxmaA2aXkCGUQlUT_17841440992533343",        # smartsystems_ IG
    "69e13b37dc821ca23dbec6e6_alK3nxmaA2aXkCGUQlUT_000xyOrgq0S2obmqX8erjAFAQ3DruitgSfv_profile",  # Hybrid Funding TikTok
]

R2_ACCOUNT_ID        = os.environ.get("R2_ACCOUNT_ID", "3289e13e9aedd43be7ffe8629c0296c8")
R2_ACCESS_KEY_ID     = _secret("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = _secret("R2_SECRET_ACCESS_KEY")
R2_BUCKET            = "sv-content-engine"
R2_ENDPOINT          = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

# Schedule JSON (persists across restarts)
SCHEDULE_JSON = os.path.join(BASE, "schedule.json")

# Day metadata for the queue
QUEUE_DAYS = {
    1:  {"label": "MINDSET — The One Shift",             "video": "day01_SV_FINAL.mp4", "caption": "day_01_social.txt"},
    2:  {"label": "DISCIPLINE — The Trade You Don't Take","video": "day02_SV_FINAL.mp4", "caption": "day_02_social.txt"},
    3:  {"label": "MINDSET — Fear as Information",        "video": "day03_SV_FINAL.mp4", "caption": "day_03_social.txt"},
    4:  {"label": "PATIENCE — Quality Over Quantity",     "video": "day04_SV_FINAL.mp4", "caption": "day_04_social.txt"},
    5:  {"label": "PSYCHOLOGY — The Market as Lab",       "video": "day05_SV_FINAL.mp4", "caption": "day_05_social.txt"},
}

def read_caption_for_day(day):
    """Read Instagram caption from a day's social.txt file."""
    meta = QUEUE_DAYS.get(day, {})
    cap_file = meta.get("caption", "")
    path = os.path.join(SCRIPTS, cap_file)
    if not os.path.exists(path):
        return f"Day {day} — Source Vessel · Hybrid Funding · hybridfunding.co"
    try:
        content = open(path, encoding="utf-8").read()
    except UnicodeDecodeError:
        content = open(path, encoding="latin-1").read()
    # Extract Instagram block if present
    if "INSTAGRAM CAPTION" in content:
        start = content.index("INSTAGRAM CAPTION") + len("INSTAGRAM CAPTION")
        rest = content[start:]
        for sep in ["━━━", "---", "==="]:
            if sep in rest:
                rest = rest[:rest.index(sep)]
                break
        return rest.strip()
    return content.strip()

def load_schedule():
    """Load schedule.json, return list."""
    if os.path.exists(SCHEDULE_JSON):
        try:
            with open(SCHEDULE_JSON) as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_schedule(data):
    with open(SCHEDULE_JSON, "w") as f:
        json.dump(data, f, indent=2)

def get_next_schedule_slot():
    """Return next available noon EDT (16:00 UTC) that isn't already taken."""
    from datetime import datetime, timedelta
    scheduled = load_schedule()
    taken = {s.get("schedule_utc") for s in scheduled}
    # Start from today or tomorrow
    now = datetime.utcnow()
    candidate = now.replace(hour=16, minute=0, second=0, microsecond=0)
    if now.hour >= 16:
        candidate += timedelta(days=1)
    for _ in range(90):
        iso = candidate.strftime("%Y-%m-%dT16:00:00.000Z")
        if iso not in taken:
            return iso
        candidate += timedelta(days=1)
    return None

def ghl_upload_video(video_path):
    """Upload video to GHL CDN using curl (bypasses Cloudflare bot block). Returns URL."""
    import subprocess, re
    result = subprocess.run(
        [
            "curl", "-s", "-X", "POST",
            GHL_UPLOAD_URL,
            "-H", f"Authorization: Bearer {GHL_PIT_TOKEN}",
            "-H", "Version: 2021-07-28",
            "-F", f"file=@{video_path};type=video/mp4",
        ],
        capture_output=True, text=True, timeout=180
    )
    if result.returncode != 0:
        raise ValueError(f"curl upload failed: {result.stderr}")
    data = json.loads(result.stdout)
    url = data.get("fileUrl") or data.get("url") or data.get("cdnUrl") or data.get("mediaUrl")
    if not url:
        raise ValueError(f"No URL in upload response: {result.stdout[:300]}")
    return url

def ghl_schedule_post(video_url, caption, schedule_utc):
    """Schedule a GHL Social Planner reel post. Returns API response dict."""
    import subprocess
    payload = json.dumps({
        "accountIds": GHL_ACCOUNTS,
        "summary": caption,
        "media": [{"url": video_url, "type": "video"}],
        "type": "reel",
        "scheduleDate": schedule_utc,
        "userId": GHL_USER_ID,
    })
    result = subprocess.run(
        [
            "curl", "-s", "-X", "POST",
            GHL_SOCIAL_API,
            "-H", f"Authorization: Bearer {GHL_PIT_TOKEN}",
            "-H", "Version: 2021-07-28",
            "-H", "Content-Type: application/json",
            "-d", payload,
        ],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise ValueError(f"curl schedule failed: {result.stderr}")
    return json.loads(result.stdout)

def post_to_ghl(video_url, caption, schedule_time=None):
    """Post/schedule to GHL Social Planner. Used by legacy /api/approve route."""
    try:
        schedule_utc = schedule_time or get_next_schedule_slot()
        result = ghl_schedule_post(video_url, caption, schedule_utc)
        ghl_id = result.get("id") or result.get("postId") or "unknown"
        return {
            "success": True,
            "post_id": ghl_id,
            "platforms": ["Hybrid Funding FB", "Suess Villiano FB", "smartsystems_ IG", "Hybrid Funding TikTok"],
            "message": f"Scheduled on GHL Social Planner (ID: {ghl_id})",
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.route("/api/approve", methods=["POST"])
def api_approve():
    try:
        data      = request.json or {}
        file_obj  = data.get("file", {})
        file_name = file_obj if isinstance(file_obj, str) else (file_obj or {}).get("name", "")
        title       = data.get("title", "SV Content · Hybrid Funding")
        description = data.get("description", "hybridfunding.co")
        tags_str    = data.get("tags", "")

        # Build R2 public URL for the video
        video_url = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com/sv-content-engine/shorts_reels/{file_name}"

        # Caption for social platforms
        caption = f"{title}\n\n{description}\n\nhybridfunding.co"

        # Post to GHL (Facebook, Instagram, TikTok, X)
        ghl_result = post_to_ghl(video_url, caption)

        # Log it
        log = {
            "file": file_name, "title": title,
            "description": description, "tags": tags_str,
            "timestamp": datetime.now().isoformat(),
            "ghl_result": ghl_result,
            "status": "posted" if ghl_result.get("success") else "queued",
        }
        os.makedirs(os.path.join(BASE, "drafts"), exist_ok=True)
        log_path = os.path.join(BASE, "drafts", f"upload_{file_name}.json")
        with open(log_path, "w") as f:
            json.dump(log, f, indent=2)

        if ghl_result.get("success"):
            return jsonify({
                "success": True,
                "message": f"Posted to {ghl_result.get('message', 'social platforms')} ✅",
                "platforms": ghl_result.get("platforms", []),
                "youtube_url": None,
            })
        else:
            return jsonify({
                "success": False,
                "queued": True,
                "message": ghl_result.get("message", "GHL social accounts not connected"),
                "action": "Go to GHL Marketing > Social Planner > Connect Accounts",
            })
    except Exception as exc:
        import traceback
        return jsonify({"success": False, "error": str(exc), "trace": traceback.format_exc()}), 200

@app.route("/api/approve-draft", methods=["POST"])
def api_approve_draft():
    data    = request.json or {}
    name    = data.get("name", "")

    # Find the script file
    script_path = _safe_path(SCRIPTS, name)
    if not script_path or not os.path.exists(script_path):
        return jsonify({"error": f"Script file not found: {name}"}), 404

    with open(script_path) as f:
        script_text = f.read().strip()

    if not script_text:
        return jsonify({"error": "Script is empty"}), 400

    # Extract day number from filename (day_06_vox_ready.txt → 6)
    import re
    m = re.search(r"day_(\d+)", name)
    if not m:
        return jsonify({"error": "Could not determine day number from filename"}), 400

    day_num = int(m.group(1))
    key = f"day_{day_num:02d}"

    # Check VoxCPM is available (generous timeout — first request can be slow on MPS)
    vox_ok = False
    vox_err = ""
    for attempt in range(3):
        try:
            health = urllib.request.urlopen("http://localhost:8808/api/health", timeout=10)
            health_data = json.loads(health.read())
            if health_data.get("status") == "ok":
                vox_ok = True
                break
        except Exception as e:
            vox_err = str(e)
            import time as _time; _time.sleep(1)
    if not vox_ok:
        return jsonify({"error": f"VoxCPM not responding after 3 attempts — make sure it is running on port 8808. ({vox_err})"}), 503

    # Already generating?
    if GEN_STATUS.get(key, {}).get("status") == "generating":
        return jsonify({"message": f"Day {day_num} is already generating...", "status": "already_running"})

    # Start generation in background
    t = threading.Thread(target=generate_voice_async, args=(day_num, script_text), daemon=True)
    t.start()

    GEN_STATUS[key] = {"status": "generating", "message": f"Generating Day {day_num} voice..."}

    return jsonify({
        "success": True,
        "message": f"Day {day_num} voice generating now. Check back in 3-5 minutes — it will appear in the Voice tab.",
        "day": day_num,
        "status": "generating",
    })

@app.route("/api/gen-status")
def api_gen_status():
    return jsonify(GEN_STATUS)

FAL_API_KEY    = _secret("FAL_API_KEY")
HEYGEN_API_KEY = _secret("HEYGEN_API_KEY")
BROLL_DIR      = os.path.join(BASE, "broll_library")
MASTERS_DIR    = os.path.join(BASE, "masters")

@app.route("/api/engine-status")
def api_engine_status():
    """Live status check for all pipeline services."""
    results = []

    # 1. VoxCPM
    try:
        r = urllib.request.urlopen("http://localhost:8808/api/health", timeout=10)
        d = json.loads(r.read())
        model = d.get("model", "VoxCPM")
        results.append({"name": "VoxCPM H1", "detail": f"{model} · Harrahs voice · Port 8808", "status": "live", "badge": "LIVE"})
    except Exception:
        results.append({"name": "VoxCPM H1", "detail": "Port 8808 — not running", "status": "error", "badge": "OFFLINE"})

    # 2. fal.ai — check account balance
    try:
        req = urllib.request.Request(
            "https://rest.alpha.fal.ai/v1/billing/balance",
            headers={"Authorization": f"Key {FAL_API_KEY}"}
        )
        r = urllib.request.urlopen(req, timeout=8)
        bal = json.loads(r.read())
        credits = bal.get("balance") or bal.get("credits") or bal.get("amount") or 0
        if float(credits) > 0:
            results.append({"name": "fal.ai", "detail": f"Balance: ${credits:.2f}", "status": "live", "badge": "FUNDED"})
        else:
            results.append({"name": "fal.ai", "detail": "Balance empty — top up at fal.ai/dashboard/billing", "status": "warn", "badge": "ADD CREDITS"})
    except Exception as e:
        # Fallback — just confirm key exists
        results.append({"name": "fal.ai", "detail": "Key configured · check fal.ai/dashboard for balance", "status": "warn", "badge": "CHECK"})

    # 3. HeyGen — check remaining quota
    try:
        req = urllib.request.Request(
            "https://api.heygen.com/v1/user/remaining_quota",
            headers={"X-Api-Key": HEYGEN_API_KEY}
        )
        r = urllib.request.urlopen(req, timeout=8)
        d = json.loads(r.read())
        quota = d.get("data", {}).get("remaining_quota", d.get("remaining_quota", 0))
        if quota and int(quota) > 0:
            results.append({"name": "HeyGen", "detail": f"Talking head engine · {quota} credits remaining", "status": "live", "badge": "LIVE"})
        else:
            results.append({"name": "HeyGen", "detail": "Credits needed — app.heygen.com → Credits", "status": "warn", "badge": "ADD CREDITS"})
    except Exception as e:
        err_str = str(e)
        if "401" in err_str or "403" in err_str:
            results.append({"name": "HeyGen", "detail": "API key invalid", "status": "error", "badge": "KEY ERROR"})
        else:
            # Key exists but couldn't check — mark as configured
            results.append({"name": "HeyGen", "detail": "Key configured · sv_talking_photo_id set", "status": "live", "badge": "CONNECTED"})

    # 4. Whisper
    whisper_ok = os.path.exists("/opt/homebrew/bin/whisper") or os.path.exists(os.path.expanduser("~/.local/bin/whisper"))
    try:
        r = subprocess.run(["whisper", "--help"], capture_output=True, timeout=3)
        whisper_ok = True
    except Exception:
        pass
    results.append({"name": "Whisper Subs", "detail": "Word-level sync · Auto-burn", "status": "live" if whisper_ok else "warn", "badge": "LIVE" if whisper_ok else "CHECK"})

    # 5. Cloudflare R2
    try:
        files_count = len([f for f in os.listdir(SHORTS) if f.endswith(".mp4")]) if os.path.exists(SHORTS) else 0
        results.append({"name": "Cloudflare R2", "detail": f"sv-content-engine · {files_count} finals", "status": "live", "badge": "LIVE"})
    except Exception:
        results.append({"name": "Cloudflare R2", "detail": "sv-content-engine bucket", "status": "live", "badge": "LIVE"})

    # 6. YouTube / Composio
    results.append({"name": "YouTube", "detail": "ca_Zp6vgFT65nyH · Composio", "status": "live", "badge": "CONNECTED"})

    # 7. GHL Social Planner
    results.append({"name": "GHL Social Planner", "detail": "FB · IG · TikTok · All accounts", "status": "live", "badge": "LIVE"})

    return jsonify(results)

@app.route("/api/broll")
def api_broll():
    """Return all B-roll clips from broll_library (all subdirs)."""
    clips = []
    if os.path.exists(BROLL_DIR):
        for root, dirs, files in os.walk(BROLL_DIR):
            for f in sorted(files):
                if f.lower().endswith((".mp4", ".mov")):
                    p = os.path.join(root, f)
                    rel = os.path.relpath(p, BROLL_DIR)
                    folder = os.path.relpath(root, BROLL_DIR)
                    s = os.stat(p)
                    clips.append({
                        "name": f,
                        "folder": folder if folder != "." else "root",
                        "rel_path": rel,
                        "size_mb": round(s.st_size/1024/1024, 1),
                        "modified": s.st_mtime
                    })
    return jsonify(clips)

@app.route("/api/masters")
def api_masters():
    return jsonify(list_files(MASTERS_DIR, [".mp4", ".mov"]))

@app.route("/stream/broll/<path:rel_path>")
def stream_broll(rel_path):
    p = _safe_path(BROLL_DIR, rel_path)
    if not p or not os.path.exists(p): return "Not found", 404
    return send_file(p, mimetype="video/mp4", conditional=True)

@app.route("/stream/masters/<name>")
def stream_masters(name):
    p = _safe_path(MASTERS_DIR, name)
    if not p or not os.path.exists(p): return "Not found", 404
    return send_file(p, mimetype="video/mp4", conditional=True)

# ── SCHEDULE TAB ROUTES ────────────────────────────────────────────────────────

@app.route("/api/queue")
def api_queue():
    """Return days that have a FINAL video but haven't been scheduled yet."""
    scheduled = load_schedule()
    scheduled_days = {s["day"] for s in scheduled}
    queue = []
    for day, meta in sorted(QUEUE_DAYS.items()):
        video_path = os.path.join(SHORTS, meta["video"])
        if not os.path.exists(video_path):
            continue  # video not rendered yet
        if day in scheduled_days:
            continue  # already scheduled
        caption = read_caption_for_day(day)
        queue.append({
            "day": day,
            "label": meta["label"],
            "video": meta["video"],
            "caption_preview": caption[:160] + ("…" if len(caption) > 160 else ""),
            "has_video": True,
            "suggested_utc": get_next_schedule_slot(),  # rolling — each call gets next open slot
        })
    return jsonify(queue)

@app.route("/api/schedule")
def api_schedule():
    """Return the current schedule.json contents."""
    return jsonify(load_schedule())

@app.route("/api/schedule-post", methods=["POST"])
def api_schedule_post():
    """Upload a day's video to GHL CDN and schedule the post."""
    data = request.json or {}
    day = int(data.get("day", 0))
    schedule_utc = data.get("schedule_utc")  # e.g. "2026-04-17T16:00:00.000Z"

    if day not in QUEUE_DAYS:
        return jsonify({"success": False, "error": f"Unknown day: {day}"}), 400

    meta = QUEUE_DAYS[day]
    video_path = os.path.join(SHORTS, meta["video"])
    if not os.path.exists(video_path):
        return jsonify({"success": False, "error": f"Video not found: {meta['video']}"}), 400

    if not schedule_utc:
        schedule_utc = get_next_schedule_slot()
    if not schedule_utc:
        return jsonify({"success": False, "error": "No available schedule slot found"}), 400

    caption = read_caption_for_day(day)

    try:
        # Upload video to GHL CDN
        video_url = ghl_upload_video(video_path)
    except Exception as e:
        return jsonify({"success": False, "error": f"Upload failed: {e}"}), 500

    try:
        # Schedule the post
        result = ghl_schedule_post(video_url, caption, schedule_utc)
        ghl_id = result.get("id") or result.get("postId") or "unknown"
    except Exception as e:
        return jsonify({"success": False, "error": f"Schedule failed: {e}", "video_url": video_url}), 500

    # Save to schedule.json
    schedule_data = load_schedule()
    schedule_data.append({
        "day": day,
        "label": meta["label"],
        "status": "scheduled",
        "ghl_post_id": ghl_id,
        "schedule_utc": schedule_utc,
        "schedule_local": "12:00 PM EDT",
        "video_url": video_url,
        "video_local": video_path,
        "caption_preview": caption[:120],
        "platforms": ["Hybrid Funding FB", "Suess Villiano FB", "smartsystems_ IG", "Hybrid Funding TikTok"],
        "scheduled_at": datetime.now().isoformat() + "Z",
    })
    save_schedule(schedule_data)

    return jsonify({
        "success": True,
        "day": day,
        "ghl_post_id": ghl_id,
        "schedule_utc": schedule_utc,
        "video_url": video_url,
        "message": f"Day {day} scheduled for {schedule_utc} across all 4 platforms ✅",
    })

def run(host=None, port=None):
    host = host or os.environ.get("SV_HOST", "127.0.0.1")
    port = int(port or os.environ.get("SV_PORT", "4444"))
    print("\n" + "="*50)
    print("  SV CONTENT ENGINE — Dashboard v2")
    print("  Mobile-optimized · Draft workflow live")
    print(f"  Open: http://localhost:{port}")
    if _MISSING_SECRETS:
        print(f"  ⚠️  missing secrets (features disabled): {', '.join(sorted(set(_MISSING_SECRETS)))}")
        print("     set them in your shell/.env — see .env.example")
    if host != "127.0.0.1" and not SV_TOKEN:
        print("  ⚠️  bound beyond localhost with NO auth token — set SV_DASHBOARD_TOKEN!")
    print("="*50 + "\n")
    app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    run()
