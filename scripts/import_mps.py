#!/usr/bin/env python3
"""
CLI wrapper for MP import.
Imports from hansard_tales package.
"""

from hansard_tales.database.import_mps import main

if __name__ == '__main__':
    exit(main())
