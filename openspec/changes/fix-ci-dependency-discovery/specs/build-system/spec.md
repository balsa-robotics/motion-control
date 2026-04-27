## MODIFIED Requirements

### Requirement: Third-party dependencies resolved via find_package
The project SHALL resolve Eigen and Google Test using `find_package` against system-installed copies. The `find_package` invocations SHALL allow CMake's default discovery order (MODULE mode then CONFIG mode) and SHALL NOT force a single mode (e.g., by passing the `CONFIG` keyword) nor suppress CMake's underlying discovery diagnostic (e.g., by passing `QUIET`). When a required dependency is not found, CMake SHALL fail at configure time with a fatal error that names the missing package and references the README install instructions, and the underlying CMake diagnostic identifying which paths and versions were considered SHALL appear in the configure output.

#### Scenario: Configure succeeds when prerequisites are installed
- **WHEN** a contributor has installed the prerequisites listed in `README.md` and runs `cmake --preset=debug`
- **THEN** `find_package` locates Eigen and Google Test, and the configure step completes successfully

#### Scenario: Configure fails clearly when a prerequisite is missing
- **WHEN** a contributor runs `cmake --preset=debug` without the required Eigen or Google Test package installed
- **THEN** CMake emits a fatal error that identifies the missing package by name and points to the README install instructions

#### Scenario: Underlying CMake diagnostic is preserved on failure
- **WHEN** a contributor runs `cmake --preset=debug` and Eigen or Google Test discovery fails (package missing, version mismatch, or path not searched)
- **THEN** CMake's standard "could not find package" diagnostic — listing the considered paths and the requested vs. found version — appears in the configure output above the project's install-hint fatal error, without requiring `--debug-find` or any other extra flag

#### Scenario: Finder is not locked to CONFIG-only discovery
- **WHEN** a maintainer reads `cmake/Dependencies.cmake`
- **THEN** the `find_package` calls for Eigen3 and GTest do not pass the `CONFIG` keyword and do not pass the `QUIET` keyword
