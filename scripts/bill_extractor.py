#!/usr/bin/env python3
"""
CLI wrapper for bill extractor.
Imports from hansard_tales package.
"""

from hansard_tales.processors.bill_extractor import main

if __name__ == '__main__':
    exit(main())
