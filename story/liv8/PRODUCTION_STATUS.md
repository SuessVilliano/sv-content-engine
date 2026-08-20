# LIV8 — Production Status (living file)

_Read at the start of every render session. Update at the end._
_Last updated: 2026-08-19_

## Pipeline decision
Rendering runs through **AgentOpus** (connected MCP, PRO plan). The local Mac
studio (VoxCPM `:8808`, ComfyUI `:8188`) is not reachable from cloud sessions,
so cloud renders use AgentOpus story-mode (Seedance transitions + photoreal
image model, anchored on the Jamaur reference). The local engine remains the
free path when working on the Mac.

- Org credits at last check: **3,232 recurring** (2026-08-19).
- Posting posture: **review gate** — nothing posts to live accounts until approved.

## Identity anchors
- **Face:** AgentOpus shared-library asset `4a2f1b5c2c8fb3ec`
  (`story/liv8/09_REFERENCE_ASSETS/jamaur_reference.jpg`). Use as `actor` anchor
  on every shot containing Jamaur.
- **Voice:** cloned voice PENDING — needs a 10–30s clean spoken sample uploaded
  to this session (the Mac reference `sv_voice_harrahs_clean.wav` is not in git).
  Interim: stock narration voice on the face-consistency test.

## Connected accounts (AgentOpus)
YouTube: Suess Villiano, Trade Hybrid · TikTok: @suessvilliano2 ·
Instagram: @suessvilliano, @hybridfunding_ · Facebook: Hybrid Funding, Trade Hybrid.

## Shot render log (S01–S17)
| Shot | Purpose | Status | Video id | Identity /10 | Notes |
|------|---------|--------|----------|--------------|-------|
| S15 | anchor: present-day close-up | pending | | | render first |
| S09 | anchor: underground | pending | | | |
| S10 | anchor: builder returns | pending | | | |
| S02 | anchor: hustle-era | pending | | | |
| S14 | anchor: convergence of selves | pending | | | |
| S01,S03–S08,S11–S13,S16,S17 | remaining | not started | | | after anchors pass |

## Gate
Anchor shots must score identity ≥ 8/10 and hold the same face across all five
before rendering the rest of the teaser.
