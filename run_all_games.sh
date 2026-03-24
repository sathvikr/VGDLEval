#!/bin/bash
set -e

BASE_URL="http://localhost:8085"
MODEL="openai:gpt-5.2"
MAX_ACTIONS=400
SUMMARY_INTERVAL=60
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

GAMES=(
    gvgai_aliens
    gvgai_avoidgeorge
    gvgai_bait
    gvgai_bees_and_birds
    gvgai_boulderdash
    gvgai_butterflies
    gvgai_chase
    gvgai_closing_gates
    gvgai_corridor
    gvgai_frogs
    gvgai_jaws
    gvgai_lemmings
    gvgai_missilecommand
    gvgai_myAliens
    gvgai_plaqueattack
    gvgai_portals
    gvgai_sokoban
    gvgai_surprise
    gvgai_survivezombies
    gvgai_watergame
    gvgai_zelda
    expt_antagonist
    expt_ee
    expt_helper
    expt_preconditions
    expt_push_boulders
    expt_relational
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

    # Find the most recent results directory (just created)
    RESULTS_DIR=$(ls -td results/*/  | head -1)

    echo "Generating plot for $GAME -> $RESULTS_DIR"
    python plot_scores.py "$RESULTS_DIR" \
        --title "$GAME (gpt-5.2)" \
        --out "${RESULTS_DIR}score_plot.png"

    # Save a mapping so we know which results dir is which game
    echo "$GAME -> $RESULTS_DIR" >> results/game_results_map.txt

    echo "Done: $GAME"
    echo ""
done

echo "All games complete. See results/game_results_map.txt for mapping."
