# build.py - Build script for TidyCore executable
import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build_directory():
    """Clean previous build artifacts."""
    build_dir = Path("build")
    dist_dir = Path("dist")
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print("✅ Cleaned build directory")
    
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print("✅ Cleaned dist directory")

def build_executable():
    """Build the executable using PyInstaller."""
    print("🔨 Building TidyCore executable...")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--name=TidyCore",
        "--onedir",  # Create one directory with all dependencies
        "--windowed",  # No console window on Windows
        "--icon=icon.png",
        "--add-data=icon.png;.",
        "--add-data=assets;assets",
        "--add-data=config.json;.",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui", 
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=qtawesome",
        "--hidden-import=packaging",
        "--hidden-import=requests",
        "--hidden-import=watchdog",
        "main.py"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ Executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False

def create_release_package():
    """Create a release package with all necessary files."""
    print("📦 Creating release package...")
    
    dist_app_dir = Path("dist/TidyCore")
    if not dist_app_dir.exists():
        print("❌ Build directory not found. Run build first.")
        return False
    
    # Create release directory
    release_dir = Path("release")
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir()
    
    # Copy the built application
    shutil.copytree(dist_app_dir, release_dir / "TidyCore")
    
    # Copy additional files
    additional_files = ["README.md", "LICENSE", "requirements.txt"]
    for file in additional_files:
        if Path(file).exists():
            shutil.copy2(file, release_dir / "TidyCore")
    
    # Create a startup script for easy launching
    startup_script = release_dir / "TidyCore" / "Start_TidyCore.bat"
    startup_script.write_text("""@echo off
echo Starting TidyCore...
TidyCore.exe
pause
""")
    
    print("✅ Release package created in 'release/TidyCore' directory")
    return True

def create_zip_distribution():
    """Create a ZIP file for distribution."""
    print("🗜️ Creating ZIP distribution...")
    
    release_dir = Path("release/TidyCore")
    if not release_dir.exists():
        print("❌ Release directory not found. Create package first.")
        return False
    
    # Get version from __init__.py
    try:
        import tidycore
        version = tidycore.__version__
    except:
        version = "1.0.0"
    
    zip_name = f"TidyCore-v{version}-Windows"
    
    # Create ZIP file
    shutil.make_archive(f"release/{zip_name}", 'zip', "release", "TidyCore")
    
    print(f"✅ Distribution ZIP created: release/{zip_name}.zip")
    return True

def main():
    """Main build process."""
    print("🚀 TidyCore Build Process")
    print("=" * 40)
    
    # Check if PyInstaller is installed
    try:
        subprocess.run(["pyinstaller", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Build process
    clean_build_directory()
    
    if build_executable():
        if create_release_package():
            create_zip_distribution()
            print("\n🎉 Build process completed successfully!")
            print("📁 Release files are in the 'release' directory")
        else:
            print("\n❌ Failed to create release package")
    else:
        print("\n❌ Build process failed")

if __name__ == "__main__":
    main()
