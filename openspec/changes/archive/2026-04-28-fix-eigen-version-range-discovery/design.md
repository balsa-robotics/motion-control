## Context

After landing `fix-ci-dependency-discovery` (drop `CONFIG`/`QUIET` from `find_package`), the `ubuntu-22.04` `build-test` job still fails at configure. The new diagnostic — now visible above the install-hint `FATAL_ERROR` — is:

```
CMake Warning at cmake/Dependencies.cmake:1 (find_package):
  Could not find a configuration file for package "Eigen3" that is compatible
  with requested version range "3.4...<6".

  The following configuration files were considered but not accepted:

    /usr/share/eigen3/cmake/Eigen3Config.cmake, version: 3.4.0
```

CMake located Eigen 3.4.0's `Eigen3Config.cmake` but the package's own `Eigen3ConfigVersion.cmake` rejected the request. CMake 3.19 introduced version-range syntax (`3.4...<6`) and exposes `PACKAGE_FIND_VERSION_RANGE` to the version-check script. Eigen 3.4.0 (Oct 2021) ships a `Eigen3ConfigVersion.cmake` that does not branch on that variable, so when given a range request the script falls through to a state where `PACKAGE_VERSION_COMPATIBLE` is not properly set, and CMake refuses the package.

Local macOS builds pass because Homebrew Eigen 5.0.1 ships a fully range-aware `Eigen3ConfigVersion.cmake` (verified by reading `/opt/homebrew/Cellar/eigen/5.0.1/share/eigen3/cmake/Eigen3ConfigVersion.cmake`, which has explicit `if (PACKAGE_FIND_VERSION_RANGE) ... endif()` handling).

Two systems, two ConfigVersion behaviors:

| System | Eigen version | ConfigVersion handles ranges? | Accepts `find_package(Eigen3 3.4)` (no range)? |
|---|---|---|---|
| ubuntu-22.04 (`libeigen3-dev`) | 3.4.0 | No | Likely yes (script computes `[3.4, 3.5)` upper, 3.4.0 is in range) |
| macOS (Homebrew `eigen`) | 5.0.1 | Yes | **No** (script computes `[3.4, 3.5)` upper, 5.0.1 falls outside) |

There is no `find_package(Eigen3 <something>)` request shape that satisfies both systems, because each rejects the version arguments the other accepts. The robust fix is to make `find_package` version-agnostic and enforce the supported range in CMake code we control.

## Goals / Non-Goals

**Goals:**
- Make CI's `cmake --preset=debug` succeed on `ubuntu-22.04` (`libeigen3-dev` 3.4.0) without changes to the workflow file or the apt package list.
- Keep local macOS builds (Homebrew Eigen 5.0.1) succeeding.
- Preserve the supported-version policy: Eigen `>= 3.4`, `< 6`. The policy is unchanged; only the *enforcement mechanism* moves from `find_package`'s version argument to an explicit post-find check.
- Produce a clear, actionable error message both when Eigen is missing entirely and when its version is outside the supported range.

**Non-Goals:**
- Changing the supported-version policy itself.
- Vendoring Eigen via `FetchContent`, submodules, or any package manager.
- Adding alternative finder backends (pkg-config, vcpkg, Conan).
- Touching `find_package(GTest)` — it is already version-less and works on both systems.
- Editing `CMakePresets.json`, `.github/workflows/ci.yml`, or any other CMake/CI file.
- Touching real-time / control-loop code. Build-only change.

## Decisions

### D1: Drop the version request from `find_package(Eigen3 ...)`

Change the call from `find_package(Eigen3 3.4...<6)` to `find_package(Eigen3)`. With no version argument, neither `PACKAGE_FIND_VERSION` nor `PACKAGE_FIND_VERSION_RANGE` is set, so the package's `Eigen3ConfigVersion.cmake` short-circuits and returns `PACKAGE_VERSION_COMPATIBLE = TRUE` for any version. This sidesteps both Eigen 3.4.0's lack of range support and Eigen 5.0.1's strict "increment last component" upper bound on non-range requests.

**Alternatives considered:**
- `find_package(Eigen3 3.4)` (drop the upper bound only). Fails on macOS Eigen 5.0.1 because its ConfigVersion computes the exclusive upper bound from the request's component count, yielding `[3.4, 3.5)` and rejecting 5.0.1.
- `find_package(Eigen3 3.4 EXACT)`. Same problem and stricter — rejects everything except 3.4.0.
- Distro-specific `HINTS` / `PATHS` to point at Ubuntu's Eigen install. Brittle; does not address the version-range incompatibility, only path discovery.
- Globally setting `CMAKE_FIND_PACKAGE_PREFER_CONFIG=OFF` to coax MODULE-mode discovery. Eigen ships no MODULE finder on either system; CMake doesn't bundle one. Has no effect here.
- Patching Eigen 3.4.0's `Eigen3ConfigVersion.cmake` in place on the runner. Modifies system files; not portable; fragile across runner image updates.

