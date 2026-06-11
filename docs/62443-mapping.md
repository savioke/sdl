# IEC 62443-4-1 Practice Mapping

How fields in our SDL artifacts satisfy the requirements of IEC 62443-4-1. Auditors ask "show me how you meet practice X" — this document points at the artifact field that answers, and the inline `<!-- TAG -->` comments in the templates make each artifact self-explanatory at the field level.

Scope is what we currently claim to cover. Practices not listed are out of scope for this iteration; revisit when the program matures.

## Practice areas

IEC 62443-4-1 organizes requirements into eight practices:

| Practice | Name | Coverage in this program |
|----------|------|--------------------------|
| SM       | Security Management              | Partial — process is documented and version-controlled in this repo |
| SR       | Specification of Security Requirements | Full — `01-requirements.md`, `02-threat-model.md` |
| SD       | Secure by Design                 | Full — `02-threat-model.md` mitigations, `03-implementation.md` |
| SI       | Secure Implementation            | Full — `03-implementation.md`, `sdl-review` skill |
| SVV      | Security Verification and Validation Testing | Full — `04-verification.md`, CI workflow |
| DM       | Defect Management                | Partial — residual risks tracked, formal CVD process out of scope here |
| SUM      | Security Update Management       | Out of scope for this repo (handled by ops/release) |
| SG       | Security Guidelines              | Out of scope for this repo (handled by product docs) |

## Field-level mapping

Each row links a specific 62443-4-1 requirement to where evidence lives.

### SM — Security Management

| Req   | Title                              | Evidence |
|-------|------------------------------------|----------|
| SM-1  | Development process                | This repo (`Plan.md`, skill prompts, templates) |
| SM-2  | Identification of responsibilities | Project repo `CODEOWNERS` + PR approval (git merge history) |
| SM-3  | Identification of applicability    | Presence of `docs/sdl/` in project repo |
| SM-5  | Process scoping                    | `.sdl-meta.yml` `scope` and `status` fields |
| SM-9  | Controls on private keys / secrets — applied here as dependency controls | `03-implementation.md` "Dependencies" section, SBOM/CVE scan output |
| SM-13 | Continuous improvement             | Git history of this repo + quarterly sample audits |

### SR — Specification of Security Requirements

| Req   | Title                              | Evidence |
|-------|------------------------------------|----------|
| SR-1  | Product security context           | `01-requirements.md` "Assets touched", "Data classification" |
| SR-2  | Threat model                       | `02-threat-model.md` (whole file) |
| SR-3  | Product security requirements      | `01-requirements.md` "Security requirements" |
| SR-4  | Product security requirements content | `01-requirements.md` "Security requirements" (authn, authz, encryption, logging, validation) |
| SR-5  | Security requirements review       | `04-verification.md` "Checks performed" + PR review |

### SD — Secure by Design

| Req   | Title                              | Evidence |
|-------|------------------------------------|----------|
| SD-1  | Secure design principles           | `02-threat-model.md` "Threats" → "Mitigation" rows |
| SD-2  | Defense in depth design            | `02-threat-model.md` "Defense in depth notes" |
| SD-3  | Security design review             | `02-threat-model.md` review + PR approval |
| SD-4  | Secure design best practices       | `03-implementation.md` "Secure coding practices applied" |

### SI — Secure Implementation

| Req   | Title                              | Evidence |
|-------|------------------------------------|----------|
| SI-1  | Security implementation review     | `03-implementation.md` "Mitigations implemented" table |
| SI-2  | Secure coding standards            | `03-implementation.md` "Secure coding practices applied"; `sdl-review` skill prompt is the standard |

### SVV — Security Verification and Validation Testing

| Req   | Title                              | Evidence |
|-------|------------------------------------|----------|
| SVV-1 | Security requirements testing      | `04-verification.md` "Checks performed" |
| SVV-2 | Threat mitigation testing          | `04-verification.md` "Checks performed" cross-referenced to threat IDs |
| SVV-3 | Vulnerability testing              | `04-verification.md` "Static analysis and SBOM" |
| SVV-4 | Penetration testing                | Out of scope per cycle; tracked at product release level |
| SVV-5 | Independence of testers            | PR review by non-author + `sdl-review` agent pass |

### DM — Defect Management

| Req   | Title                              | Evidence |
|-------|------------------------------------|----------|
| DM-1  | Receiving notifications of security-related issues | `04-verification.md` "Residual risks" + carry-forward in `.sdl-meta.yml` |
| DM-2  | Reviewing security-related issues  | `04-verification.md` "Residual risks" + PR review |
| DM-3  | Assessing security-related issues  | "Severity" / "Disposition" columns in residual risks table |
| DM-4  | Addressing security-related issues | Carry-forward mechanism resolved in subsequent cycles |

## Generating audit reports

A unified report across all project repos can be generated on demand by walking each repo's `docs/sdl/*/` and collecting:

- All `.sdl-meta.yml` files (cycle index, branch, PR, status, dates)
- All inline `<!-- SR-N -->` style tags and the surrounding section content
- PR approval / merge state from git history

The generator script is intentionally not in this repo yet — the data model is stable, the report shape will firm up after we have real cycles to audit.
