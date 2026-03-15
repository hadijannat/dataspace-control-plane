"""
tests/unit/schemas/test_odrl_schemas.py
Entry point for ODRL schema tests — delegates to schemas/odrl/tests/test_odrl_schemas.py.

Run:
    pytest tests/unit/schemas/test_odrl_schemas.py -v
    pytest tests/unit -k odrl_schemas
"""
import sys
from pathlib import Path

_FAMILY_TESTS_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "schemas" / "odrl" / "tests"
)
if str(_FAMILY_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_FAMILY_TESTS_DIR))

from test_odrl_schemas import *  # noqa: F401, F403, E402
