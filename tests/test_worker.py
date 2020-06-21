import asyncio
import datetime
from unittest.mock import call, patch

import pytest
from worker import ProcessedResource, config, worker


@pytest.fixture()
def sample_processed(sample_resource):
    """Example processed response."""

    return ProcessedResource(
        processed=True,
        processing_date=datetime.datetime.utcnow(),
        resource=sample_resource,
    )


@pytest.fixture()
def process_resource(sample_processed):
    """Mock process_resource for testing the worker."""

    with patch("worker.process_resource") as mock:
        mock.return_value = sample_processed
        yield mock


@pytest.mark.asyncio()
async def test_worker_empty_queue(process_resource, input_queue, output_queue):
    """Starting a new worker with no work to process."""

    future = asyncio.ensure_future(worker("test", input_queue, output_queue))
    # No work to do
    assert not process_resource.called
    assert output_queue.empty()
    future.cancel()


@pytest.mark.asyncio()
async def test_worker_result(
    process_resource, sample_resource, input_queue, output_queue
):
    """Worker should pull from input and put to the output."""

    future = asyncio.ensure_future(worker("test", input_queue, output_queue))
    await input_queue.put(sample_resource)
    await input_queue.join()
    process_resource.assert_called_once_with(sample_resource)
    assert input_queue.empty()
    assert output_queue.qsize() == 1
    result = await output_queue.get()
    # Result will have creation_date as a datetime
    result["creation_date"] = result["creation_date"].isoformat()
    assert result == sample_resource
    future.cancel()


@pytest.mark.asyncio()
async def test_worker_process_error(
    process_resource, sample_resource, input_queue, output_queue
):
    """Worker should handle errors from the processor."""

    process_resource.side_effect = ValueError
    future = asyncio.ensure_future(worker("test", input_queue, output_queue))
    await input_queue.put(sample_resource)
    await input_queue.join()
    process_resource.assert_called_once_with(sample_resource)
    assert input_queue.empty()
    # No output expected
    assert output_queue.empty()
    future.cancel()


@pytest.mark.asyncio()
async def test_worker_retry(
    process_resource, sample_resource, input_queue, output_queue
):
    """Worker should retry after a single error."""

    process_resource.side_effect = [
        ProcessedResource(
            processed=False,
            processing_date=datetime.datetime.utcnow(),
            resource=sample_resource,
        ),
        ProcessedResource(
            processed=True,
            processing_date=datetime.datetime.utcnow(),
            resource=sample_resource,
        ),
    ]
    future = asyncio.ensure_future(worker("test", input_queue, output_queue))
    await input_queue.put(sample_resource)
    await input_queue.join()
    second = sample_resource.copy()
    second["retries"] = 1
    process_resource.assert_has_calls(
        [call(sample_resource), call(second),]
    )
    assert input_queue.empty()
    # Only one output
    assert output_queue.qsize() == 1
    result = await output_queue.get()
    # Result will have creation_date as a datetime
    result["creation_date"] = result["creation_date"].isoformat()
    assert result == sample_resource
    future.cancel()


@pytest.mark.asyncio()
async def test_worker_max_retries(
    process_resource, sample_resource, input_queue, output_queue
):
    """Worker will give up after a sufficient number of retries."""

    fails = []
    for i in range(config.MAX_ATTEMPTS):
        resource = sample_resource.copy()
        resource["retries"] = i
        result = ProcessedResource(
            processed=False,
            processing_date=datetime.datetime.utcnow(),
            resource=resource,
        )
        fails.append(result)
    process_resource.side_effect = fails + [
        ProcessedResource(
            processed=True,
            processing_date=datetime.datetime.utcnow(),
            resource=sample_resource,
        ),
    ]
    future = asyncio.ensure_future(worker("test", input_queue, output_queue))
    await input_queue.put(sample_resource)
    await input_queue.join()
    assert process_resource.call_count == config.MAX_ATTEMPTS
    assert input_queue.empty()
    # No output expected
    assert output_queue.empty()
    future.cancel()
