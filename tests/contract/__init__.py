"""
Contract tests for Hansard Tales.

Contract tests validate that mock data matches production data structures.
They serve as an early warning system when parliament.go.ke changes its structure.

These tests verify:
- HTML structure assumptions remain valid
- Date format patterns match production
- PDF link structures match production

When contract tests fail, it indicates that parliament.go.ke has changed
and our mocks/fixtures need to be updated.
"""
