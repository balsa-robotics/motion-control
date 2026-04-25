# pre-commit-hooks

## Purpose
Defines the canonical set of commit-time checks shared by contributors and CI, anchored on a pinned `.pre-commit-config.yaml` at the repository root. The same configuration drives local Git hooks (via `pre-commit install`) and the CI format-check job, so that style, hygiene, and clang-format compliance are enforced identically before code lands on `main`.

## Requirements

### Requirement: Repository ships a pre-commit configuration
The project SHALL provide a `.pre-commit-config.yaml` file at the repository root that defines the canonical set of commit-time checks. The same file SHALL be consumed unchanged by contributor machines (via `pre-commit install` / `pre-commit run`) and by the CI workflow.

#### Scenario: Config file exists at repo root
- **WHEN** a contributor checks out the repository
- **THEN** `.pre-commit-config.yaml` is present at the repository root and is valid YAML parseable by `pre-commit`

#### Scenario: CI and local runs use the same config
- **WHEN** CI invokes `pre-commit run --all-files` and a contributor invokes the same command locally on the same commit
- **THEN** both runs execute the identical set of hooks with identical pinned revisions

### Requirement: clang-format hook pinned to version 18
The pre-commit configuration SHALL include a `clang-format` hook sourced from a mirror that pins the clang-format binary to a version in the 18.x series, matching the version targeted by `.clang-format`. The hook SHALL run only on tracked C++ source and header files (`*.cpp`, `*.hpp`, `*.h`, `*.cc`).

#### Scenario: C++ file violating style is rejected
- **WHEN** a contributor stages a C++ file that does not comply with `.clang-format` and runs `pre-commit run`
- **THEN** the clang-format hook exits non-zero and the commit is blocked

#### Scenario: Non-C++ file is not processed by clang-format
- **WHEN** a contributor stages only a Markdown or CMake file and runs `pre-commit run`
- **THEN** the clang-format hook is skipped (reports "no files to check") and does not fail the run

### Requirement: Baseline hygiene hooks included
The pre-commit configuration SHALL include, at minimum, the following hooks from `pre-commit/pre-commit-hooks`:
- `trailing-whitespace`
- `end-of-file-fixer`
- `check-yaml`
- `check-merge-conflict`
- `mixed-line-ending` configured to enforce LF line endings

#### Scenario: Trailing whitespace is flagged
- **WHEN** a contributor stages a file containing trailing whitespace and runs `pre-commit run`
- **THEN** the `trailing-whitespace` hook modifies the file (or reports the violation) and the run exits non-zero

#### Scenario: Unresolved merge conflict marker is flagged
- **WHEN** a contributor stages a file containing a `<<<<<<<` merge conflict marker and runs `pre-commit run`
- **THEN** the `check-merge-conflict` hook exits non-zero

#### Scenario: Invalid YAML is flagged
- **WHEN** a contributor stages a malformed `.yaml` or `.yml` file and runs `pre-commit run`
- **THEN** the `check-yaml` hook exits non-zero with a parse error

### Requirement: Framework and hook revisions are pinned
The `.pre-commit-config.yaml` file SHALL pin every hook repository to a specific `rev` (tag or commit), and the CI workflow SHALL install a pinned version of the `pre-commit` package itself (e.g. `pre-commit==<x.y.z>`). Floating references (`HEAD`, `main`, unversioned installs) SHALL NOT be used.

#### Scenario: All hooks declare a fixed rev
- **WHEN** the configuration is inspected
- **THEN** every entry under `repos:` has an explicit `rev` that is a tag or commit SHA, never a branch name

#### Scenario: CI installs a pinned pre-commit version
- **WHEN** the CI workflow installs `pre-commit`
- **THEN** the install command specifies an explicit version (e.g. `pip install pre-commit==<x.y.z>`) rather than a floating install

### Requirement: Developer setup is documented
`README.md` SHALL document how to install `pre-commit` locally and register the Git hook, at minimum covering `pip install pre-commit` (or `pipx install pre-commit`) followed by `pre-commit install`, plus the manual full-repo invocation `pre-commit run --all-files`.

#### Scenario: README covers local setup
- **WHEN** a contributor reads `README.md`
- **THEN** they find explicit commands for installing `pre-commit`, registering the Git hook via `pre-commit install`, and running the hooks across the full repo with `pre-commit run --all-files`
