# build-system

## Purpose
Defines how the motion_control project is configured, compiled, and consumed as a CMake project, including presets, public headers, third-party dependency resolution, and test registration.

## Requirements

### Requirement: CMake-based C++20 build
The project SHALL be configurable and buildable with CMake version 3.24 or newer, targeting the C++20 standard, after the contributor installs the external prerequisites documented in `README.md`.

#### Scenario: Build succeeds with prerequisites installed
- **WHEN** a contributor has installed the documented prerequisites and runs `cmake --preset=debug` followed by `cmake --build --preset=debug`
- **THEN** the build completes successfully and produces the library and test binaries in `build/debug/`

#### Scenario: Release preset builds without test targets
- **WHEN** a contributor runs `cmake --preset=release` followed by `cmake --build --preset=release`
- **THEN** the build completes successfully and no test targets are defined, compiled, or linked

### Requirement: Named CMake presets for Debug and Release
The project SHALL ship a `CMakePresets.json` file at the repository root defining at minimum a `debug` preset (build type Debug, tests enabled, `-Werror` on) and a `release` preset (build type Release, tests disabled).

#### Scenario: Presets are discoverable
- **WHEN** a contributor runs `cmake --list-presets`
- **THEN** both `debug` and `release` appear in the output

### Requirement: Third-party dependencies resolved via find_package
The project SHALL resolve Eigen and Google Test using `find_package` against system-installed copies (either CMake CONFIG or MODULE mode, whichever the package provides). When a required dependency is not found, CMake SHALL fail at configure time with a message that names the missing package and references the README install instructions.

#### Scenario: Configure succeeds when prerequisites are installed
- **WHEN** a contributor has installed the prerequisites listed in `README.md` and runs `cmake --preset=debug`
- **THEN** `find_package` locates Eigen and Google Test, and the configure step completes successfully

#### Scenario: Configure fails clearly when a prerequisite is missing
- **WHEN** a contributor runs `cmake --preset=debug` without the required Eigen or Google Test package installed
- **THEN** CMake emits a fatal error that identifies the missing package by name and points to the README install instructions

### Requirement: Public headers under project-prefixed include path
The project SHALL expose all public headers under `include/motion_control/` and make them available to consumers via a single CMake target (`motion_control::core`) whose `INTERFACE_INCLUDE_DIRECTORIES` points at `include/`.

#### Scenario: Consumer includes a public header
- **WHEN** a test target links against `motion_control::core` and writes `#include <motion_control/core.hpp>`
- **THEN** the header is resolved and the test target compiles and links without additional include-path configuration

### Requirement: Unit tests opt-in via BUILD_TESTING
The project SHALL only configure test targets when the standard CMake option `BUILD_TESTING` is `ON`, and the Release preset SHALL set it to `OFF` by default.

#### Scenario: Release preset does not build tests
- **WHEN** a contributor configures with `cmake --preset=release`
- **THEN** no test targets are defined and `find_package(GTest ...)` is not invoked

#### Scenario: Debug preset builds tests
- **WHEN** a contributor configures with `cmake --preset=debug`
- **THEN** test targets are defined and discoverable via `ctest --preset=debug`

### Requirement: Tests registered with CTest at case granularity
The project SHALL register Google Test cases with CTest using `gtest_discover_tests()` so that each `TEST()` case appears as an individual CTest entry.

#### Scenario: CTest lists individual cases
- **WHEN** a contributor runs `ctest --preset=debug -N`
- **THEN** each `TEST()` defined in the smoke test binary is listed as a separate CTest entry

### Requirement: Compile commands exported for tooling
The project SHALL enable `CMAKE_EXPORT_COMPILE_COMMANDS` in every preset so that a `compile_commands.json` file is produced in the build directory.

#### Scenario: compile_commands.json exists after configure
- **WHEN** a contributor runs `cmake --preset=debug`
- **THEN** `build/debug/compile_commands.json` is written and contains entries for every translation unit in the build
