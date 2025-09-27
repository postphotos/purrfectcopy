# Convenience Makefile for common developer tasks

.PHONY: demo demo-clean test coverage integration-test docker-smoke-build docker-smoke-run

demo:
	PCOPY_TEST_MODE=0 ./scripts/demo.sh

demo-clean:
	PCOPY_TEST_MODE=1 ./scripts/demo-clean.sh

test:
	pytest -q

coverage:
	pytest --cov=pcopy --cov-report=term-missing

integration-test:
	RUN_INTEGRATION_TESTS=1 pytest -q tests/test_setup_in_container.py::test_setup_sh_adds_pcopy_alias_in_container

docker-smoke-build:
	docker build -f Dockerfile.smoke -t pcopy-smoketest:smoke .

# Run the smoke image as a quick check (mounts current directory read-only by default)
docker-smoke-run:
	docker run --rm -e PCOPY_TEST_MODE=1 pcopy-smoketest:smoke
