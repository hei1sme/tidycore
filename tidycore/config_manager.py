# tidycore/config_manager.py
import json
import os
from typing import Dict, Any

def load_config(path: str = "config.json") -> Dict[str, Any]:
    """
    Loads the configuration file.

    Args:
        path (str): The path to the config.json file.

    Returns:
        A dictionary containing the configuration.
        
    Raises:
        FileNotFoundError: If the config file cannot be found.
        ValueError: If the target folder in the config does not exist.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Configuration file not found at: {path}")

    with open(path, 'r') as f:
        config = json.load(f)

    # Validate that the target folder exists
    target_folder = config.get("target_folder")
    if not target_folder or not os.path.isdir(target_folder):
        raise ValueError(
            f"The 'target_folder' specified in {path} is invalid or does not exist."
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

def save_config(config_data: Dict[str, Any], path: str = "config.json"):
    """
    Saves the provided configuration dictionary to the config file.

    Args:
        config_data (Dict[str, Any]): The configuration dictionary to save.
        path (str, optional): The path to the config file. Defaults to "config.json".
    """
    with open(path, 'w') as f:
        json.dump(config_data, f, indent=2)

# Create a simple class to act as a namespace for our functions
class ConfigManager:
    def load_config(self, path: str = "config.json") -> Dict[str, Any]:
        return load_config(path)
    
    def save_config(self, config_data: Dict[str, Any], path: str = "config.json"):
        save_config(config_data, path)