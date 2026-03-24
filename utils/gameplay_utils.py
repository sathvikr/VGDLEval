import base64
import copy
import io
import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from utils.llm_interface_utils.rich_logging import print_user_panel, print_assistant_panel
from PIL import Image

logger = logging.getLogger(__name__)

SUMMARY_PATTERN = re.compile(r"<summary>(.*?)</summary>", re.IGNORECASE | re.DOTALL)
SKETCHPAD_PATTERN = re.compile(r"<sketchpad>(.*?)</sketchpad>", re.IGNORECASE | re.DOTALL)


def append_history_entry(entry: Dict[str, Any], history: List[Dict[str, Any]], full_history: List[Dict[str, Any]]) -> None:
    """Append an entry to both the active history and the archival history."""
    history.append(entry)
    full_history.append(copy.deepcopy(entry))


def extract_summary_text(text: str) -> Optional[str]:
    """Return the <summary>...</summary> block from the supplied text, if present."""
    if not text:
        return None
    match = SUMMARY_PATTERN.search(text)
    if match:
        return match.group(1).strip()
    return None


def extract_reasoning_text(text: str) -> Optional[str]:
    """Extract the reasoning text before the <keys> tag."""
    if not text:
        return None
    keys_match = re.search(r'<keys>', text, re.IGNORECASE)
    if keys_match:
        reasoning = text[:keys_match.start()].strip()
        # Remove any <summary> or <sketchpad> blocks from the reasoning
        reasoning = re.sub(r'<summary>.*?</summary>', '', reasoning, flags=re.IGNORECASE | re.DOTALL)
        reasoning = re.sub(r'<sketchpad>.*?</sketchpad>', '', reasoning, flags=re.IGNORECASE | re.DOTALL)
        return reasoning.strip() if reasoning else None
    return None


def request_conversation_summary(
    interface,
    conversation_history: List[Dict[str, Any]],
    full_conversation_history: List[Dict[str, Any]],
    summary_prompt_text: str,
    visual_sections: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Ask the LLM to summarize the entire gameplay conversation so far.
    Resets the working conversation history to the summary context.
    """
    logger.info("Requesting conversation-only summary after episode end...")
    summary_content: List[Dict[str, Any]] = list(visual_sections or [])
    summary_content.append({"type": "text", "text": summary_prompt_text})
    summary_message = {
        "role": "user",
        "content": summary_content,
    }
    print_user_panel(summary_message["content"], title="User → Model (Summary Request)")
    append_history_entry(summary_message, conversation_history, full_conversation_history)

    response = interface.generate(messages=conversation_history)
    assistant_entry = {
        "role": "assistant",
        "content": response["output"],
    }
    print_assistant_panel(response["output"], title="Model → Assistant (Summary Response)")
    append_history_entry(assistant_entry, conversation_history, full_conversation_history)

    summary_text = extract_summary_text(response["output"]) or response["output"].strip()
    summary_entry = {
        "role": "system",
        "content": summary_text,
    }
    full_conversation_history.append(copy.deepcopy(summary_entry))

    conversation_history.clear()
    conversation_history.extend([summary_entry, assistant_entry])
    return summary_text


def save_screenshot(results_dir: str, episode_count: int, step_count: int, screenshot_bytes: bytes, suffix: Optional[str] = None) -> str:
    """Persist a screenshot PNG and return its path."""
    try:
        suffix_part = f"_{suffix}" if suffix else ""
        filename = f"episode_{episode_count}_step_{step_count}{suffix_part}.png"
        filepath = os.path.join(results_dir, "screenshots", filename)
        with open(filepath, "wb") as file:
            file.write(screenshot_bytes)
        return filepath
    except Exception as exc:
        logger.error(f"Error saving screenshot: {exc}")
        return ""


def save_action_frame(gameplay_dir: str, frame_idx: int, screenshot_bytes: bytes) -> str:
    """Persist a post-action gameplay frame PNG and return its path."""
    try:
        filename = f"frame_step_{frame_idx:05d}.png"
        filepath = os.path.join(gameplay_dir, filename)
        with open(filepath, "wb") as file:
            file.write(screenshot_bytes)
        return filepath
    except Exception as exc:
        logger.error(f"Error saving action frame: {exc}")
        return ""


def build_frame_reference(path: Optional[str], image_bytes: Optional[bytes], mime_type: str = "image/png") -> Optional[Dict[str, Optional[str]]]:
    """Create a serializable descriptor containing the image path and base64 payload."""
    if not path and not image_bytes:
        return None
    base64_data = base64.b64encode(
        _prepare_image_for_base64(image_bytes, mime_type)
    ).decode("utf-8") if image_bytes else None
    return {
        "path": path,
        "base64": base64_data,
        "mime_type": mime_type,
    }


def _prepare_image_for_base64(image_bytes: bytes, mime_type: str) -> bytes:
    """Downscale the image so the smaller dimension is at most 256px before encoding."""
    if not image_bytes:
        return image_bytes
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            width, height = img.size
            min_dim = min(width, height)
            if min_dim <= 256:
                return image_bytes
            scale = 256 / float(min_dim)
            new_size = (max(1, int(round(width * scale))), max(1, int(round(height * scale))))
            resized = img.resize(new_size, Image.LANCZOS)
            buffer = io.BytesIO()
            format_name = "JPEG" if mime_type.lower() in ("image/jpeg", "image/jpg") else "PNG"
            resized.save(buffer, format=format_name)
            return buffer.getvalue()
    except Exception as exc:
        logger.warning(f"Failed to resize image for base64 encoding: {exc}")
        return image_bytes


def get_current_score(driver) -> str:
    """Return the current score displayed by the game UI."""
    try:
        score = driver.execute_script(
            """
            return (document.getElementById('score-value')?.textContent) ??
                   (window.game?.score?.toString()) ?? null;
            """
        )
        if isinstance(score, str):
            return score.strip()
        if score is not None:
            return str(score)
        return "unknown"
    except Exception:
        return "unknown"


def save_results(results_dir: str, conversation_history: List[Dict[str, Any]], gameplay_log: List[Dict[str, Any]]) -> None:
    """Write conversation and gameplay logs to disk."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    conversation_path = os.path.join(results_dir, f"conversation_{timestamp}.json")
    with open(conversation_path, "w") as convo_file:
        serializable_history = json.loads(json.dumps(conversation_history, default=str))
        json.dump(serializable_history, convo_file, indent=2)

    gameplay_path = os.path.join(results_dir, f"gameplay_log_{timestamp}.json")
    with open(gameplay_path, "w") as log_file:
        json.dump(gameplay_log, log_file, indent=2)

    logger.info(f"Results saved to {results_dir}")


def record_gameplay_step(
    gameplay_dir: str,
    episode: int,
    step: int,
    actions: List[Optional[int]],
    action_scores: List[str],
    llm_output: str,
    screenshot: str,
    action_snapshots: List[Dict[str, Any]],
    game_ended: bool = False,
    episode_won: bool = False,
) -> None:
    """Persist a single gameplay step to disk for detailed auditing."""
    step_payload = {
        "episode": episode,
        "step": step,
        "timestamp": datetime.now().isoformat(),
        "actions": actions,
        "action_scores": action_scores,
        "llm_output": llm_output,
        "screenshot": screenshot,
        "action_snapshots": action_snapshots,
        "game_ended": game_ended,
        "episode_won": episode_won,
    }
    step_path = os.path.join(gameplay_dir, f"episode_{episode}_step_{step}.json")
    with open(step_path, "w") as step_file:
        json.dump(step_payload, step_file, indent=2)


