# motion-control — Project Context

## Overview

Real-time motion control core for humanoid and multi-joint (30+ DOF) robots. Implements the periodic command-conditioning pipeline — filtering, parallel-link kinematics, and safety — that sits between a high-level planner and physical actuators.

This module is **not a closed-loop controller**: there is no PID, QP, MPC, or whole-body solver inside it. Closed-loop control law work, if any, is upstream of this module.

This is a prototype-stage side project. There is no specific hardware target; hardware is actively mocked to enable development and testing without physical devices.

## Goals

- Real-time joint-level control loop running at 500–1000 Hz
- Parallel-link kinematics solver (FK/IK) supporting closed-loop linkage structures found in humanoid ankles, hips, etc.
- Low-pass filtering and interpolation of incoming joint commands (external planners run at lower frequency)
- Safety monitor: joint position/velocity/torque limits, emergency stop
- Hardware Abstraction Layer (HAL) with bridge/adapter pattern supporting EtherCAT and CAN

## Non-Goals

- Upper-layer planning: MPC, reinforcement learning, gait pattern generation, trajectory optimization
- Inner-loop control law: no PID, QP, or whole-body solver in this module — command-conditioning only (filter + kinematics + safety)
- State estimation / SLAM
- Simulation environment (used as a test tool, not developed here)
- ROS2 integration (Zenoh is preferred for inter-process communication)

## Architecture

The module receives joint commands (analogous to ROS2 `JointState`) from external modules via Zenoh, conditions them through filtering, parallel-link kinematics, and safety, and writes actuator commands to hardware at the configured control rate.

### Per-tick pipeline

Two paths run per tick. The command path deliberately reads state from the *previous* tick's state path so command-thread latency is decoupled from FK iteration variance.

```
                          ◀── 1 ms tick @ 1 kHz ──▶

  STATE PATH                                              COMMAND PATH
  ──────────                                              ────────────
  ① HAL.read_all()       (bus → actuator state)
       │
       ▼
  ② FK iterative          (V=1 max — must finish        ③ latest Zenoh cmd
       │                   in this tick or fault              │
       ▼                   → emergency stop)                  ▼
  state.logical, state.actuator                        ④ filter (LPF + interp,
       │  (atomically published for                          logical-joint space)
       │   the next tick's command path)                     │
       │                                                     ▼
       │                                              ⑤ pre-IK safety plugins
       │                                                 (uses prev tick logical state)
       │                                                     │
       │                                                     ▼
       │                                              ⑥ IK numerical (bounded,
       │                                                 logical → actuator)
       │                                                     │
       │                                                     ▼
       │                                              ⑦ post-IK safety plugins
       │                                                 (uses prev tick actuator state)
       │                                                     │
       │                                                     ▼
       │                                              ⑧ HAL.write_all()
       ▼                                                     │
  telemetry, logging                                         ▼
                                                          bus
```

### Settled architectural decisions

- **Clock source**: a timer in this process drives the 500–1000 Hz tick. The bus follows; no external clock (e.g., EtherCAT distributed clock) is the source of truth for this module.
- **State staleness contract**: the command path always reads the previous tick's published state (V = 1 max). FK must complete within one tick; if it does not, that is a fault → emergency stop. There is no graceful "FK lagging" mode.
- **Filter placement**: low-pass filter and interpolation operate in logical-joint space, **before** IK. IK sees time-smooth inputs. There is no post-IK filter.
- **IK / FK character**:
  - IK is closed-form / numerical with bounded runtime (logical → actuator).
  - FK is iterative (actuator → logical) and lives on the state path.
- **Safety stations**: two stations — one pre-IK (logical-joint commands and state) and one post-IK (actuator-joint commands and state). Both are plugin-able. Plugins may be stateless or stateful; stateful plugins can issue controlled stops over multiple ticks.
- **Cold-start**: at boot the module enters a passive-hold mode that reads actuator state directly from the HAL and commands it back to the same position, requiring no FK output. Normal operation begins after the first successful FK cycle.
- **HAL contract shape**: per-cycle bus API (`read_all`, `write_all`, `wait_next_cycle`). Semantics lean toward EtherCAT (synchronous PDO per cycle); a CAN/CAN-FD implementation absorbs async-to-sync impedance via per-cycle frame batching.
- **HAL implementation order**: first concrete implementation is CAN-FD via SocketCAN (simpler bring-up, single-ioctl R/W maps cleanly to per-cycle API). Eventual production target is EtherCAT via SOEM. A pure in-memory mock backs the same per-cycle API for tests.
- **Thread topology**: at minimum two RT threads — a command thread (timer-driven, deterministic) and a state thread (HAL.read + FK). The state thread may run at lower priority. Inter-thread state hand-off is wait-free.

### Deferred architectural decisions

The following are intentionally not pinned down yet. They will be decided in their own change proposals when the relevant component lands.

- **Safety plugin composition contract**: plugin interface shape (gate vs transform vs both), composition order at each station, controlled-stop arbitration when multiple plugins request different ramps.
- **Mode state machine**: full state machine for `{startup-hold, normal, controlled-stop, e-stop, …}` and the rules for transitions and arbitration.
- **State publish primitive**: whether the inter-thread state hand-off uses a Zenoh shared-memory transport, an internal double-buffered struct with atomic active-index, or both (internal primitive with secondary Zenoh fan-out for telemetry). Empirical question — needs a 1 kHz benchmark before locking in.
- **FK iteration cap**: the worst-case iteration count budgeted for FK per tick. Empirical, tied to the actual linkage topologies (humanoid ankle, hip).
- **In-process state representation**: probably `Eigen::VectorXd` everywhere given RT constraints, but to be confirmed when the first concrete component lands.

### Key Components

| Component | Responsibility |
|---|---|
| HAL | Per-cycle bus API; first impl CAN-FD via SocketCAN, target EtherCAT via SOEM; hardware mockable for testing |
| Parallel-link solver | IK closed-form / numerical (logical → actuator); FK iterative (actuator → logical), V=1 max staleness |
| Command filter | LPF + interpolation in logical-joint space, pre-IK only |
| Safety pipeline | Pre-IK + post-IK stations, plugin-able, stateless or stateful plugins, controlled-stop capable |
| RT thread topology | Command thread (timer-driven, deterministic) + state thread (HAL.read + FK), wait-free state hand-off |

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
