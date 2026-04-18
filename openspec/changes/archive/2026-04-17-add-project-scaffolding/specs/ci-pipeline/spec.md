## ADDED Requirements

### Requirement: CI runs on every push and pull request
The project SHALL define a GitHub Actions workflow at `.github/workflows/ci.yml` that runs automatically on every push to any branch and on every pull request targeting `main`.

#### Scenario: Push triggers CI
- **WHEN** a commit is pushed to any branch
- **THEN** the `ci` workflow starts and its status is reported on the commit

#### Scenario: Pull request triggers CI
- **WHEN** a pull request is opened or updated against `main`
- **THEN** the `ci` workflow starts and its status is reported on the pull request

### Requirement: CI builds Debug and verifies tests pass
The CI workflow SHALL configure the project with the `debug` preset, build all targets, and run the full test suite via CTest. The workflow SHALL fail if any test fails.

#### Scenario: All tests pass
- **WHEN** the CI workflow runs against a commit where every test passes
- **THEN** the build job reports success

#### Scenario: A test fails
- **WHEN** the CI workflow runs against a commit where at least one test fails
- **THEN** the build job reports failure and the failing test output is visible in the job logs

### Requirement: CI enforces clang-format compliance
The CI workflow SHALL run `clang-format --dry-run --Werror` across all tracked C++ source and header files, and SHALL fail if any file is not compliant with `.clang-format`.

#### Scenario: Compliant changes pass the format check
- **WHEN** a pull request only adds code that already conforms to `.clang-format`
- **THEN** the format-check step exits with status zero

#### Scenario: Non-compliant changes fail the format check
- **WHEN** a pull request introduces a C++ file that does not match `.clang-format`
- **THEN** the format-check step exits non-zero and the CI workflow fails

### Requirement: CI environment is pinned
The CI workflow SHALL run on `ubuntu-22.04` runners, use `gcc-12` as the C++ compiler, and install a pinned `clang-format` version matching the one declared in `.clang-format`.

#### Scenario: Runner image is fixed
- **WHEN** the CI workflow starts a job
- **THEN** the job runs on the `ubuntu-22.04` runner image and uses `gcc-12` for compilation

### Requirement: CI installs third-party dependencies via apt
The CI workflow SHALL install all third-party C++ library prerequisites — at minimum Eigen 3 and Google Test — via `apt` on the Ubuntu runner before invoking CMake, so that `find_package` resolves them from the system.

#### Scenario: Workflow installs required packages
- **WHEN** the CI workflow starts the `build-test` job
- **THEN** an `apt install` step runs before `cmake` and installs at least `libeigen3-dev` and `libgtest-dev`
