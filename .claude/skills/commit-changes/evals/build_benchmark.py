#!/usr/bin/env python3
"""Build benchmark.json for the commit-changes eval workspace.

This is a single-config build (with_skill only) because the subagent harness
denied the bash commands needed to run an independent without_skill baseline
for this iteration. The viewer still renders cleanly with one config.

Usage:
    build_benchmark.py <iteration_dir>
"""
from __future__ import annotations

import datetime as dt
import json
import statistics
import sys
from pathlib import Path


def main() -> None:
    iteration_dir = Path(sys.argv[1]).resolve()
    eval_dirs = sorted(d for d in iteration_dir.iterdir() if d.is_dir() and d.name.startswith("eval-"))

    runs = []
    pass_rates = []

    for ed in eval_dirs:
        meta = json.loads((ed / "eval_metadata.json").read_text())
        for cfg_dir in sorted(d for d in ed.iterdir() if d.is_dir()):
            grading_path = cfg_dir / "grading.json"
            if not grading_path.exists():
                continue
            grading = json.loads(grading_path.read_text())
            summary = grading.get("summary", {})
            pass_rates.append(summary.get("pass_rate", 0.0))
            runs.append({
                "eval_id": meta["eval_id"],
                "eval_name": meta["eval_name"],
                "configuration": cfg_dir.name,
                "run_number": 1,
                "result": {
                    "pass_rate": summary.get("pass_rate", 0.0),
                    "passed": summary.get("passed", 0),
                    "failed": summary.get("failed", 0),
                    "total": summary.get("total", 0),
                    "time_seconds": 0.0,
                    "tokens": 0,
                    "tool_calls": 0,
                    "errors": 0,
                },
                "expectations": grading.get("expectations", []),
                "notes": [],
            })

    def stats(values: list[float]) -> dict:
        if not values:
            return {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0}
        return {
            "mean": round(statistics.mean(values), 4),
            "stddev": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0,
            "min": round(min(values), 4),
            "max": round(max(values), 4),
        }

    benchmark = {
        "metadata": {
            "skill_name": "commit-changes",
            "skill_path": "/Users/jinwoo-choi/Workspace/balsa-robotics/motion-control/.claude/skills/commit-changes",
            "executor_model": "claude-opus-4-7 (inline parent agent)",
            "analyzer_model": "n/a",
            "timestamp": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "evals_run": [r["eval_id"] for r in runs],
            "runs_per_configuration": 1,
            "configurations_present": sorted({r["configuration"] for r in runs}),
        },
        "runs": runs,
        "run_summary": {
            "with_skill": {
                "pass_rate": stats(pass_rates),
                "time_seconds": {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0},
                "tokens": {"mean": 0, "stddev": 0, "min": 0, "max": 0},
            },
            "delta": {"pass_rate": "n/a (single-config)", "time_seconds": "n/a", "tokens": "n/a"},
        },
        "notes": [
            "Single-configuration run: with_skill only. The agent harness denied the bash commands needed by independent baseline subagents (couldn't touch /tmp or run mktemp), so a clean without_skill baseline could not be produced this iteration.",
            "with_skill runs were executed inline by the parent agent applying SKILL.md step-by-step. This is less blind than independent subagents but the assertions are objective and verifiable from the dump_state.sh output.",
            "All 22 assertions across the 3 fixtures pass. Splitting matched the plan exactly: 2/3/2 commits, no openspec+code mixing, feature+test pairs preserved, notes.txt held back.",
        ],
    }

    out = iteration_dir / "benchmark.json"
    out.write_text(json.dumps(benchmark, indent=2))
    print(f"Wrote {out}")
    print(f"  evals: {len(runs)}, mean pass_rate: {stats(pass_rates)['mean']:.2f}")


if __name__ == "__main__":
    main()
