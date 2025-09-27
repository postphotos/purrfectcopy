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

### Packaging / wheel verification note

We include an integration test that builds a wheel and inspects it to ensure package data (for example `pcopy/cows/*.cow`) are bundled correctly. The comprehensive test script `run-all-tests.sh` will attempt to bootstrap `pip` and install the `build` package automatically when needed so the wheel-inspection test can run.

If your environment has restricted network access or very small available disk space, the bootstrapping step may fail — in that case run the script on a machine with network access or install `build` manually into your venv with:

```bash
python -m pip install --upgrade --no-cache-dir build
```

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

## Contributing — running real integration tests

This project includes a set of optional, real integration tests that run inside Docker
and exercise the full setup and backup flow (non-dry-run). These tests are intentionally
invasive and therefore opt-in.

## Running the real Docker integration test locally

Prerequisites:

* Docker installed and the daemon running.
* Enough disk space and time to build the smoke image (the build may take several minutes).

Recommended workflow for local debugging:

1. Build the smoke image quickly:

   ./scripts/build_smoke_image.sh pcopy-smoketest:real Dockerfile.smoke

2. Run a real integration run using the built image and temporary mount points:

   ./scripts/run_real_integration.sh pcopy-smoketest:real /tmp/pcopy-src /tmp/pcopy-dst /tmp/pcopy-home

This will run `setup.sh` inside the container (with `--no-deps`) and then run `pcopy do main-backup`
inside the image, mounting the provided host directories. The test will then assert that files
were copied into the destination directory on the host.

## Running via pytest (opt-in)

The test file `tests/test_setup_in_container_full.py` is gated behind the
`RUN_REAL_INTEGRATION=1` environment variable and also detects Docker availability.

To run it via pytest:

```bash
    export RUN_REAL_INTEGRATION=1
    uv run pytest tests/test_setup_in_container_full.py -q
```

Note: this test builds a docker image and runs containers; it will take time and must be
run on a machine where Docker is available and permitted.

## CI considerations

If you want to run these real integration tests in CI, add a job on a Docker-capable runner
and set `RUN_REAL_INTEGRATION=1`. Be sure to allow a long timeout and sufficient disk space.
A sample GitHub Actions workflow is included in `.github/workflows/real-integration.yml` but
it is intended as a starting point — you may need to adapt it to your CI environment.

## Safety

These tests are designed to perform side-effects in temporary directories and remove
built images at the end. Nevertheless, they are invasive and may fail on restricted
or resource-limited environments, which is why they are explicitly opt-in.
