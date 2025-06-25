# TidyCore

A smart, modern, and configurable file organization utility that automatically tidies up your folders.

## Core Features (Phase 1)

- **Rule-Based Organization**: Automatically moves files based on configurable rules in `config.json`.
- **Robust & Safe**: Implements a cooldown period to avoid moving incomplete downloads and handles file name conflicts gracefully.
- **Ignore Lists**: Prevents specified files and folders from being moved.
- **Professional Logging**: All actions are logged to the console and to `tidycore.log`.
- **Initial Scan**: Organizes all existing files in the target directory on startup.

## Installation & Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/your-username/TidyCore.git
    cd TidyCore
    ```
2. Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate 
    ```
3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4. **Important:** Edit `config.json` and set the `target_folder` to your desired directory (e.g., your Downloads folder).

## Usage

To start the TidyCore engine, simply run:
```bash
python main.py
```
Press `Ctrl+C` to stop the program gracefully.