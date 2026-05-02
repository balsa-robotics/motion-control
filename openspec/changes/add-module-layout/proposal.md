## Why

The architecture-design session that just landed in `openspec/project.md` named the components this module is built from (HAL, parallel-link kinematics, filter, safety pipeline, RT thread topology, mode state machine, common types, orchestrator) but the source tree does not yet reflect any of them — `src/core.cpp` and `include/motion_control/core.hpp` carry an `identity_matrix()` placeholder from the initial scaffold, and `motion_control::core` is a single static library with no internal structure.

Subsequent component proposals (mock HAL, filter, FK/IK, safety plugin contract, etc.) need a stable place to land. Without a layout decision now, each component proposal will re-litigate "where does this go" and the conventions will drift. This proposal commits the directory tree, the CMake sub-library shape, the include/namespace convention, and codifies them as a `module-layout` capability spec so future contributors and proposals follow the same rules.

## What Changes

- Add per-component source directories under `src/`: `hal/`, `kinematics/`, `filter/`, `safety/`, `rt/`, `mode/`, `common/`, `core/`. Each directory holds its own `CMakeLists.txt`, but the build remains a single `motion_control_core` static library — each component's `CMakeLists.txt` contributes its sources to that library via `target_sources(motion_control_core PRIVATE ...)`. No per-component sub-library, no per-component alias.
- Add matching public-header directories under `include/motion_control/<component>/`. Each component's public header surface lives there; `#include <motion_control/<component>/<file>.hpp>` is the consumer pattern.
- Establish the convention that each component lives in the sub-namespace `motion_control::<component>`.
- Move the existing placeholder `src/core.cpp` and `include/motion_control/core.hpp` into `src/core/core.cpp` and `include/motion_control/core/core.hpp` so the layout is uniform from day one. The existing `identity_matrix()` placeholder stays put inside `motion_control::` (grandfathered) until the orchestrator gets real content in a later proposal.
- Update `src/CMakeLists.txt` so it creates the single `motion_control_core` STATIC library (and the existing `motion_control_warnings` INTERFACE), then `add_subdirectory(...)` each component to let it contribute its source list. The public alias `motion_control::core` continues to point at this library; external consumers see no API change.
- Each stub source file contains a token symbol (e.g., a `constexpr` namespace-scope value) so each component's `.cpp` is a non-empty TU and the namespace declaration has a real translation-unit home.
- Update `tests/smoke_test.cpp`'s include path to follow the new `motion_control/core/core.hpp` location. Test reorganization (per-component test directories) is deferred to component proposals.
- Add a new capability spec `openspec/specs/module-layout/spec.md` (created via the change's delta at `specs/module-layout/spec.md`) capturing requirements: per-component dirs, sub-namespaces, public-header layout, the single-library + `target_sources` pattern, reserved-component marking, and build-green-at-every-commit.
- Reserve `src/mode/` and `include/motion_control/mode/` even though the mode state machine itself is a deferred decision in `project.md`. The directory exists with a stub `mode.cpp` and `mode.hpp`; the header carries an explicit comment that the design is deferred.
- Include in the spec an explicit escape hatch: a component MAY be promoted to its own static library in a future change proposal if it grows large enough or develops a need for separate test isolation. Splitting later is a tractable refactor; pre-splitting now is not justified at the project's current scale.

## Non-Goals

- Implementing any component's actual logic — no HAL backend, no FK/IK math, no filter, no safety plugin interface, no thread topology code. This is layout only.
- Designing the safety plugin composition contract, mode state machine, state publish primitive, or any of the deferred architectural decisions listed in `project.md`. They each get their own proposal when the relevant component lands.
- Reorganizing the existing flat `tests/` directory into per-component subdirectories. Component proposals will add their own test files; we will revisit a hierarchical `tests/` layout when the flat one becomes unwieldy.
- Changing CMake target naming for external consumers. `motion_control::core` and `motion_control::warnings` continue to be the public aliases.
- Removing the `identity_matrix()` placeholder. It still serves the smoke test and acts as an "is the library wired up correctly" canary; it will be removed when the orchestrator gets real content.
- RT path: this change does not touch the RT path. It is build-and-layout only.

## Capabilities

### New Capabilities
- `module-layout`: codifies how the source tree is organized — per-component directories under `src/` and `include/motion_control/`, sub-namespaces matching component directory names, a single `motion_control_core` static library that every component contributes its sources to via `target_sources`, and reserved-component conventions for deferred-design components such as `mode/`. Includes an explicit allowance for promoting a component to its own static library in a future change if scale or test-isolation needs justify it.

### Modified Capabilities
<!-- None. The existing build-system spec stays compatible: the public alias, the include-path-rooted-at-include/, and BUILD_TESTING gating all continue to hold. -->

## Impact

- **Code**: `src/CMakeLists.txt` rewired; new `src/<component>/` directories with stub sources and per-component `CMakeLists.txt`; new `include/motion_control/<component>/` directories with stub public headers; existing `src/core.cpp` and `include/motion_control/core.hpp` move into `src/core/` and `include/motion_control/core/`; `tests/smoke_test.cpp` include path updated.
- **CI**: no workflow changes needed. The existing `build-test` job continues to pass against the new layout.
- **Local builds**: `cmake --preset=debug` continues to configure, build, and test cleanly. External consumers linking `motion_control::core` see no API change.
- **RT path**: untouched.
- **Specs**: new `module-layout` capability spec added; no existing specs modified.
- **Dependencies / packages**: no version bumps, no new packages.
- **Future proposals**: every subsequent component proposal (mock HAL, filter, kinematics, etc.) drops content into its pre-allocated directory. No "where does this go" debate per proposal.
