## 1. Author `.pre-commit-config.yaml`

- [ ] 1.1 Create `.pre-commit-config.yaml` at the repository root
- [ ] 1.2 Add `pre-commit/pre-commit-hooks` repo entry pinned to a recent release tag, with hooks: `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-merge-conflict`, `mixed-line-ending` (args: `["--fix=lf"]`)
- [ ] 1.3 Add `pre-commit/mirrors-clang-format` repo entry pinned to a tag in the `v18.*` series (e.g. `v18.1.8`), restricted via `files:` / `types:` to C++ sources and headers (`*.cpp`, `*.hpp`, `*.h`, `*.cc`)
- [ ] 1.4 Confirm the file is valid YAML (open it in an editor or run `python -c "import yaml; yaml.safe_load(open('.pre-commit-config.yaml'))"`)

## 2. Local verification pass

- [ ] 2.1 Install `pre-commit` locally (`pipx install pre-commit` or `pip install pre-commit`)
- [ ] 2.2 Run `pre-commit run --all-files` from the repo root
- [ ] 2.3 Commit any auto-fix results from `trailing-whitespace`, `end-of-file-fixer`, or `mixed-line-ending` so the tree is clean under the new hooks
- [ ] 2.4 Re-run `pre-commit run --all-files` and confirm an exit code of 0

## 3. Update the CI workflow

- [ ] 3.1 Open `.github/workflows/ci.yml` and replace the `format-check` job body
- [ ] 3.2 Keep the job name `format-check` (or rename to `pre-commit` — decide and stay consistent); runner remains `ubuntu-22.04`
- [ ] 3.3 Replace the LLVM apt-repo + `clang-format-18` install steps with: `actions/setup-python@v5` (`python-version: '3.x'`)
- [ ] 3.4 Add `actions/cache@v4` step caching `~/.cache/pre-commit`, keyed on `${{ runner.os }}-pre-commit-${{ hashFiles('.pre-commit-config.yaml') }}` with a looser restore-key fallback
- [ ] 3.5 Add `pip install pre-commit==<pin>` (pick a current stable release, e.g. `3.7.1`)
- [ ] 3.6 Replace the clang-format invocation step with `pre-commit run --all-files --show-diff-on-failure`
- [ ] 3.7 Leave the `build-test` job untouched

## 4. Document developer setup

- [ ] 4.1 Add a "Pre-commit hooks" section to `README.md` (near the existing build/test instructions)
- [ ] 4.2 Document the one-time install: `pipx install pre-commit` (with `pip install pre-commit` as an alternative) and `pre-commit install`
- [ ] 4.3 Document the manual full-repo run: `pre-commit run --all-files`
- [ ] 4.4 Mention that CI runs the exact same config, so local green means CI green for the format-check job

## 5. Housekeeping

- [ ] 5.1 If a pre-commit cache path ends up inside the repo (it normally lives in `~/.cache/pre-commit` and does not), add it to `.gitignore`; otherwise skip
- [ ] 5.2 Leave the `# Target clang-format version: 18` comment in `.clang-format` as human documentation; no edit needed
- [ ] 5.3 Remove any now-dead shell from `.github/workflows/ci.yml` (the `mapfile`/`git ls-files` snippet, the LLVM apt key dance) so the workflow diff is net-simpler

## 6. End-to-end verification

- [ ] 6.1 Push a branch and open a draft PR; confirm the `format-check` / `pre-commit` job runs, installs `pre-commit`, hits the cache on a second push, and passes
- [ ] 6.2 Deliberately introduce a formatting violation (e.g. add trailing whitespace or mis-indent a C++ file) in a scratch commit and confirm CI fails with a readable diff via `--show-diff-on-failure`; then revert
- [ ] 6.3 Confirm the `build-test` job still passes unchanged
- [ ] 6.4 Confirm `pre-commit install` on a fresh clone registers the hook and that a local `git commit` with a violation is blocked
