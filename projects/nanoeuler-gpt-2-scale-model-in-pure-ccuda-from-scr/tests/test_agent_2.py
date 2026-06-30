"""Tests for agent_2."""
import pytest
from src.agents.agent_2 import agent_2

def test_agent_2_basic():
    """Test agent_2 processes input correctly."""
    input_data = {"test": True}
    result = agent_2(input_data)
    assert isinstance(result, dict)
    assert "agent_2_output" in result

def test_agent_2_empty_input():
    """Test agent_2 handles empty input."""
    result = agent_2(dict())
    assert isinstance(result, dict)
