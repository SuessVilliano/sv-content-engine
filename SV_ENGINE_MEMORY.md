# SV ENGINE MEMORY
# Source Vessel / Hybrid Funding — Persistent State
# Read at the START of every run. Write updates at the END of every run.
# Last updated: 2026-04-15

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## CAMPAIGN STATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
campaign_start: 2026-04-15
last_run: 2026-04-16
next_day_to_write: 8
last_day_with_script: 7
last_day_with_voice: 7
last_day_with_video: 5
last_day_approved: 7 (days 6 and 7 have _APPROVED.flag files)
last_day_posted: unknown (check approved/ and scheduled/ folders)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## PILLAR ROTATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Week 1–2   (Days 01–14):  MINDSET
Week 3–4   (Days 15–28):  DISCIPLINE
Week 5–6   (Days 29–42):  STRATEGY
Week 7–8   (Days 43–56):  REALITY
(then repeats)
current_pillar: MINDSET
days_remaining_in_pillar: 6 (days 8–14 are still Mindset)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## VOICE ENGINE — VoxCPM H1 (FREE, LOCAL)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
api_url: http://localhost:8808
clone_endpoint: POST /api/clone
health_endpoint: GET /api/health
payload: {text: '...', reference_audio: '/Users/jamaurjohnson/Documents/SV_Content_Engine/assets/sv_voice_harrahs_clean.wav'}
fallback_reference: /Users/jamaurjohnson/Documents/SV_Content_Engine/assets/sv_reference.wav
output_path: /Users/jamaurjohnson/Documents/SV_Content_Engine/voice/day_XX_sv.wav
cost: $0.00

VOICE STYLE RULES (critical — never break these):
- No contractions. 'do not' not 'don't'. 'is not' not 'isn't'.
- '...' for pauses — 3 dots, no em-dash ellipsis
- Short sentences. Never more than 12 words per sentence.
- No stage directions, headers, or formatting in vox_ready file
- All caps only for 1–2 KEY words per script that need emphasis
- Voice is deliberate, measured, already arrived — never hustling

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## BEAT LIBRARY (6 beats as of 2026-04-15)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
dark_cinematic_01.mp3   → Discipline, Reality content
dark_cinematic_02.mp3   → Discipline, Reality content
Midnight_Bloom.mp3      → dark_cinematic (assigned by keyword ambiguity)
motivational_rise_01.mp3 → Mindset content
motivational_rise_02.mp3 → Mindset content
focus_ambient_01.mp3    → Strategy content

BEAT ASSIGNMENTS (do not repeat same beat on consecutive days):
day_01: motivational_rise_01.mp3
day_02: motivational_rise_02.mp3
day_03: motivational_rise_01.mp3
day_04: motivational_rise_02.mp3
day_05: motivational_rise_01.mp3
day_06: Midnight_Bloom.mp3
day_07: motivational_rise_02.mp3
last_beat_used: motivational_rise_02.mp3

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## CONTENT TOPICS USED — MINDSET PILLAR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
(Never repeat a core theme within the same pillar cycle)
day_01: Mind is the leak — psychology costs more than losses
day_02: The best trade is the one you do not take — discipline of inaction
day_03: Fear as information not instruction
day_04: Patience — fewest trades, most profit
day_05: Trading as psychological laboratory / self-discovery
day_06: Evidence-based confidence — track record before belief
day_07: Solo journey — work in silence, results speak eventually

