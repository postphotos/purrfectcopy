# Purrfect Backup 🐾

A delightful, kitten-powered `rsync` backup script with a rich, real-time Terminal User Interface (TUI) built in Python.

Release: v0.0.1 (2025-09-23)

## ✨ Features

- **Rich TUI Dashboard:** A beautiful, flicker-free dashboard that displays live backup progress.
- **Real-time Stats:** See the current file, transfer speed, total data transferred, and error count as it happens.
- **Delightful & Fun:** Features an ever-changing cast of `cowsay` characters (including custom ones!) that cheer you on with witty slogans.
- **Safe & Robust:** Powered by `rsync` for reliable and efficient backups. Uses a simple Bash launcher to handle permissions and environment setup.
- **Highly Configurable:** All slogans, quotes, and paths are easily editable in `slogans.json` and `app.py`.
- **Modern Python Tooling:** Uses `uv` for fast and efficient dependency management.

## Hey, hey wait, isn't this just RSYNC? Cowsay? With some other ridiculous goodies?

Yeah. The goal is to spark joy. Sometimes it's good to be [serious, not solemn.](https://www.youtube.com/watch?v=atn22-bmTPU) I hope you enjoy it, too!

While this python module library "just" wraps rsync, if you prefer to stare at confusing numbers and hoping you got it all right, that's fine, but it's not for all of us. Some of us want typing, code coverage and predictability. (And cowsay + cat slogans.)

Because remembering `rsync -havx--infoprogress2 & afewothers maybe one dash or --maybenone --dry-run-maybe?` hasn't gotten any easier after using rsync for over a decade, but it's still the best and there's always room for improvement.

It's our goal to keep this python application at 100% coverage. We also provide the task runner - `run-backup.sh` - to perform your backup work. We also provide a local `setup.sh` to add an alias - `pcopy` - to your `.bashrc`/`.zshrc`.

If you often find yourself scuttling data and are sick of confusing syntax (like the rest of us are!) and need some more cats inyour life, this `pcopy` application acts as a fancy alias for `rsync` defaults: A great nice-to-have and makes menial file maintence just a little less awful.

## 🛠️ Setup

Run `./setup.sh` to install and configure Purrfect Backup. The script will:

- Ensure `uv` is available (and install it via pip if needed).
- Install the Python dependencies from `requirements.txt`.
- Add a `pcopy` helper function to your shell configuration (`~/.bashrc` or `~/.zshrc`) so you can use `pcopy` from the shell.

After running the script you can either restart your shell or run `source ~/.zshrc` (or `source ~/.bashrc`) to pick up the new `pcopy` helper.

### Using pcopy (syntax)

- `pcopy source dest` — Run a backup using the given source and destination paths.
- `pcopy do main-backup` or `pcopy main-backup` — Run the "main-backup" configuration defined in your settings file (`~/.pcopy-main-backup.yml`).

### Local settings file

Create `~/.pcopy-main-backup.yml` to declare a named backup and optional rsync overrides. Example:

```yaml
main-backup:
    source: "/path/to/source"
    dest: "/path/to/destination"
rsync_options:
    - "--verbose"
    - "--progress"
```

When `pcopy` is invoked with `do main-backup` (or `main-backup`), the app will read this file and use the configured `source` and `dest` and apply any `rsync_options` listed.

## 📦 Installation

1. **Clone the Repository:**

    ```bash
    git clone <your-repo-url>
    cd purrfect-backup
    ```

2. **Install System Dependencies:**
    You will need `rsync`, `cowsay`, and a Python interpreter. It's suggested you use an environment manager like [uv](https://docs.astral.sh/uv/getting-started/installation/), which is what our setup uses.

    ```bash
    # On macOS with Homebrew
    brew install rsync cowsay
    ```

3. **Install Python Tooling (`uv`):**
    This project uses `uv` as a modern, high-speed replacement for `pip` and `venv`.

    ```bash
    pip install uv
    ```

4. **Install Python Dependencies:**
    The launcher script will do this for you, but you can also run it manually to set up the environment.

    ```bash
    uv install -r requirements.txt
    ```

## 🚀 Usage

The `run-backup.sh` script is the main entry point. It will handle permissions and run the Python application for you.

**To run a backup:**

```bash
./run-backup.sh
```

The script will automatically request `sudo` privileges.

### Command-Line Flags

You can pass flags to the launcher, and they will be forwarded to the Python application.

- **Dry Run (Simulate):** See what files would be transferred without making any changes.

    ```bash
    ./run-backup.sh --dry-run
    ```

- **Show Command:** Print the exact `rsync` command that would be executed and exit. This is great for debugging.

    ```bash
    ./run-backup.sh --dry-run-command
    ```

## 🔧 Configuration

- **Backup Paths:** To change the source or destination directories, edit the "CUSTOMIZE YOUR PATHS HERE" section at the top of `app.py`.
- **Slogans & Characters:** To add or change any of the fun text, edit the `slogans.json` file. You can even add new `.cow` files to the `cows/` directory and reference them in the JSON file!

## Docker-based smoke-test

We provide `Dockerfile.alpine` as a lightweight smoke-test image that installs system dependencies (rsync, cowsay), prepares a small sample source tree, and runs `app.py` in `--dry-run` mode. This is used by CI to validate the runtime behavior in a container similar to minimal Linux systems.

To build and run locally:

```bash
docker build -f Dockerfile.alpine -t pcopy-smoketest:latest .
docker run --rm pcopy-smoketest:latest
```

The smoke-test runs the app in dry-run mode by default so it won't modify your host files.

## Sample output

Below is an example of the TUI during a dry-run showing a dual-column view (Source / Destination)
and some playful "cat meme" cowsay messages. This is illustrative — exact output will vary
with terminal size and progress.

```text
Purrfect Backup — Dry Run

Source: /home/user/photos            | Destination: /backup/photos
---------------------------------------------------------------
Files:  12/120                        | Transferred:  0.0B
Speed:  0.0B/s                       | Elapsed: 00:00

[  5% ] Copying: 2025/08/01_cat1.jpg  | [  5% ] -> /backup/photos/2025/08/01_cat1.jpg
[  5% ] Copying: 2025/08/02_cat2.jpg  | [  5% ] -> /backup/photos/2025/08/02_cat2.jpg

    ,_     "Backup complete"
 ( o.o)  < Meowtain of memes incoming
    > ^

Progress: [#####....................................] 5%

```

## License

This is released under [GPL 3.0](LICENSE).
