## Why

The repository was just initialized with OpenSpec but has no buildable code, no build system, no CI, and no linting setup. Before any feature work (HAL, kinematics, control loop) can start, we need a C++20 foundation that can compile, run tests, and enforce formatting on every push.

## What Changes

- Add a CMake root configuration targeting C++20, with presets for Debug and Release builds
- Establish the standard directory layout (`src/`, `include/`, `tests/`, `cmake/`)
- Add `.clang-format` (base style chosen to align with modern C++; final config tunable later)
- Declare Eigen and Google Test as external dependencies discovered with `find_package`; document how to install them (system package manager on Linux, Homebrew on macOS) in `README.md`
- Add a GitHub Actions workflow: build + unit test + clang-format check on push / PR
- Update `README.md` with build & test instructions
- Add a minimal "hello" library target and test to verify the pipeline end-to-end

No RT-path code is introduced in this change; this is purely developer infrastructure.

## Capabilities

### New Capabilities
- `build-system`: CMake-based build that produces library targets and test targets, linking against system-installed third-party dependencies discovered via `find_package`
- `ci-pipeline`: GitHub Actions workflow running build, unit tests, and format-check on every push and pull request

### Modified Capabilities
<!-- None — this is the first change after init -->

## Non-Goals

- Any motion-control runtime logic (HAL, kinematics, safety, control loop — all deferred to later changes)
- Zenoh, EtherCAT, CAN integration (follows HAL work)
- Cross-compilation to target hardware, packaging, or release automation
- Coverage reporting, sanitizer builds, and benchmark infrastructure (future CI enhancements)
- Static analysis via `clang-tidy` (deferred until there is real code to calibrate the check set against)
- PREEMPT_RT-specific tooling (will be added when RT code lands)

## Impact

**New files**
- `CMakeLists.txt` (root), `cmake/` helpers, `CMakePresets.json`
- `.clang-format`
- `.github/workflows/ci.yml`
- `src/`, `include/`, `tests/` skeletons with a hello/smoke target
- Updated `README.md`

**External dependencies (to be installed by contributor / CI, not vendored)**
- Eigen 3 (header-only; Ubuntu: `libeigen3-dev`, macOS: `brew install eigen`)
- Google Test (Ubuntu: `libgtest-dev` / `googletest-dev`, macOS: `brew install googletest`)

**No impact on**
- RT path (no runtime code yet)
- Existing specs (none exist)
- External systems
