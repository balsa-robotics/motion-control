## 1. Author `.pre-commit-config.yaml`

- [x] 1.1 Create `.pre-commit-config.yaml` at the repository root
- [x] 1.2 Add `pre-commit/pre-commit-hooks` repo entry pinned to a recent release tag, with hooks: `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-merge-conflict`, `mixed-line-ending` (args: `["--fix=lf"]`)
- [x] 1.3 Add `pre-commit/mirrors-clang-format` repo entry pinned to a tag in the `v18.*` series (e.g. `v18.1.8`), restricted via `files:` / `types:` to C++ sources and headers (`*.cpp`, `*.hpp`, `*.h`, `*.cc`)
- [x] 1.4 Confirm the file is valid YAML (open it in an editor or run `python -c "import yaml; yaml.safe_load(open('.pre-commit-config.yaml'))"`)

## 2. Local verification pass

- [x] 2.1 Install `pre-commit` locally (`pipx install pre-commit` or `pip install pre-commit`)
- [x] 2.2 Run `pre-commit run --all-files` from the repo root
- [x] 2.3 Commit any auto-fix results from `trailing-whitespace`, `end-of-file-fixer`, or `mixed-line-ending` so the tree is clean under the new hooks
- [x] 2.4 Re-run `pre-commit run --all-files` and confirm an exit code of 0

## 3. Update the CI workflow

- [x] 3.1 Open `.github/workflows/ci.yml` and replace the `format-check` job body
- [x] 3.2 Keep the job name `format-check` (or rename to `pre-commit` — decide and stay consistent); runner remains `ubuntu-22.04`
- [x] 3.3 Replace the LLVM apt-repo + `clang-format-18` install steps with: `actions/setup-python@v5` (`python-version: '3.x'`)
- [x] 3.4 Add `actions/cache@v4` step caching `~/.cache/pre-commit`, keyed on `${{ runner.os }}-pre-commit-${{ hashFiles('.pre-commit-config.yaml') }}` with a looser restore-key fallback
- [x] 3.5 Add `pip install pre-commit==<pin>` (pick a current stable release, e.g. `3.7.1`)
- [x] 3.6 Replace the clang-format invocation step with `pre-commit run --all-files --show-diff-on-failure`
- [x] 3.7 Leave the `build-test` job untouched

## 4. Document developer setup

- [x] 4.1 Add a "Pre-commit hooks" section to `README.md` (near the existing build/test instructions)
- [x] 4.2 Document the one-time install: `pipx install pre-commit` (with `pip install pre-commit` as an alternative) and `pre-commit install`
- [x] 4.3 Document the manual full-repo run: `pre-commit run --all-files`
- [x] 4.4 Mention that CI runs the exact same config, so local green means CI green for the format-check job

## 5. Housekeeping

- [x] 5.1 If a pre-commit cache path ends up inside the repo (it normally lives in `~/.cache/pre-commit` and does not), add it to `.gitignore`; otherwise skip
- [x] 5.2 Leave the `# Target clang-format version: 18` comment in `.clang-format` as human documentation; no edit needed
- [x] 5.3 Remove any now-dead shell from `.github/workflows/ci.yml` (the `mapfile`/`git ls-files` snippet, the LLVM apt key dance) so the workflow diff is net-simpler
