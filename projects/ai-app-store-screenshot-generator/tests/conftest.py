"""Shared test fixtures."""
import pytest

@pytest.fixture
def sample_input():
    return {"test": True, "data": "sample"}
