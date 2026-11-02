# Everyday commands. `make setup` once, then `make run`.
.PHONY: setup index web run test gate docker

setup:          ## install deps, fetch the corpus (needs SEC_USER_AGENT), build the index
	uv sync
	uv run playwright install chromium
	uv run enterprise-rag fetch-data
	$(MAKE) index

index:          ## build the search collections (main + the one with poisoned test pages)
	uv run enterprise-rag build-index
	uv run enterprise-rag build-index --with-fixtures

web:            ## build the React app into web/dist
	npm --prefix web ci
	npm --prefix web run build

run: web        ## start the demo at http://127.0.0.1:8000
	uv run enterprise-rag serve

test:           ## lint and unit tests
	uv run ruff check src tests
	uv run pytest -q

gate:           ## CI leak gate over the committed test runs
	uv run enterprise-rag gate eval/runs/*-rag-test-safety.json eval/runs/*-test-retrieval.json

docker:         ## build the container image (after `make setup`)
	docker build -t enterprise-rag .
