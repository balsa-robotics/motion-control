#!/usr/bin/env bash
# Dumps the post-action git state for grading.
#   dump_state.sh <baseline_ref> <output_dir>
# Saves files into <output_dir>:
#   git_log.txt              full oneline log
#   new_commits_messages.txt full body of each commit since baseline
#   new_commits_files.txt    files touched by each commit since baseline
#   status_after.txt         remaining dirty state
#   baseline_head.txt        baseline ref
#   final_head.txt           HEAD after work
set -euo pipefail
BASELINE="${1:?usage: dump_state.sh <baseline_ref> <output_dir>}"
OUT="${2:?usage: dump_state.sh <baseline_ref> <output_dir>}"
mkdir -p "$OUT"

git log --oneline --all > "$OUT/git_log.txt"
git log "${BASELINE}..HEAD" \
    --format='===COMMIT===%n%H%n%s%n---BODY---%n%B---ENDBODY---' \
    > "$OUT/new_commits_messages.txt"
git log "${BASELINE}..HEAD" \
    --name-status --format='===COMMIT===%n%H%n%s%n---FILES---' \
    > "$OUT/new_commits_files.txt"
git status --porcelain > "$OUT/status_after.txt"
echo "$BASELINE" > "$OUT/baseline_head.txt"
git rev-parse HEAD > "$OUT/final_head.txt"
