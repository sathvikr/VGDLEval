# VGDL LLM Gameplay Runner

## Overview
This repository contains a Selenium-driven harness (`llm_gameplay.py`) that lets multimodal LLMs (OpenAI `gpt-5.1` or Gemini `gemini-3-pro-preview`) play VGDL games served from this project. The script streams game frames, keeps structured conversation history, requests action plans, executes the actions inside the browser canvas, and records everything (screens, logs, and videos) under `results/`.

## Prerequisites
- Python 3.10+ with `selenium`, `openai`, `google-generativeai`, `pillow`, and `rich` installed (e.g. `pip install selenium openai google-generativeai pillow rich`).
- Firefox and `geckodriver` available on your PATH for Selenium.
- `ffmpeg` CLI installed for gameplay video generation.
- API credentials exported as `OPENAI_API_KEY` and/or `GOOGLE_API_KEY`.
- Static server hosting this repo on `localhost:8080` (from repo root: `python -m http.server 8080`).

## Information Flow
1. `llm_gameplay.py` launches Firefox, clicks **Start LLM**, and captures the initial canvas frame.
2. The frame is saved as PNG for auditing, and the raw bytes are always encoded as base64 inline attachments before being sent to the LLM.
3. The first turn uses `prompts/initial_prompt.md`. Subsequent turns use `prompts/followup_prompt.md`, injecting the live score, every per-action score from the previous step, and only the screenshots that resulted from the immediately preceding actions.
4. The LLM responds with reasoning plus `<actions>[...]</actions>`. Parsed key presses are fired into the canvas via Selenium, with a screenshot and score captured after each key press.
5. After `--summary_interval` actions, the next prompt switches to `prompts/followup_summary_prompt.md`, instructing the model to emit `<summary>...</summary>`. That summary replaces all prior turns (for token efficiency) while the full, unsummarized transcript—including every image reference—is archived separately.
6. When the game signals a terminal state, the harness explicitly tells the model that the episode ended, asks for a conversation-only recap via `prompts/conversation_summary_prompt.md` (including the last actions, their per-action scores, and the exact assistant response), stores the returned `<summary>`, and clicks **Retry**. The next gameplay turn sends `prompts/restart_prompt.md`, which mirrors the initial instructions but injects “Summary of the game based on the previous gameplays: …” along with the newly captured initial screenshot so the LLM can immediately start from that recap.
7. Each action frame is saved to `results/<session>/gameplay/frame_step_*.png`, an ffmpeg video is rendered, and JSON logs hold both the raw LLM conversation and structured gameplay telemetry.

Gemini’s inline base64 ingestion path follows the official “Image understanding” guidance, which documents how to pass `inlineData` parts directly in a `generateContent` call (see https://ai.google.dev/gemini-api/docs/image-understanding).

## Running the Gameplay Script
1. Serve the games locally:
   ```bash
   python -m http.server 8080
   ```
2. In another terminal, run the gameplay harness. Example:
   ```bash
   python llm_gameplay.py \
     --model openai \
     --url http://localhost:8080/games/gvgai_aliens/0.html \
     --max_actions 400 \
     --summary_interval 120
   ```

### Key Arguments
- `--model`: `openai` (uses `gpt-5.1`) or `gemini` (uses `gemini-3-pro-preview`).
- `--url`: Full URL of the hosted VGDL game instance (must be reachable from the Selenium browser).
- `--max_actions`: Total key presses allowed across all retries/episodes.
- `--summary_interval`: Summarize conversation after N actions (0 disables).
## Output Artifacts
Each run creates `results/<timestamp>/` containing:
- `screenshots/`: Episode/step PNGs taken before each LLM turn.
- `gameplay/frame_step_*.png`: One image per executed action plus `gameplay.mp4` generated via ffmpeg.
- `gameplay/episode_<n>_step_<m>.json`: Fine-grained per-step logs (actions, post-action scores, relative frame paths).
- `conversation_<timestamp>.json`: Full conversation history, including summaries and the inline base64 blobs that were sent to the LLM.
- `gameplay_log_<timestamp>.json`: Condensed chronological log for quick inspection.

## Troubleshooting Notes
- Ensure Firefox + `geckodriver` versions match; Selenium will crash early if the driver is missing.
- Missing API keys or quota limits manifest as provider-specific exceptions surfaced in the console logs.
- If `ffmpeg` is absent, gameplay still runs, but the MP4 will be skipped (a warning is logged).
- When experimenting with `base64` mode, remember that the repository still writes every PNG for auditing; only the data transmitted to the LLM changes.

