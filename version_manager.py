# version_manager.py - Version management and release preparation
import re
import sys
from pathlib import Path
from datetime import datetime

def get_current_version():
    """Get the current version from __init__.py"""
    init_file = Path("tidycore/__init__.py")
    if not init_file.exists():
        print("❌ __init__.py not found")
        return None
    
    content = init_file.read_text()
    match = re.search(r'__version__ = "([^"]+)"', content)
    if match:
        return match.group(1)
    return None

def update_version(new_version):
    """Update the version in __init__.py"""
    init_file = Path("tidycore/__init__.py")
    if not init_file.exists():
        print("❌ __init__.py not found")
        return False
    
    content = init_file.read_text()
    updated_content = re.sub(
        r'__version__ = "[^"]+"',
        f'__version__ = "{new_version}"',
        content
    )
    
    init_file.write_text(updated_content)
    print(f"✅ Version updated to {new_version}")
    return True

def create_release_notes(version, previous_version=None):
    """Create release notes for the version"""
    template_file = Path("RELEASE_NOTES_TEMPLATE.md")
    if not template_file.exists():
        print("❌ Release notes template not found")
        return False
    
    template = template_file.read_text()
    
    # Replace placeholders
    release_notes = template.replace("{version}", version)
    if previous_version:
        release_notes = release_notes.replace("{previous_version}", previous_version)
    else:
        release_notes = release_notes.replace("{previous_version}", "previous")
    
    # Save release notes
    release_file = Path(f"RELEASE_NOTES_v{version}.md")
    release_file.write_text(release_notes)
    
    print(f"✅ Release notes created: {release_file}")
    return True

def bump_version(version_type="patch"):
    """Bump version number (major, minor, patch)"""
    current = get_current_version()
    if not current:
        return None
    
    # Remove any pre-release suffixes (like -beta)
    base_version = current.split('-')[0]
    parts = base_version.split('.')
    
    if len(parts) != 3:
        print("❌ Invalid version format. Expected x.y.z")
        return None
    
    major, minor, patch = map(int, parts)
    
    if version_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif version_type == "minor":
        minor += 1
        patch = 0
    elif version_type == "patch":
        patch += 1
    else:
        print("❌ Invalid version type. Use: major, minor, patch")
        return None
    
    new_version = f"{major}.{minor}.{patch}"
    return new_version

def prepare_release(version_type="patch"):
    """Prepare a new release"""
    print(f"🚀 Preparing {version_type} release...")
    
    current_version = get_current_version()
    if not current_version:
        return False
    
    new_version = bump_version(version_type)
    if not new_version:
        return False
    
    print(f"📝 Current version: {current_version}")
    print(f"📝 New version: {new_version}")
    
    # Confirm with user
    response = input(f"Continue with release v{new_version}? (y/N): ")
    if response.lower() != 'y':
        print("❌ Release cancelled")
        return False
    
    # Update version
    if not update_version(new_version):
        return False
    
    # Create release notes
    if not create_release_notes(new_version, current_version):
        return False
    
    print(f"\n🎉 Release v{new_version} prepared!")
    print("Next steps:")
    print("1. Review and edit the release notes")
    print("2. Commit the version changes")
    print("3. Create a git tag: git tag v" + new_version)
    print("4. Push to GitHub: git push origin v" + new_version)
    print("5. GitHub Actions will automatically build and create the release")
    
    return True

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python version_manager.py [patch|minor|major|current]")
        print("  patch  - Increment patch version (1.0.0 -> 1.0.1)")
        print("  minor  - Increment minor version (1.0.0 -> 1.1.0)")
        print("  major  - Increment major version (1.0.0 -> 2.0.0)")
        print("  current - Show current version")
        return
    
    command = sys.argv[1]
    
    if command == "current":
        version = get_current_version()
        if version:
            print(f"Current version: {version}")
        else:
            print("❌ Could not determine current version")
    elif command in ["patch", "minor", "major"]:
        prepare_release(command)
    else:
        print("❌ Unknown command. Use: patch, minor, major, or current")

if __name__ == "__main__":
    main()
