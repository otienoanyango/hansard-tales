# ADR 003: Use Pydantic for Data Validation

## Status

Accepted

## Context

The Hansard Tales system handles complex parliamentary data with strict validation requirements. We need a robust data validation and serialization solution that:

1. Validates data types and constraints
2. Provides clear error messages
3. Supports JSON serialization
4. Integrates with type hints
5. Has good IDE support
6. Performs well

Options considered:

- **Pydantic**: Modern, type-hint based, excellent validation
- **dataclasses**: Built-in, simple, limited validation
- **attrs**: Mature, flexible, more boilerplate
- **marshmallow**: Schema-based, more verbose
- **Manual validation**: Full control, high maintenance

## Decision

We will use **Pydantic v2** for all data models and validation.

### Rationale

**Pydantic Advantages:**
- Type-hint based (Pythonic, modern)
- Automatic validation on instantiation
- Excellent error messages
- JSON serialization built-in
- IDE autocomplete and type checking
- High performance (Rust core in v2)
- Immutable models (frozen=True)
- Extensive validation options

**Example:**

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import date

class Document(BaseModel):
    model_config = ConfigDict(frozen=True)  # Immutable

    title: str = Field(..., min_length=1, max_length=500)
    date: date
    parliament_term: int = Field(..., ge=1, le=20)
    source_hash: str = Field(..., pattern=r'^[a-f0-9]{64}$')

    @field_validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
```

## Consequences

### Positive

- **Type Safety**: Catch errors at validation time, not runtime
- **Self-Documenting**: Models serve as documentation
- **IDE Support**: Autocomplete and type checking work perfectly
- **JSON API Ready**: Automatic serialization/deserialization
- **Immutability**: Frozen models prevent accidental mutations
- **Performance**: Pydantic v2 is very fast (Rust core)
- **Validation**: Rich validation options (regex, ranges, custom validators)

### Negative

- **Learning Curve**: Developers need to learn Pydantic patterns
  - Mitigation: Good documentation and examples
- **Dependency**: External dependency (not stdlib)
  - Mitigation: Pydantic is stable and widely used
- **Migration**: Pydantic v1 to v2 has breaking changes
  - Mitigation: Start with v2 from the beginning

### Neutral

- **Verbosity**: More code than plain dataclasses
  - Trade-off: Validation and safety worth the extra code

## Design Patterns

### Immutable Source Tracking

```python
class SourceReference(BaseModel):
    model_config = ConfigDict(frozen=True)  # Immutable

    source_url: str
    source_hash: str
    download_date: datetime
    page_number: Optional[int] = None
```

### Nested Models

```python
class Statement(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    text: str
    source: SourceReference  # Nested model
    topics: List[str] = Field(default_factory=list)
```

### Custom Validators

```python
class Bill(BaseModel):
    bill_number: str

    @field_validator('bill_number')
    def validate_bill_number(cls, v):
        if not re.match(r'^Bill No\. \d+ of \d{4}$', v):
            raise ValueError('Invalid bill number format')
        return v
```

## Integration with SQLAlchemy

Pydantic models are separate from ORM models:

```python
# Pydantic model (validation, API)
class Document(BaseModel):
    title: str
    date: date

# SQLAlchemy model (database)
class DocumentORM(Base):
    __tablename__ = "documents"
    title = Column(String(500))
    date = Column(Date)

# Conversion
def to_orm(doc: Document) -> DocumentORM:
    return DocumentORM(**doc.model_dump())

def from_orm(doc_orm: DocumentORM) -> Document:
    return Document.model_validate(doc_orm)
```

## Testing Strategy

Pydantic models are easy to test:

```python
def test_document_validation():
    # Valid document
    doc = Document(title="Test", date=date.today(), ...)
    assert doc.title == "Test"

    # Invalid document
    with pytest.raises(ValidationError):
        Document(title="", date=date.today(), ...)  # Empty title

@given(st.text(min_size=1, max_size=500))
def test_document_title_property(title):
    """Property test: any valid title should work."""
    doc = Document(title=title, date=date.today(), ...)
    assert doc.title == title.strip()
```

## Performance Considerations

Pydantic v2 is highly optimized:

- Validation: ~10x faster than v1
- Serialization: ~5x faster than v1
- Memory: Efficient Rust core

For 10K documents:
- Validation: ~50ms
- JSON serialization: ~100ms

Performance is not a concern for our use case.

## References

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Pydantic v2 Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [Type Hints PEP 484](https://www.python.org/dev/peps/pep-0484/)

## Related ADRs

- None

## Date

2025-01-15
