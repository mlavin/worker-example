import asyncio
import json
import logging
import logging.config
import os
import random
from datetime import datetime
from typing import List

import aiohttp
import pydantic

log = logging.getLogger(__name__)


class Resource(pydantic.BaseModel):
    id: str
    source: str
    title: str
    creation_date: datetime
    message: str
    tags: List[str]
    author: str
    retries: int = 0


class ProcessedResource(pydantic.BaseModel):
    processed: bool
    processing_date: datetime
    resource: Resource


class Config(pydantic.BaseModel):
    INPUT: str = "https://storage.googleapis.com/onna-exercise-data/records_1.json"
    WORKERS: int = 10
    PROCESSING_TIME: float = 5.0
    DELAY_TIME: float = 5.0
    FAILURE_RATE: float = 25.0
    MAX_ATTEMPTS: int = 3


config = Config(**os.environ)


async def process_resource(resource: dict):
    """Processesing logic for each resource item."""

    await asyncio.sleep(random.random() * config.PROCESSING_TIME)
    try:
        processed = ProcessedResource(
            processed=random.random() > (config.FAILURE_RATE / 100),
            processing_date=datetime.utcnow(),
            resource=resource,
        )
    except pydantic.ValidationError as e:
        raise ValueError(f"Invalid resource body: {e}")
    return processed


async def worker(name: str, input_queue: asyncio.Queue, output_queue: asyncio.Queue):
    """Worker coroutine to pull work off the queue and process it."""

    while True:
        resource = await input_queue.get()
        await asyncio.sleep(random.random() * config.DELAY_TIME)
        try:
            processed = await process_resource(resource)
            result = processed.resource.dict()
            retries = result.pop("retries", 0)
            if processed.processed:
                log.info(
                    f"Successfully processed resource: {result['id']} (worker-{name})",
                )
                await output_queue.put(result)
            elif retries < (config.MAX_ATTEMPTS - 1):
                resource = resource.copy()
                retries += 1
                resource["retries"] = retries
                log.warning(
                    f"Retry #{retries} for resource: {result['id']} (worker-{name})",
                )
                await input_queue.put(resource)
            else:
                log.error(
                    f"Max retries exceeded for resource: {result['id']} (worker-{name})"
                )
        except ValueError:
            # Invalid resource entry. Log and don't retry.
            log.exception(
                f"Invalid resource: {resource.get('id', 'unknown')} (worker-{name})",
            )
        finally:
            # Ack the queue item
            input_queue.task_done()


def encoder(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()


async def writer(queue: asyncio.Queue):
    """Output file writer."""

    results = []
    while True:
        processed = await queue.get()
        results.append(processed)
        with open("output.json", "w") as f:
            json.dump(results, f, default=encoder)
        queue.task_done()


async def main():
    """Main loop to spawn workers, populate the work queue, and process results."""

    input_queue, output_queue = asyncio.Queue(), asyncio.Queue()
    workers = [
        asyncio.ensure_future(worker(str(i), input_queue, output_queue))
        for i in range(config.WORKERS)
    ]
    output = asyncio.ensure_future(writer(output_queue))
    async with aiohttp.ClientSession() as session:
        async with session.get(config.INPUT) as resp:
            inputs = await resp.json()
    for item in inputs:
        await input_queue.put(item)
    await input_queue.join()
    await output_queue.join()
    for w in workers:
        w.cancel()
    output.cancel()


if __name__ == "__main__":
    logging.config.fileConfig("logging.ini", disable_existing_loggers=False)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
