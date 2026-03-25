import argparse
import json
import time
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from dotenv import load_dotenv
# Load .env file from the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, '.env'))
from selenium import webdriver
from selenium.webdriver.common.by import By

from llm_interface.api import OpenAIInterface, GoogleInterface
from utils.game_utils import (
    execute_action,
    get_game_screenshot,
    get_game_state_matrix,
    is_game_ended,
    is_game_won,
    click_start_llm,
    click_retry,
    click_next_instance,
)
from utils.parsing_utils import parse_actions, KEY_MAPPING
from utils.gameplay_utils import (
    append_history_entry,
    extract_summary_text,
    extract_reasoning_text,
    request_conversation_summary,
    save_screenshot,
    save_action_frame,
    build_frame_reference,
    get_current_score,
    save_results,
    record_gameplay_step,
)
from utils.llm_interface_utils.rich_logging import print_user_panel, print_assistant_panel

REVERSE_KEY_MAPPING = {value: key for key, value in KEY_MAPPING.items()}
REVERSE_KEY_MAPPING[None] = "NOOP"


def actions_to_names(actions: List[Optional[int]]) -> str:
    """Convert key codes to human-readable names for logging/prompts."""
    if not actions:
        return "None"
    names = []
    for action in actions:
        names.append(REVERSE_KEY_MAPPING.get(action, str(action)))
    return ", ".join(names)


def format_frame_description(entry: Dict[str, Any], include_excerpt: bool = True) -> str:
    """Produce a compact textual tag for a stored frame."""
    episode = entry.get("episode")
    step = entry.get("step")
    action_index = entry.get("action_index")
    action_name = entry.get("action_name", "UNKNOWN")
    score = entry.get("score", "N/A")
    base = f"Episode {episode}, Step {step}, Action #{action_index} ({action_name}) | Score: {score}"
    if not include_excerpt:
        return base
    assistant_excerpt = entry.get("assistant_excerpt", "")
    assistant_excerpt = assistant_excerpt.replace("\n", " ").strip()
    if len(assistant_excerpt) > 160:
        assistant_excerpt = assistant_excerpt[:160] + "..."
    return f"{base} | Assistant response: {assistant_excerpt}"


def append_frame_visual(sections: List[Dict[str, Any]], label: str, frame_ref: Optional[Dict[str, Optional[str]]]) -> None:
    """Attach a labeled image payload to the provided message sections."""
    if not frame_ref:
        return
    base64_data = frame_ref.get("base64")
    if not base64_data:
        return
    mime_type = frame_ref.get("mime_type", "image/png")
    sections.append({"type": "text", "text": label})
    sections.append({
        "type": "image_base64",
        "data": base64_data,
        "mime_type": mime_type
    })


def append_ascii_state(sections: List[Dict[str, Any]], label: str, ascii_grid: Optional[str]) -> None:
    """Attach a labeled ASCII game-state block to the provided message sections."""
    if not ascii_grid:
        return
    sections.append({"type": "text", "text": f"{label}\n```\n{ascii_grid}\n```"})


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    parser = argparse.ArgumentParser(description="LLM Gameplay Script")
    parser.add_argument("--model", type=str, required=True, help="Model to use in format 'provider:model_name' (e.g., 'openai:gpt4' or 'gemini:gemini-2.5-pro')")
    parser.add_argument("--url", type=str, required=True, help="Game URL")
    parser.add_argument("--max_actions", type=int, default=1000, help="Maximum total actions")
    parser.add_argument(
        "--summary_interval",
        type=int,
        default=60,
        help="Summarize and reset prompt history every N steps (0 disables summarization)."
    )
    parser.add_argument(
        "--state_representation",
        type=str,
        default="screenshot",
        choices=["screenshot", "ascii"],
        help="How game state is conveyed to the LLM: 'screenshot' (base64 images) or 'ascii' (2-D text grid)."
    )
    parser.add_argument(
        "--scratchpad",
        action="store_true",
        default=False,
        help="Enable scratchpad: inject the last N reasoning steps into followup prompts."
    )
    parser.add_argument(
        "--max_scratchpad_entries",
        type=int,
        default=10,
        help="Maximum number of reasoning steps to keep in the scratchpad buffer."
    )
    return parser.parse_args()

