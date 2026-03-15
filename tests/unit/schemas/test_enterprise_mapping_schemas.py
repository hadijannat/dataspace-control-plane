"""
tests/unit/schemas/test_enterprise_mapping_schemas.py
Entry point for enterprise-mapping schema tests — delegates to
schemas/enterprise-mapping/tests/test_enterprise_mapping_schemas.py.

Run:
    pytest tests/unit/schemas/test_enterprise_mapping_schemas.py -v
    pytest tests/unit -k enterprise_mapping_schemas
"""
import sys
from pathlib import Path

_FAMILY_TESTS_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "schemas" / "enterprise-mapping" / "tests"
)
if str(_FAMILY_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_FAMILY_TESTS_DIR))

from test_enterprise_mapping_schemas import *  # noqa: F401, F403, E402
