## Context

Today the repo enforces formatting only in CI, via a dedicated `format-check` job in `.github/workflows/ci.yml`. That job:
- Adds the LLVM apt repo, installs `clang-format-18`, then
- Uses a bespoke shell snippet (`git ls-files '*.cpp' '*.hpp' '*.h' '*.cc' | xargs clang-format --dry-run --Werror`) to check every tracked C++ file.

Two problems:
1. Contributors have no out-of-the-box way to run the exact same check locally before pushing. They have to read the workflow, replicate the command, and install the same clang-format version by hand.
2. The shell snippet is a small but real surface area for drift (file globs, clang-format version, exit-code handling) that diverges from whatever developers happen to run locally.

The project already pins `.clang-format` to clang-format 18. `pre-commit` is the de facto standard for wiring this kind of check: it installs hook environments per-repo, pins both framework and hook versions in `.pre-commit-config.yaml`, and — importantly — the same config drives both local `git commit` and `pre-commit run --all-files` in CI.

Constraints:
- The `build-test` CI job is untouched; this change only replaces `format-check`.
- No RT code is affected; this is pure developer tooling.
- Python/pip is required on the runner (negligible — GitHub-hosted `ubuntu-22.04` ships with Python 3).
- Local use requires contributors to have Python + `pip` available; macOS and Linux both satisfy this by default.

## Goals / Non-Goals

**Goals:**
- Define one canonical source of truth (`.pre-commit-config.yaml`) for formatting and hygiene checks.
- Run that same config unchanged in CI, via `pre-commit run --all-files`.
- Pin `pre-commit`, each hook repo revision, and the clang-format binary so local and CI runs are byte-for-byte reproducible.
- Keep CI wall-clock neutral or better by caching hook environments.
- Make the local setup a two-line operation (`pip install pre-commit && pre-commit install`).

**Non-Goals:**
- Adding `clang-tidy`, static analyzers, sanitizers, or coverage hooks (deferred to a later change).
- Auto-pushing formatting fixes from CI. CI only verifies.
- Configuring `pre-push` or `pre-merge-commit` stages.
- Enforcing commit message style (Conventional Commits) via a hook.
- Supporting Windows-native developer environments.

## Decisions

