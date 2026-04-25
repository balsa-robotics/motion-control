## MODIFIED Requirements

### Requirement: CI enforces clang-format compliance
The CI workflow SHALL enforce `clang-format` compliance by executing the project's `pre-commit` configuration via `pre-commit run --all-files`, which invokes the pinned clang-format 18 hook defined in `.pre-commit-config.yaml`. The workflow SHALL fail if any tracked C++ source or header file does not match `.clang-format`. The workflow SHALL NOT invoke `clang-format` directly or maintain a bespoke file-discovery snippet.

#### Scenario: Compliant changes pass the format check
- **WHEN** a pull request only adds code that already conforms to `.clang-format`
- **THEN** `pre-commit run --all-files` exits with status zero and the CI job reports success

#### Scenario: Non-compliant changes fail the format check
- **WHEN** a pull request introduces a C++ file that does not match `.clang-format`
- **THEN** `pre-commit run --all-files` exits non-zero, the CI job fails, and the diff produced by clang-format is visible in the job logs (via `--show-diff-on-failure`)

#### Scenario: Hygiene violations also fail the check
- **WHEN** a pull request introduces trailing whitespace, a missing final newline, an unresolved merge marker, or malformed YAML
- **THEN** the corresponding `pre-commit` hook fails and the CI job reports failure

### Requirement: CI environment is pinned
The CI workflow SHALL run on `ubuntu-22.04` runners, use `gcc-12` as the C++ compiler for the build-test job, and install a pinned version of the `pre-commit` package for the format-check job. The clang-format binary used by the format check SHALL be pinned via the `rev` of the clang-format hook in `.pre-commit-config.yaml` to a version in the 18.x series matching `.clang-format`.

#### Scenario: Runner image is fixed
- **WHEN** the CI workflow starts a job
- **THEN** the job runs on the `ubuntu-22.04` runner image and, for the build-test job, uses `gcc-12` for compilation

#### Scenario: pre-commit version is pinned
- **WHEN** the CI workflow installs `pre-commit`
- **THEN** the install command specifies an explicit version (e.g. `pip install pre-commit==<x.y.z>`), not a floating install

#### Scenario: clang-format version is pinned via pre-commit
- **WHEN** the format-check job runs `pre-commit run --all-files`
- **THEN** the clang-format binary used is the one fetched from the pinned hook `rev` in `.pre-commit-config.yaml`, in the 18.x series

## REMOVED Requirements

### Requirement: CI installs third-party dependencies via apt
**Reason:** This requirement conflated two concerns — installing C++ runtime prerequisites (Eigen, Google Test) for the `build-test` job, and installing `clang-format` for the `format-check` job. With `format-check` switching to `pre-commit` (which fetches its own pinned clang-format binary), only the build-test job still needs apt-installed C++ libraries. The C++ library install is now covered by the retained scenarios in the build-test job itself, and no requirement-level statement is needed solely for that job.

**Migration:** No migration required for consumers. The `build-test` job continues to `apt install libeigen3-dev libgtest-dev` as before; this is now an implementation detail of that job rather than a spec-level requirement. If future ci-pipeline work needs to re-elevate C++ library installation to a spec requirement, it can be re-added with build-test-specific wording.
