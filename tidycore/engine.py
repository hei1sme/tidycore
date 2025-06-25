# tidycore/engine.py
import os
import shutil
import time
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
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
        
        self.managed_categories = list(self.rules.keys()) + ["Others"]
        
        self.cooldown_files: Dict[str, float] = {}

    def run(self):
        """Starts the file watching process."""
        self.logger.info("TidyCore Engine starting...")
        self.logger.info(f"Watching folder: {self.target_folder}")
        self.logger.info(f"Cooldown period set to {self.cooldown_period} seconds.")
        
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
        entries_to_process = []
        with os.scandir(self.target_folder) as entries:
            for entry in entries:
                if self._should_process(entry.path):
                    entries_to_process.append(entry.path)
        
        for path in entries_to_process:
            self._organize_item(path)
            
        self.logger.info("Initial scan complete.")
    
    # --- NEW: Helper function to handle adding items to the queue ---
    def _queue_item_for_processing(self, path: str):
        """Checks if an item should be processed and adds it to the cooldown queue."""
        if self._should_process(path):
            # Don't re-add an item that is already in the queue
            if path not in self.cooldown_files:
                self.logger.info(f"New item detected: {os.path.basename(path)}. Starting cooldown.")
                self.cooldown_files[path] = time.time()

    def on_created(self, event):
        """Called when a file or directory is created."""
        self._queue_item_for_processing(event.src_path)

    # --- NEW: The `on_modified` handler to catch finalized downloads ---
    def on_modified(self, event):
        """
        Called when a file or directory is modified.
        This is crucial for catching files that are renamed after being downloaded
        (e.g., .crdownload -> .docx).
        """
        self._queue_item_for_processing(event.src_path)

    def _process_cooldown_files(self):
        """Checks and organizes files that have passed their cooldown period."""
        now = time.time()
        ready_to_process = []
        
        for path, detected_time in list(self.cooldown_files.items()):
            if now - detected_time > self.cooldown_period:
                ready_to_process.append(path)
        
        for path in ready_to_process:
            if path in self.cooldown_files:
                del self.cooldown_files[path]
            if os.path.exists(path):
                self._organize_item(path)

    def _should_process(self, path: str) -> bool:
        """Determines if a file or folder should be processed."""
        if not os.path.exists(path):
            return False

        base_name = os.path.basename(path)
        ext = os.path.splitext(base_name)[1].lower()

        # Check against ignore list (full name or extension)
        if base_name in self.ignore_list or (ext and ext in self.ignore_list):
            self.logger.debug(f"Ignoring '{base_name}' as it is in the ignore_list.")
            return False
        
        if base_name.startswith('.'):
            self.logger.debug(f"Ignoring '{base_name}' as it is a hidden file.")
            return False
            
        if os.path.isdir(path) and base_name in self.managed_categories:
            self.logger.debug(f"Ignoring '{base_name}' as it is a managed category folder.")
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
        
        if Path(path).resolve() == destination_dir.resolve():
            self.logger.warning(f"Skipping '{os.path.basename(path)}' as its destination is itself.")
            return

        destination_path = self._resolve_conflict(destination_dir / os.path.basename(path))
        
        try:
            shutil.move(path, destination_path)
            self.logger.info(f"Moved '{os.path.basename(path)}' -> '{destination_path.relative_to(self.target_folder)}'")
        except Exception as e:
            self.logger.error(f"Failed to move {os.path.basename(path)}. Error: {e}")

    def _get_category(self, path: str) -> Tuple[str, Optional[str]]:
        """Determines the category and sub-category for a given path."""
        if os.path.isdir(path):
            main_category = self._get_folder_dominant_category(path)
            return main_category, None

        if os.path.isfile(path):
            ext = os.path.splitext(path)[1].lower()
            if not ext: return "Others", None
            
            for category, sub_rules in self.rules.items():
                if isinstance(sub_rules, list):
                    if ext in sub_rules:
                        return category, None
                elif isinstance(sub_rules, dict):
                    for sub_category, extensions in sub_rules.items():
                        if ext in extensions:
                            return category, sub_category
        
        return "Others", None

    def _get_folder_dominant_category(self, folder_path: str) -> str:
        """Scans a folder to find its dominant file category."""
        category_counts: Dict[str, int] = {category: 0 for category in self.rules.keys()}
        
        try:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    category, _ = self._get_category(os.path.join(root, file))
                    if category in category_counts:
                        category_counts[category] += 1
        except Exception as e:
            self.logger.error(f"Could not scan folder '{os.path.basename(folder_path)}'. Error: {e}")
            return "Others"
        
        if not any(category_counts.values()):
            return "Others"

        dominant_category = max(category_counts, key=category_counts.get)
        return dominant_category

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