### D1. Use the official `pre-commit` framework, not a custom Git hook script
**Decision:** Adopt the [`pre-commit`](https://pre-commit.com) framework with `.pre-commit-config.yaml`.

**Alternatives considered:**
- Hand-rolled `.githooks/` script installed via `git config core.hooksPath`. Rejected: no hook pinning, no environment isolation, no cross-language hook support, and we'd still need to replicate it in CI.
- `lefthook` / `husky`. Rejected: `husky` requires Node in the repo (we have none); `lefthook` is viable but has a smaller ecosystem for clang-format hooks and no clear advantage here.

**Rationale:** `pre-commit` is the path the C++ / open-source ecosystem converges on, has first-class `clang-format` and `pre-commit-hooks` integrations, and explicitly supports the "same config in CI" pattern.

### D2. Pin the clang-format hook to version 18 via `pre-commit/mirrors-clang-format`
**Decision:** Use `pre-commit/mirrors-clang-format` at the tag corresponding to clang-format 18.x (e.g. `v18.1.8`). The hook ships a prebuilt clang-format binary per platform, removing the apt dance.

**Alternatives considered:**
- Keep using `apt install clang-format-18` in CI and just wrap it in a `local` pre-commit hook. Rejected: that forces every local contributor to install the same apt package, defeating the "two-line setup" goal.
- `ssciwr/clang-format-hook`. Viable, but `pre-commit/mirrors-clang-format` is the upstream-mirrored option and is what most C++ projects use.

**Rationale:** One pin line in `.pre-commit-config.yaml` replaces both the LLVM apt repo setup and the `clang-format-18` install step in CI, and gives every contributor the same binary.

### D3. Baseline hygiene hooks from `pre-commit-hooks`
**Decision:** Include these hooks from `pre-commit/pre-commit-hooks`:
- `trailing-whitespace`
- `end-of-file-fixer`
- `check-yaml`
- `check-merge-conflict`
- `mixed-line-ending` (configured to `--fix=lf`)

**Alternatives considered:**
- Omit hygiene hooks entirely and only run clang-format. Rejected: these five hooks are cheap, catch real problems (unresolved merge markers in PRs, CRLF line endings sneaking in from non-Linux editors), and are what every project of this shape ends up adding eventually.
- Add `check-added-large-files` too. Deferred: we don't have binary-file pressure yet; can add later without churn.

**Rationale:** The marginal cost is near zero and the hooks catch classes of problems that are currently silent.

### D4. CI replaces the entire `format-check` job with a single `pre-commit` invocation
**Decision:** Rewrite the `format-check` job so it:
1. Checks out the repo.
2. Sets up Python (`actions/setup-python@v5`, `python-version: '3.x'`).
3. Caches `~/.cache/pre-commit` keyed on the OS and the `.pre-commit-config.yaml` hash, using `actions/cache@v4`.
4. Installs `pre-commit` via `pip install pre-commit==<pinned>`.
5. Runs `pre-commit run --all-files --show-diff-on-failure`.

No more apt repo setup, no more `gpg --dearmor`, no more bash `mapfile` file discovery.

**Alternatives considered:**
- Use the `pre-commit/action` GitHub Action. It's convenient but adds an external dependency that mostly wraps the four lines above; we prefer the explicit, self-contained form. (Revisit if we add more hooks and the wrapper becomes worth it.)
- Run `pre-commit run` only on files changed in the PR. Rejected for now: `--all-files` gives full repo coverage and catches drift when hook versions bump. Volume is trivial at this repo size.

**Rationale:** Fewer moving parts, cache makes it fast, and the workflow reads like what a contributor would run locally.

### D5. Pin `pre-commit` itself, not just the hooks
**Decision:** Pin the `pre-commit` package version in the CI `pip install` command (e.g. `pre-commit==3.7.1`).

**Rationale:** `pre-commit` version bumps can change hook behavior (stages, skip semantics, config schema). Pinning both the framework and the hook `rev`s is the only way to guarantee local and CI runs stay in lockstep.

### D6. Keep the pinned clang-format version single-sourced in `.pre-commit-config.yaml`
**Decision:** `.clang-format` already has a comment `# Target clang-format version: 18`. Leave it. The pin authority moves to `.pre-commit-config.yaml`, and the comment stays as human-readable documentation.

**Rationale:** Two pin points (`.clang-format` version comment and `.pre-commit-config.yaml` rev) are fine as long as only one is machine-read. Duplicating in both places is acceptable here since the `.clang-format` note is a comment, not a constraint.

## Risks / Trade-offs

- **Risk:** The initial `pre-commit run --all-files` after merge flags trailing-whitespace / EOF issues across the current tree, breaking CI immediately.
  → **Mitigation:** Run `pre-commit run --all-files` locally as part of the implementation; commit any resulting fixes in the same PR that adds the hooks.

- **Risk:** CI gains a new network dependency on PyPI (`pip install pre-commit`) and on GitHub release assets (for the clang-format mirror).
  → **Mitigation:** `actions/cache@v4` caches hook environments, so steady-state runs fetch nothing. PyPI outages would fail the `format-check` job only; `build-test` is unaffected.

- **Risk:** Contributors on exotic setups without Python 3 / pip hit friction.
  → **Mitigation:** Document `pip install pre-commit` (or `pipx install pre-commit`) in README. Python 3 is already present on macOS and modern Linux; this is a very small audience.

- **Risk:** Pins drift out of date silently.
  → **Mitigation:** `pre-commit autoupdate` is a one-line command; revisit quarterly or whenever a hook stops working. Out of scope for this change.

- **Trade-off:** Two hook sources of truth for formatting (the CI `pre-commit` invocation, and any editor clang-format integration a contributor has locally). This is fine — editor integrations are advisory; the pre-commit hook is the gate.

## Migration Plan

1. Land `.pre-commit-config.yaml` and the updated CI workflow in a single PR.
2. Run `pre-commit run --all-files` locally; commit any bulk cleanup (trailing whitespace, EOF newlines) in the same PR so the first green CI run is clean.
3. Announce in the PR description that contributors should run `pip install pre-commit && pre-commit install` in their clone. No hard cutover — CI is the enforcement point.
4. Rollback: reverting the PR restores the previous `format-check` job verbatim. No data migration, no external system state.

## Open Questions

- Should we standardize on `pipx install pre-commit` over `pip install --user pre-commit` in the README? Pick whichever is less likely to collide with system Python on macOS; default to `pipx` in the doc if we have no strong reason otherwise.
- Do we want to add a `make pre-commit` or CMake target that wraps the install + run, for contributors who don't want to touch Python tooling directly? Deferred — revisit only if real contributor friction shows up.
