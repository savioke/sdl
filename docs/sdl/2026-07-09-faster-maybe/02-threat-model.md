# 02 — Threat Model

<!-- SR-2: Threat model. SD-1, SD-2: Secure design and defense in depth. -->

## Components and data flows

- **`lib/new_cycle.py`** — cycle scaffolder. Runs with developer privileges on workstations and in agent sessions; takes the git branch name as input and writes a new folder under the target repo's `docs/sdl/`.
- **`lib/gen_index.py`** — index generator. Reads cycle `.sdl-meta.yml`/markdown files, writes `docs/sdl/INDEX.md`; also runs read-only in this repo's CI as `--check`.
- **Skill edits** (`sdl-spec` fast path + tool steps, `sdl-review`, `sdl-dep-update`) — baseline:B2 executable-spec assets; they change what agents do in every consumer repo.
- **`self-check.yml`** — two new steps (new test modules, `gen_index.py --check`) using the already-pinned actions; no new action, no secret use.

## Threats <!-- SR-2 -->

### T1 — Path traversal via hostile branch name

- **Category:** Tampering
- **Component / flow:** `new_cycle.py` slug/path construction. Branch names are attacker-influenceable text (a developer may run the tool on a checked-out fork branch), and the slug becomes a directory name written with developer privileges.
- **Description:** A branch name like `../../.claude/skills/x` that survived into the folder path would let a scaffold write outside `docs/sdl/`, including into agent-executed locations.
- **Likelihood / Impact:** low / medium
- **Mitigation:** traversal is impossible by construction — the slug alphabet is restricted to `[a-z0-9-]` (`lib/new_cycle.py` `slugify`), inputs that normalize to nothing fail closed with an error, and the tool refuses existing folders. Unit-tested against traversal inputs (`test_traversal_attempts_cannot_escape`, `test_cycle_stays_under_docs_sdl`).
- **Mitigation type:** preventive
- **Defense in depth notes:** the tool errors rather than falling back if the target repo has no `docs/sdl/`, so it cannot create trees in arbitrary directories.

### T2 — Fast path degrades the evidence trail

- **Category:** Repudiation
- **Component / flow:** the `sdl-spec` fast path — single-pass authoring of all four artifacts with no interview.
- **Description:** An agent (or a hurried developer steering one) applies the fast path to a change that does cross a new trust boundary, producing artifacts that look complete but skipped the judgment the interview exists to force. The audit trail then overstates the review that happened.
- **Likelihood / Impact:** medium / medium
- **Mitigation:** the skill wording scopes the fast path (small, already implemented, no new trust boundary or external input) and mandates dropping back to the interview when that doesn't hold; `validate.py` is untouched, so the gate's artifact requirements are unchanged; the human PR reviewer sees the artifacts next to the diff.
- **Mitigation type:** preventive (wording) + detective (PR review)
- **Defense in depth notes:** the fast path compresses orchestration only — an artifact authored in one pass is subject to the same non-stub validation and the same review categories as one authored in three.

## Threats inherited from prior cycles <!-- SR-2 -->

- **baseline:B2** — skill `.md` files edited; they remain gated as code by the validator and reviewed in the PR diff. Disposition unchanged.
- **baseline:B3** — the new lib tools run with developer privileges like `install.sh`; they are small, stdlib-only, unit-tested, and write only under `docs/sdl/`. `accept` disposition unchanged.
- **baseline:B1** — the tools ship via the same governance clone as `validate.py`, but unlike it they never run in consumer CI, so the blast radius is a workstation, not every consumer's `GITHUB_TOKEN`. Existing mitigations (PR review, unit tests, self-gate) apply.
- **2026-06-11-reduce-human-interaction** — wrote no numbered threats; its concern (removing checkpoints must not remove evidence) carries directly into T2.

## Out-of-scope threats

- INDEX.md content injection from cycle files — cycle files are repo-controlled, pipes are escaped, and INDEX is informational (never a gate input); owner: PR review of cycle content.
- `gen_index.py --check` in CI — read-only, no secrets touched; covered by the existing CI posture (baseline:B6 pins).
- `new_cycle.py` importing `validate.py` — same directory, same trust domain, same distribution channel.

## Noted for future cycles

- If these tools ever run in consumer CI (e.g. an auto-scaffolding bot), re-threat-model: branch names on fork PRs are fully attacker-controlled there, and the write target is no longer the developer's own checkout.
- If INDEX summaries ever feed automation rather than human readers, revisit content-injection handling beyond pipe escaping.
