---
spec_id: mnemo-forge-poc
objective: Build a sanitized MIT-licensed PostgreSQL + pgvector + MnemoForge API POC under the test workspace.
created: 2026-11-11
status: complete
---

## Constitution

- The project is a new public repository under the test workspace.
- The repository is MIT licensed.
- The repository contains no credentials, access-bearing URLs, internal hostnames, internal IPs, private user IDs, customer data, robot serial numbers, ticket IDs, or unsanitized logs.
- The POC is code and documentation only. It must not install Docker, start Docker, start PostgreSQL, deploy services, or publish to GitHub during this phase.
- PostgreSQL is the canonical store. The API owns tenant filtering, lifecycle scoring, feedback, and version policy.
- Old memory versions remain auditable. Decay lowers ranking and does not delete data.

## Acceptance items

- [x] 1. The project has an MIT `LICENSE`, a public `README.md`, and a sanitized `docs/design.md` — verify: `test -f LICENSE && test -f README.md && test -f docs/design.md` — expected: exit 0 and no secret-like values in the files.
- [x] 2. The project defines a stable Memory API contract for write, search, read, access, feedback, restore, and version replacement — verify: `rg -n "write_memory|search_memory|record_access|feedback|restore|supersedes" src tests docs` — expected: every operation appears in code or tests.
- [x] 3. A service can write a memory and another service can read it within the same tenant and scope — verify: `pytest -q tests/test_shared_reads.py` — expected: all tests pass.
- [x] 4. Cross-tenant reads and writes are rejected or return no data — verify: `pytest -q tests/test_tenant_isolation.py` — expected: all tests pass and no cross-tenant record is returned.
- [x] 5. A memory that is 90 days inactive is ranked lower but remains recoverable — verify: `pytest -q tests/test_decay_restore.py` — expected: the 90-day score is lower than the fresh score, the record remains stored, and restore returns it to active ranking.
- [x] 6. Feedback is append-only, idempotent, and changes ranking according to the documented policy — verify: `pytest -q tests/test_feedback.py` — expected: duplicate feedback does not duplicate state and accepted/rejected feedback changes the score.
- [x] 7. A new version supersedes an old version while preserving historical reads — verify: `pytest -q tests/test_version_replacement.py` — expected: current search returns the new version, historical lookup returns the old version, and the supersedes link is present.
- [x] 8. The PostgreSQL adapter uses parameterized queries and applies tenant filters before result expansion — verify: `rg -n "execute|tenant_id|parameter" src && pytest -q tests/test_repository_contract.py` — expected: no string-built SQL path is used for user data and tests pass.
- [x] 9. The POC has a deterministic test repository so the feature tests run without Docker or a live database — verify: `pytest -q` — expected: exit 0 without starting external services.
- [x] 10. A secret and private-data scan covers source, tests, fixtures, and documentation — verify: `python scripts/sanitize_check.py` — expected: exit 0 with no findings.

## Clarifications

- The project name is `mnemo-forge`.
- The first implementation may use a deterministic in-memory repository for feature tests. The PostgreSQL adapter and SQL schema are required code artifacts, but no database process is started in this phase.
- The API framework is selected during implementation if it preserves the contract and keeps the POC easy to run.
- The first embedding adapter is deterministic and local to tests. A production embedding provider is outside this POC.
- `cooling` and `dormant` are ranking states. They do not delete or overwrite the source record.
- Tenant isolation is required at the API and repository layers. PostgreSQL RLS may be added as a defense-in-depth schema option, but tests must not depend on a live PostgreSQL server.

## Plan

1. Create the Python package, public API models, lifecycle policy, and deterministic repository.
2. Add the PostgreSQL schema and adapter with parameterized SQL.
3. Add the API transport layer without starting it.
4. Add feature tests for shared reads, tenant isolation, decay and restore, feedback, and version replacement.
5. Add sanitization checks, README usage, and MIT license verification.
6. Run static checks and unit tests only.

## Verification audit

- 2026-11-11: `PYTHONPATH=src python3 -m unittest discover -s tests -v` passed 7 tests.
- 2026-11-11: `python3 -m compileall -q src tests scripts` passed.
- 2026-11-11: `python3 scripts/sanitize_check.py` passed.
- 2026-11-11: route, SQL schema, MIT license, clean Git status, and public-data pattern checks passed.
- The environment did not have pytest, and no dependency installation was performed. The equivalent standard-library unittest runner was used to keep this phase code-only.
