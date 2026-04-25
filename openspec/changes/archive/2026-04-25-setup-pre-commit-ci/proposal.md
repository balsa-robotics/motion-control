## Why

Formatting and simple hygiene checks today only run in GitHub Actions, after a contributor has already pushed. Feedback cycles are slow, and the clang-format job reimplements a file-discovery and invocation shell snippet that is not reproducible locally. Adopting `pre-commit` gives every contributor the same checks before they ever push, and lets CI reuse the exact same config — keeping local and remote checks in lockstep.

This change is purely developer infrastructure. It does **not** touch the RT path; no runtime code is added or modified.

## What Changes

- Add a `.pre-commit-config.yaml` at the repository root with hooks for:
  - `clang-format` pinned to version 18 (matching `.clang-format`), scoped to tracked C++ source/header files
  - Standard baseline hooks from `pre-commit-hooks`: `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-merge-conflict`, `mixed-line-ending`
- Pin the `pre-commit` framework and hook revisions so local and CI runs are reproducible
- Replace the existing `format-check` job in `.github/workflows/ci.yml` with a job that runs `pre-commit run --all-files`, removing the bespoke clang-format install/invocation snippet
- Cache the `pre-commit` hook environments in CI keyed on `.pre-commit-config.yaml`
- Update `README.md` with a short "Setting up pre-commit" section covering `pip install pre-commit` and `pre-commit install`
- Extend `.gitignore` if needed for the pre-commit cache directory

## Capabilities

### New Capabilities
- `pre-commit-hooks`: Developer-facing commit-time hook configuration that defines the canonical set of formatting and hygiene checks run on every commit and reused verbatim by CI

### Modified Capabilities
- `ci-pipeline`: The "CI enforces clang-format compliance" requirement becomes "CI enforces all pre-commit hooks", executed via `pre-commit run --all-files` instead of a bespoke clang-format invocation; the environment-pinning requirement gains a pinned `pre-commit` installation step

## Non-Goals

- Adding `clang-tidy`, static analyzers, coverage, or sanitizer hooks — deferred until there is real C++ logic to tune them against
- Auto-fixing / auto-formatting pushes from CI (CI will only verify, never commit back)
- Commit message linting (e.g., Conventional Commits enforcement via `commitlint` or `commitizen`) — out of scope here
- Pre-push or pre-merge-commit stages — only the default `pre-commit` stage is configured in this change
- Windows developer support for the hook runner — Linux and macOS are the supported local environments

## Impact

**New files**
- `.pre-commit-config.yaml`

**Modified files**
- `.github/workflows/ci.yml` — replace `format-check` job body with `pre-commit` invocation
- `README.md` — add pre-commit setup instructions
- `.gitignore` — only if a new cache path needs to be ignored

**Developer workflow**
- Contributors SHOULD install `pre-commit` and run `pre-commit install` once per clone; the hooks then run automatically on `git commit`
- Contributors can manually run `pre-commit run --all-files` to preflight the full repo

**CI**
- The `format-check` job is replaced by a `pre-commit` job. Wall-clock impact should be neutral or faster due to hook caching
- The set of enforced checks expands slightly (trailing whitespace, final newline, YAML validity, merge conflict markers, mixed line endings), which may cause an initial one-time cleanup commit

**No impact on**
- RT path (no runtime code touched)
- `build-system` capability (CMake, presets, `find_package` wiring are unchanged)
- The `build-test` CI job (only `format-check` is replaced)
- External systems or runtime dependencies
