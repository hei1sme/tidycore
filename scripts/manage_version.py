# version_manager.py
"""
Script to manage version updates for TidyCore releases.
"""
import re
from pathlib import Path

def get_current_version():
    """Get the current version from __init__.py"""
    init_file = Path("tidycore/__init__.py")
    content = init_file.read_text()
    match = re.search(r'__version__ = ["\']([^"\']+)["\']', content)
    return match.group(1) if match else "1.0.0"

def update_version(new_version):
    """Update the version in __init__.py"""
    init_file = Path("tidycore/__init__.py")
    content = init_file.read_text()
    new_content = re.sub(
        r'__version__ = ["\'][^"\']+["\']',
        f'__version__ = "{new_version}"',
        content
    )
    init_file.write_text(new_content)
    print(f"Updated version to {new_version}")

def increment_version(version_type="patch"):
    """Increment version number (major.minor.patch)"""
    current = get_current_version()
    parts = current.split(".")
    
    if len(parts) != 3:
        print(f"Invalid version format: {current}")
        return current
    
    major, minor, patch = map(int, parts)
    
    if version_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif version_type == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    
    new_version = f"{major}.{minor}.{patch}"
    update_version(new_version)
    return new_version

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print(f"Current version: {get_current_version()}")
        print("Usage: python version_manager.py [major|minor|patch|set VERSION]")
    elif sys.argv[1] == "set" and len(sys.argv) == 3:
        update_version(sys.argv[2])
    elif sys.argv[1] in ["major", "minor", "patch"]:
        new_version = increment_version(sys.argv[1])
        print(f"Version updated to: {new_version}")
    else:
        print("Invalid command. Use: major, minor, patch, or set VERSION")
