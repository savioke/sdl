# 02 — Threat Model

<!-- SR-2: Threat model. SD-1, SD-2: Secure design and defense in depth. -->

## Components and data flows

- `lib/dep_facts.py` — reads `git diff base...HEAD`, classifies it with
  `validate.check_dep_class_diff`, and emits a triage verdict plus generated
  record rows. With `--write`, edits `dep-update.md`.
- `lib/open_risks.py` — reads every cycle's `04-verification.md` and
  `.sdl-meta.yml`. Read-only.
- `lib/cycle_stamp.py` — reads git metadata; with `--write`, edits three field
  lines in `04-verification.md`.
- **New flow:** program → SDL artifact. Previously artifacts were written only by
  a human or an agent; `new_cycle.py` copied templates but never modified
  content.
- **Changed flow:** the dependency triage decision now reaches the author as an
  exit code from the same function the gate calls, instead of via the agent's
  reading of a prose table.
- Unchanged: the gate, the release channel, the trust boundaries, and the human
  read-before-push attestation.

## Threats <!-- SR-2 -->

### T1 — A tool corrupts the audit artifact it is editing

- **Category:** Tampering
- **Component / flow:** `dep_facts.py --write` → `dep-update.md`;
  `cycle_stamp.py --write` → `04-verification.md`
- **Description:** These are the first programs to modify the *content* of an SDL
  artifact. A defect in the region-matching could drop findings, duplicate a
  field, or rewrite content outside the intended scope — in a file that is the
  evidence of record, where a quiet deletion is worse than a crash.
- **Likelihood / Impact:** low / medium
- **Mitigation:** Both writers are scoped by construction and fail loudly.
  `fill_updates_table` replaces only the lines between the `| package |` header's
  separator and the first non-table line, and raises `ValueError` if the header
  is absent rather than writing nothing and reporting success. `stamp` rewrites
  only three labelled field lines, `count=1` each, and returns the labels it
  could not find so the caller exits non-zero. Neither writer appends. Tests pin
  the boundaries directly: the Checks boxes and Notes survive a table rewrite,
  findings and the residual-risk table survive a stamp, re-running either
  replaces rather than duplicates, and a missing anchor is an error.
- **Mitigation type:** preventive
- **Defense in depth notes:** SD-2 — `check_dep_record` re-parses the written
  record and rejects a stub, an empty table, or a declared major; `check_nonstub`
  rejects an artifact reduced to scaffolding. Both run in CI regardless of which
  tool produced the file. The human reads the record before pushing, unchanged.

### T2 — Generated output is read as more complete than it is

- **Category:** Repudiation (false assurance)
- **Component / flow:** `dep_facts.py` → author → `dep-update.md` Checks section
- **Description:** A generated table carries an air of authority that invites
  over-trust, and this tool's coverage is genuinely partial in two ways. It does
  not parse language-ecosystem lockfiles, so a diff that bumps npm or Go packages
  yields no rows for them; and two escalation triggers — manifest changes beyond
  version fields, and an advisory affecting the new version — are not
  mechanically detectable at all. An author who reads "ROUTINE" plus a table as
  "the machine checked it" could check attestation boxes for work nobody did,
  which is exactly the falsified audit trail the tier's design warns against.
- **Likelihood / Impact:** medium / medium
- **Mitigation:** The tool states its limits on every run, rather than in
  documentation the reader may not have open. Changed manifests are listed by
  name under an explicit "this tool does not parse ecosystem lockfiles"; both
  non-mechanical triggers print under "Still yours to verify"; and a diff with no
  action-pin bumps emits an explicit marker instead of an empty-looking table.
  `--write` refuses rather than writing an empty table. The Checks boxes and
  Notes are never touched by any tool. Tests assert each of these outputs.
- **Mitigation type:** preventive
- **Defense in depth notes:** SD-2 — `check_dep_record` independently rejects a
  record that declares no updates, so a manifest-only bump cannot pass with the
  empty table the generator would leave. The tier's coverage limits are also
  stated in `docs/dependency-updates.md`.

