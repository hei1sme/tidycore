# tidycore/engine.py
import os
import shutil
import time
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class TidyCoreEngine(FileSystemEventHandler):
    """
    The core engine for TidyCore. It watches the target directory
    and organizes files based on the provided configuration.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("TidyCore")
        self.target_folder = Path(self.config["target_folder"])
        self.rules = self.config.get("rules", {})
        self.ignore_list = self.config.get("ignore_list", [])
        self.cooldown_period = self.config.get("cooldown_period_seconds", 5)
        
        # A dictionary to track files in their cooldown period
        self.cooldown_files: Dict[str, float] = {}

    def run(self):
        """Starts the file watching process."""
        self.logger.info("TidyCore Engine starting...")
        self.logger.info(f"Watching folder: {self.target_folder}")
        self.logger.info(f"Cooldown period set to {self.cooldown_period} seconds.")
        
        # Initial scan to organize existing files
        self.initial_scan()

        observer = Observer()
        observer.schedule(self, str(self.target_folder), recursive=False)
        observer.start()

        try:
            while True:
                time.sleep(5)
                self._process_cooldown_files()
        except KeyboardInterrupt:
            self.logger.info("Shutdown signal received. Stopping engine.")
            observer.stop()
        observer.join()
        
    def initial_scan(self):
        """Performs a one-time scan of the directory on startup."""
        self.logger.info("Performing initial scan of target folder...")
        with os.scandir(self.target_folder) as entries:
            for entry in entries:
                if self._should_process(entry.path):
                    self._organize_item(entry.path)
        self.logger.info("Initial scan complete.")

    def on_created(self, event):
        """Called when a file or directory is created."""
        if self._should_process(event.src_path):
            self.logger.info(f"New item detected: {os.path.basename(event.src_path)}. Starting cooldown.")
            self.cooldown_files[event.src_path] = time.time()

    def _process_cooldown_files(self):
        """Checks and organizes files that have passed their cooldown period."""
        now = time.time()
        ready_to_process = []
        
        for path, detected_time in self.cooldown_files.items():
            if now - detected_time > self.cooldown_period:
                ready_to_process.append(path)
        
        for path in ready_to_process:
            del self.cooldown_files[path]
            if os.path.exists(path):
                self._organize_item(path)

    def _should_process(self, path: str) -> bool:
        """Determines if a file or folder should be processed."""
        base_name = os.path.basename(path)
        
        # Ignore if in ignore list
        if base_name in self.ignore_list:
            return False
        
        # Ignore hidden files/folders (dotfiles)
        if base_name.startswith('.'):
            return False
            
        # Ignore if it's a TidyCore-managed category folder in the root
        if os.path.isdir(path) and base_name in self.rules:
            self.logger.debug(f"Ignoring category folder: {base_name}")
            return False

        return True

    def _organize_item(self, path: str):
        """Organizes a single file or folder."""
        if not os.path.exists(path):
            self.logger.warning(f"Item {os.path.basename(path)} no longer exists. Skipping.")
            return

        self.logger.info(f"Processing: {os.path.basename(path)}")
        
        category, sub_category = self._get_category(path)
        
        destination_dir = self.target_folder / category
        if sub_category and sub_category != category:
            destination_dir = destination_dir / sub_category

        os.makedirs(destination_dir, exist_ok=True)
        
        destination_path = self._resolve_conflict(destination_dir / os.path.basename(path))
        
        try:
            shutil.move(path, destination_path)
            self.logger.info(f"Moved '{os.path.basename(path)}' -> '{destination_path.relative_to(self.target_folder)}'")
        except Exception as e:
            self.logger.error(f"Failed to move {os.path.basename(path)}. Error: {e}")

    def _get_category(self, path: str) -> Tuple[str, Optional[str]]:
        """Determines the category and sub-category for a given path."""
        if os.path.isfile(path):
            ext = os.path.splitext(path)[1].lower()
            if not ext: return "Others", None # Files without extension
            
            for category, sub_rules in self.rules.items():
                if isinstance(sub_rules, list):
                    if ext in sub_rules:
                        return category, None
                elif isinstance(sub_rules, dict):
                    for sub_category, extensions in sub_rules.items():
                        if ext in extensions:
                            return category, sub_category
        
        return "Others", None # Folders and uncategorized files go to others for now

    def _resolve_conflict(self, destination_path: Path) -> Path:
        """
        If a file already exists at the destination, appends a number.
        Example: file.txt -> file (1).txt
        """
        if not destination_path.exists():
            return destination_path

        base = destination_path.stem
        ext = destination_path.suffix
        parent = destination_path.parent
        counter = 1

        while True:
            new_name = f"{base} ({counter}){ext}"
            new_path = parent / new_name
            if not new_path.exists():
                self.logger.warning(f"Conflict at {destination_path}. Renaming to {new_name}.")
                return new_path
            counter += 1