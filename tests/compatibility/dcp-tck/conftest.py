"""
tests/compatibility/dcp-tck/conftest.py
DCP TCK wrapper suite.

Only activated when the repo exposes DCP-facing protocol surfaces.
Pin TCK version in lock.yaml. Run with: bash tests/scripts/run_dcp_tck.sh

All tests in this suite are @pytest.mark.compatibility and @pytest.mark.nightly
unless run in the DCP protocol smoke subset for PRs.

DCP has three independent actors that each require their own SUT configuration:
  - Credential Service (VPP, CIP protocols)
  - Issuer (CIP protocol)
  - Verifier (VPP protocol)
"""
from __future__ import annotations

import pytest


def pytest_collect_file(parent, file_path):
    # TCK is run as an external process via dcp-tck/scripts/.
    # This conftest exists to register markers and document the suite.
    pass
