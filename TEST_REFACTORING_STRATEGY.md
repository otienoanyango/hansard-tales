# Test Refactoring Strategy: Property vs Unit Tests

## Quick Answer

**Use both when they serve different purposes:**
- **Unit tests:** Document specific examples (HOW it works)
- **Property tests:** Prove universal rules (it ALWAYS works)

**Use only one when they're duplicative:**
- Small input space (< 10 values) → Parametrized unit test
- Format validation → Property test only
- Universal invariants → Property test only

## The Problem

We have ~15 property tests and ~135 unit tests. Some are complementary (good), but some are duplicative (wasteful).

**Example of duplication:**
```python
# Both test the same thing
def test_period_morning(): assert extract_period("Morning") == "P"
@given(...) def test_period_property(...): # Tests same 3 values
```

## When They're Complementary (Keep Both)

### 1. Complex Parsing
- **Unit:** "15th October 2025" → "2025-10-15" (example)
- **Property:** For ANY text, never crashes (robustness)
- **Different purposes** ✅

### 2. State Machines  
- **Unit:** Document each of 4 states clearly
- **Property:** Prove all 4 combinations work
- **Different purposes** ✅

### 3. Error Handling
- **Unit:** Show HOW specific errors handled
- **Property:** Prove ALL errors handled
- **Different purposes** ✅

## When They're Duplicative (Choose One)

### 1. Simple Validation (< 10 values)
```python
# Wasteful: 3 unit tests + 1 property test for 3 values
# Better: 1 parametrized test
@pytest.mark.parametrize("text,expected", [
    ("Morning", "P"), ("Afternoon", "A"), ("Evening", "E")
])
```

### 2. Format Validation
```python
# Wasteful: Unit test + property test
# Better: Property test only (covers infinite inputs)
@given(st.dates(), st.sampled_from(['A', 'P', 'E']))
def test_filename_format(date, period): ...
```

## Refactoring Plan

### Remove These (Duplicative):
1. Filename format unit tests → Keep property test
2. Period extraction property test → Keep parametrized unit test
3. Backup filename unit tests → Keep property test
4. Numeric suffix unit tests → Keep property test

### Keep These (Complementary):
1. Date extraction - both unit and property
2. Download decision logic - both unit and property
3. Error handling - both unit and property
4. Session linking - both unit and property

## Impact

**Before:**
- 150 tests
- 45 seconds
- Some confusion about which test to update

**After:**
- 120 tests (20% reduction)
- 30 seconds (33% faster)
- Clear purpose for each test

## Decision Framework

```
Small input space (< 10)?     → Parametrized unit test
Universal invariant?           → Property test only
Documenting examples?          → Unit tests
State machine?                 → Both
Complex parsing?               → Both
Simple format validation?      → Property test only
```

## Maintainability Winner

**Property tests** are most maintainable when:
- Input space is large
- Testing universal rules
- Finding edge cases

**Parametrized unit tests** are most maintainable when:
- Input space is small (3-10 values)
- Clear input/output pairs
- Documenting behavior

**Individual unit tests** are most maintainable when:
- Documenting complex scenarios
- Integration points
- Specific edge cases need highlighting

## Bottom Line

**For Hansard Tales:**
- Remove ~30 duplicative tests
- Keep ~10 valuable property tests
- Convert ~10 tests to parametrized
- Result: Faster, clearer, more maintainable test suite

The spec now includes this refactoring in tasks 19-22!
