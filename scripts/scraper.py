#!/usr/bin/env python3
"""
CLI wrapper for Hansard scraper.
Imports from hansard_tales package.
"""

from hansard_tales.scrapers.hansard_scraper import main

if __name__ == '__main__':
    exit(main())
