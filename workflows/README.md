# ComfyUI Workflow Templates (free local generation)

The cost router runs free local generation by submitting a **ComfyUI workflow**
to your local ComfyUI server (`COMFYUI_URL`, default `http://localhost:8188`).

Drop one JSON per local model here, named after the model id used in the brand
config's `generation` block:

```
workflows/
  wan2.2.json         # image_to_video local model
  ltx-video.json      # text_to_video local model
  ltx-2.3-audio.json  # music_video local model
```

A per-brand override can live at `<brand.base_dir>/workflows/<model>.json` and
takes priority over the repo copy.

## How to make one

1. Build the graph you want in ComfyUI (Wan / LTX nodes, etc.).
2. **Save (API Format)** — this exports the prompt graph the router POSTs to
   `/prompt`. (Enable *Dev mode* in ComfyUI settings if you don't see it.)
3. Save it here as `<model>.json`.
4. Replace the dynamic inputs with these tokens — the router substitutes them
   at run time (plain string replace, so they work anywhere in the JSON):

   | Token               | Becomes                                  |
   |---------------------|------------------------------------------|
   | `{{PROMPT}}`        | the text prompt (quotes escaped)         |
   | `{{SECONDS}}`       | clip duration                            |
   | `{{IMAGE_PATH}}`    | source still (image_to_video)            |
   | `{{AUDIO_PATH}}`    | song file (music_video)                  |
   | `{{OUTPUT_PREFIX}}` | filename prefix for the SaveVideo node   |
   | `{{SEED}}`          | seed (epoch seconds if unset)            |

   Example — a CLIP text node's input becomes:
   ```json
   "inputs": { "text": "{{PROMPT}}" }
   ```

## Notes

- No template for a model → the router raises a clear error instead of silently
  falling back to a paid API. That's intentional: local-first never costs money
  by accident.
- Test a template without a full run:
  `python3 router.py gen --kind text_to_video --prompt "test" --dry-run`
- This folder is committed; the heavy model checkpoints are **not** — install
  those inside ComfyUI itself.
