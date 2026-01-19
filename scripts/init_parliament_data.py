#!/usr/bin/env python3
"""
CLI wrapper for parliament data initialization.
Imports from hansard_tales package.
"""

from hansard_tales.database.init_parliament_data import main

if __name__ == '__main__':
    exit(main())
