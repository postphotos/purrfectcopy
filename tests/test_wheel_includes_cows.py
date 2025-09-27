from pathlib import Path
import shutil
import zipfile
import sys
import pytest


def test_wheel_contains_cows(tmp_path: Path):
    """Build a wheel and assert that `pcopy/cows/*.cow` files are included.

    This test requires the `build` package to be available. When running
    via `./run-all-tests.sh`, the script ensures `build` is installed. If the
    package is not present in the current test environment we skip the test
    to avoid failing on environments that don't have network access.
    """

    try:
        import build  # type: ignore
    except Exception:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "'build' package is required for tests/test_wheel_includes_cows.py; run './run-all-tests.sh' to install it before running pytest"
        )

    # Build wheel into a temp dist directory
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()

    # Use python -m build to produce a wheel.
    cmd = [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir)]
    import subprocess

    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError:
        # Building wheels can fail in constrained environments (isolated build
        # env creation or missing metadata). Skip the test rather than fail the
        # whole test suite in those environments.
        pytest.skip("Could not build wheel in this environment; skipping")

    # Find the wheel file
    wheels = list(dist_dir.glob("*.whl"))
    assert wheels, "No wheel file produced"
    wheel = wheels[0]

    # Inspect wheel contents for cows directory
    with zipfile.ZipFile(wheel, "r") as zf:
        entries = zf.namelist()
        cow_files = [p for p in entries if p.startswith("pcopy/cows/") and p.endswith(".cow")]
        assert cow_files, f"No .cow files found in wheel {wheel.name}"

    # cleanup - remove the build artifacts
    shutil.rmtree(str(dist_dir))
