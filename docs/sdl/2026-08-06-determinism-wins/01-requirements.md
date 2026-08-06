# 01 — Requirements

<!-- SR-1: Product security context. SR-2: Threat model inputs. -->

## Summary

Three cycle steps that never needed a model become commands. `lib/dep_facts.py`
answers dependency triage as an exit code and generates the record's Updates
table from the diff; `lib/open_risks.py` lists the residual risks earlier cycles
left open; `lib/cycle_stamp.py` stamps the reviewer, date, and diff range a
review artifact records. All three replace prose instructions an agent
previously reasoned through, and the first two remove a step where a value was
transcribed by hand into an audit artifact. The motivation is cost: the process
is adopted voluntarily, and every minute a small PR spends waiting on an agent
is an argument against adopting it.

## Scope

In scope: the three tools, their tests, the skill prose that calls them, a
version-comment capture group added to `validate.PIN_LINE_RE`, and this repo's
`self-check.yml` (test discovery and tool smoke-runs).

Out of scope, deliberately: the gate's own behavior — `validate.py`'s checks are
unchanged, so nothing that passed before can fail now. Also out of scope, and
noted for later: an OSV advisory lookup (network dependency and a new failure
mode, wanted but not this cycle), and a threat-ID coverage check in the
validator, which would change gate outcomes and therefore needs a major release
rather than this minor one.

## Assets touched <!-- SR-1 -->

Integrity assets per `baseline.md`: the three new files ship inside
`plugins/sdl/` and reach consumer workstations and CI through the release
channel, so they join the set the baseline already tracks. The skill
instructions changed are already-listed integrity assets.

New for this cycle: two of the tools **write into SDL artifacts** —
`dep_facts.py --write` into `dep-update.md`, `cycle_stamp.py --write` into
`04-verification.md`. Those artifacts are the audit evidence the whole process
exists to produce. Before this change no tool modified an artifact's content;
`new_cycle.py` only copies templates.

## Trust boundaries crossed <!-- SR-2 -->

No new boundary. Per `baseline.md` the standing crossings are this repo →
consumer CI, and this repo → developer workstation; these tools ship across the
same ones the validator and skills already do, run locally against a git
checkout with the developer's own privileges, and open no network connection.

What changes *inside* the existing boundary is narrower and worth naming: a
program now edits an attestation artifact that only a human or an agent used to
write.

## Data classification <!-- SR-1 -->

Unchanged. Public repo, no secrets, no PII, no customer data. The tools read the
git diff and files under `docs/sdl/`, all already public.

## External inputs introduced <!-- SR-2 -->

None. No network calls, no new environment variables, no listeners. Input is
`git diff` output and repo-local markdown. Stdlib only, per the baseline's
standing requirement that this repo's tooling carry no dependency
supply-chain of its own.

## Security requirements <!-- SR-3, SR-4 -->

- A tool that writes an audit artifact must touch only the fields it owns, and
  must never fill in an attestation — no tool checks a box on a human's behalf.
- A generated artifact must state the limits of its own coverage, so a reader
  cannot mistake partial generation for a completed check.
- The gate's verdicts must not change: no previously-passing PR may fail.
- No new runtime dependency; standard library only.

## Related prior cycles

- `2026-07-09-dep-update-tier` — defined the routine tier, its triage table, and
  the classifier this cycle exposes to the author.
- `2026-08-06-use-sub-agent-for-dep-update` — moved `sdl-dep-update` to a
  detached Sonnet subagent. This cycle shrinks what that agent has to get right.
- `2026-07-09-faster-maybe` — the standing goal of cutting per-cycle overhead.

## Carried-forward residual risks

None claimed. `open_risks.py` (this cycle's own tool) reports seven open items;
none is closed here.

Worth recording rather than claiming:
`2026-08-06-use-sub-agent-for-dep-update:R2` ("record honesty under Sonnet is
unmeasured") is *narrowed* by this cycle — the versions in a dependency record
are now generated rather than transcribed, so the largest category of silent
error is gone. It is not closed: R2 is about the record as a whole, including
the attested checks, which remain the agent's word. Following the convention
this repo already uses, a partially-addressed risk stays open in its own cycle
rather than being claimed here.
