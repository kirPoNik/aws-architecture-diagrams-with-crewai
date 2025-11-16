#!/usr/bin/env python
"""
Wrapper script for backward compatibility.
Calls the CLI entry point from the installed package.
"""

import sys
from aws_diagram_generator.cli import main

if __name__ == '__main__':
    sys.exit(main())
