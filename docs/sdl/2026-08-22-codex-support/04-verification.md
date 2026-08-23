# 04 — Verification

<!-- SVV-1: Security requirements testing. SVV-2: Threat mitigation testing.
     SVV-3: Vulnerability testing. DM-1: Defect management. -->

## Review pass

- **Reviewer:** sdl-review (Codex) + Joe Cooper
- **Date:** 2026-08-22
- **Diff range:** `origin/main...codex-support` plus reviewed working-tree changes

## Checks performed <!-- SVV-1, SVV-2 -->

<!-- Write a subsection ONLY for categories the diff actually touches.
     Collapse all non-applicable categories into the single "Not applicable"
     line at the end. Most changes touch two to four categories. -->

### Plugin packaging and supply chain

- **Finding:** The Codex manifest validates and exposes only existing skills.
  Both host catalogs use `git-subdir` sources pinned to the current release, and
  release automation validates both before side effects and moves both only
  after the new tag is pushed.
- **References:** `plugins/sdl/.codex-plugin/plugin.json`, `scripts/release.sh`,
  external `.agents/plugins/marketplace.json`

### External JSON and release validation

- **Finding:** Both fixed catalog paths use bounded reads and structural/type
  checks. The Claude catalog must carry the release version; the Codex catalog
  may omit its duplicated version but must agree when one is present. Unit tests
  cover the new behavior and local manifest divergence.
- **References:** `scripts/check_release.py`, `scripts/test_check_release.py`

### Workstation command execution

- **Finding:** The installer invokes a fixed local `codex` executable with
  constant subcommands and a quoted marketplace URL. Failure is warned about
  independently and no `eval` or generated command is used.
- **References:** `scripts/install.sh`

<!-- Repeat for each category the diff touches, then one collapsed line: -->

**Not applicable (no code in these areas):** databases, network endpoints,
authentication or authorization, cryptography, secrets, application logging,
concurrency, frontend rendering, containers, native memory

## Static analysis and SBOM <!-- SVV-3, SM-9 -->

- Codex plugin validator: passed.
- Core plugin/library suite: 144 tests passed.
- Release-check unit suite: 52 tests passed.
- ShellCheck, changed-Python Ruff, JSON parsing, Bash syntax, whitespace, SDL
  validation, and generated-index checks: passed.

## Residual risks <!-- DM-1 -->

<!-- Anything not verified or accepted as known risk. Each entry should be
     specific enough that a future cycle can carry it forward via .sdl-meta.yml. -->

| ID  | Description | Severity | Disposition | Carry-forward target |
|-----|-------------|----------|-------------|----------------------|
| R1 | The external marketplace has no independent schema CI in this change; an authorized writer could still repoint both catalogs together. | medium | accept; paired release validation and daily drift detection provide defense in depth | Revisit when a second plugin or maintainer is added. |
| R2 | End-to-end Codex installation cannot succeed until the first v2.1.0 tag contains the Codex manifest. | low | mitigate-later; bootstrap deliberately protects the existing Claude release | After release, test a clean marketplace add, plugin install, and skill invocation. |
