## Why

The CI `build-test` job fails at configure time with `Eigen3 (>= 3.4) not found.` even though `libeigen3-dev` is installed on the `ubuntu-22.04` runner. The root cause is in `cmake/Dependencies.cmake`: `find_package(Eigen3 ... CONFIG QUIET)` restricts the search to CMake CONFIG mode and suppresses the underlying diagnostic, so when the package's CONFIG file is not located through CMake's default search heuristics the project fails with a generic message that hides why. The same brittle `QUIET` pattern is repeated for `GTest`, so any future GoogleTest discovery hiccup will be just as opaque.

This also drifts from the existing `build-system` spec, which already requires that third-party dependencies be resolved "via `find_package` against system-installed copies (either CMake CONFIG or MODULE mode, whichever the package provides)" — the current implementation picks CONFIG only.

## What Changes

- Update `cmake/Dependencies.cmake` so that `find_package(Eigen3 ...)` tries CMake's default discovery (MODULE mode first, then CONFIG mode), instead of forcing CONFIG only.
- Apply the same fix to `find_package(GTest ...)` in the same file.
- Drop `QUIET` from both `find_package` calls so the underlying CMake "considered paths / version mismatch" diagnostic is printed before our `FATAL_ERROR` install hint, restoring actionable failure output in CI logs.
- Keep the existing `FATAL_ERROR` install-hint blocks (Ubuntu / macOS instructions, README pointer) unchanged so the user-facing error contract is preserved.
- Verify on CI: the `ubuntu-22.04` `build-test` job configures, builds, and tests cleanly without changing the `apt-get install` package list.

## Non-Goals

- Vendoring Eigen or GoogleTest via `FetchContent`, git submodules, or any other source-fetch mechanism. CI continues to consume the system `libeigen3-dev`, `libgtest-dev`, and `libgmock-dev` packages.
- Adding alternative finder backends (pkg-config, vcpkg, Conan).
- Touching real-time / control-loop code. This change is build-only.
- Bumping the minimum Eigen, GTest, CMake, or compiler versions documented in `README.md`.

## Capabilities

### New Capabilities
<!-- None. -->

### Modified Capabilities
- `build-system`: Tighten the "Third-party dependencies resolved via find_package" requirement so the contract explicitly forbids forcing CONFIG-only or `QUIET` discovery (which suppresses CMake's own diagnostic), and adds a scenario covering the underlying diagnostic surfacing on configure failure.

## Impact

- **Code**: `cmake/Dependencies.cmake` (only file modified).
- **CI**: `.github/workflows/ci.yml` `build-test` job starts succeeding again; no workflow edits required.
- **Local builds**: Ubuntu and macOS contributors who already have the documented prerequisites installed see no behavior change on the happy path. On the failure path, they get richer CMake output above the existing install-hint message.
- **RT path**: None — build-system change only.
- **Specs**: Delta to `build-system` spec only.
- **Dependencies / packages**: No version bumps, no new packages.
