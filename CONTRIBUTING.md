# Contributing

This guide outlines the process for running the project's tests locally. This includes unit tests, coverage reports, and container-based smoke tests that replicate the continuous integration (CI) environment.

## Prerequisites

Before you begin, ensure you have the following installed:

* **Python 3.11**
* **pip**
* **Docker:** Required for running the container-based smoke tests.
* **uv (recommended):** A fast Python package installer.

## Development Setup

### 1. Install Dependencies

You can install the necessary dependencies using `pip` or the recommended `uv`.

**With `uv`:**

```bash
pip install uv
uv pip install -r requirements.txt
```

**With `pip`:**

```bash
pip install -r requirements.txt
```

### 2. Running Tests

This project includes unit tests, coverage reports, and container-based smoke tests.

#### Unit Tests and Coverage

To run the test suite and generate a coverage report for the `pcopy` package, use the following command:

```bash
uv run pytest --cov=pcopy --cov-report=term-missing
```

#### Container-Based Smoke Tests (Optional)

These smoke tests mirror the behavior of the CI pipeline. A helper script is available to run them locally.

```bash
chmod +x scripts/run_container_tests.sh
./scripts/run_container_tests.sh
```

#### Comprehensive Test Script

A convenience script is also provided to run `pyright`, `pytest` with coverage, and the container smoke tests (if Docker is available).

```bash
chmod +x run-all-tests.sh
./run-all-tests.sh
```

## Understanding the Container Tests

The container-based smoke tests perform the following actions:

* Build the `Dockerfile.alpine` image.
* Execute three test scenarios:
    1. A dry-run as the `root` user.
    2. A real run as the `root` user.
    3. A dry-run as a non-root user (triggered by `RUN_AS=nonroot`).

### CI Behavior

The GitHub Actions workflow utilizes the same Docker image and runs these three scenarios. If you make changes to the `Dockerfile`, please ensure the image still builds successfully in the CI environment.

### Important Notes

* The real-run test may execute `rsync` within the container, which can modify the container's local `/data` directory. It will not affect your host machine unless you have explicitly mounted host volumes.
* The `Dockerfile` currently fetches external assets during the build process. For more deterministic CI builds, consider replacing these with static test assets in the future.

### Running the single container integration test

If you only want to run the specific container integration test that verifies `setup.sh` and `pcopy do main-backup --dry-run`, use:

```bash
uv run pytest tests/test_setup_in_container.py::test_setup_sh_adds_pcopy_alias_in_container -q
```

If Docker is not available or the image build fails in your environment, the test automatically falls back to a deterministic local path that runs `./setup.sh --no-deps` and `PCOPY_TEST_MODE=1 ./run-backup.sh do main-backup --dry-run` so you still get verification on systems without Docker.

### Requiring the container check in branch protection

If you'd like to enforce the container smoke-test in your repository's protected branches, add the job name `Container Smoke Test` to the required status checks in GitHub:

1. Go to your repository Settings → Branches → Branch protection rules.
2. Edit or create a rule for `main`.
3. Under "Require status checks to pass before merging", add `Container Smoke Test` to the list of required checks.

This ensures pull requests cannot be merged until the container smoke-test job completes successfully on CI.
