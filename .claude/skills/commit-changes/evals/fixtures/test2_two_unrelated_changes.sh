#!/usr/bin/env bash
# Materializes a temp git repo with three unrelated changes in the dirty tree:
#  1. planner/limits.cpp + its test (paired, must commit together)
#  2. logging/logger.cpp (alone, unrelated subsystem)
#  3. README.md typo fix (alone, unrelated docs)
# Prints the repo path on stdout.
set -euo pipefail

TMPDIR=$(mktemp -d -t commit-skill-test2-XXXXXX)
cd "$TMPDIR"

git init -q -b main
git config user.email "test@example.com"
git config user.name "Test User"
git config core.hooksPath /dev/null

# --- Baseline commit with all the files that will be modified ---
mkdir -p openspec/changes/archive openspec/specs \
         src/planner src/logging tests/planner include/planner

cat > README.md <<'EOF'
# Motion Control

This is teh control stack. It plans trajectories and executes them on the
hardware. See docs/ for more.
EOF

cat > .gitignore <<'EOF'
build/
EOF

cat > include/planner/limits.hpp <<'EOF'
#pragma once
namespace planner { bool within_velocity_limit(double v); }
EOF

cat > src/planner/limits.cpp <<'EOF'
#include "planner/limits.hpp"
namespace planner {
bool within_velocity_limit(double /*v*/) { return true; }
}
EOF

cat > tests/planner/test_limits.cpp <<'EOF'
#include "planner/limits.hpp"
#include <cassert>
int main() { assert(planner::within_velocity_limit(0.0)); return 0; }
EOF

cat > src/logging/logger.cpp <<'EOF'
#include <cstdio>
namespace logging {
void log_line(const char* msg) {
    std::printf("[log] %s\n", msg);
}
}
EOF

touch openspec/changes/archive/.gitkeep

git add README.md .gitignore include/planner/limits.hpp \
        src/planner/limits.cpp tests/planner/test_limits.cpp \
        src/logging/logger.cpp openspec/changes/archive/.gitkeep
git commit -q -m "chore: initialize repo"

mkdir -p openspec/changes/seed-feature
cat > openspec/changes/seed-feature/proposal.md <<'EOF'
# Seed feature
Baseline proposal so the openspec layout is non-empty.
EOF
git add openspec/changes/seed-feature/proposal.md
git commit -q -m "proposal: add seed feature"

# --- Dirty state: three unrelated changes ---

# 1. Planner limits — adds real bounds checking. Update header, impl, AND test.
cat > include/planner/limits.hpp <<'EOF'
#pragma once
namespace planner {
bool within_velocity_limit(double v);
bool within_acceleration_limit(double a);
}
EOF

cat > src/planner/limits.cpp <<'EOF'
#include "planner/limits.hpp"
#include <cmath>
namespace planner {
constexpr double kVmax = 5.0;
constexpr double kAmax = 10.0;
bool within_velocity_limit(double v) { return std::abs(v) <= kVmax; }
bool within_acceleration_limit(double a) { return std::abs(a) <= kAmax; }
}
EOF

cat > tests/planner/test_limits.cpp <<'EOF'
#include "planner/limits.hpp"
#include <cassert>
int main() {
    assert(planner::within_velocity_limit(0.0));
    assert(!planner::within_velocity_limit(99.0));
    assert(planner::within_acceleration_limit(0.0));
    assert(!planner::within_acceleration_limit(99.0));
    return 0;
}
EOF

# 2. Logger — switch from text to JSON output. Unrelated subsystem.
cat > src/logging/logger.cpp <<'EOF'
#include <cstdio>
namespace logging {
void log_line(const char* msg) {
    std::printf("{\"level\":\"info\",\"msg\":\"%s\"}\n", msg);
}
}
EOF

# 3. README typo — "teh" -> "the". Wholly unrelated.
cat > README.md <<'EOF'
# Motion Control

This is the control stack. It plans trajectories and executes them on the
hardware. See docs/ for more.
EOF

# Stage everything to keep the eval simple and deterministic.
git add include/planner/limits.hpp src/planner/limits.cpp \
        tests/planner/test_limits.cpp src/logging/logger.cpp README.md

echo "$TMPDIR"
