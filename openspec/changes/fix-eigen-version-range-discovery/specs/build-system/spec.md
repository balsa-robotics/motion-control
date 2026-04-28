## MODIFIED Requirements

### Requirement: Third-party dependencies resolved via find_package
The project SHALL resolve Eigen and Google Test using `find_package` against system-installed copies. The `find_package` invocations SHALL allow CMake's default discovery order (MODULE mode then CONFIG mode) and SHALL NOT force a single mode (e.g., by passing the `CONFIG` keyword) nor suppress CMake's underlying discovery diagnostic (e.g., by passing `QUIET`). When a required dependency is not found, CMake SHALL fail at configure time with a fatal error that names the missing package and references the README install instructions, and the underlying CMake diagnostic identifying which paths and versions were considered SHALL appear in the configure output. For Eigen specifically, the `find_package(Eigen3)` call SHALL NOT pass a version argument or version range; the supported version policy (`>= 3.4`, `< 6`) SHALL instead be enforced by an explicit version check in `cmake/Dependencies.cmake` that runs after `find_package` succeeds. This is required because system-installed `Eigen3ConfigVersion.cmake` files vary in their support for CMake's version-range syntax (Eigen 3.4.0 on Ubuntu 22.04 does not support ranges; Eigen 5.0.1 on macOS Homebrew rejects non-range single-version requests for major versions other than its own), and no `find_package` version argument satisfies both. When the located Eigen version falls outside the supported range, CMake SHALL fail at configure time with a fatal error that names the version found and the supported range.

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

#### Scenario: Eigen version policy enforced after find_package
- **WHEN** a maintainer reads `cmake/Dependencies.cmake`
- **THEN** the `find_package(Eigen3 ...)` call passes no version argument and no version range, and the file contains an explicit check that fails the configure with a fatal error if `Eigen3_VERSION` is less than 3.4 or greater than or equal to 6

#### Scenario: Configure fails clearly when Eigen version is unsupported
- **WHEN** a contributor runs `cmake --preset=debug` on a system whose installed Eigen version is below 3.4 or 6.0 or above
- **THEN** CMake emits a fatal error that names the located Eigen version and states the supported range (`>= 3.4`, `< 6`), distinct from the "package missing" install-hint error
