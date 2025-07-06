# build_release.py
"""
Script to build TidyCore release executable using PyInstaller.
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build_directories():
    """Clean previous build directories."""
    # Change to parent directory to work with the project root
    os.chdir(Path(__file__).parent.parent)
    
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            print(f"Cleaning {dir_name} directory...")
            try:
                shutil.rmtree(dir_name)
            except PermissionError as e:
                print(f"Warning: Could not clean {dir_name}: {e}")
                print("This may cause issues with the build. Close any running instances and try again.")

def build_executable():
    """Build the executable using PyInstaller."""
    print("Building TidyCore executable...")
    
    # PyInstaller command with options
    cmd = [
        'pyinstaller',
        '--onefile',                    # Single file executable
        '--windowed',                   # No console window
        '--name=TidyCore',              # Executable name
        '--icon=icon.png',              # Application icon
        '--add-data=icon.png;.',        # Include icon file
        '--add-data=config;config',     # Include config directory
        '--paths=src',                  # Add src to Python path
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtWidgets',
        '--hidden-import=PySide6.QtGui',
        '--hidden-import=qtawesome',
        '--hidden-import=requests',
        '--hidden-import=packaging',
        '--hidden-import=watchdog',
        'main.py'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Build successful!")
        return True
    else:
        print("❌ Build failed!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False

def create_release_package():
    """Create the release package."""
    if not Path('dist/TidyCore.exe').exists():
        print("❌ TidyCore.exe not found in dist/ directory")
        return False
    
    print("Creating release package...")
    
    # Create release directory
    release_dir = Path('release')
    release_dir.mkdir(exist_ok=True)
    
    # Copy executable
    shutil.copy2('dist/TidyCore.exe', release_dir)
    
    # Copy essential files
    files_to_include = [
        'README.md',
        'LICENSE',
        'icon.png'
    ]
    
    for file in files_to_include:
        if Path(file).exists():
            shutil.copy2(file, release_dir)
    
    # Copy config directory
    config_src = Path('config')
    config_dst = release_dir / 'config'
    if config_src.exists():
        shutil.copytree(config_src, config_dst, dirs_exist_ok=True)
    
    print(f"✅ Release package created in {release_dir}")
    return True

def main():
    """Main build process."""
    print("🚀 Starting TidyCore release build...")
    
    # Check if PyInstaller is installed
    try:
        subprocess.run(['pyinstaller', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PyInstaller not found. Please install it with: pip install pyinstaller")
        return 1
    
    # Clean previous builds
    clean_build_directories()
    
    # Build executable
    if not build_executable():
        return 1
    
    # Create release package
    if not create_release_package():
        return 1
    
    print("🎉 Build process completed successfully!")
    print("📦 Release package is ready in the 'release' directory")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
