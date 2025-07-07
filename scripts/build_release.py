# build_release.py
"""
Script to build TidyCore release executable using PyInstaller.
"""
import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None

def get_version():
    """Get the current version from the package."""
    # Add src to path to import tidycore
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
    try:
        from tidycore import __version__
        return __version__
    except ImportError:
        print("Warning: Could not import version from tidycore. Using default version.")
        return "1.0.0"

def clean_build_directories():
    """Clean previous build directories."""
    # Change to parent directory to work with the project root
    os.chdir(Path(__file__).parent.parent)
    
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            print(f"Cleaning {dir_name} directory...")
            try:
                # Force remove any readonly files first
                for root, dirs, files in os.walk(dir_name):
                    for file in files:
                        file_path = Path(root) / file
                        try:
                            file_path.chmod(0o777)  # Make writable
                        except:
                            pass
                shutil.rmtree(dir_name)
            except PermissionError as e:
                print(f"Warning: Could not clean {dir_name}: {e}")
                print("This may cause issues with the build. Close any running instances and try again.")

def clean_release_directory(release_dir):
    """Clean a specific release directory with proper permission handling."""
    if not release_dir.exists():
        return True
        
    print(f"Cleaning existing release directory: {release_dir}")
    try:
        # Force remove any readonly files
        for root, dirs, files in os.walk(release_dir):
            for file in files:
                file_path = Path(root) / file
                try:
                    file_path.chmod(0o777)  # Make writable
                except:
                    pass
        
        # Try to remove the directory
        shutil.rmtree(release_dir)
        return True
        
    except PermissionError as e:
        print(f"Warning: Could not clean release directory: {e}")
        print("Attempting to kill any processes that might be using the files...")
        
        # Try to kill any TidyCore processes that might be locking files
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name']):
                if 'TidyCore' in proc.info['name']:
                    print(f"Terminating process: {proc.info['name']} (PID: {proc.info['pid']})")
                    proc.terminate()
                    proc.wait(timeout=5)
        except ImportError:
            print("psutil not available - cannot automatically terminate processes")
        except Exception as term_e:
            print(f"Warning: Could not terminate processes: {term_e}")
        
        # Try again after killing processes
        try:
            shutil.rmtree(release_dir)
            return True
        except PermissionError:
            print("Please close any running TidyCore instances and try again.")
            return False

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
        '--hidden-import=unicodedata',  # Fix for requests/idna module
        '--hidden-import=_codecs',      # Core codec support
        '--hidden-import=_locale',      # Locale support for unicode
        '--hidden-import=_string',      # String operations
        '--hidden-import=idna',
        '--hidden-import=idna.core',    # Specific idna.core import
        '--hidden-import=idna.idnadata', # Additional idna data
        '--hidden-import=idna.uts46data', # Additional UTS46 data
        '--hidden-import=encodings',    # Encoding support
        '--hidden-import=encodings.utf_8', # UTF-8 encoding
        '--hidden-import=encodings.ascii', # ASCII encoding
        '--hidden-import=encodings.latin_1', # Latin-1 encoding
        '--hidden-import=encodings.cp1252', # Windows encoding
        '--hidden-import=encodings.utf_16', # UTF-16 encoding
        '--hidden-import=encodings.utf_32', # UTF-32 encoding
        '--hidden-import=encodings.idna', # IDNA encoding
        '--hidden-import=charset_normalizer',
        '--hidden-import=urllib3',
        '--hidden-import=certifi',
        '--hidden-import=ssl',          # SSL support
        '--hidden-import=_ssl',         # Internal SSL module
        '--hidden-import=_socket',      # Socket support
        '--hidden-import=socket',       # Socket module
        '--hidden-import=select',       # Select module for sockets
        '--hidden-import=OpenSSL',      # OpenSSL support (if available)
        '--hidden-import=cryptography', # Cryptography support
        '--hidden-import=hashlib',      # Hash functions
        '--hidden-import=hmac',         # HMAC support
        '--hidden-import=zipfile',
        '--hidden-import=tempfile',
        '--hidden-import=shutil',
        '--hidden-import=threading',    # For update manager
        '--hidden-import=json',         # For config handling
        '--hidden-import=pathlib',      # Path operations
        '--hidden-import=webbrowser',   # For opening URLs
        '--hidden-import=datetime',     # For date formatting
        '--hidden-import=subprocess',   # For process management
        '--hidden-import=platform',     # For system detection
        '--hidden-import=locale',       # Locale support
        '--hidden-import=codecs',       # Codec support
        '--hidden-import=functools',    # Functools for requests
        '--hidden-import=email',        # Email support for urllib3
        '--hidden-import=email.message', # Email message support
        '--hidden-import=email.mime',   # Email MIME support
        '--hidden-import=email.mime.text', # Email MIME text support
        '--hidden-import=typing_extensions', # Typing extensions
        '--hidden-import=base64',       # Base64 encoding for certificates
        '--hidden-import=binascii',     # Binary/ASCII conversions
        '--hidden-import=_hashlib',     # Internal hashlib module
        '--hidden-import=_random',      # Random number generation for SSL
        '--collect-all=encodings',      # Collect all encodings
        '--collect-all=idna',          # Collect all idna modules
        '--collect-all=certifi',       # Collect all certifi modules
        '--collect-data=encodings',     # Collect encoding data files
        '--collect-data=certifi',       # Collect SSL certificates - CRITICAL for HTTPS
        '--collect-data=idna',         # Collect IDNA data files
        '--collect-submodules=ssl',     # Collect all SSL submodules
        '--collect-submodules=certifi', # Collect all certifi submodules
        '--collect-submodules=requests', # Collect all requests submodules
        '--collect-submodules=urllib3',  # Collect all urllib3 submodules
        '--collect-submodules=charset_normalizer', # Collect charset_normalizer
        '--collect-submodules=idna',   # Collect all IDNA submodules
        '--collect-submodules=unicodedata', # Collect all unicodedata submodules
        # Additional PyInstaller options to fix Unicode and SSL issues
        '--copy-metadata=certifi',     # Copy certifi metadata
        '--copy-metadata=requests',    # Copy requests metadata
        '--copy-metadata=urllib3',     # Copy urllib3 metadata
        '--copy-metadata=idna',        # Copy idna metadata
        '--copy-metadata=charset-normalizer', # Copy charset-normalizer metadata
        # Additional hooks directory for custom hooks
        '--additional-hooks-dir=scripts',    # Look for additional hooks in scripts dir
        # Bundle Python standard library explicitly for problematic modules
        '--collect-submodules=unicodedata', # Explicitly bundle unicodedata
        # Force inclusion of critical low-level modules
        '--hidden-import=_ctypes',     # Required for many extensions
        '--hidden-import=ctypes',      # Higher level ctypes interface
        '--hidden-import=ctypes.util', # Utility functions for ctypes
        '--hidden-import=_decimal',    # Decimal module C extension
        '--hidden-import=decimal',     # Decimal arithmetic
        '--hidden-import=array',       # Array module
        '--hidden-import=math',        # Math functions
        '--hidden-import=_struct',     # Struct packing/unpacking
        '--hidden-import=struct',      # Struct module
        '--noupx',                     # Don't use UPX compression (can cause issues)
        '--debug=imports',             # Debug import issues
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
    
    # Get current version
    version = get_version()
    
    # Create versioned release directory (clean it first if it exists)
    release_dir = Path(f'release/TidyCore-v{version}')
    if not clean_release_directory(release_dir):
        return False
        return False
    
    release_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy executable
    try:
        shutil.copy2('dist/TidyCore.exe', release_dir)
    except PermissionError as e:
        print(f"❌ Permission error copying executable: {e}")
        print("Please ensure no TidyCore instances are running and try again.")
        return False
    
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
    
    # Create ZIP file with proper naming for auto-update compatibility
    zip_name = f'TidyCore-v{version}-Windows.zip'
    zip_path = Path('release') / zip_name
    
    print(f"Creating ZIP package: {zip_name}")
    
    # Create a temporary structure for the ZIP that's flat for easier extraction
    temp_zip_dir = Path('release') / 'temp_for_zip'
    temp_zip_dir.mkdir(exist_ok=True)
    
    # Copy files to temp directory with flat structure
    shutil.copy2(release_dir / 'TidyCore.exe', temp_zip_dir)
    for file in files_to_include:
        if (release_dir / file).exists():
            shutil.copy2(release_dir / file, temp_zip_dir)
    
    # Copy config directory to temp
    if (release_dir / 'config').exists():
        shutil.copytree(release_dir / 'config', temp_zip_dir / 'config', dirs_exist_ok=True)
    
    # Create ZIP from temp directory
    shutil.make_archive(
        str(zip_path.with_suffix('')),  # Remove .zip as make_archive adds it
        'zip',
        str(temp_zip_dir),  # Use temp_zip_dir as the root, not its parent
        '.'     # Archive everything in the temp directory as root
    )
    
    # Clean up temp directory
    shutil.rmtree(temp_zip_dir)
    
    print(f"✅ Release package created in {release_dir}")
    print(f"✅ ZIP package created: {zip_path}")
    return True

def main():
    """Main build process."""
    print("🚀 Starting TidyCore release build...")
    
    # Get version
    version = get_version()
    print(f"📦 Building TidyCore v{version}")
    
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
    print(f"📦 Release package is ready in the 'release/TidyCore-v{version}' directory")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
