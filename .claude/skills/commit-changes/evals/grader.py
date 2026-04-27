#!/usr/bin/env python3
"""Grade a commit-changes eval run.

Reads the dump produced by fixtures/dump_state.sh and emits grading.json
with one expectation entry per assertion in eval_metadata.json.

Usage:
    grader.py <eval_dir> <run_subdir>
        eval_dir: e.g. .../iteration-1/eval-0-proposal-plus-impl
        run_subdir: "with_skill" or "without_skill"
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Commit:
    sha: str
    subject: str
    body: str
    files: list[tuple[str, str]] = field(default_factory=list)  # (status, path)

    @property
    def paths(self) -> list[str]:
        return [p for _, p in self.files]


def parse_messages(text: str) -> list[Commit]:
    commits: list[Commit] = []
    blocks = [b for b in text.split("===COMMIT===") if b.strip()]
    for block in blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue
        sha = lines[0].strip()
        subject = lines[1].strip() if len(lines) > 1 else ""
        body_text = "\n".join(lines[2:])
        body = ""
        if "---BODY---" in body_text and "---ENDBODY---" in body_text:
            body = body_text.split("---BODY---", 1)[1].split("---ENDBODY---", 1)[0]
        commits.append(Commit(sha=sha, subject=subject, body=body))
    return commits


def parse_files(text: str, commits: list[Commit]) -> None:
    by_sha = {c.sha: c for c in commits}
    blocks = [b for b in text.split("===COMMIT===") if b.strip()]
    for block in blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue
        sha = lines[0].strip()
        files: list[tuple[str, str]] = []
        in_files = False
        for line in lines[2:]:
            if line.strip() == "---FILES---":
                in_files = True
                continue
            if not in_files or not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                status = parts[0]
                # Renames have format: R100 oldpath newpath — record both paths.
                if status.startswith("R") and len(parts) >= 3:
                    files.append((status, parts[1]))
                    files.append((status, parts[2]))
                else:
                    files.append((status, parts[1]))
        if sha in by_sha:
            by_sha[sha].files = files


def load_run(run_dir: Path) -> list[Commit]:
    msgs = (run_dir / "outputs" / "new_commits_messages.txt").read_text()
    files = (run_dir / "outputs" / "new_commits_files.txt").read_text()
    commits = parse_messages(msgs)
    parse_files(files, commits)
    return commits


CONVENTIONAL_TYPES = (
    "proposal", "archive", "feat", "fix", "chore", "docs",
    "test", "refactor", "perf", "build", "ci", "style",
)
SUBJECT_RE = re.compile(
    r"^(" + "|".join(CONVENTIONAL_TYPES) + r")(\([^)]+\))?:\s+\S"
)


def is_openspec_path(p: str) -> bool:
    return p.startswith("openspec/changes/") or p.startswith("openspec/specs/")


def is_code_path(p: str) -> bool:
    return (
        p.startswith("src/")
        or p.startswith("include/")
        or p.startswith("tests/")
        or p.startswith("test/")
    )


def has_co_authored(commit: Commit) -> bool:
    return "Co-Authored-By: Claude" in commit.body


def has_signed_off(commit: Commit) -> bool:
    return "Signed-off-by:" in commit.body


def grade_eval(
    commits: list[Commit],
    assertions: list[dict],
    eval_name: str,
    status_after: str,
) -> list[dict]:
    """Return list of expectation dicts with text/passed/evidence."""
    out: list[dict] = []

    for a in assertions:
        name = a["name"]
        desc = a["description"]
        passed, evidence = check(name, commits, eval_name, status_after)
        out.append({"text": desc, "passed": passed, "evidence": evidence})
    return out


def check(name: str, commits: list[Commit], eval_name: str, status_after: str):
    n = len(commits)

    if name == "exactly_2_new_commits":
        return n == 2, f"new commit count = {n}"
    if name == "exactly_3_new_commits":
        return n == 3, f"new commit count = {n}"

    if name == "proposal_commit_exists_and_is_isolated":
        for c in commits:
            if c.subject.startswith("proposal:"):
                bad = [p for p in c.paths if not p.startswith("openspec/changes/motion-profile-generator/")]
                if not bad:
                    return True, f"{c.sha[:7]} '{c.subject}' contains only proposal paths"
                return False, f"{c.sha[:7]} mixed in: {bad}"
        return False, "no commit with 'proposal:' subject found"

    if name == "archive_commit_exists_and_is_isolated":
        for c in commits:
            if c.subject.startswith("archive:"):
                bad = [p for p in c.paths if not p.startswith("openspec/changes/")]
                if not bad:
                    return True, f"{c.sha[:7]} '{c.subject}' archive isolated"
                return False, f"{c.sha[:7]} mixed in non-openspec: {bad}"
        return False, "no commit with 'archive:' subject found"

    if name == "impl_commit_pairs_feature_with_tests":
        for c in commits:
            if not c.subject.startswith("proposal:"):
                if any("src/planner/profile.cpp" in p for p in c.paths) and \
                   any("tests/planner/test_profile.cpp" in p for p in c.paths):
                    return True, f"{c.sha[:7]} contains both impl and test"
        return False, "no non-proposal commit pairs profile.cpp with test_profile.cpp"

    if name == "planner_commit_pairs_feature_with_tests":
        for c in commits:
            if any("src/planner/limits.cpp" in p for p in c.paths) and \
               any("tests/planner/test_limits.cpp" in p for p in c.paths):
                return True, f"{c.sha[:7]} '{c.subject}' contains both"
        return False, "no commit pairs limits.cpp with test_limits.cpp"

    if name == "logger_commit_isolated":
        for c in commits:
            if any("src/logging/logger.cpp" in p for p in c.paths):
                bad = [p for p in c.paths if "planner" in p or p.endswith("README.md")]
                if not bad:
                    return True, f"{c.sha[:7]} '{c.subject}' logger only"
                return False, f"{c.sha[:7]} also touches: {bad}"
        return False, "no commit touches logger.cpp"

    if name == "readme_commit_isolated":
        for c in commits:
            if any(p == "README.md" for p in c.paths):
                bad = [p for p in c.paths if "planner" in p or "logging" in p]
                if not bad and len([p for p in c.paths if p == "README.md"]) == len(c.paths):
                    return True, f"{c.sha[:7]} '{c.subject}' README only"
                return False, f"{c.sha[:7]} also touches: {bad or c.paths}"
        return False, "no commit touches README.md"

    if name == "readme_uses_docs_type":
        for c in commits:
            if any(p == "README.md" for p in c.paths):
                ok = c.subject.startswith("docs:") or c.subject.startswith("docs(")
                return ok, f"{c.sha[:7]} subject = '{c.subject}'"
        return False, "no commit touches README.md"

    if name == "cleanup_commit_isolated":
        for c in commits:
            if any("src/util/string_utils.cpp" in p for p in c.paths):
                bad = [p for p in c.paths if is_openspec_path(p)]
                if not bad:
                    return True, f"{c.sha[:7]} '{c.subject}' cleanup isolated"
                return False, f"{c.sha[:7]} also touches openspec: {bad}"
        return False, "no commit touches src/util/string_utils.cpp"

    if name == "no_commit_mixes_openspec_and_code":
        for c in commits:
            has_os = any(is_openspec_path(p) for p in c.paths)
            has_code = any(is_code_path(p) for p in c.paths)
            if has_os and has_code:
                return False, f"{c.sha[:7]} mixes openspec + code: {c.paths}"
        return True, f"all {len(commits)} commits cleanly separated"

    if name == "no_commit_mixes_subsystems":
        for c in commits:
            subsystems = set()
            for p in c.paths:
                if "planner" in p:
                    subsystems.add("planner")
                elif "logging" in p:
                    subsystems.add("logging")
                elif p == "README.md":
                    subsystems.add("docs")
            if len(subsystems) > 1:
                return False, f"{c.sha[:7]} mixes: {subsystems} via {c.paths}"
        return True, f"all {len(commits)} commits stay within one subsystem"

    if name == "notes_txt_not_committed":
        # notes.txt should not appear in any commit; should still be untracked.
        for c in commits:
            if any("notes.txt" in p for p in c.paths):
                return False, f"{c.sha[:7]} included notes.txt"
        if "notes.txt" in status_after:
            return True, "notes.txt remains untracked in working tree"
        return True, "notes.txt not in any commit"

    if name == "all_new_commits_have_co_authored_by":
        missing = [c.sha[:7] for c in commits if not has_co_authored(c)]
        if missing:
            return False, f"missing trailer in: {missing}"
        return True, f"all {len(commits)} commits have Co-Authored-By"

    if name == "all_new_commits_have_signed_off_by":
        missing = [c.sha[:7] for c in commits if not has_signed_off(c)]
        if missing:
            return False, f"missing trailer in: {missing}"
        return True, f"all {len(commits)} commits have Signed-off-by"

    if name == "subject_uses_conventional_type":
        bad = [(c.sha[:7], c.subject) for c in commits if not SUBJECT_RE.match(c.subject)]
        if bad:
            return False, f"non-conventional subjects: {bad}"
        return True, f"all {len(commits)} subjects use conventional type"

    return False, f"[grader] unknown assertion: {name}"


def main():
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    eval_dir = Path(sys.argv[1]).resolve()
    run_subdir = sys.argv[2]
    run_dir = eval_dir / run_subdir

    metadata = json.loads((eval_dir / "eval_metadata.json").read_text())
    eval_name = metadata.get("eval_name", eval_dir.name)
    assertions = metadata["assertions"]

    commits = load_run(run_dir)
    status_after = (run_dir / "outputs" / "status_after.txt").read_text()
    expectations = grade_eval(commits, assertions, eval_name, status_after)

    passed = sum(1 for e in expectations if e["passed"])
    total = len(expectations)
    grading = {
        "eval_id": metadata.get("eval_id"),
        "eval_name": eval_name,
        "run": run_subdir,
        "commit_count": len(commits),
        "expectations": expectations,
        "summary": {
            "passed": passed,
            "failed": total - passed,
            "total": total,
            "pass_rate": round(passed / total, 4) if total else 0.0,
        },
    }
    out_path = run_dir / "grading.json"
    out_path.write_text(json.dumps(grading, indent=2))

    print(f"{eval_name} [{run_subdir}]: {passed}/{total} passed → {out_path}")
    for e in expectations:
        mark = "✓" if e["passed"] else "✗"
        print(f"  {mark} {e['text']}\n     {e['evidence']}")


if __name__ == "__main__":
    main()
