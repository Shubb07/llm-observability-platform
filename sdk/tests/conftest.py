from __future__ import annotations

import pytest

from llm_observability_sdk import config


@pytest.fixture(autouse=True)
def reset_sdk_state():
    """Every test starts from a clean slate — config.init() mutates a module
    global, so a test that forgets to reset it would leak into the next one."""
    yield
    config._transport = None
