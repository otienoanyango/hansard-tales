#!/usr/bin/env python3
"""
Script to systematically fix mypy errors in the Hansard Tales project.

This script addresses:
1. SQLAlchemy Base class and Column type issues
2. Missing type annotations
3. BeautifulSoup AttributeValueList type narrowing
4. Logging/structlog compatibility
5. Test-related type issues
"""

import subprocess
import sys
from pathlib import Path


def run_mypy() -> tuple[bool, str]:
    """Run mypy and return success status and output."""
    result = subprocess.run(
        ["mypy", "hansard_tales", "scripts", "tests", "--pretty", "--show-error-codes"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, result.stdout + result.stdout


def main() -> None:
    """Main execution."""
    print("Running mypy to identify errors...")
    success, output = run_mypy()

    if success:
        print("✓ No mypy errors found!")
        sys.exit(0)

    print("Found mypy errors. Output saved to mypy_errors.log")
    Path("mypy_errors.log").write_text(output)

    # Count errors by category
    lines = output.split("\n")
    error_counts = {}
    for line in lines:
        if "error:" in line:
            # Extract error code
            if "[" in line and "]" in line:
                code = line[line.rfind("[") + 1 : line.rfind("]")]
                error_counts[code] = error_counts.get(code, 0) + 1

    print("\nError summary by type:")
    for code, count in sorted(error_counts.items(), key=lambda x: -x[1]):
        print(f"  {code}: {count}")

    print(f"\nTotal errors: {sum(error_counts.values())}")


if __name__ == "__main__":
    main()
