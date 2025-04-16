#!/usr/bin/env python3
# appreciate.py - Entry point for the Appreciation Protocol CLI

import os
import sys
import platform

# Add the project root to Python path to ensure imports work
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Apply Windows fixes before importing KERI modules if needed
if platform.system() == 'Windows':
    from adapter.keri.windows_fix import apply_windows_fixes
    apply_windows_fixes()

# Now import the CLI app
from cli import app

if __name__ == "__main__":
    app()