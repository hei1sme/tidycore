# tidycore/engine.py
import os
import shutil
import time
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from tidycore.signals import signals
from tidycore.config_manager import ConfigManager

class TidyCoreEngine(FileSystemEventHandler):
    """
    The core engine for TidyCore. It watches the target directory
    and organizes files based on on the provided configuration.
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger("TidyCore")
        self.target_folder = Path(self.config["target_folder"])
        self.rules = self.config.get("rules", {})
        self.ignore_list = self.config.get("ignore_list", [])
        self.cooldown_period = self.config.get("cooldown_period_seconds", 5)
        self.managed_categories = list(self.rules.keys()) + ["Others"]
        self.config_manager = ConfigManager()
        self.cooldown_files: Dict[str, float] = {}
        self.is_running = True
        self.observer = Observer()
        self.files_organized_today = 0
        self.files_organized_total = 0

    def run(self):
        """Starts the file watching process."""
        self.logger.info("TidyCore Engine thread started.")
        self.initial_scan()
        
        self.observer.schedule(self, str(self.target_folder), recursive=False)
        self.observer.start()
        signals.status_changed.emit(self.is_running)

        try:
            while self.observer.is_alive():
                if self.is_running:
                    self._process_cooldown_files()
                time.sleep(1)
        except Exception as e:
            self.logger.critical(f"An error occurred in the engine loop: {e}", exc_info=True)
        finally:
            if self.observer.is_alive():
                self.observer.stop()
            self.observer.join()
            self.logger.info("TidyCore Engine thread has stopped.")

    def pause(self):
        """Pauses the file processing loop."""
        if self.is_running:
            self.is_running = False
            self.logger.info("Engine paused.")
            signals.status_changed.emit(self.is_running)

    def resume(self):
        """Resumes the file processing loop."""
        if not self.is_running:
            self.is_running = True
            self.logger.info("Engine resumed.")
            signals.status_changed.emit(self.is_running)
            
    def stop(self):
        """Stops the observer thread gracefully."""
        self.logger.info("Engine stop signal received.")
        if self.observer.is_alive():
            self.observer.stop()

    def request_status(self):
        """Allows the GUI to request the current status upon startup."""
        self.logger.debug("GUI requested status update.")
        signals.status_changed.emit(self.is_running)

    def initial_scan(self):
        self.logger.info("Performing initial scan of target folder...")
        entries_to_process = []
        with os.scandir(self.target_folder) as entries:
            for entry in entries:
                if self._should_process(entry.path):
                    entries_to_process.append(entry.path)
        
        for path in entries_to_process:
            self._organize_item(path)
            
        self.logger.info("Initial scan complete.")
    
    def _queue_item_for_processing(self, path: str):
        if self._should_process(path):
            if path not in self.cooldown_files:
                self.logger.info(f"New item detected: {os.path.basename(path)}. Starting cooldown.")
                self.cooldown_files[path] = time.time()

    def on_created(self, event):
        self._queue_item_for_processing(event.src_path)

    def on_modified(self, event):
        self._queue_item_for_processing(event.src_path)

    def _process_cooldown_files(self):
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
        base_name = os.path.basename(path)
        
        # --- MODIFICATION: Add a check for the "ignore" strategy ---
        folder_strategy = self.config.get("folder_handling_strategy", "smart_scan")
        if folder_strategy == "ignore" and os.path.isdir(path):
            # If strategy is to ignore folders, check if the item is a directory.
            # We must NOT ignore our own managed category folders, which are handled later.
            if base_name not in self.managed_categories:
                 self.logger.debug(f"Ignoring folder '{base_name}' as per 'ignore' strategy.")
                 return False
        
        if not os.path.exists(path):
            return False

        ext = os.path.splitext(base_name)[1].lower()

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
        if not os.path.exists(path):
            self.logger.warning(f"Item {os.path.basename(path)} no longer exists. Skipping.")
            return

        self.logger.info(f"Processing: {os.path.basename(path)}")
        original_path_str = str(path)
        
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
            log_msg = f"Moved '{os.path.basename(path)}' -> '{destination_path.relative_to(self.target_folder)}'"
            self.logger.info(log_msg)
            signals.log_message.emit(log_msg)
            
            self.files_organized_today += 1
            self.files_organized_total += 1
            signals.update_stats.emit(self.files_organized_today, self.files_organized_total)
            
            signals.file_organized.emit(category)

            if os.path.isdir(destination_path):
                signals.folder_decision_made.emit(original_path_str, str(destination_path), category)

        except Exception as e:
            log_msg = f"Failed to move {os.path.basename(path)}. Error: {e}"
            self.logger.error(log_msg)
            signals.log_message.emit(f"[ERROR] {log_msg}")

    def undo_move(self, source_path: str, original_path: str):
        """Moves an item back from its organized location."""
        if not os.path.exists(source_path):
            log_msg = f"[ERROR] Cannot undo: Source '{os.path.basename(source_path)}' no longer exists."
            self.logger.error(log_msg)
            signals.log_message.emit(log_msg)
            return

        try:
            destination_path = self._resolve_conflict(Path(original_path))
            shutil.move(source_path, destination_path)
            log_msg = f"[UNDO] Moved '{os.path.basename(source_path)}' back."
            self.logger.info(log_msg)
            signals.log_message.emit(log_msg)
        except Exception as e:
            log_msg = f"Failed to undo move for {os.path.basename(source_path)}. Error: {e}"
            self.logger.error(log_msg)
            signals.log_message.emit(f"[ERROR] {log_msg}")

    def add_to_ignore_list(self, item_name: str):
        """Adds an item to the config's ignore list and saves it."""
        self.logger.info(f"Adding '{item_name}' to ignore list.")
        if "ignore_list" not in self.config:
            self.config["ignore_list"] = []
            
        if item_name not in self.config["ignore_list"]:
            self.config["ignore_list"].append(item_name)
            self.config_manager.save_config(self.config)
            self.ignore_list = self.config["ignore_list"]
            signals.log_message.emit(f"'{item_name}' added to ignore list.")
            # Notify the rest of the app that the config has changed
            signals.config_changed.emit()
        else:
            signals.log_message.emit(f"'{item_name}' is already in the ignore list.")

    def _get_category(self, path: str) -> Tuple[str, Optional[str]]:
        """Determines the category and sub-category for a given path."""
        # --- MODIFIED: The core logic change is here ---
        if os.path.isdir(path):
            strategy = self.config.get("folder_handling_strategy", "smart_scan")
            
            if strategy == "smart_scan":
                main_category = self._get_folder_dominant_category(path)
                return main_category, None
            elif strategy == "move_to_others":
                return "Others", None
            # If strategy is "ignore", it will have been filtered out by _should_process,
            # so we don't need to explicitly handle it here. Fallback for safety.
            return "Others", None

        if os.path.isfile(path):
            ext = os.path.splitext(path)[1].lower()
            if not ext: return "Others", None
            
            for category, sub_rules in self.rules.items():
                if isinstance(sub_rules, list): # Simple flat category
                    if ext in sub_rules:
                        return category, None
                elif isinstance(sub_rules, dict): # Nested or mixed category
                    # Check for flat extensions first using our special key
                    if ext in sub_rules.get("__extensions__", []):
                        return category, None
                    
                    # Then check the actual sub-categories
                    for sub_category, extensions in sub_rules.items():
                        if sub_category == "__extensions__":
                            continue # Already checked
                        if ext in extensions:
                            return category, sub_category
        
        return "Others", None

    def _get_folder_dominant_category(self, folder_path: str) -> str:
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