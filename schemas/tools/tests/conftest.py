"""
schemas/tools/tests/conftest.py

Insert schemas/tools/ into sys.path before test collection so the bare-module
imports used by the tooling scripts (from _support import ...) work correctly
regardless of the working directory pytest is invoked from.
"""
from __future__ import annotations

import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
