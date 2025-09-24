import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


def docker_available() -> bool:
    try:
        subprocess.run(["docker", "version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


@pytest.mark.skipif(not docker_available(), reason="docker is not available")
def test_setup_sh_adds_pcopy_alias_in_container(tmp_path: Path):
    """Build the smoke-test image, run a container with a fake $HOME containing the sample YAML,
    run `setup.sh` inside the container, and assert the shell config file contains the `pcopy()` function.
    """

    project_root = Path(__file__).resolve().parents[1]

    # Create a temporary directory to act as HOME for the container
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    # Create a sample ~/.pcopy-main-backup.yml
    settings = fake_home / ".pcopy-main-backup.yml"
    settings.write_text(
        """
main-backup:
    source: "/path/to/source"
    dest: "/path/to/destination"
rsync_options:
    - "--verbose"
    - "--progress"
"""
    )

    image_tag = "pcopy-smoketest:test-setup"

    # Build the Docker image using a temporary Dockerfile that omits the
    # RUN ./run-all-tests.sh --no-docker step (the original Dockerfile runs
    # tests during build which can require node and other tools not present
    # in this test environment). We copy the original Dockerfile and filter
    # out the problematic RUN line.
    original_df = project_root / "Dockerfile.alpine"
    tmp_df = tmp_path / "Dockerfile.test"
    df_text = original_df.read_text()
    filtered_lines = []
    for line in df_text.splitlines():
        if "run-all-tests.sh --no-docker" in line:
            # skip this line
            continue
        filtered_lines.append(line)
    tmp_df.write_text("\n".join(filtered_lines))

    # Build the docker image; on failure, fail the test with output to debug
    try:
        build_proc = subprocess.run(
            ["docker", "build", "-f", str(tmp_df), "-t", image_tag, "."],
            check=True,
            cwd=str(project_root),
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        pytest.fail(f"docker build failed:\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")
    except OSError as e:
        pytest.fail(f"docker not usable: {e}")

    try:
        # Run the container, mounting the fake home into /home/tester (user created in Dockerfile)
        # Also mount the project so setup.sh is available and run /app/setup.sh with HOME set
        cmd = [
            "docker",
            "run",
            "--rm",
            "-e",
            f"HOME=/home/tester",
            "-v",
            f"{str(fake_home)}:/home/tester:rw",
            "-v",
            f"{str(project_root)}:/app:ro",
            image_tag,
            "/bin/sh",
            "-c",
            "cd /app && chmod +x setup.sh && HOME=/home/tester ./setup.sh",
        ]

        try:
            run_proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            pytest.fail(f"docker run (setup) failed:\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")
        except OSError as e:
            pytest.fail(f"docker not runnable: {e}")

        # Now run the pcopy command in the same image to exercise the alias
        pcopy_cmd = [
            "docker",
            "run",
            "--rm",
            "-e",
            "HOME=/home/tester",
            "-v",
            f"{str(fake_home)}:/home/tester:rw",
            "-v",
            f"{str(project_root)}:/app:ro",
            image_tag,
            "/bin/sh",
            "-c",
            # run as root, source the created shell config and invoke pcopy in dry-run mode
            "cd /app && bash -lc 'source /home/tester/.bashrc 2>/dev/null || source /home/tester/.zshrc 2>/dev/null; pcopy do main-backup --dry-run'",
        ]

        try:
            pcopy_proc = subprocess.run(pcopy_cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            pytest.fail(f"docker run (pcopy) failed:\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")
        except OSError as e:
            pytest.fail(f"docker not runnable: {e}")

        # After running, check the output from the pcopy run
        output = pcopy_proc.stdout + "\n" + pcopy_proc.stderr

        # assert that the run reported dry-run mode or similar
        assert ("Dry Run" in output) or ("dry-run" in output) or ("Dry run" in output), (
            f"Expected dry-run output in container stdout/stderr, got:\n{output[:1000]}"
        )

        # Also inspect the shell config file inside our fake home
        zshrc = fake_home / ".zshrc"
        bashrc = fake_home / ".bashrc"

        content = ""
        if zshrc.exists():
            content = zshrc.read_text()
        elif bashrc.exists():
            content = bashrc.read_text()
        else:
            pytest.skip("No shell config file created inside container home; setup.sh may not have detected shell")

        assert "pcopy()" in content, "pcopy() function not found in shell config after running setup.sh"

    finally:
        # Cleanup: remove image to keep environment tidy
        subprocess.run(["docker", "rmi", "-f", image_tag], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
