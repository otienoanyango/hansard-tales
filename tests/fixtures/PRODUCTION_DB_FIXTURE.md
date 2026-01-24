# Production Database Fixture

## Overview

The `production_db` fixture provides a temporary database with the complete production schema for testing. This fixture ensures schema consistency across all tests by using the production `initialize_database()` function.

## Purpose

**Problem**: The old `temp_db` fixture created a custom schema that could diverge from production, leading to integration test failures.

**Solution**: The `production_db` fixture uses the actual production database initialization code, ensuring tests always use the same schema as production.

## Usage

### Basic Usage

```python
def test_my_feature(production_db):
    """Test with production database schema."""
    conn = sqlite3.connect(production_db)
    cursor = conn.cursor()
    
    # Use production schema
    cursor.execute("SELECT * FROM parliamentary_terms")
    # ...
    
    conn.close()
```

### What the Fixture Provides

The `production_db` fixture:

1. **Creates a temporary database file** - Automatically cleaned up after test
2. **Initializes production schema** - Uses `initialize_database()` from production code
3. **Runs all migrations** - Applies all database migrations automatically
4. **Inserts current term** - Adds term 13 (2022-09-08 to 2027-09-07) for convenience
5. **Cleans up automatically** - Removes temporary file after test completes

### Schema Includes

The production database includes:

**Tables:**
- `parliamentary_terms` - Parliamentary sessions
- `mps` - Members of Parliament
- `mp_terms` - Junction table linking MPs to terms
- `hansard_sessions` - Daily parliamentary sittings
- `statements` - Individual MP statements
- `downloaded_pdfs` - PDF download tracking

**Views:**
- `current_mps` - Currently serving MPs
- `mp_current_term_performance` - MP performance in current term
- `mp_historical_performance` - MP performance across all terms

**Indexes:**
- Performance indexes on all major tables
- Unique indexes for duplicate prevention

**Migrations:**
- `add_download_metadata` - Adds `period_of_day` and `session_id` columns

## Migration from temp_db

### Old Pattern (Deprecated)

```python
def test_old_way(temp_db):
    """Old test using temp_db."""
    # Uses custom schema that may diverge from production
    conn = sqlite3.connect(temp_db)
    # ...
```

### New Pattern (Recommended)

```python
def test_new_way(production_db):
    """New test using production_db."""
    # Uses production schema - guaranteed consistency
    conn = sqlite3.connect(production_db)
    # ...
```

### Why Migrate?

1. **Schema Consistency** - Tests use exact production schema
2. **Catch Issues Early** - Schema mismatches caught in unit tests
3. **Realistic Testing** - Tests run against production-like database
4. **Automatic Migrations** - All migrations applied automatically
5. **Better Maintenance** - Single source of truth for schema

## Backward Compatibility

The `temp_db` fixture is still available for backward compatibility but is **deprecated**. It includes a deprecation notice in its docstring.

**Migration Strategy:**
1. New tests should use `production_db`
2. Existing tests can continue using `temp_db` temporarily
3. Gradually migrate existing tests to `production_db`
4. Eventually remove `temp_db` fixture

## Implementation Details

### Location

The fixture is defined in `tests/conftest.py`:

```python
@pytest.fixture
def production_db():
    """Create temporary database with production schema."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    # Use production initialization
    initialize_database(db_path)
    
    # Run all migrations
    migrate(db_path, verify=False)
    
    # Insert current parliamentary term
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO parliamentary_terms (term_number, start_date, end_date, is_current)
        VALUES (13, '2022-09-08', '2027-09-07', 1)
    """)
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    Path(db_path).unlink()
```

### Dependencies

- `hansard_tales.database.init_db.initialize_database` - Production schema initialization
- `hansard_tales.database.migrations.add_download_metadata.migrate` - Migration runner

## Testing the Fixture

The fixture itself is tested in `tests/test_production_db_fixture.py`:

```bash
# Run fixture tests
pytest tests/test_production_db_fixture.py -v
```

