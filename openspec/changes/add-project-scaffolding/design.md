## Context

This is the first real change after `openspec init`. The repository currently has only a `LICENSE`, a near-empty `README.md`, a `.gitignore`, and OpenSpec metadata. There is no build system, no source files, no test harness, and no CI.

The project will grow into a real-time C++20 motion-control core with strict performance constraints (500–1000 Hz control loop, PREEMPT_RT, isolated cores). Those constraints are **not** exercised by this change, but the scaffolding choices must not actively obstruct them later — for example, the build system must support multiple independent library targets (HAL, kinematics, safety, control) with controlled link dependencies, and CI must be able to grow to include sanitizer and latency-test jobs.

Developer workflow is macOS-primary for authoring, Linux for CI/target runtime. The scaffolding must be buildable on both.

## Goals / Non-Goals

**Goals:**
- One-command build: `cmake --preset=debug && cmake --build build/debug`
- One-command test: `ctest --preset=debug`
- Every push/PR runs build + tests + format check on Ubuntu
- Contributors build and test with a short, documented list of OS-packaged dependencies (no custom toolchains, no vendored source trees)
- The skeleton compiles an actual library + test so the toolchain is end-to-end verified from day one
- Build targets and CMake conventions leave room to add per-capability subdirectories later without rework

**Non-Goals:**
- Optimal / fastest CI (build time tuning comes when it hurts)
- Multi-compiler / multi-OS matrices (Linux + gcc is the only target that matters)
- Sanitizer, coverage, or benchmark jobs (follow-up changes)
- IDE-specific configuration files checked into the repo

## Decisions

### D1: CMake as the build system
**Choice:** CMake ≥ 3.24 with `CMakePresets.json` for named build configs.
**Alternatives:** Bazel, Meson.
**Rationale:** CMake is the lingua franca of C++ robotics, matches Eigen/GTest/Zenoh upstreams, and presets give us IDE + CLI + CI parity without ad-hoc flags. Bazel is overkill at prototype scale; Meson has thinner ecosystem support for our downstream deps.

### D2: Dependency management via `find_package` + README-documented prerequisites
**Choice:** Treat Eigen and Google Test as external prerequisites discovered via `find_package(Eigen3 CONFIG REQUIRED)` and `find_package(GTest CONFIG REQUIRED)`. Installation commands live in `README.md` (Ubuntu: `apt install libeigen3-dev libgtest-dev`; macOS: `brew install eigen googletest`). CI installs them via `apt` before invoking CMake.
**Alternatives:** CMake `FetchContent`, vcpkg manifest mode, Conan, git submodules.
**Rationale:** At this scale — two well-packaged dependencies, a solo developer, Linux CI — `find_package` is the lowest-friction path. No extra tooling, no network fetch during configure, fast incremental CI, and no CMake cache pollution from dep subprojects. Both dependencies are widely packaged on Ubuntu 22.04+ and macOS Homebrew. Neither FetchContent nor vcpkg buys enough at this point to justify the ceremony.

**Expected migration path:** when a dependency without good OS packaging lands (Zenoh is the likely first), the options are (a) add its upstream APT repo to README/CI, (b) introduce FetchContent surgically for that single dep, or (c) migrate the whole project to vcpkg in a dedicated change. This is accepted tech debt, deferred until the pain is concrete.

### D3: Directory layout — flat now, modular later
**Choice:**
```
src/           # library sources
include/motion_control/   # public headers (project-prefixed)
tests/         # GTest-based unit tests
cmake/         # reusable CMake helpers
```
**Alternatives:** Per-module layout (`modules/<cap>/{src,include,tests}`).
**Rationale:** Flat layout is the right amount of structure for a single initial capability. When 3+ independent capabilities (HAL, kinematics, safety) start pulling on each other, migrate to a per-module layout in a dedicated change — premature modularization now would create empty directories and confusing CMake indirection.

### D4: `.clang-format` base — LLVM style
**Choice:** `BasedOnStyle: LLVM` with minor overrides (`ColumnLimit: 100`, `PointerAlignment: Left`).
**Alternatives:** Google, Mozilla, WebKit, Microsoft, or fully custom.
**Rationale:** User wants "modern, not Google". LLVM style is consistent with modern LLVM/clang codebases, 2-space indent feels cleaner for template-heavy code than Google's 2-space-with-wraps, and it's well-supported by every IDE. Easy to tune a handful of keys later without a style migration.

### D5: Static analysis (clang-tidy) deferred
**Choice:** No `clang-tidy` configuration is shipped in this change. Static analysis is deferred to a follow-up change that lands after the first real code (HAL or kinematics).
**Alternatives:** Ship `.clang-tidy` non-enforcing from day one, or enforce it immediately.
**Rationale:** A check set calibrated against no code is guesswork. Tuning which `modernize-*` / `bugprone-*` / `readability-*` checks carry their weight requires real patterns to evaluate against. A dedicated follow-up change will introduce clang-tidy with an informed check list calibrated against actual code.

### D6: CI — Ubuntu 22.04, gcc-12, Debug + Release
**Choice:** Single OS (ubuntu-22.04), single compiler (gcc-12), two build types.
**Alternatives:** Matrix across macOS/Windows, clang as well.
**Rationale:** Target runtime is Linux + PREEMPT_RT; macOS is dev-only and covered by contributors running `cmake` locally. Adding compilers/OSes now multiplies CI time without catching bugs that matter for the deployment target. Revisit when a second compiler or OS becomes load-bearing.

### D7: Test discovery via `gtest_discover_tests`
**Choice:** Use `gtest_discover_tests()` so each TEST case appears as an individual CTest entry.
**Alternatives:** `gtest_add_tests` (parse-based), single lump test.
**Rationale:** `discover_tests` runs the binary to enumerate cases, giving accurate CTest filtering and parallel execution at case granularity.

### D8: Smoke target from day one
**Choice:** Ship a minimal `motion_control_core` library (a single namespace with one trivial function) and a matching `smoke_test` that links against it.
**Alternatives:** Empty scaffold, README-only verification.
**Rationale:** An end-to-end pipeline verified once beats a beautiful scaffold that has never compiled. The smoke target is the thing future capability work replaces/extends.

## Risks / Trade-offs

- **[System dep version drift across machines]** → Document minimum versions in the README (Eigen ≥ 3.4, GTest ≥ 1.11). The CI runner image is the canonical reference — anything that builds there is authoritative.
- **[A future dependency isn't packaged on Ubuntu/brew]** → Accepted. When it happens, reach for the surgical options listed under D2 rather than preemptively rearchitecting now.
- **[clang-format version skew produces spurious diffs]** → CI installs a pinned `clang-format-18`; `.clang-format` header comments the expected version; contributors are told to match.
- **[Early CMake conventions harden into cruft]** → Keep `cmake/` helpers tiny and documented; revisit layout at the 3-capability mark.
- **[RT-path assumptions leaking into scaffolding]** → This change deliberately ships no RT code; later changes own RT compile flags, linker settings, and CPU-pinning harnesses.

## Migration Plan

Greenfield addition — no existing state to migrate. Rollback is `git revert` of the change commit. No external systems affected.

## Open Questions

- Add `compile_commands.json` symlink convention for IDE tooling in this change or a follow-up? → Default plan: enable `CMAKE_EXPORT_COMPILE_COMMANDS` in presets; no symlink script yet.
- Enable `-Werror` from day one? → Default plan: yes in Debug, no in Release (to avoid surprising warnings from Eigen internals breaking release builds).
