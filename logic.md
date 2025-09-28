# PurrfectCopy: What actually happens when a backup runs

This document explains, in plain language, the exact sequence of steps the program performs when you run a backup (either in dry-run or real mode). It shows the commands that get built and explains why the code takes each step. It's written so a non-developer can understand the overall flow and what to expect.

1. High-level overview

- The program has two main ways to perform a backup:
  1. A Python-first approach that makes timestamped safety copies of changed files and then uses rsync if available.
  2. A subprocess approach that runs rsync directly and streams its output to a small status UI.

- Before the backup starts the program will display the full rsync command it plans to run (both for a dry-run preview and for the real run) so you can inspect it.

- After the run finishes the program records a short summary (last-run metadata) into the YAML settings file so the interactive menu can show when and how the job last ran.

1. Exact step-by-step flow

1. Decide which mode to run in

- If you asked for the interactive demo mode, the program shows a fake demo and exits.
- If the configuration opts to use the Python copy logic (the default in recent versions), the program will try the Python path first.
- Tests and special flags can force simulated behavior so the tests are deterministic.

1. Python-first copy logic (safe default)

- The program walks the source folder tree and compares timestamps for each file with the corresponding destination file.
- For every file where the source file is newer than the destination file, the program makes a timestamped copy of the destination file (a safety copy) before the new file is applied. The safety copy has a suffix with a timestamp like `20250927_173709`.

  Example: if the destination has `/backup/foo.txt` and you are about to overwrite it, the program creates `/backup/foo.20250927_173709.txt` with the old contents so you can recover it later.

- After creating safety copies for changed files, the program either calls `rsync` (if available and allowed) to do the efficient file transfer, or — if `rsync` is disabled/unavailable — performs a simple Python copy of new files.

- The function that does this work returns a small dictionary describing what happened: which files were timestamped, which new files were copied, whether rsync ran, and any rsync output.

1. rsync direct/subprocess path (streaming output)

- If the Python step falls back to running `rsync` (or if Python-first was not used), the program builds a single `rsync` command and runs it.

- The runner builds this `rsync` command using these exact flags by default:

  Minimal run (used in menu previews and the streaming runner):

  ```sh
  rsync -a --info=progress2 /path/to/source /path/to/dest
  ```

  The Python copy implementation (when it decides to call `rsync`) uses a more verbose rsync invocation for a real sync pass:

  ```sh
  rsync -avh --progress2 --partial --no-whole-file --inplace --update --log-file /path/to/log /path/to/source/ /path/to/dest
  ```

  If the program is doing a dry-run preview it adds the `--dry-run` flag to the minimal command.

1. rsync flags explained (plain English)

- `rsync`: the program used to synchronize files efficiently.
- `-a` (archive): keep file attributes and copy recursively (files, directories, timestamps, permissions).
- `-v` (verbose) / `-h` (human readable): print more information during the run in human-friendly units.
- `--info=progress2` / `--progress2`: show a progress summary as rsync runs.
- `--partial` / `--no-whole-file` / `--inplace`: help rsync resume and update large files efficiently.
- `--update`: don't overwrite destination files that are newer.
- `--dry-run`: show what rsync would do without making changes.
- `--log-file /path/to/log`: capture rsync's runtime log in a file.

1. Trailing slash semantics (why `/source/` matters)

- The Python copy logic calls `rsync` with the source path followed by a path separator (a trailing slash). This tells `rsync` to copy the contents of the source folder into the destination folder, rather than copying the source directory itself as a subfolder of the destination. For most backup scenarios this is the expected behavior.

1. What the interactive menu shows you

- The interactive menu prints two things before you confirm a run:
  - The full rsync command for a dry-run (preview).
  - The full rsync command for the real run.

- This gives you an exact command you could run manually if you prefer.

1. Persistence: the last-run summary

- After a run (or during a simulated test run), the runner writes a small record into the settings YAML file under the named job's entry. That record includes:

  - `timestamp`: when the run finished
  - `status`: numeric exit code (0 = success)
  - `status_str`: `'PASS'` or `'FAILED'` or `'RUNNING'`
  - `dry_run`: boolean showing whether the run was a dry-run
  - `transferred_bytes`: total bytes rsync reported (if available)
  - `elapsed_seconds`: how long the run took (best-effort)
  - `errors_count` and `errors_sample`: a small list of recent error messages
  - `duplicates` and `dupes_saved`: information about duplicate/versioned files when the backup-versions directory is enabled

- This is why the interactive menu can show when a job last ran and whether it passed.

1. Test modes and deterministic simulation

- The code supports a test mode (`PCOPY_TEST_MODE=1`) to produce deterministic, synthetic rsync-like output. Tests use this mode so unit and integration tests are fast and predictable without requiring an actual `rsync` binary or Docker environment.

1. Error handling and fallbacks (robustness)

- If `rsync` is not installed or cannot be run, the application:
  - In Python-first mode, falls back to a simple Python-based copy of new files (safe and portable, though not as fast or featureful as `rsync`).
  - In the streaming runner mode, detects `FileNotFoundError` for `rsync` and prints a helpful message noting "rsync not found" so the user/automation can take corrective steps.

- When the Python path fails for any reason, the program will try the subprocess path as a last resort so most reasonable environments still end up with a successful run.

Appendix — concrete command examples you will see

- Dry-run preview printed to the screen:

```sh
rsync -a --info=progress2 --dry-run /path/to/source /path/to/dest
```

- Actual rsync invocation used by the Python copy pass (more options):

```sh
rsync -avh --progress2 --partial --no-whole-file --inplace --update --log-file /path/to/log /path/to/source/ /path/to/dest
```

Appendix — timestamped safety copy example

- Original destination file: `/backup/report.txt`
- If the source has a newer `report.txt`, the program creates a safety copy of the destination before overwriting it, for example:

  `/backup/report.20250927_173709.txt`

Why this design?

- Safety: timestamped copies mean accidental overwrites are recoverable.
- Testability: the pure-Python copy path makes behavior deterministic for unit tests and CI when `rsync` or Docker are not available.
- Performance: calling `rsync` (when available) preserves speed and efficiency for large backups.
- Transparency: the exact `rsync` commands are printed for inspection — you can copy that line and run it yourself.

Short checklist of what happens when you run a named backup

- Program reads the named job from the settings file.
- Program displays the rsync dry-run and run commands in the menu (if interactive).
- Program marks the job as `RUNNING` (persisting the `RUNNING` state so the menu shows progress).
- Program makes timestamped backups of files that would be overwritten.
- Program runs `rsync` (or uses Python to copy new files) to update the destination.
- Program records the run summary in the settings YAML.

If you want a small visual "before/after" directory example or a one-line cheat-sheet for the rsync flags, say which you prefer and I'll add it.
