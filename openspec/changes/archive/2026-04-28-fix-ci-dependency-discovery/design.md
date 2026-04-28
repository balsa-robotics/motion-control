## Context

`cmake/Dependencies.cmake` currently calls:

```cmake
find_package(Eigen3 3.4...<6 CONFIG QUIET)
if(NOT Eigen3_FOUND)
  message(FATAL_ERROR "Eigen3 (>= 3.4) not found. ...")
endif()

if(BUILD_TESTING)
  find_package(GTest QUIET)
  if(NOT GTest_FOUND)
    message(FATAL_ERROR "GoogleTest not found. ...")
  endif()
endif()
```

Two properties combine to break the CI `build-test` job on `ubuntu-22.04`:

1. **`CONFIG`** restricts discovery to a CONFIG-mode search (`<Pkg>Config.cmake` / `<lower>-config.cmake`). It skips MODULE mode entirely, so any `FindEigen3.cmake` shipped alongside Eigen or in CMake's own modules is ignored. If the system's CONFIG file isn't found through CMake's default search heuristics on a given runner, discovery fails outright.
2. **`QUIET`** suppresses CMake's own diagnostic ("considered the following paths… version `X` did not satisfy `Y`…"), so the only output is our generic `FATAL_ERROR` install hint, which is not enough to tell whether the package is missing, in the wrong path, or version-mismatched.

The existing `build-system` spec already states the contract: deps SHALL be resolved with `find_package` "either CMake CONFIG or MODULE mode, whichever the package provides," and the failure SHALL identify the missing package. The current code is stricter than the spec on input (CONFIG-only) and weaker than the spec on output (no real diagnostic above our message).

CI image: `ubuntu-22.04` with `libeigen3-dev` (3.4.0), `libgtest-dev`, `libgmock-dev`, CMake 3.28 from `lukka/get-cmake`.

## Goals / Non-Goals

**Goals:**
- Make CI's `cmake --preset=debug` succeed against the existing apt package set, with no workflow changes.
- Honor the `build-system` spec contract by allowing both MODULE and CONFIG resolution.
- When discovery does fail, surface CMake's underlying reason (search paths considered, version found vs. requested) above our existing install-hint block.
- Keep the `FATAL_ERROR` install-hint blocks intact so users still see actionable Ubuntu/macOS commands.

**Non-Goals:**
- Vendoring Eigen or GTest via `FetchContent`, submodules, or a package manager.
- Changing pinned versions of Eigen, GTest, CMake, gcc, or the runner image.
- Refactoring `Dependencies.cmake` beyond the two `find_package` calls (e.g., no extraction into a helper function).
- Touching `CMakePresets.json`, the build job's apt list, or any other CI step.

## Decisions

### D1: Drop `CONFIG` from both `find_package` calls

Use the default discovery order (MODULE first, then CONFIG). Eigen 3.4's Debian/Ubuntu package ships both a `FindEigen3.cmake`-style module and a CONFIG file; GTest on Ubuntu provides a `FindGTest` module shipped with CMake itself plus a CONFIG file from `libgtest-dev`. Allowing either keeps the call resilient to whichever the runner exposes.

**Alternatives considered:**
- Keep `CONFIG` and add explicit `HINTS` / `PATHS` for Ubuntu's `/usr/lib/cmake/eigen3` — brittle; bakes a distro-specific path into a cross-platform finder.
- Force `MODULE` only — works for CMake's bundled `FindGTest`, but Eigen upstream has been moving toward CONFIG; would lock us out of newer installations.
- Use `CMAKE_FIND_PACKAGE_PREFER_CONFIG=ON` globally — broader blast radius than necessary; affects every future `find_package` call.

### D2: Drop `QUIET` from both `find_package` calls

`QUIET` only buys us cleaner "happy path" log output, which we don't need in a one-line dependency check. Removing it makes CMake print its standard "could not find package configuration file" diagnostic with the considered paths and version data, immediately above our `FATAL_ERROR`. That single line is usually enough to triage a future failure without re-running with `--debug-find`.

**Alternatives considered:**
- Keep `QUIET` and add `--debug-find` to the CI invocation — noisier on every run; doesn't help local contributors.
- Keep `QUIET` and append our own "Considered: …" string — duplicates what CMake already emits when not quieted.

### D3: Preserve the `FATAL_ERROR` install-hint blocks

The user-facing contract from the `build-system` spec requires that the missing package be named with install instructions. Removing the `if(NOT <Pkg>_FOUND) message(FATAL_ERROR ...)` blocks would lose that. Keep them; they now print *below* CMake's underlying diagnostic.

### D4: Keep the GTest finder gated on `BUILD_TESTING`

No change to the `if(BUILD_TESTING)` wrapping. The `release` preset still skips GTest discovery entirely.

### D5: Keep the Eigen version range `3.4...<6`

The `README.md` minimum-version table lists Eigen 3.4 as the floor; the upper bound of `<6` is a future-proofing guard. Both stay. Version-range syntax requires CMake ≥ 3.19 and we already require 3.24, so this is safe in MODULE mode too.

## Risks / Trade-offs

- **[Risk] Removing `QUIET` slightly changes happy-path log output.** → Mitigation: the added lines are short and only printed once per configure; this is normal CMake behavior and is what users see for every other dependency in larger projects.
- **[Risk] MODULE-mode `FindEigen3.cmake` may not define the modern `Eigen3::Eigen` imported target on every system.** → Mitigation: Ubuntu 22.04's `libeigen3-dev` and macOS's Homebrew `eigen` both provide `Eigen3::Eigen` via either the module or the CONFIG file; if a runner ships only an old module, the existing `FATAL_ERROR` will still fire and the user is told to install the documented version. Source files that consume Eigen via `Eigen3::Eigen` already exist; if a regression appears we'll see it at link time on that specific platform, not silently.
- **[Risk] Diagnostic still doesn't pinpoint the cause on some failures.** → Mitigation: this change is the cheapest first step. If a future failure is still opaque, we can add `--debug-find` to the CI configure step in a follow-up; we're not painting ourselves into a corner.
- **[Trade-off] We don't pin Eigen via `FetchContent`.** → Accepted: vendoring is a much larger change with its own caching, license, and build-time costs. The proposal's non-goals call this out explicitly.

## Migration Plan

1. Edit `cmake/Dependencies.cmake` per D1–D3.
2. Re-run `cmake --preset=debug` locally on macOS (Homebrew Eigen + GTest) to confirm the happy path still configures.
3. Push to a branch; verify the GitHub Actions `build-test` job goes green on `ubuntu-22.04`.
4. No data migration, no rollback complexity — revert is a single-file `git revert` if needed.

## Open Questions

None blocking implementation. If CI still fails after this change, the now-visible CMake diagnostic will guide the next step (likely adding `HINTS` for a specific path or re-examining the runner image's package layout).
