---
name: commit-changes
description: Generate atomic commits from staged or untracked changes, with openspec-aware splitting (proposal/archive moves never share a commit with code). Use whenever the user wants to commit, save, stage, or finalize their work — including phrases like "commit my changes", "split this into atomic commits", "commit what I have", "save these changes", or "make commits". Always use this skill when committing in an openspec project so granularity stays consistent.
license: MIT
compatibility: Requires git, pre-commit, and an openspec layout (openspec/changes/, openspec/specs/, openspec/changes/archive/).
metadata:
  author: jinwoo-choi
  version: "1.0"
---

Help the user turn the working tree into a clean series of atomic commits. The user reviews and approves the plan before anything lands. Pre-commit hooks run; failures are repaired, not skipped.

The point of this skill is **consistency of commit granularity** across the project. The user is using openspec, where proposals and archive moves are bookkeeping for the spec workflow — they should never share a commit with the code that implements them, because that mixes two different review concerns and breaks `git bisect` and `git revert` symmetry.

---

## Inputs

- A working tree with staged, unstaged, and/or untracked changes.
- Optional user hints in the prompt (e.g. "skip the README change", "all in one commit", "include the untracked test file").

If the working tree is fully clean, say so and stop — there is nothing to commit.

---

## Steps

### 1. Survey the working tree

Run these in parallel:

```bash
git status --short
git diff --stat        # unstaged
git diff --stat --cached  # staged
git log -n 5 --oneline   # to match recent style
```

For each modified or untracked file, you may also need `git diff <file>` or `git diff --cached <file>` to understand the change. Read enough to describe each change in one short sentence — you do not need to read every line.

If something looks like a secret (`.env`, `*.pem`, files with `credential`/`token`/`secret` in the name), flag it and ask the user before including it. Never auto-stage secrets.

### 2. Classify each change

Bucket every changed path into one of these categories. The category determines both **the commit type** and **whether the change can share a commit with anything else**.

| Path pattern | Category | Conventional type | Shares a commit with? |
|---|---|---|---|
| `openspec/changes/<name>/` (added or modified, not under `archive/`) | **proposal** | `proposal:` | Other files **only inside the same proposal directory** |
| `openspec/changes/<name>/` → `openspec/changes/archive/YYYY-MM-DD-<name>/` (rename/move) | **archive** | `archive:` | Other files **only inside the same archive move** |
| `openspec/specs/<capability>/` | **spec edit** | `proposal:` | Other spec files in the same capability |
| Code, tests, build files, docs, configs (everything else) | **code** | `feat` / `fix` / `chore` / `docs` / `test` / `refactor` / `perf` / `build` / `ci` / `style` | Other code files **in the same logical change** |

**Why this split exists:** proposal and archive are spec-bookkeeping. They describe *intent* and *closure*, not behavior. If you mix them with implementation, a `git revert` of the implementation also reverts the bookkeeping (or vice versa), and reviewers can't separate "did we agree on this?" from "is the code correct?". Keep them isolated.

### 3. Group code changes into atomic commits

Within the **code** category, group files so that one commit = one logical change. Use these heuristics:

- **A feature and its tests belong together.** If `src/foo.cpp` adds a function and `tests/test_foo.cpp` exercises it, that is one commit. Splitting them produces a broken build between the two commits.
- **A fix and its regression test belong together**, same reason.
- **Unrelated edits to different subsystems are different commits.** If one diff touches motion planning and another touches logging, those are two commits even if you authored them in the same session.
- **Pure formatting / whitespace / clang-format reflows** that are unrelated to a behavior change get their own `style:` commit. (Note: pre-commit auto-fixes from trailing-whitespace / clang-format are different — see step 6.)
- **Dependency or build-system bumps** are their own `build:` or `chore:` commit.
- **Doc-only changes** unrelated to the current feature are their own `docs:` commit. README updates that explain a feature you're adding can ride with that feature.

If the user hinted at grouping in the prompt ("just one commit" or "split out the README"), respect it.

### 4. Draft the commit messages

Match the recent log style. From the working repo:

```
feat: setup initial pre-commit
proposal: add initial proposal for pre-commit
chore: archive changes for setup-pre-commit-ci   # historical — new commits use archive:
```

Format every message as:

```
<type>: <subject in imperative mood, lower-case, no trailing period>

<optional body explaining the why, wrapped at ~72 chars>
```

- Subject under ~70 characters.
- For `proposal:` commits, the subject names the proposal: `proposal: add motion-profile-generator`.
- For `archive:` commits, the subject names what is being archived: `archive: motion-profile-generator`.
- Use a body when the *why* is non-obvious. Skip it for trivial commits.

**Trailers** (always, in this order):

```
Co-Authored-By: Claude <noreply@anthropic.com>
```

