## 1. Directory skeleton

- [ ] 1.1 Create top-level directories: `src/`, `include/motion_control/`, `tests/`, `cmake/`
- [ ] 1.2 Add `.gitkeep` files where needed so empty directories commit cleanly

## 2. Root CMake configuration

- [ ] 2.1 Create root `CMakeLists.txt` with `cmake_minimum_required(VERSION 3.24)` and `project(motion_control CXX)`
- [ ] 2.2 Set `CMAKE_CXX_STANDARD 20`, `CMAKE_CXX_STANDARD_REQUIRED ON`, `CMAKE_CXX_EXTENSIONS OFF`
- [ ] 2.3 Enable `CMAKE_EXPORT_COMPILE_COMMANDS`
- [ ] 2.4 Add `include(CTest)` and gate the `tests/` subdirectory on `BUILD_TESTING`
- [ ] 2.5 `add_subdirectory(src)` and conditional `add_subdirectory(tests)`

## 3. CMake presets

- [ ] 3.1 Create `CMakePresets.json` at repo root
- [ ] 3.2 Add `debug` preset (`CMAKE_BUILD_TYPE=Debug`, `BUILD_TESTING=ON`, `-Werror` via compile options)
- [ ] 3.3 Add `release` preset (`CMAKE_BUILD_TYPE=Release`, `BUILD_TESTING=OFF`)
- [ ] 3.4 Add matching build and test presets (`buildPresets`, `testPresets`)

## 4. Third-party dependency wiring

- [ ] 4.1 In the root CMake configuration, call `find_package(Eigen3 3.4 CONFIG REQUIRED)` and confirm the `Eigen3::Eigen` imported target is available
- [ ] 4.2 Guarded on `BUILD_TESTING`, call `find_package(GTest CONFIG REQUIRED)` and confirm the `GTest::gtest_main` imported target is available
- [ ] 4.3 On `find_package` failure, emit a `FATAL_ERROR` message that names the missing package and points contributors to the README install instructions
- [ ] 4.4 (Optional) Factor the `find_package` calls into `cmake/Dependencies.cmake` if the root `CMakeLists.txt` starts to feel cluttered

## 5. Core library target

- [ ] 5.1 Create `src/CMakeLists.txt` defining the `motion_control_core` static library
- [ ] 5.2 Add alias `motion_control::core`
- [ ] 5.3 Set `target_include_directories` to expose `include/` as `INTERFACE`
- [ ] 5.4 Link `Eigen3::Eigen` as `INTERFACE` (header-only propagation)
- [ ] 5.5 Add `include/motion_control/core.hpp` with a placeholder namespace and a trivial function declaration
- [ ] 5.6 Add `src/core.cpp` implementing the trivial function

## 6. Smoke test

- [ ] 6.1 Create `tests/CMakeLists.txt`
- [ ] 6.2 Define `smoke_test` executable linking against `motion_control::core` and `GTest::gtest_main`
- [ ] 6.3 Add `tests/smoke_test.cpp` with one `TEST()` that exercises the placeholder function
- [ ] 6.4 Register tests via `gtest_discover_tests(smoke_test)`

## 7. Formatting config

- [ ] 7.1 Create `.clang-format` with `BasedOnStyle: LLVM`, `ColumnLimit: 100`, `PointerAlignment: Left`, pinned clang-format version noted in a header comment
- [ ] 7.2 Run `clang-format` over all new sources to confirm they are self-consistent

## 8. Continuous integration

- [ ] 8.1 Create `.github/workflows/ci.yml` with a `build-test` job on `ubuntu-22.04`
- [ ] 8.2 Install `gcc-12`, `libeigen3-dev`, and `libgtest-dev` via `apt`, and set `gcc-12` as the active C++ compiler in the job
- [ ] 8.3 Configure + build with the `debug` preset, then run `ctest --preset=debug --output-on-failure`
- [ ] 8.4 Add a second `format-check` job that installs `clang-format-18` and runs `clang-format --dry-run --Werror` on all tracked C++ files
- [ ] 8.5 Require both jobs to pass for a green CI status

## 9. Documentation

- [ ] 9.1 Update `README.md` with project description, prerequisites (CMake ≥ 3.24, gcc-12+ or clang equivalent), and quickstart commands
- [ ] 9.2 Document the `debug` / `release` preset usage and how to run tests

## 10. End-to-end verification

- [ ] 10.1 From a clean checkout, run `cmake --preset=debug && cmake --build --preset=debug` and confirm success
- [ ] 10.2 Run `ctest --preset=debug` and confirm the smoke test passes
- [ ] 10.3 Run `cmake --preset=release && cmake --build --preset=release` and confirm no test targets are built
- [ ] 10.4 Push a throwaway branch and confirm the CI workflow runs and passes on both `build-test` and `format-check` jobs
- [ ] 10.5 Intentionally break formatting in a scratch file, confirm `format-check` fails, then revert
