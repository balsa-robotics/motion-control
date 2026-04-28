## 1. Update the dependency finder

- [x] 1.1 Edit `cmake/Dependencies.cmake`: change the Eigen3 call to `find_package(Eigen3 3.4...<6)` (drop both `CONFIG` and `QUIET`); leave the `if(NOT Eigen3_FOUND) message(FATAL_ERROR ...)` install-hint block unchanged.
- [x] 1.2 In the same file, change the GTest call to `find_package(GTest)` (drop `QUIET`); leave the `if(NOT GTest_FOUND) message(FATAL_ERROR ...)` install-hint block and the surrounding `if(BUILD_TESTING)` guard unchanged.
- [x] 1.3 Re-read `cmake/Dependencies.cmake` end-to-end to confirm no other `find_package` calls regressed and that the file still ends with `include(GoogleTest)` inside the `BUILD_TESTING` block.

## 2. Local verification

- [x] 2.1 From the repository root, delete `build/debug/` if present, then run `cmake --preset=debug` on the local macOS dev box (Homebrew Eigen + GoogleTest) and confirm configure completes with no errors.
- [x] 2.2 Run `cmake --build --preset=debug` and confirm the library and test binaries link.
- [x] 2.3 Run `ctest --preset=debug --output-on-failure` and confirm the existing tests still pass.
- [x] 2.4 Negative-path check: temporarily rename or unset Eigen so discovery fails, run `cmake --preset=debug`, and confirm the output now contains CMake's own "Could not find a package configuration file"-style diagnostic *above* the project's `FATAL_ERROR` install hint. Restore the environment afterward.

## 3. Spec sync

- [x] 3.1 Run `openspec validate fix-ci-dependency-discovery` (or the equivalent status check) and confirm no validation errors are reported against the modified `build-system` spec.
- [ ] 3.2 Hand off to `/opsx:archive` once the change has been merged so the delta is folded back into `openspec/specs/build-system/spec.md`.
