#!/bin/bash
# Re-run failed scratchpad ablation games after repo restructure.
# Baseline: surprise, plaqueattack
# Scratchpad: all 9

set -e
cd "$(dirname "$0")"/..

MODEL="openai:gpt-5.2"
BASE_URL="http://localhost:8085/games"
SUMMARY_INTERVAL=60

echo "=========================================="
echo "  RE-RUN: ASCII baseline (2 failed)"
echo "=========================================="

echo ">>> [ASCII baseline] gvgai_surprise (max_actions=100)"
python3 llm_gameplay.py \
    --model "$MODEL" --url "$BASE_URL/gvgai_surprise/0.html" \
    --max_actions 100 --summary_interval $SUMMARY_INTERVAL \
    --state_representation ascii \
    2>&1 | tee "results/log_ascii_gvgai_surprise.txt"

echo ">>> [ASCII baseline] gvgai_plaqueattack (max_actions=400)"
python3 llm_gameplay.py \
    --model "$MODEL" --url "$BASE_URL/gvgai_plaqueattack/0.html" \
    --max_actions 400 --summary_interval $SUMMARY_INTERVAL \
    --state_representation ascii \
    2>&1 | tee "results/log_ascii_gvgai_plaqueattack.txt"

echo ""
echo "=========================================="
echo "  RE-RUN: ASCII + scratchpad (all 9)"
echo "=========================================="

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

get_max_actions() {
    if [ "$1" = "gvgai_surprise" ]; then echo 100; else echo 400; fi
}

for game in "${GAMES[@]}"; do
    ma=$(get_max_actions "$game")
    echo ""
    echo ">>> [ASCII + scratchpad] $game  (max_actions=$ma)"
    python3 llm_gameplay.py \
        --model "$MODEL" --url "$BASE_URL/$game/0.html" \
        --max_actions "$ma" --summary_interval $SUMMARY_INTERVAL \
        --state_representation ascii --scratchpad \
        2>&1 | tee "results/log_ascii_scratchpad_${game}.txt"
    echo "<<< Done: $game"
done

echo ""
echo "=========================================="
echo "  ALL RE-RUNS COMPLETE"
echo "=========================================="