### D2: Enforce the supported version range in our CMake code

After `find_package(Eigen3)` succeeds, add:

```cmake
if(Eigen3_VERSION VERSION_LESS 3.4 OR Eigen3_VERSION VERSION_GREATER_EQUAL 6)
  message(FATAL_ERROR
    "Eigen3 ${Eigen3_VERSION} is not supported. "
    "Need >= 3.4 and < 6. See README.md."
  )
endif()
```

The check uses `VERSION_LESS` / `VERSION_GREATER_EQUAL`, which work consistently across CMake 3.24+ and require no special version-range support from the Eigen package. The bound semantics (`>= 3.4`, `< 6`) are identical to what the original `3.4...<6` range encoded.

**Alternatives considered:**
- A `version-check` helper function in a new CMake module. Premature for one dependency; this is a 4-line `if(...)` block.
- Using `Eigen3_VERSION_MAJOR`/`_MINOR` arithmetic. The string comparison via `VERSION_LESS` is more idiomatic in CMake and handles 3.4.x patch versions correctly.

### D3: Keep the existing `if(NOT Eigen3_FOUND)` install-hint block

The user-facing contract from the `build-system` spec requires that a missing dependency produce a fatal error naming the package and pointing to the README. That contract is unchanged; the existing `if(NOT Eigen3_FOUND) message(FATAL_ERROR ...)` block continues to fire when no Eigen is installed at all. Only the version-range enforcement moves to a separate, post-find block.

### D4: Leave the `GTest` call alone

`find_package(GTest)` already passes no version argument and works on both systems. There is no analogous failure mode to fix.

### D5: Distinct error messages for "missing" vs. "wrong version"

The two failure paths are reported separately:

- `Eigen3_FOUND` is false → existing FATAL_ERROR with install instructions for Ubuntu and macOS.
- `Eigen3_FOUND` is true but `Eigen3_VERSION` is out of range → new FATAL_ERROR naming the version found and the supported range.

This matters in practice: an out-of-range Eigen tells the contributor to bump or pin a system package, not to install one. Conflating both into a single message would be misleading.

## Risks / Trade-offs

- **[Risk] An Eigen version below 3.4 on a contributor's system would now be located by `find_package` (which sets `Eigen3_FOUND = TRUE`) before our version check runs.** → Mitigation: The version-check block fires immediately afterward and produces a clear "not supported" FATAL_ERROR. The build still fails at configure time, just with a different message than before. No silent acceptance.
- **[Risk] If Eigen 6 ships and a contributor has it installed, the build would fail with our explicit "out of range" message rather than CMake's range-mismatch message.** → Accepted: this is intended. The version-policy upper bound is a deliberate guard against breaking ABI/API changes; we want the explicit message.
- **[Risk] A future Eigen release may change `Eigen3_VERSION` formatting in ways that break `VERSION_LESS` comparisons.** → Mitigation: CMake's `VERSION_*` operators handle dotted decimal versions and have been stable across CMake 3.x; both Ubuntu and Homebrew Eigen versions seen in practice (3.4.0, 5.0.1) parse correctly. If a future release uses a non-numeric suffix we would see it at configure time on that platform.
- **[Trade-off] We give up the syntactic clarity of `find_package(Eigen3 3.4...<6)`.** → Accepted: the readability of the inline range is appealing but it is unenforceable across the systems we actually target. The 4-line explicit check is only marginally less readable and trades nothing for portability.

## Migration Plan

1. Edit `cmake/Dependencies.cmake` per D1, D2, D3 (a single `find_package` line change plus a new 4-line `if(...)` block).
2. Re-run `cmake --preset=debug` locally on macOS (Homebrew Eigen 5.0.1) to confirm the happy path still configures and links.
3. Push to a branch; verify the GitHub Actions `build-test` job goes green on `ubuntu-22.04`.
4. No data migration. Rollback is a single-file `git revert` if needed; the previous (broken-on-CI) state was the prior commit.

## Open Questions

None blocking implementation. If a future Eigen release changes the public API in a way that breaks our code, the upper-bound guard (`< 6`) will fail loudly at configure time and we will respond with a separate change.