Then append the sign-off via `git commit -s` (do not write `Signed-off-by:` by hand — `-s` adds it correctly using the configured git user).

### 5. Show the plan and wait for approval

Before touching the index, show the user the plan in this exact shape so it's easy to scan:

```
Proposed commits (N):

1. proposal: add motion-profile-generator
   - openspec/changes/motion-profile-generator/proposal.md
   - openspec/changes/motion-profile-generator/tasks.md

2. feat(planner): implement trapezoidal motion profile
   - src/planner/profile.cpp
   - include/planner/profile.hpp
   - tests/planner/test_profile.cpp

3. archive: setup-pre-commit-ci
   - openspec/changes/setup-pre-commit-ci/ → openspec/changes/archive/2026-04-27-setup-pre-commit-ci/

Untracked, NOT included:
   - notes.txt   (looks like personal notes — confirm if you want it in)

Skipped (looks sensitive):
   - .env.local
```

Then use the **AskUserQuestion tool** to ask: "Proceed with these commits, or adjust?" Offer choices: `Proceed`, `Adjust grouping`, `Adjust messages`, `Cancel`.

Do not start committing until the user picks `Proceed`. If they ask to adjust, revise the plan and show it again.

### 6. Execute commits one at a time

For each commit in the plan, in order:

1. **Reset the index** so previous staged state doesn't leak in:
   ```bash
   git reset
   ```
2. **Stage exactly the files for this commit** by name. Do not use `git add -A` or `git add .` — that risks pulling in unintended files.
   ```bash
   git add path/one path/two
   ```
   For archive moves, stage the rename: `git add -A openspec/changes/<name> openspec/changes/archive/YYYY-MM-DD-<name>` (the rename detection will collapse it).
3. **Commit with sign-off and the message via heredoc**:
   ```bash
   git commit -s -m "$(cat <<'EOF'
   <type>: <subject>

   <optional body>

   Co-Authored-By: Claude <noreply@anthropic.com>
   EOF
   )"
   ```
4. **Handle pre-commit hook outcomes**:
   - **Hook passed** → continue to the next commit.
   - **Hook auto-fixed files** (trailing-whitespace, end-of-file-fixer, mixed-line-ending, clang-format will modify the working tree and exit non-zero on first run): re-stage the same paths and re-run the same `git commit` command. Do this once. If the hook still fails after that, treat it as a real failure (next bullet).
   - **Hook reported a real error** (lint failure, merge conflict marker, etc.): stop. Show the hook output to the user, ask how to proceed. **Never pass `--no-verify`.** The whole point is that the project's checks run.
5. **Verify the commit landed**: `git log -1 --stat`. Confirm the expected files are in it and trailers are present.

If any commit fails mid-sequence, stop and report which commits landed and which didn't. Do not try to "recover" by force-pushing or amending — let the user decide.

### 7. Final summary

After all commits land, show:

```
Created N commits:
  abc1234 proposal: ...
  def5678 feat(planner): ...
  9012abc archive: ...

Run `git log -n N --stat` to review, or `git push` when ready.
```

Do not push. Pushing is the user's call.

---

## Edge cases

- **Empty working tree**: say so and stop.
- **Only untracked files, nothing modified**: still works — the plan just stages untracked files for their respective commits. Confirm each one with the user before including.
- **User says "one commit, don't split"**: honor it. Still apply the message format and trailers, still run hooks, still wait for approval.
- **Merge in progress / rebase in progress / detached HEAD**: stop and tell the user — committing in those states needs their judgment, not yours.
- **First commit in a brand-new repo with no `HEAD`**: `git log` will fail, that's fine. Skip the recent-log-style step and use a clean Conventional Commits default.
- **Renames git didn't auto-detect**: if a file looks like a rename (similar content under a new name), use `git add -A` for that pair within the staging step for that commit, so git records it as a rename rather than delete + add.
- **A single hunk needs to span two commits**: this is the only case where you may use `git add -p` to stage hunks selectively. Show the user what you're doing before doing it.

---

## What good looks like

- Every commit is independently revertable and the build is green at every commit.
- Spec bookkeeping (`proposal:`, `archive:`) is never mixed with implementation.
- A reviewer reading `git log --oneline` can tell what each commit does without opening the diff.
- No `--no-verify`. No force-push. No amends to commits the user didn't ask you to amend.

## Guardrails

- Never commit without showing the plan and getting explicit approval.
- Never bypass pre-commit hooks. Re-stage and retry once after auto-fixes; otherwise surface the failure.
- Never auto-stage anything that looks like a secret. Ask first.
- Never `git add -A` / `git add .` blindly — always stage by explicit path.
- Never push, force-push, or amend an existing commit unless the user explicitly asks.
- If the user is mid-rebase or mid-merge, stop and ask.
