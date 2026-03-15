"""
tests/unit/schemas/test_vc_schemas.py
Entry point for VC schema tests — delegates to schemas/vc/tests/test_vc_schemas.py.

Run:
    pytest tests/unit/schemas/test_vc_schemas.py -v
    pytest tests/unit -k vc_schemas
"""
import sys
from pathlib import Path

_FAMILY_TESTS_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "schemas" / "vc" / "tests"
)
if str(_FAMILY_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_FAMILY_TESTS_DIR))

from test_vc_schemas import *  # noqa: F401, F403, E402
