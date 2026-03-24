#!/bin/bash
set -e

BASE_URL="http://localhost:8085"
MODEL="openai:gpt-5.2"
SUMMARY_INTERVAL=60
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Same 9 games shown in all_games_plot.png
GAMES=(
    gvgai_zelda
    gvgai_aliens
    gvgai_butterflies
    gvgai_chase
    gvgai_boulderdash
    gvgai_bait
    gvgai_frogs
    gvgai_surprise
    gvgai_plaqueattack
)

cd "$SCRIPT_DIR"

> results/ascii_ablation_dirs.txt

for GAME in "${GAMES[@]}"; do
    # Match baseline: surprise=100, everything else=400
    MA=400
    if [ "$GAME" = "gvgai_surprise" ]; then
        MA=100
    fi
    echo "=========================================="
    echo "Running (ASCII): $GAME  max_actions=$MA"
    echo "=========================================="
    URL="${BASE_URL}/games/${GAME}/0.html"

    python3 llm_gameplay.py \
        --model "$MODEL" \
        --url "$URL" \
        --max_actions "$MA" \
        --summary_interval "$SUMMARY_INTERVAL" \
        --state_representation ascii \
    2>&1 | tee "results/last_ascii_${GAME}.log"

    RESULTS_DIR=$(ls -td results/*/ | head -1)

    echo "Generating plot for $GAME -> $RESULTS_DIR"
    python3 plot_scores.py "$RESULTS_DIR" \
        --title "$GAME (gpt-5.2, ASCII)" \
        --no-gif

    echo "$GAME -> $RESULTS_DIR" >> results/ascii_game_results_map.txt
    echo "$RESULTS_DIR" >> results/ascii_ablation_dirs.txt

    echo "Done: $GAME"
    echo ""
done

echo "All 9 ASCII ablation games complete."
