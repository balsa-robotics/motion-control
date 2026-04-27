#!/usr/bin/env bash
# Materializes a temp git repo with: a new openspec proposal AND the code/tests
# that implement it, all in the dirty tree (mostly staged, some unstaged).
# Prints the repo path on stdout.
set -euo pipefail

TMPDIR=$(mktemp -d -t commit-skill-test1-XXXXXX)
cd "$TMPDIR"

git init -q -b main
git config user.email "test@example.com"
git config user.name "Test User"
# Disable any global pre-commit / hook installs that may be configured globally.
git config core.hooksPath /dev/null

# --- Baseline commits so HEAD exists and recent log style is established ---
mkdir -p openspec/changes/archive openspec/specs
echo "# Test repo" > README.md
echo "build/" > .gitignore
touch openspec/changes/archive/.gitkeep
git add README.md .gitignore openspec/changes/archive/.gitkeep
git commit -q -m "chore: initialize repo"

# Seed a recent log style — match the user's real repo.
mkdir -p openspec/changes/seed-feature
cat > openspec/changes/seed-feature/proposal.md <<'EOF'
# Seed feature
Baseline proposal so the openspec layout is non-empty.
EOF
git add openspec/changes/seed-feature/proposal.md
git commit -q -m "proposal: add seed feature"

# --- Dirty state: proposal + implementation together ---
mkdir -p openspec/changes/motion-profile-generator
cat > openspec/changes/motion-profile-generator/proposal.md <<'EOF'
# Motion profile generator

## Why
The motion control stack needs a trapezoidal velocity profile for smooth
point-to-point moves. We currently jump straight to vmax which causes jerk.

## What
Add a profile generator that takes (start, end, vmax, amax) and returns a
sampled trajectory of (t, p, v, a) tuples.
EOF

cat > openspec/changes/motion-profile-generator/tasks.md <<'EOF'
# Tasks
- [ ] Implement trapezoidal profile in src/planner/profile.cpp
- [ ] Public header at include/planner/profile.hpp
- [ ] Cover edge cases (zero distance, vmax unreachable) in tests
EOF

mkdir -p src/planner include/planner tests/planner
cat > include/planner/profile.hpp <<'EOF'
#pragma once
#include <vector>

namespace planner {

struct ProfilePoint { double t, p, v, a; };

std::vector<ProfilePoint>
trapezoidal(double start, double end, double vmax, double amax);

}  // namespace planner
EOF

cat > src/planner/profile.cpp <<'EOF'
#include "planner/profile.hpp"
#include <cmath>

namespace planner {

std::vector<ProfilePoint>
trapezoidal(double start, double end, double vmax, double amax) {
    std::vector<ProfilePoint> out;
    // Naive placeholder — endpoints only.
    out.push_back({0.0, start, 0.0, amax});
    out.push_back({1.0, end,   0.0, -amax});
    return out;
}

}  // namespace planner
EOF

cat > tests/planner/test_profile.cpp <<'EOF'
#include "planner/profile.hpp"
#include <cassert>

int main() {
    auto pts = planner::trapezoidal(0.0, 1.0, 1.0, 1.0);
    assert(!pts.empty());
    assert(pts.front().p == 0.0);
    assert(pts.back().p == 1.0);
    return 0;
}
EOF

# Stage most of the change (mix staged/unstaged for realism).
git add openspec/changes/motion-profile-generator/proposal.md \
        openspec/changes/motion-profile-generator/tasks.md \
        include/planner/profile.hpp \
        src/planner/profile.cpp
# Leave the test file unstaged.
# (tests/planner/test_profile.cpp remains untracked.)

echo "$TMPDIR"
