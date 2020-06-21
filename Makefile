%.txt: %.in
	pip-compile --upgrade --build-isolation --generate-hashes --output-file $@ $^

init:
	pip install --upgrade pip-tools pip setuptools wheel

update: init requirements.txt dev.txt

install: init requirements.txt dev.txt
	python -m pip install -r requirements.txt -r dev.txt

test:
	python -m pytest --cov=worker --cov-report html --cov-report term-missing

.PHONY: init update install test
