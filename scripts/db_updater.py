#!/usr/bin/env python3
"""
CLI wrapper for database updater.
Imports from hansard_tales package.
"""

from hansard_tales.database.db_updater import main

if __name__ == '__main__':
    exit(main())
