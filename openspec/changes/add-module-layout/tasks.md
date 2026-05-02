## 1. Rewire `src/CMakeLists.txt` for the single-library shape

- [x] 1.1 Rewrite `src/CMakeLists.txt` so it: keeps the existing `motion_control_warnings` INTERFACE library and `motion_control::warnings` alias; declares `add_library(motion_control_core STATIC)` with no source list inline; declares the `motion_control::core` alias; sets `target_include_directories(motion_control_core PUBLIC $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/include>)`; sets `target_link_libraries(motion_control_core PUBLIC Eigen3::Eigen PRIVATE motion_control::warnings)`; then calls `add_subdirectory(...)` for `hal`, `kinematics`, `filter`, `safety`, `rt`, `mode`, `common`, and `core` in that order. After this rewrite, the build will fail to configure until the component directories from section 2 exist — this is expected and the next section completes the change.

## 2. Create the eight component directories

For each component, create the directory plus three files: stub header, stub source, and a tiny `CMakeLists.txt` whose only job is `target_sources(motion_control_core PRIVATE <component>.cpp)`. Each task is end-to-end so a partial commit never breaks the build.

The stub header pattern is:

```cpp
#pragma once
namespace motion_control::<component> {
// Layout placeholder. Real declarations land in subsequent proposals.
}  // namespace motion_control::<component>
```

The stub source pattern is:

```cpp
#include "motion_control/<component>/<component>.hpp"
namespace motion_control::<component> {
inline constexpr int placeholder_v = 0;
}  // namespace motion_control::<component>
```

The per-component `CMakeLists.txt` is exactly:

```cmake
target_sources(motion_control_core
  PRIVATE
    <component>.cpp
)
```

- [x] 2.1 `hal`: create `include/motion_control/hal/hal.hpp`, `src/hal/hal.cpp`, `src/hal/CMakeLists.txt` per the patterns above.
- [x] 2.2 `kinematics`: same pattern. Combined dir for FK + IK; do not split.
- [x] 2.3 `filter`: same pattern.
- [x] 2.4 `safety`: same pattern.
- [x] 2.5 `rt`: same pattern.
- [x] 2.6 `mode`: same pattern, **plus** the stub header (`include/motion_control/mode/mode.hpp`) carries a comment that explicitly notes the mode state machine is a deferred architectural decision and points at `openspec/project.md` for context (per the spec's "Reserved component directories" requirement).
- [x] 2.7 `common`: same pattern.
- [x] 2.8 `core`: relocate the existing placeholder. Move `src/core.cpp` → `src/core/core.cpp` (preserve content; `identity_matrix()` stays in the bare `motion_control::` namespace, grandfathered per design D5), move `include/motion_control/core.hpp` → `include/motion_control/core/core.hpp`, and create `src/core/CMakeLists.txt` whose only contribution is `target_sources(motion_control_core PRIVATE core.cpp)`. Update `tests/smoke_test.cpp` to `#include <motion_control/core/core.hpp>`.

## 3. Local verification

- [x] 3.1 Delete `build/debug/`, run `cmake --preset=debug` and confirm configure succeeds.
- [x] 3.2 Run `cmake --build --preset=debug` and confirm `motion_control_core` (the single static library) plus `smoke_test` build clean. The library archive should contain a TU per component.
- [x] 3.3 Run `ctest --preset=debug --output-on-failure` and confirm `smoke.identity_matrix_is_identity` still passes.
- [x] 3.4 Sanity-check the layout: confirm `ls src/` shows exactly the eight component dirs plus `CMakeLists.txt`, and `ls include/motion_control/` shows exactly the eight component dirs and nothing else.

## 4. Spec sync

- [x] 4.1 Run `openspec validate add-module-layout` and confirm no validation errors against the new `module-layout` spec.
- [ ] 4.2 Hand off to `/opsx:archive` once the change has been merged so the new `module-layout` capability spec is folded into `openspec/specs/module-layout/spec.md`.
