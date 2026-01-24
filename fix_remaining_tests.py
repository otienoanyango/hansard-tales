#!/usr/bin/env python3
"""
Script to apply HTTP mocking pattern to all download tracking tests.
This ensures tests don't make real network calls.
"""

import re

# Read the test file
with open('tests/test_end_to_end.py', 'r') as f:
    content = f.read()

# Pattern to find tests that need fixing
# They create scraper then try to mock Session after
tests_to_fix = [
    'test_duplicate_detection_file_and_db',
    'test_duplicate_detection_file_only',
    'test_duplicate_detection_db_only',
    'test_duplicate_detection_neither_exists',
    'test_new_downloads_use_standardized_format',
    'test_multiple_downloads_same_date_different_periods',
    'test_numeric_suffix_for_duplicate_period',
]

# For each test, wrap the scraper creation in the HTTP mock
for test_name in tests_to_fix:
    # Find the test
    pattern = rf'(    def {test_name}\(self, temp_workspace\):.*?)(        # Create scraper\s+scraper = HansardScraper\(\s+storage=storage,\s+db_path=str\(db_path\)\s+\))'
    
    replacement = r'\1        # Mock HTTP at the module level BEFORE creating scraper\n        with patch(\'hansard_tales.scrapers.hansard_scraper.requests.Session\') as MockSession:\n            mock_session = Mock()\n            mock_response = Mock()\n            mock_response.status_code = 200\n            mock_response.iter_content = lambda chunk_size: [b\'PDF content\']\n            mock_response.raise_for_status = Mock()\n            mock_session.get.return_value = mock_response\n            MockSession.return_value = mock_session\n            \n            # Create scraper - will use mocked session\n            scraper = HansardScraper(\n                storage=storage,\n                db_path=str(db_path)\n            )'
    
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

print("Pattern matching complete. Manual fixes still needed for proper indentation.")
print("Please review the changes carefully.")
