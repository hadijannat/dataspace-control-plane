"""
tests/unit/schemas/test_dpp_schemas.py
Entry point for DPP schema tests — delegates to schemas/dpp/tests/test_dpp_schemas.py.

Run:
    pytest tests/unit/schemas/test_dpp_schemas.py -v
    pytest tests/unit -k dpp_schemas
"""
import sys
from pathlib import Path

_FAMILY_TESTS_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "schemas" / "dpp" / "tests"
)
if str(_FAMILY_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_FAMILY_TESTS_DIR))

from test_dpp_schemas import *  # noqa: F401, F403, E402