REMAINING MINDSET TOPICS (days 8–14 — use these):
- Identity shift: trader who follows the plan vs. trader who needs to make money today
- Detachment from outcome — process score vs. P&L score
- Morning routine / pre-session intention ritual
- Managing the session AFTER a loss (the 20-minute rule)
- Why funded traders outlast solo traders (structure vs. willpower)
- The cost of one undisciplined session — how one bad day erases weeks
- Consistency as the only real edge

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## CHARACTER — SV (Source Vessel / Suess Villiano)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Full character brief: /SV_Content_Engine/assets/character_sheet/SV_Character_Sheet.md
Video generation: Nano Banana → Seedance image-to-video (always start from Nano Banana still)
B-ROLL ENGINE PRIORITY (cheapest to most expensive):
  1. Kling 1.6 Pro  -- fal-ai/kling-video/v1.6/pro/text-to-video  (~$0.25/5s) PRIMARY
  2. Kling 2.0 Pro  -- fal-ai/kling-video/v2.0/pro/text-to-video  (~$0.50/5s) HIGH QUALITY
  3. Seedance 2.0   -- fal-ai/bytedance/seedance-2.0 (~$0.45/clip) character shots
  4. Veo 3 Fast     -- google gemini API (~$0.50/clip) needs billing on liv8-377321
Kling_endpoint: fal-ai/kling-video/v1.6/pro/text-to-video (PRIMARY B-roll)
fal_api_key: d8d27e53-7a69-4ea4-a16f-284e97caa9fe:12c01f980a45fdffad46a3cdb6e8f312
fal_status: BALANCE EXHAUSTED — top up at fal.ai/dashboard/billing before B-roll auto-generates

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SOCIAL / DISTRIBUTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dashboard: http://localhost:4444 (run: python3 dashboard.py)
GHL location_id: alK3nxmaA2aXkCGUQlUT
GHL pit_token: pit-33dcb1f3-6ddd-4188-97f9-1504518f6e39
Posting: GHL Social Planner → FB, IG, TikTok, X (all platforms)
YouTube: Connected via Composio
R2 storage: sv-content-engine bucket (Cloudflare R2)
Upload script: /SV_Content_Engine/upload_to_r2.sh

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SV BRAND VOICE — LOCKED RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tone: Calm. Certain. Deliberate. Already figured it out.
Never: Hyped. Rushed. Salesy. Preachy. AI-sounding.
Signature openers: 'Most traders miss this...' / 'Pay attention...' / 'The truth is...'
Core thesis: 'You do not need more information. You need more control.'
Scripts sound like a mentor who has nothing to prove — not a course seller.
Every line must survive being read aloud slowly. If it sounds rushed, cut it.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## STYLE NOTES FROM APPROVED CONTENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Approved days 6 and 7 confirm: vox scripts with no headers, no formatting, just clean prose
- Sentences average 8–10 words
- '...' used between thoughts, not within a sentence
- Each script ends on a single definitive sentence — no question marks in the close
- Scripts that tested well: day_06 (evidence-based confidence) and day_07 (solo journey)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## DAILY RUN CHECKLIST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
START: Read this file. Know where you are before writing anything.
1. Check beats/ for new files → auto-assign mood
2. Check scripts/ to find actual next_day_to_write (count existing day_XX files)
3. Write 1 full content package (short + long + social + vox_ready + broll_prompts)
4. Attempt VoxCPM voice generation: POST to localhost:8808/api/clone
5. Assign beat (rotate, do not repeat consecutive)
6. Update this memory file with: last_run date, topics used, beat assigned, day progress
7. iMessage Jamaur at liv8ent@gmail.com with the standard report
END: Write updated memory file back to this path.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## KNOWN ISSUES / ACTION ITEMS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- fal.ai balance exhausted → Seedance B-roll blocked. Top up at fal.ai/dashboard/billing
- ElevenLabs clone voice requires paid plan → DO NOT USE. VoxCPM is primary and free.
- day_01 short/long/social scripts written 2026-04-15 (previously only vox_ready existed)
- Dashboard (localhost:4444) must be running for approve-draft workflow to trigger voice gen

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## HEYGEN — TALKING HEAD VIDEO ENGINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
api_key: sk_V2_hgu_k9GvV8Bbud0_BeD4VvnSwIgNO8ECptMC0BHmBZqnSpUv
generate_endpoint: POST https://api.heygen.com/v2/video/generate
status_endpoint:   GET  https://api.heygen.com/v1/video_status.get?video_id=XX
talking_photos:    5665 photos on account (confirmed 2026-04-15)
credit_status:     INSUFFICIENT — API credits needed (separate from subscription credits)
                   Top up at: app.heygen.com → Credits

