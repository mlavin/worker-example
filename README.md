# Worker Example

![Test Suite](https://github.com/mlavin/worker-example/workflows/Run%20Tests/badge.svg)

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Sample worker ETL process. This pulls example resources from a remote URL
and processes them in parallel with workers with basic validation and retry
logic. Each successfully processed resource is written into the `output.json`
file.


## Local Setup

Running locally requires that you have Python 3.8 and git installed. First,
you should clone this repository

```bash
# Clone repo
git clone git@github.com:mlavin/worker-example.git
# Navigate into the cloned project
cd worker-example
```

Next, you'll need to install the Python requirements. It's recommended to
install the dependencies into a local virtual environment.

```bash
# Create a new virtual environment
python3.8 -m venv env
# Activate env
source env/bin/activate
# Install project dependencies
make install
```

With everything installed you can now run the worker process:

```bash
python3.8 worker.py
```

## Configuration

The worker process has some configuration options which can be set through
environment variables.

  - `WORKERS`: Concurrency for the processing workers (default 10)
  - `INPUT`: Input URL for the ingestion
  - `PROCESSING_TIME`: Max processing time for each worker in seconds (default 5)
  - `DELAY_TIME`: Max delay time for a resource to be handed to a worker (default 5)
  - `FAILURE_RATE`: Random failure rate of the processing (default 25.0%)
  - `MAX_ATTEMPTS`: Max processsing attempts to process a resource (default 3)

These can be set when running via:

```bash
WORKERS=25 MAX_ATTEMPS=2 python3.8 worker.py
```

See the `Config` class in `worker.py` for more details/implementation on the
process configuration.


## Testing

The test suite is run using `pytest`. With all of the dependencies installed
you can run the test suite via

```bash
make test
```

This will discover the tests written in the `tests/` directory and report
the test coverage both in the terminal and as HTML in a generated `htmlcov`
directory.


## Structure/Updates

The `Resource` class defines the expected resource structure and validation
logic. The `ProcessedResouce` class is a small wrapper used for current work
in progress. Along with those definitions, `process_resource` contains the
main processing logic. The `worker` coroutines are spawned to work through
the queue of resource items feeding them to `process_resource` and handling
the retry logic. `writer` feeds off the output queue to update the `output.json`.
The `main` function glues this all together by creating the queues, spawning
the workers and writer, fetching the input URL and populating the input
work queue.

The requirements are defined in `requirements.in` which is used to generate
pinned requirements using `pip-tools`. Similarly for the testing requirements
which are defined in `dev.in` and pinned in `dev.txt`. If you want to bump
the requirements to the latest releases without any other updates/additions
you can rebuild them via:

```bash
touch requirements.in
make requirements.txt
```

You should not modifiy `requirements.txt` and `dev.txt` directly and they
should always be generated by `pip-tools`.

## Limitations

There is minimal validation of the incoming resources. This consists of checking
for the existance of the expected keys and that the `creation_date` is a
valid date value.

Currently there is no graceful shutdown of the worker when stopped/killed
in the middle of a run. `output.json` is written as the items are processed
but items which are currently in the middle of processing will not be given
the chance to finish.