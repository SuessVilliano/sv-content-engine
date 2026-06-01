# SV Studio — One Roof

Type what you want → it builds it → you see it in the platform. Free-first, so a
day of content costs cents, not hundreds.

## Run it

```
pip install -r requirements.txt   # flask is the only hard requirement
cp .env.example .env              # fill in keys; .env is gitignored
set -a; source .env; set +a       # load them

python3 launch.py            # preflight every service, then boot the Studio
python3 launch.py --check    # just check what's up / what to start
python3 launch.py --lan      # expose on the LAN (requires SV_DASHBOARD_TOKEN)
```

`launch.py` checks Flask, VoxCPM (:8808), ComfyUI (:8188) + workflows, ffmpeg,
and librosa/whisper, prints exactly what to start for anything offline, then
boots the dashboard at http://localhost:4444. Anything missing degrades
gracefully — the Studio always runs; only that one capability waits.

### Security
- **Secrets live in the environment**, never in source (see `.env.example`).
  Any key that was ever committed should be rotated.
- The dashboard **binds to `127.0.0.1` by default**. To reach it from another
  device use `--lan`, which *requires* `SV_DASHBOARD_TOKEN` — without auth,
  anyone on the network could spend your generation credits or post to your
  socials. Requests then pass the token via `X-SV-Token` header or `?token=`.
- File-serving routes are path-traversal guarded; uploads are size-capped
  (`SV_MAX_UPLOAD_MB`, default 300) and concurrency-capped
  (`SV_MAX_CONCURRENT_JOBS`, default 2).

### Tests

```
python3 -m pytest        # 40 tests: parse/plan/execute, beat-edit, looks, auth, traversal
```


```
  ✨ Studio (dashboard, localhost:4444)
     command bar → Plan (free preview) / Build (queue)
        │
        ▼
  engine.py      sentence → JobSpec → plan → job   (Claude or free rules)
  brands.py      who it's for: voice, avatar, pillars, folders, accounts
  router.py      free local (Wan/LTX/ComfyUI) by default; paid hero on request; budget-guarded
  music_video.py drop a song → auto lyrics + beat → cut clips ON the beat
  filters.py     one-click cinematic looks
```

Drop a song on the Studio → beat + lyrics detected → build to the beat → then
✂️ Edit any music video in-platform (reorder clips, swap looks, re-cut) and
re-render — no external tool, all under one roof.

## The pieces (all built, all tested)

| Module | What it does | Cost |
|--------|--------------|------|
| `brands.py` | Many brands from one engine: music, each business, each avatar | free |
| `router.py` | Picks free-local vs paid-hero per clip; caps spend; logs every cent | free / pennies |
| `music_video.py` | MP3 → lyrics (Whisper) + beat (librosa) → beat-synced edit + burned lyrics | free (local) |
| `filters.py` | Cinematic / noir / vintage / neon / grain / vignette … stackable | free |
| `engine.py` | Natural language → job. Detects kind, duration, looks, platform, hero | ~free |
| `dashboard.py` | ✨ Studio command bar + job cards + preview | free |

## Run it

```bash
python3 dashboard.py            # open http://localhost:4444 → Studio tab
```

Type, for example:
- `make me a 30s moody trading short about discipline, cinematic look`
- `music video for midnight_bloom.mp3, neon, cut on the beat`
- `60s ugc ad for my candle brand, warm and dreamy look, tiktok`

Hit **Plan** to see the steps + exact cost for free. Hit **Build** to produce it.

## What keeps it cheap

- **Voice**: VoxCPM, local, $0.
- **Video**: Wan 2.2 / LTX-Video in ComfyUI on your own GPU, $0. Paid APIs
  (Veo/Kling/Seedance) only fire for a clip you mark **hero**.
- **Avatars**: set a brand's `avatar.engine` to `heygem` (free, local) instead
  of `heygen` (paid) and talking heads cost $0 too.
- **Budget guard**: per-brand `daily_usd` / `monthly_usd` caps block accidental
  spend. `python3 router.py spend` shows the running total.

## What needs setup on your Mac (one time)

1. **ComfyUI** + Wan 2.2 & LTX-Video models → export one workflow per model into
   `workflows/` (token contract in `workflows/README.md`). Until then, local
   generation reports a clear "start ComfyUI / add workflow" message instead of
   silently spending.
2. **Transcription/beat libs** for music: `pip install faster-whisper librosa`.
3. Optional keys (only for hero shots / better NL): `FAL_API_KEY`,
   `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `HEYGEN_API_KEY`, `GHL_PIT_TOKEN`.

## Roadmap (next builds)

- [x] **Live execution** — Build runs the pipeline in the background (script →
      VoxCPM voice → router/ComfyUI clips → ffmpeg assemble), streams per-step
      progress to the Studio, and shows an inline preview when done. Steps that
      can't run (service offline) skip with a clear reason instead of hanging,
      so the job ends `partial` rather than failing.
- [x] **Drop-an-MP3 upload** — drag a song onto the Studio; it analyses beat +
      lyrics in-browser (`/api/upload-song` → `engine.ingest_song`), shows tempo /
      beats / sections / lyric preview, then one click builds the music video to
      the beat. Degrades cleanly with an install hint if librosa/whisper missing.
- [x] **In-platform editor** — every finished music video gets an ✂️ Edit panel:
      reorder/drop clips, toggle looks (they stack), pick the cut mode
      (downbeat/beat/bars/seconds) and N, then re-render to the beat
      (`/api/edit` → `engine.rerender`). Edits are versioned on the job.

### Live execution — how it runs
`engine.execute(job, brand)` walks the planned steps, writing each artifact into
`<brand>/jobs/<id>/` and updating the job JSON after every step (the Studio polls
`/api/job/<id>` every 4s while running). The final video is copied into the
brand's `shorts_reels/` so the Library tab sees it too. A queued-job worker
(`engine.process_queue`) is available for cron/headless runs.

The **talking-head** step is wired for HeyGen (talking-photo → poll → download,
composited as the short's lead visual). It's opt-in: set `SV_ENABLE_AVATAR=1`
plus the brand's `avatar.talking_photo_id` and `avatar.heygen_voice_id`, so it
never spends credits unless you ask. Offline/disabled, it skips and the b-roll
path continues. *(Live HeyGen calls haven't been validated end-to-end yet —
test with one short before batching.)*
