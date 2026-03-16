"""Pytest configuration and fixtures."""

import os

import pytest


@pytest.fixture(autouse=True)
def ensure_api_key():
    """Ensure API_KEY is set for tests that hit protected endpoints."""
    if "API_KEY" not in os.environ:
        os.environ["API_KEY"] = "test-key-123"
    yield
    # Don't clear - other tests might need it
