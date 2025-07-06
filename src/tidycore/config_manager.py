# tidycore/config_manager.py
import json
import os
from typing import Dict, Any
from .utils import get_absolute_path
from pathlib import Path

CONFIG_PATH = get_absolute_path("config/config.json")

def load_config() -> Dict[str, Any]:
    """
    Loads and resolves the configuration file.
    It can automatically find the user's Downloads folder.
    
    Returns:
        A dictionary containing the configuration.

    Raises:
        FileNotFoundError: If the config file cannot be found.
        ValueError: If the target folder in the config does not exist.
    """
    path = CONFIG_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"Configuration file not found at: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # --- Path Resolution Logic ---
    target_folder = config.get("target_folder")
    if target_folder == "{USER_DOWNLOADS}":
        # Find the user's home directory and append 'Downloads'
        # This works on Windows, macOS, and Linux.
        downloads_path = Path.home() / "Downloads"
        config["target_folder"] = str(downloads_path)
        
    # Validate that the final target folder exists
    # Use .get() to avoid a KeyError if target_folder is missing from config
    resolved_target = config.get("target_folder")
    if not resolved_target or not os.path.isdir(resolved_target):
        raise ValueError(
            f"The target folder '{resolved_target}' is invalid or does not exist."
        )
    
    # Normalize file extensions to lowercase for consistent matching
    rules = config.get("rules", {})
    if rules: # Ensure rules exist before trying to iterate
        for category, extensions in rules.items():
            if isinstance(extensions, list):
                config["rules"][category] = [ext.lower() for ext in extensions]
            elif isinstance(extensions, dict):
                for sub_category, sub_extensions in extensions.items():
                    config["rules"][category][sub_category] = [ext.lower() for ext in sub_extensions]

    return config

def save_config(config_data: Dict[str, Any]):
    """
    Saves the provided configuration dictionary to the config file.

    Args:
        config_data (Dict[str, Any]): The configuration dictionary to save.
    """
    path = CONFIG_PATH
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2)

# Create a simple class to act as a namespace for our functions
class ConfigManager:
    def load_config(self) -> Dict[str, Any]:
        """Loads config from the default path."""
        return load_config()
    
    def save_config(self, config_data: Dict[str, Any]):
        """Saves config to the default path."""
        save_config(config_data)