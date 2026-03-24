"""
Generate comparison plots for screenshot vs ASCII ablation study.
Produces:
  1. results/ascii_all_games_plot.png       – 3x3 grid of ASCII-mode results
  2. results/ablation_comparison_plot.png    – side-by-side screenshot vs ASCII
"""

import glob
import json
import os
import sys

import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------------------
# Helpers (reused from plot_scores.py)
# ---------------------------------------------------------------------------

def load_step_data(results_dir: str):
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


def _normalize_score(current, all_scores):
    if not all_scores:
        return 0.0
    min_s = min(all_scores)
    max_s = max(all_scores)
    if max_s == min_s:
        return 0.0
    return 0.9 * (current - min_s) / (max_s - min_s)


def build_levels_won_series(steps):
    action_indices = []
    y_values = []
    levels_won = 0
    idx = 0
    for step in steps:
        scores = step.get("action_scores", [])
        game_ended = step.get("game_ended", False)
        episode_won = step.get("episode_won", False)
        numeric_scores = []
        for s in scores:
            try:
                numeric_scores.append(float(s))
            except (ValueError, TypeError):
                numeric_scores.append(0.0)
        for i, score_val in enumerate(numeric_scores):
            action_indices.append(idx)
            y_values.append(levels_won + _normalize_score(score_val, numeric_scores))
            idx += 1
        if game_ended and episode_won:
            levels_won += 1
    return action_indices, y_values, levels_won


def get_total_levels(results_dir: str, default: int = 5) -> int:
    metadata_path = os.path.join(results_dir, "metadata.json")
    if not os.path.exists(metadata_path):
        return default
    try:
        with open(metadata_path) as f:
            metadata = json.load(f)
        game_name = metadata.get("game_name", "")
        if not game_name:
            return default
        base_dir = os.path.dirname(os.path.dirname(results_dir))
        games_dir = os.path.join(base_dir, "games", game_name)
        if not os.path.isdir(games_dir):
            return default
        level_files = glob.glob(os.path.join(games_dir, "*.html"))
        return len(level_files) if level_files else default
    except Exception:
        return default


# ---------------------------------------------------------------------------
# Game → session directory mappings
# ---------------------------------------------------------------------------

# Baseline screenshot sessions (best run per game from the original data)
SCREENSHOT_SESSIONS = {
    "gvgai_zelda":        "../results/20260312_125209",
    "gvgai_aliens":       "../results/20260312_025404",
    "gvgai_butterflies":  "../results/20260312_125946",
    "gvgai_chase":        "../results/20260312_030613",
    "gvgai_boulderdash":  "../results/20260312_031233",
    "gvgai_bait":         "../results/20260312_124529",
    "gvgai_frogs":        "../results/20260312_130605",
    "gvgai_surprise":     "../results/20260312_022310",
    "gvgai_plaqueattack": "../results/20260312_132120",
}

ASCII_SESSIONS = {
    "gvgai_zelda":        "../results/20260324_163850",
    "gvgai_aliens":       "../results/20260324_164448",
    "gvgai_butterflies":  "../results/20260324_164929",
    "gvgai_chase":        "../results/20260324_165433",
    "gvgai_boulderdash":  "../results/20260324_165934",
    "gvgai_bait":         "../results/20260324_170728",
    "gvgai_frogs":        "../results/20260324_171428",
    "gvgai_surprise":     "../results/20260324_172721",
    "gvgai_plaqueattack": "../results/20260324_172904",
}

GAME_ORDER = [
    "gvgai_zelda", "gvgai_aliens", "gvgai_butterflies",
    "gvgai_chase", "gvgai_boulderdash", "gvgai_bait",
    "gvgai_frogs", "gvgai_surprise", "gvgai_plaqueattack",
]


def plot_single_mode(sessions, title, out_path):
    """Plot a 3x3 grid for one mode (screenshot or ASCII)."""
    fig, axes = plt.subplots(3, 3, figsize=(14, 10))
    fig.suptitle(title, fontsize=16, fontweight="bold")

    for i, game in enumerate(GAME_ORDER):
        ax = axes[i // 3][i % 3]
        results_dir = sessions[game]
        steps = load_step_data(results_dir)
        total_levels = get_total_levels(results_dir)

        if steps:
            xi, yi, _ = build_levels_won_series(steps)
            if xi:
                ax.plot(xi, yi, linewidth=1)

        ax.set_title(game.replace("gvgai_", ""), fontsize=11)
        ax.set_xlabel("Steps", fontsize=9)
        ax.set_ylabel("Levels won", fontsize=9)
        ax.set_ylim(-0.1, total_levels + 0.1)
        ax.set_yticks(range(0, total_levels + 1))

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Saved {out_path}")


def plot_comparison(screenshot_sessions, ascii_sessions, out_path):
    """Plot a 3x3 grid with both modes overlaid per game."""
    fig, axes = plt.subplots(3, 3, figsize=(14, 10))
    fig.suptitle(
        "Screenshot vs ASCII Grid  (gpt-5.2, 400 actions)",
        fontsize=16, fontweight="bold",
    )

    for i, game in enumerate(GAME_ORDER):
        ax = axes[i // 3][i % 3]
        total_levels = 5

        # Screenshot
        ss_dir = screenshot_sessions[game]
        ss_steps = load_step_data(ss_dir)
        total_levels = get_total_levels(ss_dir)
        if ss_steps:
            xi, yi, _ = build_levels_won_series(ss_steps)
            if xi:
                ax.plot(xi, yi, linewidth=1, color="tab:blue", alpha=0.8, label="Screenshot")

        # ASCII
        asc_dir = ascii_sessions[game]
        asc_steps = load_step_data(asc_dir)
        if asc_steps:
            xi, yi, _ = build_levels_won_series(asc_steps)
            if xi:
                ax.plot(xi, yi, linewidth=1, color="tab:orange", alpha=0.8, label="ASCII")

        ax.set_title(game.replace("gvgai_", ""), fontsize=11)
        ax.set_xlabel("Steps", fontsize=9)
        ax.set_ylabel("Levels won", fontsize=9)
        ax.set_ylim(-0.1, total_levels + 0.1)
        ax.set_yticks(range(0, total_levels + 1))
        if i == 0:
            ax.legend(fontsize=8, loc="upper left")

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Saved {out_path}")


def main():
    # ASCII-only 3x3
    plot_single_mode(
        ASCII_SESSIONS,
        "Game steps vs. score (gpt-5.2, ASCII) (2026-03-24)",
        "../results/ascii_all_games_plot.png",
    )

    # Comparison overlay
    plot_comparison(
        SCREENSHOT_SESSIONS,
        ASCII_SESSIONS,
        "../results/ablation_comparison_plot.png",
    )


if __name__ == "__main__":
    main()
