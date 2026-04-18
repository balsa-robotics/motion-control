# motion-control — Project Context

## Overview

Real-time motion control core for humanoid and multi-joint (30+ DOF) robots. Implements the control loop, parallel-link kinematics, command smoothing, and safety features that sit between a high-level planner and physical actuators.

This is a prototype-stage side project. There is no specific hardware target; hardware is actively mocked to enable development and testing without physical devices.

## Goals

- Real-time joint-level control loop running at 500–1000 Hz
- Parallel-link kinematics solver (FK/IK) supporting closed-loop linkage structures found in humanoid ankles, hips, etc.
- Low-pass filtering and interpolation of incoming joint commands (external planners run at lower frequency)
- Safety monitor: joint position/velocity/torque limits, emergency stop
- Hardware Abstraction Layer (HAL) with bridge/adapter pattern supporting EtherCAT and CAN

## Non-Goals

- Upper-layer planning: MPC, reinforcement learning, gait pattern generation, trajectory optimization
- State estimation / SLAM
- Simulation environment (used as a test tool, not developed here)
- ROS2 integration (Zenoh is preferred for inter-process communication)

## Architecture

The control loop receives joint control commands (analogous to ROS2 `JointState`) from external modules via Zenoh, and delivers actuator commands to hardware at the configured control frequency.

Key architectural notes:
- External command frequency may be lower than control frequency → LPF/interpolation is required
- Multiple RT threads with explicit priority separation
- Control loop architecture (sense/plan/act layering, cascaded vs. whole-body) is **TBD — requires a dedicated design session**
- HAL uses bridge/adapter pattern to abstract EtherCAT vs. CAN differences

### Key Components

| Component | Responsibility |
|---|---|
| HAL (bridge) | Abstracts EtherCAT / CAN; hardware is mockable for testing |
| Parallel-link solver | FK/IK for closed-loop kinematic chains |
| Command smoother | LPF and interpolation for under-sampled command inputs |
| Safety monitor | Limit checking, fault detection, emergency stop |
| RT scheduler | Multi-threaded RT loop management, CPU affinity, priority |

## Tech Stack

| Area | Choice |
|---|---|
| Language | C++20 |
| Build | CMake |
| CI | GitHub Actions |
| RT environment | Linux + PREEMPT_RT, isolated CPU cores |
| Numerics | Eigen |
| IPC / messaging | Zenoh (preferred over ROS2) |
| Serialization | TBD |
| Hardware protocols | EtherCAT, CAN (via HAL bridge) |
| Code style | clang-format; considering C++ Core Guidelines over Google Style |
| Testing | Google Test; unit tests first, simulation integration later |

## Conventions

- **Commits**: Conventional Commits (`feat:`, `fix:`, `chore:`, etc.)
- **C++ standard**: C++20
- **Formatting**: clang-format (style config TBD, leaning toward C++ Core Guidelines-compatible)
- **Testing**: Google Test; hardware layer is always mockable; no tests should require physical hardware
- **Real-time constraints**: no dynamic memory allocation on the RT path, no blocking syscalls in RT threads
