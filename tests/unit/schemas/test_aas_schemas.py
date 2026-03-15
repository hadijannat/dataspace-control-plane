"""
tests/unit/schemas/test_aas_schemas.py
Entry point for AAS schema tests — delegates to schemas/aas/tests/test_aas_schemas.py.

Run:
    pytest tests/unit/schemas/test_aas_schemas.py -v
    pytest tests/unit -k aas_schemas
"""
import sys
from pathlib import Path

_FAMILY_TESTS_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "schemas" / "aas" / "tests"
)
if str(_FAMILY_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_FAMILY_TESTS_DIR))

from test_aas_schemas import *  # noqa: F401, F403, E402
