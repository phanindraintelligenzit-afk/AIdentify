"""Tests for data_extractor."""
import pytest
from src.agents.data_extractor import data_extractor

def test_data_extractor_basic():
    """Test data_extractor processes input correctly."""
    input_data = {"test": True}
    result = data_extractor(input_data)
    assert isinstance(result, dict)
    assert "data_extractor_output" in result

def test_data_extractor_empty_input():
    """Test data_extractor handles empty input."""
    result = {aname}(dict())
    assert isinstance(result, dict)
