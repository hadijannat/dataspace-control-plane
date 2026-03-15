"""
tests/compatibility/dsp-tck/conftest.py
DSP TCK wrapper suite.

Only activated when the repo exposes DSP-facing protocol surfaces.
Pin TCK version in lock.yaml. Run with: bash tests/scripts/run_dsp_tck.sh

All tests in this suite are @pytest.mark.compatibility and @pytest.mark.nightly
unless run in the DSP protocol smoke subset for PRs.
"""
from __future__ import annotations

import pytest


def pytest_collect_file(parent, file_path):
    # TCK is run as an external process via run_dsp_tck.sh.
    # This conftest exists to register markers and document the suite.
    pass
