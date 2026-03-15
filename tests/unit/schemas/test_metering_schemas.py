"""
tests/unit/schemas/test_metering_schemas.py
Entry point for metering schema tests — delegates to schemas/metering/tests/test_metering_schemas.py.

Run:
    pytest tests/unit/schemas/test_metering_schemas.py -v
    pytest tests/unit -k metering_schemas
"""
import sys
from pathlib import Path

_FAMILY_TESTS_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "schemas" / "metering" / "tests"
)
if str(_FAMILY_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_FAMILY_TESTS_DIR))

from test_metering_schemas import *  # noqa: F401, F403, E402
