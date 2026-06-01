# SV Studio — One Roof

Type what you want → it builds it → you see it in the platform. Free-first, so a
day of content costs cents, not hundreds.

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

- [ ] **Live execution** — `engine.run()` drives VoxCPM/ComfyUI/ffmpeg so a Build
      produces a real file that appears in the Studio preview.
- [ ] **Drop-an-MP3 upload** in the Studio tab (browser → song.json → build).
- [ ] **In-platform editor** — trim, reorder, swap look, re-cut to the beat.