CONFIRMED PIPELINE (ready once credits added):
  Step 1: VoxCPM generates voice .wav (free, local, Harrahs H1 voice)
  Step 2: Upload .wav to Cloudflare R2 → get public URL
  Step 3: POST to HeyGen /v2/video/generate:
    {
      video_inputs: [{
        character: { type: 'talking_photo', talking_photo_id: '[SV_PHOTO_ID]' },
        voice: { type: 'audio', audio_url: '[R2_URL_OF_WAV]' }
      }],
      dimension: { width: 1080, height: 1920 }
    }
  Step 4: Poll status endpoint until complete → download video_url
  Step 5: Save to shorts_reels/day_XX_SV_FINAL.mp4

⚠️  ACTION REQUIRED — JAMAUR MUST DO:
  1. Top up HeyGen API credits at app.heygen.com
  2. Identify SV talking photo ID from the 5665 on account
     → Go to app.heygen.com → Talking Photos → find SV face → copy ID
  3. Paste SV talking photo ID below:
     sv_talking_photo_id: 872aba25a4da419d982d180df7ad156a

avatar_id_from_old_config: AjSHTFMHCghJkAe2wywi
avatar_id_status: REPLACED — use sv_talking_photo_id above
                  Use talking_photo approach instead (confirmed working).

INTEGRATION ROLE IN PIPELINE:
  HeyGen replaces: Seedance character shots (requires fal.ai credits)
  HeyGen produces: The SV talking head layer (9:16 vertical, lip-synced to VoxCPM audio)
  B-roll overlays still come from: Veo 3 / Seedance (when fal.ai is funded)
  Assembly: ffmpeg composites talking head + B-roll + subtitles → final short

sv_talking_photo_description: Real photo of Jamaur — black turtleneck, gold Cuban link chain, dark glasses, looking directly at camera. Cinematic red/warm tones. Face fills frame. Best for HeyGen lip sync.
sv_talking_photo_selected: 2026-04-15
sv_talking_photo_backup_id: 686f4e54da284cb7907c9ef27dbe3086 (luxury car showroom, full body — backup option)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## VEO 3 — GOOGLE AI STUDIO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
gemini_api_key: AIzaSyBrQQgLBYISDZmxmixGx12SQD31H_QoaxI
google_cloud_project: liv8-377321
veo_status: KEY_VALID — billing not yet enabled on project
veo_models_available:
  - veo-3.0-generate-001 (primary)
  - veo-3.1-generate-preview (newest)
  - veo-3.1-fast-generate-preview (fastest)
  - veo-3.1-lite-generate-preview (cheapest)
  - veo-2.0-generate-001 (Vertex AI only)

TO UNLOCK: Enable billing at console.cloud.google.com/billing?project=liv8-377321
Once billing is on, Veo generates automatically on every daily run.

GENERATION SCRIPT: /tmp/veo_sv.py (ready to run)
OUTPUT DIR: /Users/jamaurjohnson/Documents/SV_Content_Engine/broll_library/[Pillar]/

BROLL TONE BY PILLAR:
  MINDSET    → dark interiors, trading desks, eyes, stillness
  DISCIPLINE → precision objects, clean lines, clocks, journals
  STRATEGY   → chess pieces, blueprints, maps, architecture
  REALITY    → raw city, hustle, truth, unfiltered moments

VEO CALL (Python, runs after billing enabled):
  import google.genai as genai, google.genai.types as types
  client = genai.Client(api_key='AIzaSyBrQQgLBYISDZmxmixGx12SQD31H_QoaxI')
  op = client.models.generate_videos(
      model='veo-3.0-generate-001',
      prompt='[prompt]',
      config=types.GenerateVideosConfig(aspect_ratio='9:16', number_of_videos=1)
  )