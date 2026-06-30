"""Tests for agent_1."""
import pytest
from src.agents.agent_1 import agent_1

def test_agent_1_basic():
    """Test agent_1 processes input correctly."""
    input_data = {"test": True}
    result = agent_1(input_data)
    assert isinstance(result, dict)
    assert "agent_1_output" in result

def test_agent_1_empty_input():
    """Test agent_1 handles empty input."""
    result = agent_1(dict())
    assert isinstance(result, dict)
