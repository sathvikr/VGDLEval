import math
import os
from datetime import datetime

import matplotlib.pyplot as plt

from plot_scores import load_step_data, has_level_data, build_levels_won_series, build_raw_score_series, get_total_levels


def main():
    map_file = os.path.join("../results", "game_results_map.txt")
    games = []
    with open(map_file) as f:
        for line in f:
            line = line.strip()
            if " -> " not in line:
                continue
            game_name, results_dir = line.split(" -> ", 1)
            results_dir = results_dir.strip().rstrip("/")
            games.append((game_name.strip(), results_dir))

    n = len(games)
    cols = 4
    rows = math.ceil(n / cols)

    today = datetime.now().strftime("%Y-%m-%d")
    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 3.5 * rows))
    fig.suptitle(f"Game steps vs. score (gpt-5.2) ({today})", fontsize=18, fontweight="bold", y=0.98)

    axes_flat = axes.flatten()

    for i, (game_name, results_dir) in enumerate(games):
        ax = axes_flat[i]
        steps = load_step_data(results_dir)

        if steps and has_level_data(steps):
            total_levels = get_total_levels(results_dir)
            action_indices, y_values, total_won = build_levels_won_series(steps)
            if action_indices:
                ax.plot(action_indices, y_values, linewidth=1)
            ax.set_ylim(-0.1, total_levels + 0.1)
            ax.set_yticks(range(0, total_levels + 1))
            ax.set_ylabel("Levels won", fontsize=8)
        else:
            action_indices, scores = build_raw_score_series(steps)
            if action_indices:
                ax.plot(action_indices, scores, linewidth=1)
            ax.set_ylabel("Score", fontsize=8)

        ax.set_title(game_name, fontsize=10)
        ax.set_xlabel("Steps", fontsize=8)
        ax.tick_params(labelsize=7)

    for j in range(n, len(axes_flat)):
        axes_flat[j].set_visible(False)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    out_path = os.path.join("../results", "all_games_plot.png")
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Plot saved to {out_path}")


if __name__ == "__main__":
    main()
