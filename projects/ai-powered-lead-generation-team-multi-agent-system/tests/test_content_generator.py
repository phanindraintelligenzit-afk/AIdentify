"""Tests for content_generator."""
import pytest
from src.agents.content_generator import content_generator

def test_content_generator_basic():
    """Test content_generator processes input correctly."""
    input_data = {"test": True}
    result = content_generator(input_data)
    assert isinstance(result, dict)
    assert "content_generator_output" in result

def test_content_generator_empty_input():
    """Test content_generator handles empty input."""
    result = {aname}(dict())
    assert isinstance(result, dict)
