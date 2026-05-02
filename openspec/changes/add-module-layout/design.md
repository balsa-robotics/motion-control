## Context

The architecture-design session captured in `openspec/project.md` settled the component vocabulary for this module:

```
HAL  ·  parallel-link kinematics (FK/IK)  ·  command filter  ·
safety pipeline (pre-IK + post-IK plugin stations)  ·
RT thread topology  ·  mode state machine (deferred)  ·
shared types  ·  orchestrator
```

The current source tree carries none of this. It is the original scaffold:

```
src/                              include/motion_control/
  core.cpp        ── identity_      core.hpp
                     matrix()
  CMakeLists.txt  ── builds
                     motion_control::core
tests/
  smoke_test.cpp  ── links
                     motion_control::core
```

Subsequent proposals will land mock HAL, filter, FK/IK, the safety plugin contract, and so on. Each will need a directory and a sub-library to live in. Picking those names and shapes once, now, avoids each later proposal re-deriving the same convention. Codifying the rules as a capability spec turns "the convention" into something reviewable instead of folklore.

## Goals / Non-Goals

**Goals:**
- One directory per architectural component, with names that match the vocabulary in `project.md`. A reader who knows the architecture can find the code without grep.
- One static sub-library per component. External consumers continue to link a single alias (`motion_control::core`) and transitively get everything; the granularity is internal.
- A namespace convention (`motion_control::<component>`) that mirrors the directory tree, so include path, namespace, and library name are all derivable from each other.
- A capability spec (`module-layout`) that future proposals are validated against. Adding a new component without a directory becomes a spec violation, not a code-review oversight.
- Build green at every commit. The smoke test continues to pass.

**Non-Goals:**
- Component implementation. No HAL backend, no FK math, no filter, no plugin interface design.
- Test reorganization beyond fixing the include path. Per-component test directories arrive when there are per-component tests.
- New CMake macros, helper functions, or build-system abstractions. Each component's `CMakeLists.txt` is plain and ~10 lines.
- Touching the RT path or any production code.
- Resolving the deferred architectural decisions listed in `project.md`. The `mode/` directory is a placeholder that anchors a name; it does not commit to a state machine shape.

## Decisions

### D1: Eight component directories

```
src/                          include/motion_control/
  hal/                          hal/
  kinematics/                   kinematics/
  filter/                       filter/
  safety/                       safety/
  rt/                           rt/
  mode/                         mode/
  common/                       common/
  core/                         core/
```

Names derive directly from `project.md`'s vocabulary:

| Dir | Component (per `project.md`) |
|---|---|
| `hal/` | HAL — per-cycle bus API, mock + CAN-FD + EtherCAT impls live here |
| `kinematics/` | Parallel-link solver (IK closed-form + FK iterative) |
| `filter/` | Command filter (LPF + interpolation, pre-IK only) |
| `safety/` | Safety pipeline (pre-IK + post-IK stations, plugins) |
| `rt/` | RT thread topology, scheduling, priority/affinity, state hand-off |
| `mode/` | Mode state machine (deferred — placeholder dir only) |
| `common/` | Shared types: joint state, commands, time, etc. |
| `core/` | Orchestrator: owns threads and wires the pipeline; the public face |

**Alternatives considered:**
- Splitting `kinematics/` into `fk/` and `ik/` — rejected. They share types and helpers; one component, two functions. Splitting now would force premature interface decisions about what they share.
- Renaming `core/` to `engine/` or `runtime/` to free up the word "core" — rejected. The existing `motion_control::core` alias already means "the orchestrator-with-everything-linked"; renaming the directory while keeping the alias would be confusing. The alias is the canonical name; the directory follows.
- A flat `src/` with files prefixed by component (`hal_*.cpp`, `kinematics_*.cpp`) — rejected. Doesn't scale beyond a handful of files per component, and every file has to repeat the prefix.
- Creating directories only for components that have content today (skipping `mode/`, `rt/`, etc.) — rejected. We want the spec to describe the full layout up front so subsequent proposals know the names. Reserving an empty directory now is cheaper than agreeing on the name later under deadline pressure.

### D2: A single `motion_control_core` STATIC library that every component contributes to

The build produces one static library, `motion_control_core`, aliased as `motion_control::core` (preserving the existing public alias). Each component's `src/<component>/CMakeLists.txt` is a small manifest that uses `target_sources` to add its files to that library — there are no per-component sub-libraries, no per-component aliases.

Top-level `src/CMakeLists.txt`:

