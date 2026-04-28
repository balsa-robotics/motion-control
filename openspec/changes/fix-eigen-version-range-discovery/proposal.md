## Why

CI is still failing on `ubuntu-22.04` even after the previous `fix-ci-dependency-discovery` change exposed CMake's underlying diagnostic. The new diagnostic shows `find_package` did locate `/usr/share/eigen3/cmake/Eigen3Config.cmake` at version 3.4.0, but rejected it as "not compatible with requested version range `3.4...<6`". The root cause is that Eigen 3.4.0's bundled `Eigen3ConfigVersion.cmake` predates CMake 3.19's version-range syntax and does not honor `PACKAGE_FIND_VERSION_RANGE`. macOS Homebrew Eigen (5.0.1) ships a modern, range-aware version file, which is why local builds were green.

A naïve "drop the range" fix (`find_package(Eigen3 3.4)`) does not work either: Eigen 5.0.1's version file then computes an exclusive upper bound of `3.5.0` from the two-component request and rejects 5.0.1 itself. The only request shape that works on both Eigen 3.4.0 (Ubuntu) and Eigen 5.0.1 (macOS) is *no* version constraint at the `find_package` level, with the supported range enforced manually after the find.

## What Changes

- In `cmake/Dependencies.cmake`, change the Eigen3 call to `find_package(Eigen3)` with no version request, so neither system's `Eigen3ConfigVersion.cmake` quirks gate discovery.
- After `Eigen3_FOUND` is true, add an explicit `if(Eigen3_VERSION VERSION_LESS 3.4 OR Eigen3_VERSION VERSION_GREATER_EQUAL 6) message(FATAL_ERROR ...)` block that enforces the same `3.4 ≤ Eigen < 6` policy the original range encoded.
- Keep the existing "package not found" install-hint `FATAL_ERROR` block (the one that fires when `Eigen3_FOUND` is false). Adjust nothing else in that branch.
- No change to the GTest call (already version-less and working).
- No change to `BUILD_TESTING` gating, `include(GoogleTest)`, or any other discovery.

## Non-Goals

- Bumping Eigen's supported version range (still `>= 3.4`, `< 6`).
- Vendoring Eigen via `FetchContent`, submodules, or a package manager.
- Touching `find_package(GTest)` — it is already version-less and works.
- Editing `.github/workflows/ci.yml` or its `apt-get install` package list.
- Changing `CMakePresets.json` or any other CMake file outside `cmake/Dependencies.cmake`.
- Touching real-time / control-loop code. This change is build-only.

## Capabilities

### New Capabilities
<!-- None. -->

### Modified Capabilities
- `build-system`: The "Third-party dependencies resolved via find_package" requirement currently allows the `find_package` invocation itself to encode the version range. The delta tightens this: for Eigen specifically, the supported version range MUST be enforced by an explicit post-`find_package` check, not by the `find_package` version argument, because system-installed Eigen `Eigen3ConfigVersion.cmake` files vary in their support for CMake 3.19 version-range syntax. A new scenario covers this enforcement path.

## Impact

- **Code**: `cmake/Dependencies.cmake` (only file modified).
- **CI**: `.github/workflows/ci.yml` `build-test` job starts succeeding on `ubuntu-22.04`; no workflow edits required.
- **Local builds**: macOS contributors with Homebrew Eigen 5.0.1 see no behavior change on the happy path. Ubuntu/Linux contributors with `libeigen3-dev` 3.4.0 also see no behavior change on the happy path. On the version-out-of-range failure path, both groups now get a clear "Eigen X.Y.Z is not in the supported range [3.4, 6)" error.
- **RT path**: None — build-system change only, no real-time constraints touched.
- **Specs**: Delta to `build-system` spec only.
- **Dependencies / packages**: No version bumps, no new packages.
