# Security check categories

Categories the `sdl-review` skill considers when inspecting a diff. Not a static rule library — these are prompts for the model to apply its own knowledge of the language, framework, and current best practices in the diff.

For each category, decide whether the diff introduces or modifies code in that area. If it does, verify with file:line references. If it does not, mark "no" and skip.

---

## Input handling

- **New external inputs.** HTTP request bodies/params, queue messages, file uploads, IPC, stdin from external processes, env vars sourced from runtime config.
- **New deserialization of untrusted input.** JSON, YAML, pickle, protobuf, msgpack, XML.
- **New file I/O with user-controlled paths.** Path traversal, symlink following, write outside intended directory.
- **Command execution with user-controlled arguments.** Shell injection, argument injection.
- **New regular expressions on untrusted input.** ReDoS potential, especially nested quantifiers.

## Data and persistence

- **New database queries.** Parameterization, ORM query construction, raw SQL, dynamic table/column names from untrusted input.
- **New NoSQL queries.** Operator injection (Mongo `$where`, Redis Lua eval).
- **New cache writes/reads of sensitive data.** Cache key collisions, TTL on sensitive entries.
- **New PII or credential persistence.** Encryption at rest, retention policy alignment.

## Network and transport

- **New external HTTP/RPC calls.** TLS verification, timeouts set, retry/backoff, error handling, response trust.
- **New listening sockets or open ports.** Bind address, default firewall posture.
- **New WebSocket / SSE / long-lived connections.** Authn re-validation, idle timeouts.

## Authentication and authorization

- **New endpoints, RPC methods, queue consumers.** Authn middleware/decorator present, authz check explicit.
- **Changes to existing auth code.** Test coverage, no bypassable role checks, no weakening of session policy.
- **New token issuance or validation.** Algorithm allowlist (no `none`), expiry, audience and issuer checks.
- **New password/secret handling.** Hashing algorithm (Argon2id, bcrypt, scrypt), no plaintext storage, secure comparison.

## Cryptography

- **New cryptographic primitives.** Approved algorithms only (no MD5/SHA1 for security, no ECB, no DES/3DES, no RC4).
- **Hardcoded keys, IVs, salts, nonces.** Reject in source; load from secret manager or KDF.
- **Random number generation for security.** Use CSPRNG (`crypto/rand`, `secrets`, `os.urandom`), never `math/rand` or `Math.random`.
- **New TLS configuration.** Minimum version 1.2, certificate validation enabled, no `InsecureSkipVerify` / `verify=False`.

## Secrets

- **Secrets in source.** API keys, tokens, passwords, private keys committed.
- **Secrets in logs.** Tokens, passwords, full PII written to log statements.
- **Secrets in error messages or HTTP responses.** Stack traces with credentials, debug output to clients.

## Logging and observability

- **New logging of user data.** PII redaction, structured fields, sensitive data classification.
- **New audit-relevant events.** Auth events, privilege changes, data access on regulated assets — should be logged.
- **Log injection.** Untrusted input written verbatim into structured logs.

## Concurrency and resource use

- **New unbounded loops over user input.** DoS potential.
- **New unbounded allocations from user input.** Memory exhaustion (large request body, deep nesting).
- **New goroutines / threads / async tasks spawned per request.** Concurrency limits, leak potential.
- **New locks or shared state.** Deadlock or race potential, especially around auth state.

## Dependencies

- **New direct dependencies.** Maintenance status, registry source (typosquat-prone names), license, transitive footprint.
- **Major version bumps.** Breaking change review, especially security-relevant libraries (crypto, auth, parsers).
- **Removed dependencies.** Confirm no orphaned uses; confirm replacement is at least as secure.

## Frontend and browser-facing (when applicable)

- **New rendering of user-controlled HTML / DOM.** XSS via innerHTML, dangerouslySetInnerHTML, attribute injection.
- **New URL construction with user input.** Open redirect, javascript: URLs.
- **New CORS or CSP changes.** Tightening only; loosening requires explicit justification.
- **New cookie handling.** Secure, HttpOnly, SameSite attributes set appropriately.

## Build, CI, and supply chain

- **New CI workflow steps.** Secrets exposure, third-party action pinning by SHA, permissions block scoped.
- **New container base images.** Pin by digest, scan, minimize footprint.
- **New install scripts.** Network fetches in build, integrity verification.

## Native and lower-level (C/C++)

- **New buffer handling.** Bounds checks, prefer safe-string APIs, no `strcpy`/`sprintf`/`gets`.
- **New integer arithmetic on sizes.** Overflow before allocation or comparison.
- **New manual memory management.** Lifetime, double-free, use-after-free.
- **New format strings with user input.** `printf("%s", user_input)`, never `printf(user_input)`.

---

When in doubt about whether a category genuinely applies, err toward applying it — consider it and reach a verdict rather than skipping silently. Silent skips are how things get missed.

A verdict of "does not apply" for a category the diff never touches goes in the single collapsed "Not applicable" line in `04-verification.md`, not its own `### Category` subsection. Reserve subsections for categories the diff touches.
