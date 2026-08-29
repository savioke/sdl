# 04 — Verification

<!-- SVV-1: Security requirements testing. SVV-2: Threat mitigation testing.
     SVV-3: Vulnerability testing. DM-1: Defect management. -->

## Review pass

- **Reviewer:** <agent + dev name(s)>
- **Date:**
- **Diff range:** <merge-base..HEAD>

## Checks performed <!-- SVV-1, SVV-2 -->

<!-- Write a subsection ONLY for categories the diff actually touches.
     Collapse all non-applicable categories into the single "Not applicable"
     line at the end. Most changes touch two to four categories. -->

### <Category the diff touches, e.g. "New SQL queries">

- **Finding:**
- **References:** <file:line, file:line>

<!-- Repeat for each category the diff touches, then one collapsed line: -->

**Not applicable (no code in these areas):** <comma-separated list of the categories that don't apply>

## Defects found and fixed during review <!-- DM-1 -->

<!-- OPTIONAL — omit the section entirely when there is nothing to record.
     Only defects in a security control, or in a mitigation 02 claims. One to
     three sentences each: what was wrong, what it allowed, what fixed it.
     Anything else found during review is recorded by the commit that fixed it.
     A concern investigated and found not to be a defect is not recorded here. -->

## Static analysis and SBOM <!-- SVV-3, SM-9 -->

<!-- Existing tooling output relevant to this change. Flagged issues addressed. -->

## Residual risks <!-- DM-1 -->

<!-- Anything not verified or accepted as known risk. Each entry should be
     specific enough that a future cycle can carry it forward via .sdl-meta.yml.
     Only risks that live in the code as it stands now. Code this diff deleted
     has no residual risk, and neither does functionality that moved to another
     repo — those go in "Risks closed by removal" below and are done. -->

| ID  | Description | Severity | Disposition | Carry-forward target |
|-----|-------------|----------|-------------|----------------------|
| R1  |             |          | accept | defer | mitigate-later |  |

## Risks closed by removal

<!-- OPTIONAL — omit the section entirely when this diff removed nothing.
     One line each, past tense and final:
       "R2 (2026-05-01-token-cache): closed by removal of the token cache."
       "B3: closed by removal of the legacy admin endpoint; row dropped from baseline.md."
     No caveats about what would happen if the code came back, and no notes on
     what a project the code moved to should do about it. That belongs in that
     project's own SDL docs, not here. -->
