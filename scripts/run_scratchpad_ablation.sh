#!/bin/bash
# Ablation study: ASCII (baseline) vs ASCII + Scratchpad
# Same 9 games as the screenshot-vs-ascii ablation, same model and max_actions.

set -e
cd "$(dirname "$0")"/.."

MODEL="openai:gpt-5.2"
BASE_URL="http://localhost:8085/games"
MAX_ACTIONS=400
SUMMARY_INTERVAL=60

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

# Override max_actions for surprise (matches prior ablation)
get_max_actions() {
    if [ "$1" = "gvgai_surprise" ]; then
        echo 100
    else
        echo $MAX_ACTIONS
    fi
}

echo "=========================================="
echo "  SCRATCHPAD ABLATION — ASCII baseline"
echo "=========================================="
for game in "${GAMES[@]}"; do
    ma=$(get_max_actions "$game")
    echo ""
    echo ">>> [ASCII baseline] $game  (max_actions=$ma)"
    python3 llm_gameplay.py \
        --model "$MODEL" \
        --url "$BASE_URL/$game/0.html" \
        --max_actions "$ma" \
        --summary_interval $SUMMARY_INTERVAL \
        --state_representation ascii \
        2>&1 | tee "results/log_ascii_${game}.txt"
    echo "<<< Done: $game"
done

echo ""
echo "=========================================="
echo "  SCRATCHPAD ABLATION — ASCII + scratchpad"
echo "=========================================="
for game in "${GAMES[@]}"; do
    ma=$(get_max_actions "$game")
    echo ""
    echo ">>> [ASCII + scratchpad] $game  (max_actions=$ma)"
    python3 llm_gameplay.py \
        --model "$MODEL" \
        --url "$BASE_URL/$game/0.html" \
        --max_actions "$ma" \
        --summary_interval $SUMMARY_INTERVAL \
        --state_representation ascii \
        --scratchpad \
        2>&1 | tee "results/log_ascii_scratchpad_${game}.txt"
    echo "<<< Done: $game"
done

echo ""
echo "=========================================="
echo "  ALL RUNS COMPLETE"
echo "=========================================="