Tests verify:
- ✅ Database file is created
- ✅ All production tables exist
- ✅ All production views exist
- ✅ All indexes are created
- ✅ Current term is inserted
- ✅ Migration columns exist
- ✅ Schema matches production exactly
- ✅ Foreign keys are defined
- ✅ Unique constraints exist
- ✅ CHECK constraints work
- ✅ Cleanup happens automatically

## Benefits

### For Developers

1. **Confidence** - Tests use production schema
2. **Speed** - No need to manually create schema
3. **Simplicity** - Just use the fixture
4. **Consistency** - All tests use same schema

### For Testing

1. **Realistic** - Tests run against production-like database
2. **Complete** - All tables, views, indexes included
3. **Migrated** - All migrations applied automatically
4. **Clean** - Fresh database for each test

### For Maintenance

1. **Single Source** - Schema defined in one place
2. **Automatic Updates** - Schema changes propagate to tests
3. **No Drift** - Tests can't diverge from production
4. **Easy Migration** - Just change fixture name

## Common Patterns

### Testing Database Operations

```python
def test_insert_mp(production_db):
    """Test inserting an MP."""
    conn = sqlite3.connect(production_db)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO mps (name, constituency, party)
        VALUES (?, ?, ?)
    """, ("John Doe", "Nairobi", "Party A"))
    
    conn.commit()
    
    cursor.execute("SELECT * FROM mps WHERE name = ?", ("John Doe",))
    result = cursor.fetchone()
    
    assert result is not None
    assert result[1] == "John Doe"
    
    conn.close()
```

### Testing with Current Term

```python
def test_with_current_term(production_db):
    """Test using current parliamentary term."""
    conn = sqlite3.connect(production_db)
    cursor = conn.cursor()
    
    # Current term is already inserted
    cursor.execute("SELECT id FROM parliamentary_terms WHERE is_current = 1")
    term_id = cursor.fetchone()[0]
    
    # Use term_id in your test
    cursor.execute("""
        INSERT INTO hansard_sessions (term_id, date, title, pdf_url)
        VALUES (?, ?, ?, ?)
    """, (term_id, "2024-01-15", "Morning Session", "http://example.com/test.pdf"))
    
    conn.commit()
    conn.close()
```

### Testing Migrations

```python
def test_migration_columns(production_db):
    """Test that migration columns exist."""
    conn = sqlite3.connect(production_db)
    cursor = conn.cursor()
    
    # Migration columns should exist
    cursor.execute("PRAGMA table_info(downloaded_pdfs)")
    columns = [row[1] for row in cursor.fetchall()]
    
    assert 'period_of_day' in columns
    assert 'session_id' in columns
    
    conn.close()
```

## Troubleshooting

### Issue: Column doesn't exist

**Problem**: Test fails with "no such column" error

**Solution**: The column might not be in production schema. Check `hansard_tales/database/init_db.py` to see available columns.

### Issue: Migration not applied

**Problem**: Migration columns missing

**Solution**: Ensure migration is in `hansard_tales/database/migrations/` and is imported in the fixture.

### Issue: Test is slow

**Problem**: Database initialization takes time

**Solution**: This is expected. The fixture creates a complete production database. Consider using module-scoped fixtures for test classes:

```python
@pytest.fixture(scope="module")
def module_production_db():
    """Module-scoped production database."""
    # Same implementation as production_db
    # But shared across all tests in module
```

## Requirements Validated

This fixture validates the following requirements from the test calibration spec:

- **Requirement 3.1**: All tests use production `initialize_database()` function
- **Requirement 3.2**: Tests cannot create custom schemas
- **Requirement 3.5**: Shared fixture creates databases using production initialization

## Related Documentation

- [Test Calibration Spec](.kiro/specs/test-calibration-and-integration-fixes/requirements.md)
- [Database Schema](hansard_tales/database/init_db.py)
- [Migrations](hansard_tales/database/migrations/)
- [Testing Guidelines](testing-guidelines.md)
