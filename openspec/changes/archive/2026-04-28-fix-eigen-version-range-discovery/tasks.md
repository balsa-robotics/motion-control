## 1. Update the dependency finder

- [x] 1.1 Edit `cmake/Dependencies.cmake`: change the Eigen3 call from `find_package(Eigen3 3.4...<6)` to `find_package(Eigen3)` (no version argument, no range).
- [x] 1.2 In the same file, immediately below the existing `if(NOT Eigen3_FOUND) message(FATAL_ERROR ...) endif()` block, add a new block: `if(Eigen3_VERSION VERSION_LESS 3.4 OR Eigen3_VERSION VERSION_GREATER_EQUAL 6) message(FATAL_ERROR "Eigen3 ${Eigen3_VERSION} is not supported. Need >= 3.4 and < 6. See README.md.") endif()`. Keep wording distinct from the "not found" install-hint message so the two failure modes are visually distinguishable.
- [x] 1.3 Re-read `cmake/Dependencies.cmake` end-to-end to confirm: the GTest call is unchanged, the `BUILD_TESTING` guard and `include(GoogleTest)` are unchanged, and no other `find_package` invocations regressed.

## 2. Local verification

- [x] 2.1 From the repository root, delete `build/debug/` if present, then run `cmake --preset=debug` on the local macOS dev box (Homebrew Eigen 5.0.1) and confirm configure completes with no errors and the new version-range check does not fire.
- [x] 2.2 Run `cmake --build --preset=debug` and confirm the library and test binaries link.
- [x] 2.3 Run `ctest --preset=debug --output-on-failure` and confirm the existing tests still pass.
- [x] 2.4 Negative-path check (missing Eigen): configure into a throwaway build dir with `CMAKE_IGNORE_PREFIX_PATH=/opt/homebrew` so Eigen is undiscoverable, and confirm the existing "not found" install-hint `FATAL_ERROR` still fires (CMake's underlying diagnostic above, install hint below). Discard the throwaway build dir.
- [x] 2.5 Negative-path check (out-of-range version): in a throwaway build dir, force the version check to fire — for example by passing `-DEigen3_VERSION=2.9.9` after the find via a temporary `set(Eigen3_VERSION 2.9.9)` injection in a private wrapper, OR by temporarily changing the lower bound in the check from `3.4` to `99.0` and re-configuring — and confirm the new "Eigen3 X.Y.Z is not supported. Need >= 3.4 and < 6." `FATAL_ERROR` fires distinctly from the "not found" message. Revert the temporary change afterward.

## 3. Spec sync

- [x] 3.1 Run `openspec validate fix-eigen-version-range-discovery` and confirm no validation errors are reported against the modified `build-system` spec delta.
- [x] 3.2 Hand off to `/opsx:archive` once the change has been merged so the delta is folded back into `openspec/specs/build-system/spec.md`.
