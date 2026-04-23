# 04 — Verification

<!-- SVV-1: Security requirements testing. SVV-2: Threat mitigation testing.
     SVV-3: Vulnerability testing. DM-1: Defect management. -->

## Review pass

- **Reviewer:** <agent + dev name(s)>
- **Date:**
- **Diff range:** <merge-base..HEAD>

## Checks performed <!-- SVV-1, SVV-2 -->

<!-- For each security-checks.md category that applied to this diff,
     record the finding. sdl-review writes these with file:line refs. -->

### <Category, e.g. "New SQL queries">

- **Applies:** yes | no
- **Finding:**
- **References:** <file:line, file:line>

## Static analysis and SBOM <!-- SVV-3, SM-9 -->

<!-- Existing tooling output relevant to this change. Flagged issues addressed. -->

## Residual risks <!-- DM-1 -->

<!-- Anything not verified or accepted as known risk. Each entry should be
     specific enough that a future cycle can carry it forward via .sdl-meta.yml. -->

| ID  | Description | Severity | Disposition | Carry-forward target |
|-----|-------------|----------|-------------|----------------------|
| R1  |             |          | accept | defer | mitigate-later |  |

## Sign-off

- [ ] Threat model mitigations verified or residual risk recorded
- [ ] Secure coding checks for applicable categories complete
- [ ] Static analysis and dependency scan reviewed
- [ ] Residual risks documented and dispositioned
