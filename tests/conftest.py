from asyncio import Queue
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def mock_random():
    """Mock the random number generation for deterministic testing."""

    with patch("worker.random") as mock:
        # Default random will always return 1
        mock.random.return_value = 1
        yield mock


@pytest.fixture(scope="session", autouse=True)
def mock_sleep():
    """Patch sleep calls to improve test runtime."""

    with patch("worker.asyncio.sleep") as mock:
        yield mock


@pytest.fixture()
def sample_resource():
    """Example resource dict for testing."""

    return {
        "id": "924c8cfbd9f94155985bf262cf2c3c67",
        "source": "MessagingSystem",
        "title": "Lover",
        "creation_date": "2020-01-01T17:16:52.228009",
        "message": "We can leave the Christmas lights up 'til January.",
        "tags": ["music", "taylor", "pop"],
        "author": "Taylor Swift",
    }


@pytest.fixture()
def input_queue():
    """Setup input Queue."""

    return Queue()


@pytest.fixture()
def output_queue():
    """Setup output Queue."""

    return Queue()
