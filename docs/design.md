# MnemoForge POC Design

## Goal

Provide one auditable memory service that multiple agents and business services can read and update through a stable API. The POC keeps the memory record, source event, feedback, version relationship, activation event, and tenant boundary explicit.

## Architecture

```text
client services
      |
      v
stateless Memory API
      |
      +--> PostgreSQL facts, events, feedback, versions
      +--> pgvector embeddings
      +--> lifecycle policy for activation and decay
      +--> tenant and scope filters
```

The API is the policy boundary. PostgreSQL is the canonical store. Embedding generation is an adapter so the POC can use a remote provider or a deterministic test implementation without changing the memory contract.

## POC behaviors

### Shared reads

A memory written by one service is readable by another service only when the tenant and scope allow it. Search responses include the memory ID, current version, source event ID, status, score components, and activation reason.

### Version replacement

A new version points to the version it supersedes. The old version remains queryable for audit and historical reads. Current reads prefer the active version.

### Feedback

The API accepts `accepted`, `rejected`, `corrected`, and `useful` feedback. Feedback is append-only and changes future ranking through a transparent score adjustment.

### Ninety-day decay

The POC uses a query-time decay score. A 30-day half-life is the initial test value. A memory that has not been activated for 90 days remains stored but enters `cooling` or `dormant` ranking. Restore creates an event and returns the memory to active ranking.

```text
decay(age_days) = exp(-ln(2) * age_days / 30)
```

The formula is a testable starting policy. It is not a permanent product decision.

### Tenant isolation

Every read and write requires a tenant ID. Repository queries apply tenant filtering before lexical, vector, or version expansion. The POC exposes the same rule in the API and in the PostgreSQL adapter.

## Canonical entities

- `memory_records` stores the current and historical memory versions.
- `source_events` stores sanitized provenance events.
- `memory_feedback` stores append-only feedback.
- `memory_access_events` stores activation and access signals.
- `memory_outbox` stores retryable embedding and maintenance work.

## Sanitization rules

- Use placeholders such as `tenant_demo`, `subject_demo`, and `source_demo`.
- Do not include real service URLs, internal IP addresses, file system paths, user IDs, emails, tokens, database URLs, customer names, robot serial numbers, ticket IDs, or signed URLs.
- Keep secrets out of source, tests, fixtures, screenshots, logs, and commit messages.
- Keep sample embeddings deterministic and synthetic.
- Keep the public README and design document independent of any private deployment.

## Resource boundary

The first local POC targets 10,000 memories, 768-dimensional embeddings, one PostgreSQL instance, and a 20 GB data volume. The POC does not install, start, or package Docker.

## Non-goals

- Production deployment or high availability
- Authentication provider integration
- Background model training
- Automatic deletion of old memories
- QMD integration
- Graph database integration
