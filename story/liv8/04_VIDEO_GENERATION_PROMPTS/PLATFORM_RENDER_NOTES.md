# Platform Render Notes

## Higgsfield-style workflow
- Train/lock one canonical recurring character first.
- Render shots individually, not as a single 60-second generation.
- Use cinematic camera controls only when motivated by story.
- Favor 4–6 second source clips and trim in edit.

## Seedance/Veo/other multimodal workflow
- Feed canonical portrait + selected style reference for each shot.
- Repeat identity constraints in every generation.
- Generate clean plates without title text; add typography in edit.
- For transformations (conversation -> system), split into multiple shots if a single
  generation produces unstable geometry.

## Master specs
- 3840x2160 preferred
- 24 fps
- 16:9
- 1/48-ish motion-blur feeling
- clean plate with no baked captions
- 5–10% extra handle frames when possible

## Social
Generate center-safe compositions so the master can be reframed to 1080x1920.