```cmake
add_library(motion_control_warnings INTERFACE)
target_compile_options(motion_control_warnings INTERFACE
  -Wall -Wextra -Wpedantic
  $<$<BOOL:${MOTION_CONTROL_WERROR}>:-Werror>
)
add_library(motion_control::warnings ALIAS motion_control_warnings)

add_library(motion_control_core STATIC)
add_library(motion_control::core ALIAS motion_control_core)

target_include_directories(motion_control_core
  PUBLIC  $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/include>
)
target_link_libraries(motion_control_core
  PUBLIC  Eigen3::Eigen
  PRIVATE motion_control::warnings
)

add_subdirectory(hal)
add_subdirectory(kinematics)
add_subdirectory(filter)
add_subdirectory(safety)
add_subdirectory(rt)
add_subdirectory(mode)
add_subdirectory(common)
add_subdirectory(core)
```

Each per-component `src/<component>/CMakeLists.txt` collapses to:

```cmake
target_sources(motion_control_core
  PRIVATE
    hal.cpp
)
```

That's the entire file. Adding a new file to a component is a one-line edit there.

Why this shape, not per-component libraries:

- **Project scale.** With ~1 cpp/hpp pair today and a target maturity of ~5–15k LOC, per-component static libraries add boilerplate that does not earn its keep. Field practice (Lakos's *Large-Scale C++ Software Design*, BSL/folly/Boost-style organization) advises matching build granularity to project scale and starting coarser than feels right; promoting a component to its own library later is cheap, demoting fine ones is not.
- **Boilerplate cost.** Each per-component sub-library would carry `add_library(... STATIC ...)`, an alias declaration, `target_include_directories`, `target_link_libraries(... motion_control::warnings)`, and possibly an Eigen link — ~10 lines × 8 components = 80 lines of repetitive build code. The single-library version is 3 lines per component.
- **Benefits we are not actually getting.** The original case for sub-libraries was test-link granularity. At our scale the link-time difference between linking `motion_control::core` (everything) vs `motion_control::hal` (one component) is microseconds and never user-visible.
- **Modern CMake idiom.** `target_sources` (CMake ≥ 3.13) is purpose-built for this: assemble a library from source files contributed by subdirectories without spawning a sub-library per directory.

**Escape hatch.** The `module-layout` spec includes an explicit "MAY" clause: a component CAN be promoted to its own static library in a future change proposal if (a) it grows large enough that incremental rebuild time becomes a concern, or (b) it develops a public surface that benefits from being linked independently. The default is the single-library shape; promotion is a tractable refactor when the situation actually justifies it.

**Alternatives considered:**
- Per-component `STATIC` sub-libraries with a `motion_control::<component>` alias each, plus an aggregating `PUBLIC` link in the orchestrator. *(This was the original D2.)* Rejected for the reasons above — premature granularity for a project of this size.
- Per-component `INTERFACE` libraries (header-only style). Rejected — components are not header-only; they will have implementation files.
- Per-component `OBJECT` libraries archived into one static library at the top. Rejected — `OBJECT`'s symbol-visibility quirks and the extra library type are not worth the marginal benefit over `target_sources`.
- Single `STATIC` library with all sources listed in the top-level `src/CMakeLists.txt` (no per-component `CMakeLists.txt`). *Defensible.* Rejected only because per-component `CMakeLists.txt` keeps file ownership local to the component dir — adding a file means editing one small file in one place, not editing the top-level. The boilerplate is genuinely small (3 lines per file).

### D3: Sub-namespace per component

Every component's public symbols live in `motion_control::<component>::…`:

```cpp
// include/motion_control/hal/hal.hpp
namespace motion_control::hal {
  // ...
}
```

The orchestrator's symbols (formerly the bare `motion_control::` namespace, e.g., `motion_control::identity_matrix()`) keep their existing un-nested form for now (`motion_control::identity_matrix()` stays put). When the orchestrator gets real content, it will adopt `motion_control::core::…` or stay in the bare namespace; that decision lives with the orchestrator proposal, not this one.

**Alternatives considered:**
- Flat namespace, prefix conventions instead. Rejected — sub-namespaces are the C++ idiom; ADL works correctly; no ambiguity at call sites.
- Anonymous namespaces inside `.cpp`s only. Rejected — components have public surfaces; they need a stable public namespace.

### D4: Stub source + header per component

Each component starts with one `.cpp` and one `.hpp`. The source contributes a token symbol to give the namespace a real translation-unit home; the header declares the namespace so consumers can `#include` it:

```cpp
// src/hal/hal.cpp
#include "motion_control/hal/hal.hpp"

namespace motion_control::hal {
inline constexpr int placeholder_v = 0;
}  // namespace motion_control::hal
```

```cpp
// include/motion_control/hal/hal.hpp
#pragma once

namespace motion_control::hal {
// Layout placeholder. Real declarations land in subsequent proposals.
}  // namespace motion_control::hal
```

Real content replaces these placeholders when each component proposal lands. Empty-archive concerns from the per-sub-library design no longer apply (we have one library with eight TUs), but having one `.cpp` per component is still useful: it gives the component a single canonical place where future implementation lands, and it is what each component's `target_sources` is referencing.

**Alternatives considered:**
- Header-only stubs (no `.cpp`). Rejected — `target_sources` in each per-component `CMakeLists.txt` then references a phantom file or has nothing to do, and adding the first real source later requires touching the build wiring as well. Starting every component with one `.cpp` keeps the pattern uniform.
- A shared "everything-empty" stub source pulled in via every component. Rejected — couples components at a fundamental level for no reason.

### D5: Move the existing placeholder into `src/core/`

The current `src/core.cpp` and `include/motion_control/core.hpp` move to `src/core/core.cpp` and `include/motion_control/core/core.hpp`. The smoke test's include path updates from `motion_control/core.hpp` to `motion_control/core/core.hpp`. The `identity_matrix()` symbol stays in the bare `motion_control::` namespace; we are not retroactively re-namespacing scaffolding code in this proposal.

**Alternatives considered:**
- Delete the placeholder entirely and adjust the smoke test to test something component-specific. Rejected — the smoke test currently asserts `identity_matrix()` is identity, which is a meaningful "the build is wired up" canary. Deleting it without a replacement leaves no end-to-end signal.
- Leave the placeholder where it is (at `src/core.cpp` and `include/motion_control/core.hpp`) outside the new layout. Rejected — the layout is supposed to be uniform; carving an exception for the placeholder undermines the spec.

### D6: `motion_control::core` continues to be the single public alias

External consumers link `motion_control::core`. With the single-library shape from D2, this is simply the alias for `motion_control_core`, which contains every component's sources directly — no aggregation logic, no transitive `PUBLIC`-link list to maintain. We do not introduce `motion_control::all` or any other alias.

The existing `build-system` spec requirement — "single CMake target (`motion_control::core`) whose `INTERFACE_INCLUDE_DIRECTORIES` points at `include/`" — continues to hold. We do not modify that spec.

### D7: Tests stay flat in `tests/` for now

The current `tests/smoke_test.cpp` and `tests/CMakeLists.txt` remain. We update only the include path in the smoke test (D5). When the first per-component test arrives in a component proposal, that proposal can either drop a new file into the flat `tests/` or introduce a per-component subdirectory. We do not pre-emptively reorganize.

**Alternatives considered:**
- Reorganize `tests/` into `tests/hal/`, `tests/kinematics/`, etc. now, with empty placeholders. Rejected — empty test directories add nothing, and CMake's `gtest_discover_tests` invocation already operates per-binary; we can add per-component test binaries when there's something to put in them.

## Risks / Trade-offs

- **[Risk] Future contributors add a component directory without updating the spec** → Mitigation: the `module-layout` spec includes a scenario asserting that every directory under `src/` has a matching directory under `include/motion_control/` and a matching `target_sources(motion_control_core PRIVATE ...)` contribution, which is mechanically auditable.
- **[Risk] Reserved `mode/` directory implies a mode design exists when it does not** → Mitigation: the spec text and the directory's stub header explicitly note that mode is reserved-but-deferred; the placeholder header documents this in a comment so a reader of the code (not just the spec) sees it.
- **[Risk] A component genuinely outgrows the single-library shape** (large, separate-test-isolation, separate-public-surface needs) → Mitigation: the spec includes an explicit allowance for promoting a component to its own static library in a future change proposal. The default shape is the single library; the escape hatch is documented and tractable.
- **[Trade-off] We commit to component names before any of them have implementation experience.** → Accepted: the names come from `project.md`'s vocabulary, which itself came from the dedicated design session. If a name turns out wrong (e.g., `rt/` should have been `runtime/`), that's a single rename in a follow-up proposal. The cost of leaving names unspecified now is higher: every component proposal re-litigates the question.
- **[Trade-off] Eight stub `.cpp` files add ~tens of ms each to a clean build.** → Accepted: ~8 stub TUs add negligible CI time; the structural payoff (uniform component shape, predictable place for first real source to land) is worth it.

## Migration Plan

1. Create the eight `src/<component>/` directories, each with a `CMakeLists.txt`, stub `<component>.cpp`, and matching `include/motion_control/<component>/<component>.hpp`.
2. Move `src/core.cpp` and `include/motion_control/core.hpp` into `src/core/core.cpp` and `include/motion_control/core/core.hpp`. Update the include in `tests/smoke_test.cpp`.
3. Replace `src/CMakeLists.txt` to add_subdirectory each component and to wire the orchestrator's `PUBLIC` link list.
4. Add `openspec/specs/module-layout/spec.md` (via the change's `specs/module-layout/spec.md` delta).
5. Configure, build, and test on macOS (Homebrew Eigen, AppleClang) and confirm green. CI will exercise the Linux side.
6. Validate the change with `openspec validate add-module-layout`.

## Open Questions

None blocking. Adjacent topics (orchestrator namespace shape, per-component test reorganization, plugin contract for safety, mode state machine, state publish primitive) are all out of scope and tracked in `project.md`'s "Deferred architectural decisions".
