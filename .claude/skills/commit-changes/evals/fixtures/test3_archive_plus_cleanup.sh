#!/usr/bin/env bash
# Materializes a temp git repo with:
#  1. An openspec change directory being archived (rename/move).
#  2. An unrelated small code cleanup in src/util/string_utils.cpp.
#  3. An untracked notes.txt that looks like personal scratch — must NOT auto-stage.
# Prints the repo path on stdout.
set -euo pipefail

TMPDIR=$(mktemp -d -t commit-skill-test3-XXXXXX)
cd "$TMPDIR"

git init -q -b main
git config user.email "test@example.com"
git config user.name "Test User"
git config core.hooksPath /dev/null

# --- Baseline state: the openspec change directory exists, code exists ---
mkdir -p openspec/changes/setup-pre-commit-ci openspec/changes/archive \
         openspec/specs src/util include/util tests/util

cat > README.md <<'EOF'
# Motion Control
EOF
cat > .gitignore <<'EOF'
build/
EOF

cat > openspec/changes/setup-pre-commit-ci/proposal.md <<'EOF'
# Setup pre-commit CI

## Why
Catch formatting / lint issues before they hit main.

## What
Wire pre-commit into the CI workflow.
EOF

cat > openspec/changes/setup-pre-commit-ci/tasks.md <<'EOF'
# Tasks
- [x] Add .pre-commit-config.yaml
- [x] Wire into CI
EOF

cat > include/util/string_utils.hpp <<'EOF'
#pragma once
#include <string>
namespace util {
std::string trim(const std::string& s);
// Old helper, no longer called anywhere.
std::string dead_helper(const std::string& s);
}
EOF

cat > src/util/string_utils.cpp <<'EOF'
#include "util/string_utils.hpp"
#include <algorithm>
#include <cctype>

namespace util {

std::string trim(const std::string& s) {
    auto a = s.begin();
    auto b = s.end();
    while (a != b && std::isspace(static_cast<unsigned char>(*a))) ++a;
    while (b != a && std::isspace(static_cast<unsigned char>(*(b - 1)))) --b;
    return std::string(a, b);
}

// Old helper, no longer used. Should be removed.
std::string dead_helper(const std::string& s) {
    return s + "_dead";
}

}  // namespace util
EOF

touch openspec/changes/archive/.gitkeep

git add README.md .gitignore \
        openspec/changes/setup-pre-commit-ci/proposal.md \
        openspec/changes/setup-pre-commit-ci/tasks.md \
        openspec/changes/archive/.gitkeep \
        include/util/string_utils.hpp \
        src/util/string_utils.cpp
git commit -q -m "chore: initialize repo"

# A few prior commits so log style is visible.
mkdir -p openspec/changes/seed-feature
cat > openspec/changes/seed-feature/proposal.md <<'EOF'
# Seed feature
Baseline proposal for log-style reference.
EOF
git add openspec/changes/seed-feature/proposal.md
git commit -q -m "proposal: add seed feature"

# Pretend we already implemented and shipped setup-pre-commit-ci.
echo "# pre-commit config marker" > .pre-commit-config.yaml
git add .pre-commit-config.yaml
git commit -q -m "feat: setup initial pre-commit"

# --- Dirty state ---

# 1. Archive the change: rename the directory.
mkdir -p openspec/changes/archive/2026-04-27-setup-pre-commit-ci
git mv openspec/changes/setup-pre-commit-ci/proposal.md \
       openspec/changes/archive/2026-04-27-setup-pre-commit-ci/proposal.md
git mv openspec/changes/setup-pre-commit-ci/tasks.md \
       openspec/changes/archive/2026-04-27-setup-pre-commit-ci/tasks.md
rmdir openspec/changes/setup-pre-commit-ci

# 2. Unrelated cleanup: drop the dead helper.
cat > include/util/string_utils.hpp <<'EOF'
#pragma once
#include <string>
namespace util {
std::string trim(const std::string& s);
}
EOF

cat > src/util/string_utils.cpp <<'EOF'
#include "util/string_utils.hpp"
#include <algorithm>
#include <cctype>

namespace util {

std::string trim(const std::string& s) {
    auto a = s.begin();
    auto b = s.end();
    while (a != b && std::isspace(static_cast<unsigned char>(*a))) ++a;
    while (b != a && std::isspace(static_cast<unsigned char>(*(b - 1)))) --b;
    return std::string(a, b);
}

}  // namespace util
EOF

git add include/util/string_utils.hpp src/util/string_utils.cpp

# 3. Untracked personal notes — must NOT be auto-committed.
cat > notes.txt <<'EOF'
TODO: ask team about renaming MotionPlanner -> TrajectoryPlanner
TODO: figure out why the test runner is slow on macOS
EOF

echo "$TMPDIR"