### T3 — A defect in the shared pin regex is contradicted by nothing

- **Category:** Tampering (loss of defense in depth)
- **Component / flow:** `PIN_LINE_RE` → both `dep_facts` and `validate`
- **Description:** One regex identifies a pinned `uses:` line for both the tool
  that writes the record and the gate check that reads the diff. The record's
  versions therefore agree with that check by construction — which is the point —
  but it means a defect in the regex is not surfaced by the two sides differing.
- **Likelihood / Impact:** low / medium
- **Mitigation:** Bounded on three sides. The regex **fails closed**: a `uses:`
  line it does not positively recognize as a SHA pin carrying a parseable version
  comment is rejected as a non-pin change, so an unfamiliar or malformed comment
  escalates to a full cycle rather than being parsed into a wrong row. The
  sharing is confined to pin *identification* — `check_dep_record` reads the
  written markdown with separate code (`parse_version_major` over table cells)
  and never consults `PIN_LINE_RE`, so major-bump rejection does not depend on
  it. And `check_pins.py` resolves each pin comment against the upstream tag,
  catching a comment that misstates what its SHA is.
- **Mitigation type:** preventive
- **Defense in depth notes:** SD-2 — the third check is not guaranteed
  everywhere: `check_pins.py` reaches consumers by policy adoption rather than
  through the gate (`2026-07-09-dep-update-tier:R2`, still open), so in a
  consumer repo that skips it the pin comment is unverified. Human
  read-before-push is unchanged. Residual recorded in 04 (R1).

## Threats inherited from prior cycles <!-- SR-2 -->

- **`baseline:B2`** (skill-instruction injection) applies and its "any skill
  change" revisit trigger fires: three skills changed. Not widened — the skills
  gain no tools or capabilities, and now instruct the agent to run repo-local
  scripts that ship through the same gated, reviewed channel as the skills
  themselves. Confirmed in scope, disposition unchanged.
- **`baseline:B1`** (a change to shipped tooling runs in every consumer's
  context) applies to three new shipped files. Contained by the same controls: PR
  review, unit tests, the self-gate, and the minor-release contract. None of the
  three runs in consumer CI — the gate calls only `validate.py` — so their blast
  radius is developer workstations, narrower than B1's stated worst case.
- **`2026-07-09-dep-update-tier` T3** (manifest *content* can carry executable
  config; accepted at the routine tier, owned by policy) is unchanged, and is
  precisely the gap T2 above works to keep visible.

## Out-of-scope threats

- `open_risks.py` has no threat of its own worth a stanza: read-only,
  repo-local, no network, and its output informs an interview rather than a gate
  decision. A bug makes it under- or over-report open risks to a human who can
  check the files. Recorded so the next maintainer need not re-derive it.
- Malicious input to the tools via a crafted diff or artifact: an attacker who
  can write to the branch can write the record directly. The tools grant no
  capability that editing the file did not already grant.
- Vendor/model dependence: unchanged, and reduced at the margin — three steps
  that needed a model now need none, so consumers on any agent get identical
  answers.

## Noted for future cycles

- An OSV advisory lookup would close the larger half of T2 by making the one
  remaining high-value trigger mechanical. It needs a network-failure story
  (fail loudly, never degrade to "no advisories found") before it can ship.
- A threat-ID coverage check — every `T<n>` in `02` has a row in `03` — is the
  cheapest of the semantic checks `validate.py`'s own docstring defers. It
  changes gate outcomes and so requires a major release.
- If ecosystem lockfile parsing is ever added to `dep_facts`, T2's mitigation
  must be re-examined: "states its limits" stops being sufficient once a reader
  reasonably expects full coverage.
- `open_risks.py` treats a `carry_forward:` claim as closure. The repo's
  convention is that a partially-addressed risk is re-recorded as a new R-item in
  the claiming cycle, which keeps that correct — if the convention ever drifts,
  the tool will under-report.