def parse_model_string(model_string: str) -> Tuple[str, str]:
    """Parse model string in format 'provider:model_name' into provider and model name."""
    if ":" not in model_string:
        raise ValueError(f"Model string must be in format 'provider:model_name', got: {model_string}")
    parts = model_string.split(":", 1)
    provider = parts[0].strip().lower()
    model_name = parts[1].strip()
    if not provider or not model_name:
        raise ValueError(f"Both provider and model name must be specified, got: {model_string}")
    return provider, model_name

def get_interface(model_provider: str, model_name: str):
    if model_provider == "openai":
        return OpenAIInterface(model_name=model_name, enable_thinking=False)
    elif model_provider == "gemini":
        return GoogleInterface(model_name=model_name, enable_thinking=False)
    else:
        raise ValueError(f"Unknown model provider: {model_provider}")

def main():
    args = parse_arguments()
    
    # Parse model string
    model_provider, model_name = parse_model_string(args.model)
    logger.info(f"Using model provider: {model_provider}, model: {model_name}")
    
    # Setup results directory
    results_base = "results"
    os.makedirs(results_base, exist_ok=True)
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = os.path.join(results_base, session_id)
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(os.path.join(results_dir, "screenshots"), exist_ok=True)
    gameplay_dir = os.path.join(results_dir, "gameplay")
    os.makedirs(gameplay_dir, exist_ok=True)

    # Save run metadata
    # Extract game name from URL (e.g. http://localhost:8085/games/gvgai_surprise/0.html -> gvgai_surprise)
    import re as _re
    _url_match = _re.search(r'/games/([^/]+)/', args.url)
    game_name = _url_match.group(1) if _url_match else "unknown"
    use_ascii = args.state_representation == "ascii"
    use_scratchpad = args.scratchpad
    max_scratchpad_entries = args.max_scratchpad_entries
    metadata = {
        "url": args.url,
        "game_name": game_name,
        "model": args.model,
        "max_actions": args.max_actions,
        "summary_interval": args.summary_interval,
        "state_representation": args.state_representation,
        "scratchpad": use_scratchpad,
        "max_scratchpad_entries": max_scratchpad_entries,
        "session_id": session_id,
    }
    with open(os.path.join(results_dir, "metadata.json"), "w") as mf:
        json.dump(metadata, mf, indent=2)

    frame_index = 0
    recent_action_scores: List[str] = []
    frame_history: List[Dict[str, Any]] = []
    actions_since_summary = 0
    pending_summary_text: Optional[str] = None
    next_prompt_mode: Optional[str] = None  # "restart" or "next_level"
    current_summary_text: Optional[str] = None

    # Scratchpad: accumulates reasoning from past steps
    scratchpad_buffer: List[str] = []

    gameplay_log: List[Dict[str, Any]] = []

    # Init Interface
    interface = get_interface(model_provider, model_name)
    
    # Maintain conversation history locally
    conversation_history: List[Dict[str, Any]] = []
    full_conversation_history: List[Dict[str, Any]] = []
    summary_interval = max(0, args.summary_interval)
    
    # Init Selenium
    options = webdriver.FirefoxOptions()
    # options.add_argument("--headless") # Optional: run headless
    driver = webdriver.Firefox(options=options)
    
    try:
        driver.get(args.url)
        logger.info(f"Navigated to {args.url}")
        
        # Load prompts – use ascii/ variants when in ASCII mode
        prompt_dir = "prompts/ascii" if use_ascii else "prompts"
        with open(os.path.join(prompt_dir, "initial_prompt.md"), "r") as f:
            initial_prompt = f.read()
        with open(os.path.join(prompt_dir, "followup_prompt.md"), "r") as f:
            followup_prompt = f.read()
        with open(os.path.join(prompt_dir, "followup_summary_prompt.md"), "r") as f:
            followup_summary_prompt = f.read()
        with open(os.path.join(prompt_dir, "conversation_summary_prompt.md"), "r") as f:
            conversation_summary_prompt = f.read()
        with open(os.path.join(prompt_dir, "win_summary_prompt.md"), "r") as f:
            win_summary_prompt = f.read()
        with open(os.path.join(prompt_dir, "restart_prompt.md"), "r") as f:
            restart_prompt = f.read()
        
        click_start_llm(driver)
        
        total_actions_count = 0
        episode_count = 1
        step_count = 0
        
        while total_actions_count < args.max_actions:
            # Check if page reloaded
            try:
                driver.find_element(By.ID, "gjs-canvas")
            except:
                time.sleep(1)
                continue
            
            # Check for restart
            try:
                start_btn = driver.find_element(By.ID, "start-llm")
                if start_btn.is_displayed():
                    logger.info("Start LLM button found (new episode?), clicking...")
                    start_btn.click()
                    time.sleep(1)
                    # Add restart marker to history if needed, or just rely on context
                    append_history_entry(
                        {"role": "system", "content": "Game restarted."},
                        conversation_history,
                        full_conversation_history,
                    )
                    step_count = 0
            except:
                pass
            
            # Capture state
            screenshot_bytes = None
            screenshot_path = ""
            screenshot_frame = None
            current_ascii_state = None
            if use_ascii:
                current_ascii_state = get_game_state_matrix(driver)
            else:
                screenshot_bytes = get_game_screenshot(driver)
                if screenshot_bytes:
                    screenshot_path = save_screenshot(results_dir, episode_count, step_count, screenshot_bytes)
                    screenshot_frame = build_frame_reference(screenshot_path, screenshot_bytes)
            log_screenshot = os.path.relpath(screenshot_path, results_dir) if screenshot_path else ""
            
            # Prepare message content
            used_summary_prompt = False
            current_content = []
            prefix_sections: List[str] = []
            force_initial_frame_only = False
            use_restart_prompt = False
            use_next_level_prompt = False
            restart_summary_text: Optional[str] = None
            next_level_summary_text: Optional[str] = None
            if next_prompt_mode == "restart" and pending_summary_text:
                use_restart_prompt = True
                force_initial_frame_only = True
                restart_summary_text = pending_summary_text
                next_prompt_mode = None
                pending_summary_text = None
            elif next_prompt_mode == "next_level" and pending_summary_text:
                use_next_level_prompt = True
                force_initial_frame_only = True
                next_level_summary_text = pending_summary_text
                next_prompt_mode = None
                pending_summary_text = None
            elif current_summary_text:
                prefix_sections.append(f"Summary of the game so far: {current_summary_text}")

            if use_restart_prompt and restart_summary_text:
                prompt_text = restart_prompt.format(summary=restart_summary_text)
            elif use_next_level_prompt and next_level_summary_text:
                prompt_text = (
                    f"Summary from the previous level of this game: {next_level_summary_text}\n\n"
                    f"{initial_prompt}"
                )
            elif len(conversation_history) == 0:
                prompt_text = initial_prompt
            else:
                score_value = get_current_score(driver)
                previous_scores = ", ".join(recent_action_scores) if recent_action_scores else "N/A"
                should_use_summary = summary_interval > 0 and actions_since_summary >= summary_interval
                used_summary_prompt = should_use_summary
                prompt_template = followup_summary_prompt if should_use_summary else followup_prompt

                # Build scratchpad section
                scratchpad_section = ""
                if use_scratchpad and scratchpad_buffer:
                    scratchpad_entries = "\n\n".join([
                        f"Step {i+1} Reasoning:\n{reasoning}"
                        for i, reasoning in enumerate(scratchpad_buffer)
                    ])
                    scratchpad_section = f"**Previous Reasoning Steps (for reference):**\n{scratchpad_entries}"

                prompt_text = prompt_template.format(
                    score=score_value,
                    scores=previous_scores,
                    scratchpad=scratchpad_section,
                )
                if prefix_sections:
                    prefix_block = "\n".join(prefix_sections)
                    prompt_text = f"{prefix_block}\n\n{prompt_text}"

            visual_sections: List[Dict[str, Any]] = []

            if use_ascii:
                # --- ASCII mode: attach text grids instead of images ---
                if force_initial_frame_only:
                    if current_ascii_state:
                        append_ascii_state(
                            visual_sections,
                            "Initial state after Retry (fresh episode).",
                            current_ascii_state,
                        )
                else:
                    if frame_history:
                        for frame_entry in frame_history:
                            label = format_frame_description(frame_entry, include_excerpt=not use_scratchpad)
                            append_ascii_state(visual_sections, label, frame_entry.get("ascii"))
                    if current_ascii_state:
                        append_ascii_state(
                            visual_sections,
                            "Current observed state before executing the next sequence of actions.",
                            current_ascii_state,
                        )
            else:
                # --- Screenshot mode (original) ---
                if force_initial_frame_only:
                    if screenshot_frame:
                        append_frame_visual(
                            visual_sections,
                            "Initial state after Retry (fresh episode).",
                            screenshot_frame
                        )
                else:
                    if frame_history:
                        for frame_entry in frame_history:
                            label = format_frame_description(frame_entry, include_excerpt=not use_scratchpad)
                            append_frame_visual(visual_sections, label, frame_entry["frame"])
                    if screenshot_frame:
                        append_frame_visual(
                            visual_sections,
                            "Current observed state before executing the next sequence of actions.",
                            screenshot_frame
                        )

            current_content = visual_sections + [{"type": "text", "text": prompt_text}]
            recent_action_scores = []
            
            print_user_panel(current_content)
            user_entry = {"role": "user", "content": current_content}
            append_history_entry(user_entry, conversation_history, full_conversation_history)
            
            logger.info("Requesting LLM response...")
            response = interface.generate(messages=conversation_history)
            
            # Log response
            assistant_output_text = response['output']
            logger.info(f"LLM Response: {assistant_output_text}")
            print_assistant_panel(assistant_output_text)
            
            # Check if model output contains RETRY
            if "RETRY" in assistant_output_text.upper():
                logger.info("Model output contains RETRY, clicking retry button...")
                click_retry(driver)
                episode_count += 1
                step_count += 1
                time.sleep(2)  # Wait for reload
                # Add restart marker to history
                append_history_entry(
                    {"role": "system", "content": "Game restarted (RETRY command)."},
                    conversation_history,
                    full_conversation_history,
                )
                scratchpad_buffer.clear()
                continue
            
            # Parse actions
            actions = parse_actions(assistant_output_text)

            # Extract reasoning and add to scratchpad
            if use_scratchpad:
                reasoning = extract_reasoning_text(assistant_output_text)
                if reasoning:
                    scratchpad_buffer.append(reasoning)
                    if len(scratchpad_buffer) > max_scratchpad_entries:
                        scratchpad_buffer.pop(0)

            # Add assistant response to history
            assistant_entry = {
                "role": "assistant",
                "content": response['output']
            }
            append_history_entry(assistant_entry, conversation_history, full_conversation_history)
            
            if used_summary_prompt:
                summary_text = extract_summary_text(assistant_output_text) or "Summary unavailable."
                summary_entry = {"role": "system", "content": summary_text}
                full_conversation_history.append(dict(summary_entry))
                conversation_history = [summary_entry, assistant_entry]
                actions_since_summary = 0
                current_summary_text = summary_text
                frame_history.clear()
                scratchpad_buffer.clear()
            
            action_snapshots: List[Dict[str, Any]] = []
            executed_actions: List[Optional[int]] = []
            new_action_scores: List[str] = []
            game_ended_this_step = False
            episode_end_score: Optional[str] = None
            episode_won_this_step = False
            step_episode = episode_count
            step_step = step_count

            # Execute actions
            for idx, action in enumerate(actions):
                if total_actions_count >= args.max_actions:
                    break

                execute_action(driver, action)
                executed_actions.append(action)
                total_actions_count += 1

                # Small delay between actions
                time.sleep(0.1)

                # Capture state and score after action
                action_shot_path = ""
                frame_entry = None
                post_ascii_state = None
                if use_ascii:
                    post_ascii_state = get_game_state_matrix(driver)
                else:
                    post_action_bytes = get_game_screenshot(driver)
                    if post_action_bytes:
                        action_shot_path = save_action_frame(gameplay_dir, frame_index, post_action_bytes)
                        frame_index += 1
                        frame_entry = build_frame_reference(action_shot_path, post_action_bytes)
                action_score = get_current_score(driver)
                if use_ascii and post_ascii_state:
                    frame_history.append({
                        "ascii": post_ascii_state,
                        "episode": episode_count,
                        "step": step_count,
                        "action_index": idx,
                        "action_name": REVERSE_KEY_MAPPING.get(action, str(action)),
                        "score": action_score,
                        "assistant_excerpt": assistant_output_text,
                    })
                elif frame_entry:
                    frame_history.append({
                        "frame": frame_entry,
                        "episode": episode_count,
                        "step": step_count,
                        "action_index": idx,
                        "action_name": REVERSE_KEY_MAPPING.get(action, str(action)),
                        "score": action_score,
                        "assistant_excerpt": assistant_output_text,
                    })
                new_action_scores.append(action_score)
                action_snapshots.append({
                    "index": idx,
                    "action_code": action,
                    "screenshot": os.path.relpath(action_shot_path, results_dir) if action_shot_path else "",
                    "score": action_score,
                })

                # Check game end
                if is_game_ended(driver):
                    logger.info(f"Episode {episode_count} ended.")
                    game_ended_this_step = True
                    episode_end_score = action_score
                    episode_won_this_step = is_game_won(driver)
                    gameplay_log.append({
                        "episode": episode_count,
                        "step": step_count,
                        "end_reason": "game_over",
                        "timestamp": datetime.now().isoformat(),
                        "screenshot": log_screenshot
                    })

                    if episode_won_this_step:
                        logger.info("Episode won. Preparing to advance to the next instance after summarization.")
                    else:
                        click_retry(driver)
                        time.sleep(2)  # Wait for reload before next attempt
                    episode_count += 1
                    step_count = 0

                    break

            recent_action_scores = new_action_scores
            actions_since_summary += len(executed_actions)

            log_entry = {
                "episode": step_episode,
                "step": step_step,
                "step_timestamp": datetime.now().isoformat(),
                "actions_executed": executed_actions,
                "action_scores": new_action_scores,
                "llm_output": response['output'],
                "screenshot": log_screenshot,
                "action_snapshots": action_snapshots,
                "game_ended": game_ended_this_step,
                "episode_won": episode_won_this_step,
            }
            gameplay_log.append(log_entry)
            record_gameplay_step(
                gameplay_dir=gameplay_dir,
                episode=step_episode,
                step=step_step,
                actions=executed_actions,
                action_scores=new_action_scores,
                llm_output=response['output'],
                screenshot=log_screenshot,
                action_snapshots=action_snapshots,
                game_ended=game_ended_this_step,
                episode_won=episode_won_this_step,
            )
            
            if game_ended_this_step:
                final_score_for_summary = episode_end_score or get_current_score(driver)
                action_names_for_summary = actions_to_names(executed_actions)
                score_series_for_summary = ", ".join(new_action_scores) if new_action_scores else "N/A"
                result_status = "WON" if episode_won_this_step else "LOST"
                summary_template = win_summary_prompt if episode_won_this_step else conversation_summary_prompt
                summary_prompt_text = summary_template.format(
                    result_status=result_status,
                    score=final_score_for_summary,
                    actions=action_names_for_summary,
                    scores=score_series_for_summary,
                    assistant_response=assistant_output_text,
                )
                summary_visual_sections: List[Dict[str, Any]] = []
                if frame_history:
                    for frame_entry in frame_history:
                        label = format_frame_description(frame_entry)
                        if use_ascii:
                            append_ascii_state(summary_visual_sections, label, frame_entry.get("ascii"))
                        else:
                            append_frame_visual(summary_visual_sections, label, frame_entry["frame"])
                summary_text = request_conversation_summary(
                    interface=interface,
                    conversation_history=conversation_history,
                    full_conversation_history=full_conversation_history,
                    summary_prompt_text=summary_prompt_text,
                    visual_sections=summary_visual_sections
                )
                pending_summary_text = summary_text
                next_prompt_mode = "next_level" if episode_won_this_step else "restart"
                current_summary_text = summary_text
                recent_action_scores = []
                actions_since_summary = 0
                frame_history.clear()
                scratchpad_buffer.clear()
                if episode_won_this_step:
                    if not click_next_instance(driver):
                        logger.warning("Failed to advance to the next instance after a win. Staying on current page.")
                    else:
                        time.sleep(2)
                continue
            
            step_count += 1
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        save_results(results_dir, full_conversation_history, gameplay_log)
        driver.quit()
        logger.info("Gameplay finished")

if __name__ == "__main__":
    main()
