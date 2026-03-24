import argparse
import glob
import json
import math
import os
from datetime import datetime

import matplotlib.pyplot as plt
from PIL import Image


def load_step_data(results_dir: str):
    """Load all step JSON files sorted by (episode, step)."""
    gameplay_dir = os.path.join(results_dir, "gameplay")
    step_files = glob.glob(os.path.join(gameplay_dir, "episode_*_step_*.json"))

    def sort_key(path):
        name = os.path.splitext(os.path.basename(path))[0]
        parts = name.split("_")
        return int(parts[1]), int(parts[3])

    step_files.sort(key=sort_key)

    steps = []
    for f in step_files:
        with open(f) as fh:
            steps.append(json.load(fh))
    return steps


def build_levels_won_series(steps):
    """Build x=action index, y=levels_won + normalized_score series."""
    action_indices = []
    y_values = []
    levels_won = 0
    idx = 0

    for step in steps:
        scores = step.get("action_scores", [])
        game_ended = step.get("game_ended", False)
        episode_won = step.get("episode_won", False)

        # Find min/max score within this episode for normalization
        numeric_scores = []
        for s in scores:
            try:
                numeric_scores.append(float(s))
            except (ValueError, TypeError):
                numeric_scores.append(0.0)

        for i, score_val in enumerate(numeric_scores):
            action_indices.append(idx)
            # y = levels_won + fractional progress within level
            # For the continuous part, normalize the score to [0, 1) within the level
            y_values.append(levels_won + _normalize_score(score_val, numeric_scores))
            idx += 1

        if game_ended and episode_won:
            levels_won += 1

    return action_indices, y_values, levels_won


def _normalize_score(current, all_scores):
    """Normalize score to [0, 0.9] range within a level's score range."""
    if not all_scores:
        return 0.0
    min_s = min(all_scores)
    max_s = max(all_scores)
    if max_s == min_s:
        return 0.0
    return 0.9 * (current - min_s) / (max_s - min_s)


def build_raw_score_series(steps):
    """Fallback: build x=action index, y=raw score (for old data without game_ended)."""
    action_indices = []
    scores = []
    idx = 0
    for step in steps:
        for s in step.get("action_scores", []):
            action_indices.append(idx)
            try:
                scores.append(float(s))
            except (ValueError, TypeError):
                scores.append(0.0)
            idx += 1
    return action_indices, scores


def get_session_date(results_dir: str) -> str:
    dirname = os.path.basename(results_dir.rstrip("/"))
    try:
        dt = datetime.strptime(dirname, "%Y%m%d_%H%M%S")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return datetime.now().strftime("%Y-%m-%d")


def has_level_data(steps):
    """Check if step data contains game_ended/episode_won fields."""
    for step in steps:
        if "game_ended" in step:
            return True
    return False


def get_total_levels(results_dir: str, default: int = 5) -> int:
    """Detect total levels from metadata.json + games directory."""
    metadata_path = os.path.join(results_dir, "metadata.json")
    if not os.path.exists(metadata_path):
        return default
    try:
        with open(metadata_path) as f:
            metadata = json.load(f)
        game_name = metadata.get("game_name", "")
        if not game_name:
            return default
        # Look for the games directory relative to results
        # results_dir is like results/20260312_022310, so games is ../../games
        base_dir = os.path.dirname(os.path.dirname(results_dir))
        games_dir = os.path.join(base_dir, "games", game_name)
        if not os.path.isdir(games_dir):
            return default
        level_files = glob.glob(os.path.join(games_dir, "*.html"))
        return len(level_files) if level_files else default
    except Exception:
        return default


def create_gameplay_gif(results_dir: str, fps: int = 10):
    gameplay_dir = os.path.join(results_dir, "gameplay")
    frame_files = sorted(glob.glob(os.path.join(gameplay_dir, "frame_step_*.png")))
    if not frame_files:
        print(f"No frames found in {gameplay_dir}")
        return None
    frames = [Image.open(f) for f in frame_files]
    out_path = os.path.join(results_dir, "gameplay.gif")
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=1000 // fps,
        loop=0,
    )
    print(f"GIF saved to {out_path} ({len(frames)} frames)")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Plot score over actions from gameplay results.")
    parser.add_argument("results_dir", help="Path to a results session directory")
    parser.add_argument("--out", default=None, help="Output image path")
    parser.add_argument("--title", default=None, help="Plot title")
    parser.add_argument("--no-gif", action="store_true", help="Skip GIF generation")
    parser.add_argument("--total-levels", type=int, default=None, help="Override total number of levels (auto-detected from game directory)")
    args = parser.parse_args()

    session_date = get_session_date(args.results_dir)
    steps = load_step_data(args.results_dir)
    if not steps:
        print("No step data found.")
        return

    total_levels = args.total_levels or get_total_levels(args.results_dir)

    out_path = args.out or os.path.join(args.results_dir, "score_plot.png")
    base_title = args.title or "Score Over Time"
    title = f"{base_title} ({session_date})"

    plt.figure(figsize=(12, 5))

    if has_level_data(steps):
        action_indices, y_values, total_won = build_levels_won_series(steps)
        if action_indices:
            plt.plot(action_indices, y_values, linewidth=1)
            plt.xlabel("Steps taken by agent")
            plt.ylabel("Levels won")
            plt.ylim(-0.1, total_levels + 0.1)
            plt.yticks(range(0, total_levels + 1))
    else:
        # Fallback for old data without game_ended fields
        action_indices, scores = build_raw_score_series(steps)
        if action_indices:
            plt.plot(action_indices, scores, linewidth=1)
            plt.xlabel("Action Step")
            plt.ylabel("Score")

    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Plot saved to {out_path}")

    if not args.no_gif:
        create_gameplay_gif(args.results_dir)


if __name__ == "__main__":
    main()
