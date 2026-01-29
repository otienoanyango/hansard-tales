# ADR 001: Use SQLite for Development

## Status

Accepted

## Context

The Hansard Tales system requires a relational database for storing structured parliamentary data (documents, statements, MPs, bills, votes, etc.). We need to choose a database that:

1. Works well for local development
2. Supports the same SQL features as production
3. Requires minimal setup
4. Can be easily migrated to production database

The main options considered were:

- **SQLite**: File-based, zero-configuration, built into Python
- **PostgreSQL**: Production-grade, requires server setup
- **MySQL**: Production-grade, requires server setup

## Decision

We will use **SQLite for development** and **PostgreSQL for production**.

### Rationale

**SQLite for Development:**
- Zero configuration required
- No server process to manage
- Database is a single file (easy to reset/backup)
- Built into Python standard library
- Supports most SQL features needed
- Fast for development workloads
- Easy to include in version control (for test fixtures)

**PostgreSQL for Production:**
- Industry-standard for production workloads
- Better concurrency handling
- Advanced features (JSONB, full-text search, etc.)
- Better performance at scale
- Robust backup and replication

### Implementation

Use SQLAlchemy ORM to abstract database differences:

```python
# Development
DATABASE_URL = "sqlite:///data/hansard.db"

# Production
DATABASE_URL = "postgresql://user:pass@host:5432/hansard_tales"
```

SQLAlchemy handles dialect differences automatically.

## Consequences

### Positive

- **Fast Development**: No database server setup required
- **Easy Testing**: Each test can use a fresh in-memory database
- **Portability**: Database is a single file
- **Low Barrier to Entry**: New developers can start immediately
- **Cost Effective**: No database hosting costs for development

### Negative

- **Feature Parity**: Some PostgreSQL features not available in SQLite
  - Mitigation: Use SQLAlchemy abstractions, avoid database-specific features
- **Concurrency Limitations**: SQLite has limited concurrent write support
  - Mitigation: Not an issue for single-developer workflows
- **Migration Testing**: Need to test migrations on both SQLite and PostgreSQL
  - Mitigation: CI/CD pipeline tests against PostgreSQL

### Neutral

- **Two Database Systems**: Need to maintain compatibility with both
  - Mitigation: SQLAlchemy handles most differences
  - Use Alembic migrations that work on both databases

## Notes

### SQLite Limitations to Avoid

1. **No ALTER TABLE for some operations**: Use Alembic batch mode
2. **Limited concurrent writes**: Not an issue for development
3. **No native UUID type**: Use string representation
4. **Case-insensitive LIKE by default**: Use COLLATE NOCASE explicitly

### Testing Strategy

- Unit tests: Use in-memory SQLite (`:memory:`)
- Integration tests: Use file-based SQLite
- CI/CD: Test against PostgreSQL container

## References

- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [SQLAlchemy Dialects](https://docs.sqlalchemy.org/en/14/dialects/)
- [Alembic Batch Operations](https://alembic.sqlalchemy.org/en/latest/batch.html)

## Related ADRs

- None (first ADR)

## Date

2025-01-15
