"""Pytest configuration and fixtures."""

import os

import pytest


@pytest.fixture(autouse=True)
def ensure_api_key():
    """Ensure API_KEY is set for tests that hit protected endpoints."""
    orig = os.environ.get("API_KEY")
    os.environ["API_KEY"] = "test-key-123"
    yield
    if orig is not None:
        os.environ["API_KEY"] = orig
    else:
        os.environ.pop("API_KEY", None)
