import pytest
from worker import process_resource


@pytest.mark.asyncio()
async def test_successfully_processed_resource(sample_resource):
    """Process a resource without error."""

    result = await process_resource(sample_resource)
    assert result.processed
    assert result.processing_date
    resource = result.resource.dict()
    # result will include the default retries
    assert resource.pop("retries") == 0
    # creation_date should be transformed into a datetime
    # but the rest of the resouce should remain unchanged
    resource["creation_date"] = resource["creation_date"].isoformat()
    assert resource == sample_resource


@pytest.mark.asyncio()
async def test_failed_processed_resource(mock_random, sample_resource):
    """Handle failed resource processing."""

    mock_random.random.return_value = 0

    result = await process_resource(sample_resource)
    assert not result.processed
    assert result.processing_date
    resource = result.resource.dict()
    # result will include the default retries
    assert resource.pop("retries") == 0
    # creation_date should be transformed into a datetime
    # but the rest of the resouce should remain unchanged
    resource["creation_date"] = resource["creation_date"].isoformat()
    assert resource == sample_resource


@pytest.mark.asyncio()
async def test_invalid_resource():
    """Processing will raise a ValueError for an invalid resource."""

    with pytest.raises(ValueError):
        await process_resource({})
