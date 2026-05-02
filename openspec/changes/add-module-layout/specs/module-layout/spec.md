## ADDED Requirements

### Requirement: One source directory per architectural component
The project SHALL organize its non-test C++ source code under per-component directories at `src/<component>/`, where `<component>` is the kebab-case (or snake_case for filesystem compatibility) name of an architectural component identified in `openspec/project.md`. The set of components SHALL include at minimum: `hal`, `kinematics`, `filter`, `safety`, `rt`, `mode`, `common`, `core`. Adding a new architectural component SHALL include adding a corresponding directory in this set; removing a component SHALL include removing its directory.

#### Scenario: A reader navigates from architecture to code
- **WHEN** a contributor reads `openspec/project.md` and identifies the HAL component
- **THEN** they find HAL's source code at `src/hal/` without searching

#### Scenario: A new architectural component is proposed
- **WHEN** a change proposal introduces a new architectural component named (for example) `telemetry`
- **THEN** the proposal SHALL also create `src/telemetry/` and the change is incomplete without it

#### Scenario: Top-level `src/` contains only component directories and the build file
- **WHEN** a maintainer lists the contents of `src/`
- **THEN** the entries are exactly the per-component directories plus `CMakeLists.txt`, with no loose `.cpp` files at the `src/` root

### Requirement: Public headers live under matching component subdirectories
The project SHALL place every public header for component `<component>` under `include/motion_control/<component>/`. The set of subdirectories under `include/motion_control/` SHALL match the set of component directories under `src/`. Consumers SHALL include public headers via `#include <motion_control/<component>/<file>.hpp>`.

#### Scenario: Component directories under src/ and include/motion_control/ stay in sync
- **WHEN** a maintainer audits the layout
- **THEN** for every directory `src/<component>/` there is exactly one `include/motion_control/<component>/`, and vice versa

#### Scenario: A consumer includes a public header
- **WHEN** test code or another component writes `#include <motion_control/hal/hal.hpp>`
- **THEN** the header is resolved against `include/motion_control/hal/hal.hpp` without additional include-path configuration

### Requirement: Sub-namespaces match component directory names
Each component's public symbols SHALL be declared in the C++ namespace `motion_control::<component>`, where `<component>` matches the directory name verbatim (with directory hyphens or other filesystem-only characters mapped to underscores in the namespace where needed). Components SHALL NOT add public symbols to the bare `motion_control::` namespace, except for symbols that pre-date this requirement (currently only `motion_control::identity_matrix()` in the orchestrator) which are grandfathered until they are removed or moved.

#### Scenario: A component declares a public type
- **WHEN** a contributor adds a public type to the filter component
- **THEN** the type is declared inside `namespace motion_control::filter { ... }`

#### Scenario: A new public symbol is reviewed
- **WHEN** a code review finds a new public symbol declared in the bare `motion_control::` namespace
- **THEN** the reviewer requires it to be moved into the appropriate `motion_control::<component>::` namespace, unless it is the grandfathered `identity_matrix()` placeholder

### Requirement: Single static library assembled via target_sources
The build SHALL produce exactly one component-bearing static library, `motion_control_core`, aliased as `motion_control::core`. Every component's `src/<component>/CMakeLists.txt` SHALL contribute its source files to that library via `target_sources(motion_control_core PRIVATE ...)` rather than declaring its own library target. There SHALL NOT be per-component sub-library targets or per-component `motion_control::<component>` alias targets.

#### Scenario: A component's CMakeLists contributes sources only
- **WHEN** a contributor opens any `src/<component>/CMakeLists.txt`
- **THEN** the file uses `target_sources(motion_control_core PRIVATE ...)` to list the component's `.cpp` files, and does NOT call `add_library(motion_control_<component> ...)`

#### Scenario: Top-level src/CMakeLists.txt declares the single library
- **WHEN** a maintainer reads `src/CMakeLists.txt`
- **THEN** it contains exactly one `add_library(motion_control_core STATIC)` call (no source list inline) and a corresponding `add_library(motion_control::core ALIAS motion_control_core)`, followed by `add_subdirectory(...)` calls for each component

#### Scenario: External consumers link a single alias
- **WHEN** test code or external consumer code writes `target_link_libraries(my_app PRIVATE motion_control::core)`
- **THEN** symbols from every component are resolved at link time, because every component's sources are already part of `motion_control_core`

### Requirement: Promoting a component to its own static library is allowed in a future change
A component MAY be promoted out of the single-library shape into its own static library in a future change proposal if it grows large enough that incremental rebuild time becomes a concern, OR if it develops a public surface that benefits from being linked independently. Such a promotion SHALL be its own change proposal, SHALL update this `module-layout` spec, and SHALL preserve the public alias `motion_control::core`'s symbol coverage so external consumers see no API change.

#### Scenario: A component is promoted to its own library
- **WHEN** a future change proposal promotes the `safety` component to a `motion_control_safety` static library
- **THEN** the proposal updates this spec, defines `motion_control::safety` as the alias, makes `motion_control::core` `PUBLIC`-link `motion_control::safety`, and removes `safety`'s direct `target_sources` contribution to `motion_control_core`

#### Scenario: A premature promotion is rejected
- **WHEN** a change proposal asks to promote a component to its own library purely for symmetry or "good practice" without a concrete scale or test-isolation justification
- **THEN** the reviewer rejects the change because the spec requires either a rebuild-time concern or an independent-link-surface concern as justification

### Requirement: Build remains green at every commit
Every commit on the trunk branch SHALL leave the project in a state where `cmake --preset=debug && cmake --build --preset=debug && ctest --preset=debug` succeeds. Adding a new component directory SHALL include the stub source, stub header, and `CMakeLists.txt` necessary to keep this true; partial commits that introduce a directory without the corresponding build wiring are not permitted.

#### Scenario: A component is added in one commit
- **WHEN** a contributor adds `src/telemetry/`, `include/motion_control/telemetry/`, the stub source and header, and the `CMakeLists.txt` wiring in a single commit
- **THEN** `cmake --preset=debug && cmake --build --preset=debug && ctest --preset=debug` succeeds at that commit

#### Scenario: A component is added without build wiring
- **WHEN** a commit adds a new directory under `src/` without updating `src/CMakeLists.txt` or supplying a sub-`CMakeLists.txt`
- **THEN** the commit fails review because the build is not green

### Requirement: Reserved component directories are explicitly marked
A component directory whose architectural design has not yet been decided (currently `mode/`) SHALL still exist with its stub `<component>.cpp`, stub `<component>.hpp`, and a `CMakeLists.txt` that contributes its single stub source to `motion_control_core` via `target_sources`. The stub header SHALL contain a code comment that explicitly notes the component is reserved and that its design is deferred.

#### Scenario: A reader sees the reserved component
- **WHEN** a contributor opens `include/motion_control/mode/mode.hpp`
- **THEN** the file contains a comment explaining that the mode state machine is a deferred architectural decision and pointing at `openspec/project.md` for context
