# 03 — Implementation

<!-- SI-1: Security implementation review. SI-2: Secure coding standards. -->

## Summary of changes

Two deterministic tools plus skill updates. `lib/new_cycle.py` scaffolds a cycle folder (slug normalization, template copy, `.sdl-meta.yml` including the dep-update class) and refuses to overwrite or re-scaffold; `lib/gen_index.py` regenerates `docs/sdl/INDEX.md` from cycle metadata, with a `--check` mode wired into `self-check.yml`. Both are stdlib-only with unit tests (`lib/test_new_cycle.py`, `lib/test_gen_index.py`). The `sdl-spec`, `sdl-review`, and `sdl-dep-update` skills now call the tools instead of hand-performing those steps, and `sdl-spec` gains a fast path: for small, already-implemented changes, all four artifacts are authored in one pass with no interview. Plugin version 0.4.0 → 0.5.0. `lib/validate.py` and the templates are untouched (verified: zero diff lines), so the gate's behavior is unchanged.

## Mitigations implemented <!-- SI-1 -->

| Threat | Mitigation | Location | Commit |
|--------|------------|----------|--------|
| T1 | Slug alphabet restricted to `[a-z0-9-]` by construction; empty result fails closed; existing folder/branch-cycle refused; missing `docs/sdl/` errors instead of creating trees. Unit-tested against traversal inputs. | `lib/new_cycle.py:38-52,74-88`; `lib/test_new_cycle.py` (`test_traversal_attempts_cannot_escape`, `test_cycle_stays_under_docs_sdl`) | pending — working tree at review time |
| T2 | Fast-path wording scoped to small/no-new-boundary changes with a mandatory drop-back to the interview; `validate.py` untouched so artifact gating is unchanged; PR review sees artifacts beside the diff. | `skills/sdl-spec/SKILL.md` "Fast path" section | pending — working tree at review time |

## Secure coding practices applied <!-- SI-2 -->

- Both tools are Python standard-library only (baseline standing requirement), no `shell=True` anywhere — the only subprocess use is inherited from `validate.py`'s list-arg `run()`.
- Fail-closed error handling: unparseable dates, missing templates, existing folders, and empty slugs all exit non-zero with a message rather than proceeding (`lib/new_cycle.py:50,78-85,127`).
- `gen_index.py` writes exactly one file (`lib/gen_index.py:126`), escapes `|` in cell content, and produces byte-stable output (`--check` verifies).
- Regexes on branch names and meta files are linear character classes — no nested quantifiers, no ReDoS surface.
- 78 unit tests pass (`python3 -m unittest lib.test_*`); `ruff check lib/` clean.

## Dependencies introduced or changed <!-- SM-9, DM-1 -->

None. No new CI actions either — `self-check.yml` additions reuse the existing SHA-pinned steps.

## Deviations from spec or threat model

None against `01-requirements.md`/`02-threat-model.md`. One addition beyond the original scope sketch: `gen_index.py --check` in CI, which keeps INDEX.md provably current rather than trusting regeneration to happen.
