# Purrfect Backup 🐾

A delightful, kitten-powered `rsync` backup script with a rich, real-time Terminal User Interface (TUI) built in Python.

![demo](https://user-images.githubusercontent.com/.../demo.gif)  
*(A GIF demonstrating the TUI in action would go here)*

## ✨ Features

- **Rich TUI Dashboard:** A beautiful, flicker-free dashboard that displays live backup progress.
- **Real-time Stats:** See the current file, transfer speed, total data transferred, and error count as it happens.
- **Delightful & Fun:** Features an ever-changing cast of `cowsay` characters (including custom ones!) that cheer you on with witty slogans.
- **Safe & Robust:** Powered by `rsync` for reliable and efficient backups. Uses a simple Bash launcher to handle permissions and environment setup.
- **Highly Configurable:** All slogans, quotes, and paths are easily editable in `slogans.json` and `app.py`.
- **Modern Python Tooling:** Uses `uv` for fast and efficient dependency management.

## 📦 Installation

1.  **Clone the Repository:**
    ```bash
    git clone <your-repo-url>
    cd purrfect-backup
    ```

2.  **Install System Dependencies:**
    You will need `rsync`, `cowsay`, and a Python interpreter.
    ```bash
    # On macOS with Homebrew
    brew install rsync cowsay
    ```

3.  **Install Python Tooling (`uv`):**
    This project uses `uv` as a modern, high-speed replacement for `pip` and `venv`.
    ```bash
    pip install uv
    ```

4.  **Install Python Dependencies:**
    The launcher script will do this for you, but you can also run it manually to set up the environment.
    ```bash
    uv install -r requirements.txt
    ```

## 🚀 Usage

The `backup.sh` script is the main entry point. It will handle permissions and run the Python application for you.

**To run a backup:**

```bash
./backup.sh
```

The script will automatically request `sudo` privileges.

### Command-Line Flags

You can pass flags to the launcher, and they will be forwarded to the Python application.

-   **Dry Run (Simulate):** See what files would be transferred without making any changes.
    ```bash
    ./backup.sh --dry-run
    ```
-   **Show Command:** Print the exact `rsync` command that would be executed and exit. This is great for debugging.
    ```bash
    ./backup.sh --dry-run-command
    ```

## 🔧 Configuration

-   **Backup Paths:** To change the source or destination directories, edit the "CUSTOMIZE YOUR PATHS HERE" section at the top of `app.py`.
-   **Slogans & Characters:** To add or change any of the fun text, edit the `slogans.json` file. You can even add new `.cow` files to the `cows/` directory and reference them in the JSON file!