# Multi-Brand Engine — Guide

The engine used to be hardcoded to one persona (Source Vessel / trading). It now
drives **any number of brands** from small JSON config files. Same engine, same
dashboard, same daily workflow — you just switch which brand is "active."

This is the upgrade that turns a single channel into a **platform** that can run
your music, each of your businesses, and multiple AI avatars side by side.

---

## The three brand types

| Type | For | What it produces |
|------|-----|------------------|
| `persona`  | A face that builds a following | Daily talking-head + B-roll shorts, pillar rotation |
| `music`    | Your songs | Beat-synced music videos, lyric videos, visualizers, snippet clips |
| `business` | A product/service | UGC-style ads: hook tests, problem→product, demos, social proof |

---

## Where things live

```
brands/
  _active.json              ← which brand the engine produces for right now
  source_vessel.json        ← your existing trading persona (migrated, unchanged behavior)
  music.template.json       ← copy → your music brand
  business_ugc.template.json← copy → each business
  avatar_persona.template.json ← copy → each new avatar/persona
brands.py                   ← the loader + CLI (stdlib only, no installs)
```

Each brand has its **own** `base_dir`, so its scripts, voice, B-roll, and posts
never collide with another brand's.

---

## Everyday commands

```bash
python3 brands.py list              # see all brands (* = active)
python3 brands.py active            # which brand is active
python3 brands.py show source_vessel# full resolved config (secrets included)
python3 brands.py paths source_vessel  # where this brand's folders are
python3 brands.py validate          # check every brand file for mistakes
```

## Switch the active brand

Either edit `brands/_active.json`:
```json
{ "active": "my_music" }
```
…or per-run with an env var (wins over the file):
```bash
SV_BRAND=my_music python3 generate_90days.py
SV_BRAND=my_music python3 dashboard.py
```

The dashboard and the generator both read the active brand automatically. If
`brands/` is missing entirely, they fall back to the original Source Vessel
defaults — nothing that works today breaks.

---

## Add a new brand in 3 steps

1. **Copy a template** to a real config (drop the `.template`):
   ```bash
   cp brands/music.template.json brands/my_music.json
   ```
2. **Edit it** — set `id`, `name`, `base_dir`, and fill in the blanks. For a
   music brand point `base_dir` at a fresh folder and drop your Suno mixes in
   its `songs/` subfolder. For a persona/business, set a `reference_image` and a
   voice `reference_audio` and **never change them** (consistency = following).
3. **Validate + activate:**
   ```bash
   python3 brands.py validate
   echo '{ "active": "my_music" }' > brands/_active.json
   ```

---

## Secrets stay out of git

Any config value written as `"env:NAME"` is read from the environment at load
time, never stored in the JSON. Set them in your shell / `.env`:

```bash
export HEYGEN_API_KEY=...
export GHL_PIT_TOKEN=...
export FAL_API_KEY=...
```

`brands.py show <id>` resolves them so you can confirm they're set, but the
committed files only ever contain the `env:` pointer.

---

## The cost knob (`generation`)

Every brand has a `generation` block that decides **free-local vs paid-hero**:

```json
"generation": {
  "default_route": "local",
  "text_to_video":  { "local": "ltx-video", "hero": "veo-3.1" },
  "image_to_video": { "local": "wan2.2",    "hero": "kling-2.0" },
  "music_video":    { "local": "ltx-2.3-audio", "hero": "freebeat" }
}
```

- `default_route: "local"` → free models (run on your own GPU / ComfyUI) for
  everything by default. This is what keeps spend near $0.
- Mark a single clip as a "hero" shot and the engine escalates to the paid model
  (`B.route_for("text_to_video", hero=True)` → `veo-3.1`).
- Optional `budget: { "daily_usd": 5, "monthly_usd": 50 }` caps paid spend.

## The cost router (`router.py`)

`router.py` reads this block and actually dispatches generation: free local
(ComfyUI) by default, paid hero only when you ask — and it refuses to spend by
accident.

```bash
python3 router.py prices                                   # price table
python3 router.py plan --kind text_to_video --count 20     # estimate a batch ($0 local)
python3 router.py plan --kind text_to_video --count 20 --hero   # estimate paid batch
python3 router.py gen  --kind image_to_video --image still.png  # run (local, free)
python3 router.py gen  --kind text_to_video  --prompt "rain" --hero   # run (paid hero)
python3 router.py gen  --kind text_to_video  --prompt "rain" --dry-run  # decide, spend nothing
python3 router.py spend                                     # ledger: today / month / all-time
```

Guarantees:
- **Never silently spends.** If ComfyUI is down or a workflow template is
  missing, it raises — it does not fall back to a paid API.
- **Budget guard.** A paid call that would breach `daily_usd`/`monthly_usd` is
  blocked (override per-call with `--allow-over-budget`).
- **Spend ledger.** Every paid clip is logged to `<base_dir>/.spend_ledger.jsonl`.

Local generation needs one ComfyUI workflow per local model in `workflows/`
(see `workflows/README.md` for the token contract).
