#!/bin/bash
set -e

BASE_URL="http://localhost:8085"
MODEL="openai:gpt-5.2"
MAX_ACTIONS=400
SUMMARY_INTERVAL=60
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

GAMES=(
    gvgai_zelda
    gvgai_aliens
    gvgai_butterflies
    gvgai_chase
    gvgai_boulderdash
    gvgai_bait
    gvgai_frogs
)

cd "$SCRIPT_DIR"

for GAME in "${GAMES[@]}"; do
    echo "=========================================="
    echo "Running: $GAME"
    echo "=========================================="
    URL="${BASE_URL}/games/${GAME}/0.html"

    python llm_gameplay.py \
        --model "$MODEL" \
        --url "$URL" \
        --max_actions "$MAX_ACTIONS" \
        --summary_interval "$SUMMARY_INTERVAL" \
    2>&1 | tee "results/last_${GAME}.log"

    RESULTS_DIR=$(ls -td results/*/ | head -1)

    echo "Generating plot for $GAME -> $RESULTS_DIR"
    python plot_scores.py "$RESULTS_DIR" \
        --title "$GAME (gpt-5.2)" \
        --out "${RESULTS_DIR}score_plot.png" \
        --no-gif

    echo "$GAME -> $RESULTS_DIR" >> results/game_results_map.txt

    echo "Done: $GAME"
    echo ""
done

echo "All 7 games complete."
