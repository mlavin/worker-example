import json
from unittest.mock import patch

import pytest
from worker import config, main


class MockResponse:
    def __init__(self, body):
        self._body = body

    async def json(self):
        return self._body

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self


@pytest.fixture(autouse=True)
def aiohttp_client():
    """Mock HTTP client."""

    with patch(
        "worker.aiohttp.ClientSession.get", return_value=MockResponse([])
    ) as mock:
        yield mock


@pytest.fixture()
def worker():
    """Mock worker coroutine."""

    with patch("worker.worker") as mock:
        yield mock


@pytest.fixture()
def writer():
    """Mock writer coroutine."""

    with patch("worker.writer") as mock:
        yield mock


@pytest.mark.asyncio
async def test_http_fetch(aiohttp_client):
    """Assert fetching the input URL."""

    await main()
    aiohttp_client.assert_called_once_with(config.INPUT)


@pytest.mark.asyncio
async def test_main_coroutines(worker, writer):
    """Assert the correct number of worker coroutines are created."""

    await main()
    assert worker.call_count == config.WORKERS
    assert writer.call_count == 1


@pytest.mark.asyncio
async def test_main_e2e(aiohttp_client, sample_resource):
    """Close to full end to end run of the main loop."""

    aiohttp_client.return_value = MockResponse([sample_resource])
    await main()
    with open("output.json", "r") as f:
        results = json.load(f)
    assert results == [
        sample_resource,
    ]
