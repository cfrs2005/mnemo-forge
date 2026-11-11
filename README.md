# MnemoForge

A small, auditable memory forge for shared agent context.

A small, auditable POC built around PostgreSQL, pgvector, and a stateless Memory API.

## Scope

The first POC covers shared reads across services, tenant isolation, version replacement, feedback, 90-day relevance decay, and explicit restore. It is designed for local development and review. It is not a production deployment package.

## Privacy and sanitization

- Examples use synthetic tenants, subjects, events, and memory content.
- No internal hostnames, credentials, cookies, tokens, customer data, robot serial numbers, or signed URLs belong in this repository.
- Runtime configuration must come from environment variables.
- Public design documents describe generic interfaces and placeholders only.

## License

MIT. See [LICENSE](LICENSE).

## Design

See [docs/design.md](docs/design.md).

## Local checks

These checks use the deterministic in-memory repository. They do not start PostgreSQL, Docker, or an HTTP server.

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 scripts/sanitize_check.py
```

The PostgreSQL adapter and `sql/001_init.sql` are code artifacts for later integration.
