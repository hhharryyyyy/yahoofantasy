PY ?= /Users/HarryYang/.asdf/installs/python/3.11.7/bin/python

.PHONY: install install-dev test test-unit test-integration lint clean

install:
	$(PY) -m pip install -U pip
	$(PY) -m pip install -r requirements.txt

install-dev: install
	$(PY) -m pip install -r test_requirements.txt

test:
	$(PY) -m pytest

test-unit:
	$(PY) -m pytest -m "not integration"

test-integration:
	@if [ "$$YF_RUN_LIVE" != "1" ]; then echo "Set YF_RUN_LIVE=1 and export YAHOO_CLIENT_ID/YAHOO_CLIENT_SECRET/YAHOO_REFRESH_TOKEN"; exit 1; fi
	$(PY) -m pytest -m integration tests/integration -o log_cli=true

lint:
	flake8 yahoofantasy

clean:
	rm -rf .pytest_cache .coverage htmlcov

