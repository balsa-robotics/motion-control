# motion-control

Real-time motion control core for articulated and parallel-linked robots (30+ DOF), targeting a 500–1000 Hz control loop on Linux PREEMPT_RT with isolated CPU cores.

This repository is a prototype-stage side project. See [`openspec/project.md`](openspec/project.md) for full project context and [`openspec/changes/`](openspec/changes/) for in-flight changes.

## Prerequisites

Install a modern C++ toolchain, CMake, Ninja, Eigen 3, and Google Test.

### Ubuntu 22.04+

```sh
sudo apt install -y \
  gcc-12 g++-12 cmake ninja-build \
  libeigen3-dev libgtest-dev libgmock-dev
```

If your distro ships CMake older than 3.24, install from [Kitware's APT repository](https://apt.kitware.com/).

### macOS

```sh
brew install cmake ninja eigen googletest
```

### Minimum versions

| Tool | Minimum |
|---|---|
| CMake | 3.24 |
| Compiler | gcc-12, clang-15, or equivalent with C++20 support |
| Eigen | 3.4 |
| Google Test | 1.11 |

## Build and test

Two named CMake presets are provided:

| Preset | Build type | Tests | Warnings-as-errors |
|---|---|---|---|
| `debug` | Debug | on | on |
| `release` | Release | off | off |

Configure, build, and test with:

```sh
cmake --preset=debug
cmake --build --preset=debug
ctest --preset=debug
```

Release build (no tests):

```sh
cmake --preset=release
cmake --build --preset=release
```

## Layout

```
include/motion_control/   # public headers (project-prefixed)
src/                      # library sources
tests/                    # GoogleTest unit tests
cmake/                    # reusable CMake helpers
openspec/                 # spec-driven change proposals and project context
.github/workflows/        # CI configuration
```

## Formatting

Code style is enforced with `clang-format` (pinned to version 18, config at `.clang-format`).

```sh
clang-format-18 -i $(git ls-files '*.cpp' '*.hpp')
```

CI runs `clang-format-18 --dry-run --Werror` on every push and pull request.
