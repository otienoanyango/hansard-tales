# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) for the Hansard Tales project. ADRs document significant architectural decisions made during the development of the system.

## What is an ADR?

An Architecture Decision Record (ADR) is a document that captures an important architectural decision made along with its context and consequences.

## Format

Each ADR follows this structure:

1. **Title**: Short noun phrase
2. **Status**: Proposed, Accepted, Deprecated, Superseded
3. **Context**: What is the issue we're seeing that is motivating this decision?
4. **Decision**: What is the change we're proposing/making?
5. **Consequences**: What becomes easier or more difficult to do because of this change?

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [001](001-use-sqlite-for-development.md) | Use SQLite for Development | Accepted |
| [002](002-chromadb-vs-qdrant.md) | ChromaDB for Development, Qdrant for Production | Accepted |
| [003](003-pydantic-for-data-validation.md) | Use Pydantic for Data Validation | Accepted |
| [004](004-css-selectors-for-scraping.md) | Use CSS Selectors for Web Scraping | Accepted |
| [005](005-standardized-filenames.md) | Standardized Filename Generation | Accepted |
| [006](006-download-tracking-table.md) | Download Tracking Table for Duplicate Prevention | Accepted |
| [007](007-prometheus-and-sentry.md) | Prometheus for Metrics, Sentry for Errors | Accepted |
| [008](008-property-based-testing.md) | Property-Based Testing with Hypothesis | Accepted |

## Creating New ADRs

When making a significant architectural decision:

1. Create a new file: `NNN-title-with-dashes.md`
2. Use the next available number (NNN)
3. Follow the standard format
4. Update this README index
5. Submit for review via pull request

## References

- [Michael Nygard's ADR template](https://github.com/joelparkerhenderson/architecture-decision-record)
- [ADR GitHub Organization](https://adr.github.io/)
