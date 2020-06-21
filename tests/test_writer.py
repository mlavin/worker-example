import asyncio
import json

import pytest
from worker import writer


@pytest.mark.asyncio
async def test_write_results(output_queue, sample_resource):
    """Write out resulting resouces from the queue."""

    future = asyncio.ensure_future(writer(output_queue))
    await output_queue.put(sample_resource)
    await output_queue.join()
    with open("output.json", "r") as f:
        results = json.load(f)
    assert results == [
        sample_resource,
    ]
    future.cancel()
