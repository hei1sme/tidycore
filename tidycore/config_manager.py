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
    for category, extensions in config.get("rules", {}).items():
        if isinstance(extensions, list):
            config["rules"][category] = [ext.lower() for ext in extensions]
        elif isinstance(extensions, dict):
            for sub_category, sub_extensions in extensions.items():
                config["rules"][category][sub_category] = [ext.lower() for ext in sub_extensions]

    return config