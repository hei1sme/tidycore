# tidycore/updater.py
# Import required modules with error handling for PyInstaller compatibility

# Early logging to debug import issues
import logging
logger = logging.getLogger("TidyCore")
logger.info("Starting updater.py module import...")

import json
import subprocess
import sys
import os
import tempfile
import zipfile
import threading
import shutil
import time
import traceback
import platform
import webbrowser
from pathlib import Path
from typing import Optional, Dict, Any

logger.info("Basic imports completed successfully")

# Handle PyInstaller build issues with external dependencies
logger.info("Attempting to import requests...")
try:
    import requests
    REQUESTS_AVAILABLE = True
    logger.info("requests imported successfully")
except ImportError as e:
    logger.warning(f"Failed to import requests: {e}. Update functionality will be limited.")
    REQUESTS_AVAILABLE = False
    # Create a dummy requests module to prevent crashes
    class DummyRequests:
        class RequestException(Exception):
            pass
        def get(self, *args, **kwargs):
            raise self.RequestException("requests module not available")
        def head(self, *args, **kwargs):
            raise self.RequestException("requests module not available")
    requests = DummyRequests()

logger.info("Attempting to import packaging...")
try:
    from packaging import version
    PACKAGING_AVAILABLE = True
    logger.info("packaging imported successfully")
except ImportError as e:
    logger.warning(f"Failed to import packaging: {e}. Version comparison will be disabled.")
    PACKAGING_AVAILABLE = False
    # Create a dummy version module
    class DummyVersion:
        def parse(self, version_string):
            # Simple string comparison fallback
            return version_string
    version = DummyVersion()

logger.info("Attempting to import PySide6...")
try:
    from PySide6.QtCore import QObject, Signal, QThread, QTimer, Qt
    from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton
    PYSIDE_AVAILABLE = True
    logger.info("PySide6 imported successfully")
except ImportError as e:
    logger.error(f"Failed to import PySide6: {e}. GUI components will not work.")
    PYSIDE_AVAILABLE = False
    # This is a critical error - we can't continue without Qt
    raise ImportError("PySide6 is required but not available")

logger.info("Attempting to import local modules...")
try:
    from . import __version__
    from .utils import get_absolute_path
    logger.info("Local modules imported successfully")
except ImportError as e:
    logger.warning(f"Failed to import local modules: {e}")
    __version__ = "unknown"
    def get_absolute_path(path):
        return os.path.abspath(path)

logger.info("All imports completed")

class UpdateDownloadThread(QThread):
    """Thread for downloading updates without blocking the UI."""
    
    progress_updated = Signal(int)
    download_complete = Signal(str)  # file path
    download_error = Signal(str)     # error message
    
    def __init__(self, download_url: str, logger):
        super().__init__()
        self.download_url = download_url
        self.logger = logger
    
    def run(self):
        """Download the update file."""
        try:
            if not REQUESTS_AVAILABLE:
                self.download_error.emit("requests module not available")
                return
            
            self.logger.info(f"Starting download from: {self.download_url}")
            
            if not self.download_url:
                raise ValueError("Download URL is empty")
            
            # Create temp directory
            temp_dir = tempfile.mkdtemp(prefix="tidycore_update_")
            self.logger.info(f"Created temp directory: {temp_dir}")
            
            # Download the update
            self.logger.info("Making HTTP request...")
            response = requests.get(self.download_url, stream=True, timeout=30)
            response.raise_for_status()
            self.logger.info(f"HTTP response received: {response.status_code}")
            
            # Determine file extension
            if self.download_url.endswith('.exe'):
                update_file = Path(temp_dir) / "TidyCore_update.exe"
            else:
                update_file = Path(temp_dir) / "update.zip"
            
            self.logger.info(f"Saving to: {update_file}")
            
            # Get total size for progress tracking
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            self.logger.info(f"File size: {total_size} bytes")
            
            # Save downloaded file with progress updates
            with open(update_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Update progress
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            self.progress_updated.emit(int(progress))
                            
                            # Log progress occasionally
                            if downloaded % (1024 * 1024) == 0:  # Every MB
                                self.logger.info(f"Downloaded: {downloaded} / {total_size} bytes ({progress:.1f}%)")
            
            self.logger.info(f"Download completed: {update_file}")
            self.download_complete.emit(str(update_file))
            
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            self.download_error.emit(str(e))

class UpdateChecker(QThread):
    """Background thread to check for updates."""
    
    update_available = Signal(dict)  # Emits update info if available
    no_update = Signal()
    error_occurred = Signal(str)
    
    def __init__(self, repo_owner: str = "hei1sme", repo_name: str = "TidyCore"):
        super().__init__()
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        self.logger = logging.getLogger("TidyCore")
    
    def run(self):
        """Check for updates in background thread."""
        try:
            if not REQUESTS_AVAILABLE:
                self.error_occurred.emit("requests module not available")
                return
                
            self.logger.info("Checking for updates...")
            
            # Make request to GitHub API
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            
            release_info = response.json()
            latest_version = release_info.get("tag_name", "").lstrip("v")
            
            if not latest_version:
                self.error_occurred.emit("Invalid release information")
                return
            
            current_version = __version__
            
            # Compare versions
            if PACKAGING_AVAILABLE:
                if version.parse(latest_version) > version.parse(current_version):
                    update_info = {
                        "version": latest_version,
                        "download_url": self._get_download_url(release_info),
                        "release_notes": release_info.get("body", "No release notes available"),
                        "published_at": release_info.get("published_at", ""),
                        "assets": release_info.get("assets", [])
                    }
                    self.update_available.emit(update_info)
                else:
                    self.no_update.emit()
            else:
                # Simple string comparison fallback
                if latest_version != current_version:
                    update_info = {
                        "version": latest_version,
                        "download_url": self._get_download_url(release_info),
                        "release_notes": release_info.get("body", "No release notes available"),
                        "published_at": release_info.get("published_at", ""),
                        "assets": release_info.get("assets", [])
                    }
                    self.update_available.emit(update_info)
                else:
                    self.no_update.emit()
                
        except requests.RequestException as e:
            self.error_occurred.emit(f"Network error: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"Update check failed: {str(e)}")
    
    def _get_download_url(self, release_info: Dict[str, Any]) -> Optional[str]:
        """Extract the appropriate download URL for the current platform."""
        assets = release_info.get("assets", [])
        
        # Log available assets for debugging
        self.logger.info(f"Available assets: {[asset.get('name', 'Unknown') for asset in assets]}")
        
        if not assets:
            self.logger.warning("No assets found in release")
            return None
        
        # Determine platform-specific filename pattern
        import platform
        system = platform.system().lower()
        
        if system == "windows":
            # More comprehensive patterns for Windows
            patterns = ["windows", "win", ".exe", ".zip"]
        elif system == "darwin":
            patterns = ["macos", "mac", "darwin"]
        else:
            patterns = ["linux"]
        
        # First priority: Look for platform-specific executable or zip
        for asset in assets:
            name = asset.get("name", "").lower()
            # Check for Windows-specific naming patterns
            if system == "windows":
                if any(pattern in name for pattern in ["windows", "win"]) and (".exe" in name or ".zip" in name):
                    download_url = asset.get("browser_download_url")
                    self.logger.info(f"Found platform-specific asset: {asset.get('name')} -> {download_url}")
                    return download_url
        
        # Second priority: Look for any zip or exe file
        for asset in assets:
            name = asset.get("name", "").lower()
            if ".zip" in name or ".exe" in name:
                download_url = asset.get("browser_download_url")
                self.logger.info(f"Found executable/zip asset: {asset.get('name')} -> {download_url}")
                return download_url
        
        # Third priority: Look for any binary asset (not source code)
        for asset in assets:
            name = asset.get("name", "").lower()
            if not any(src in name for src in ["source", "src", "tar.gz", ".tar"]):
                download_url = asset.get("browser_download_url")
                self.logger.info(f"Found binary asset: {asset.get('name')} -> {download_url}")
                return download_url
        
        # Fourth priority: Fallback to first asset if available
        if assets:
            download_url = assets[0].get("browser_download_url")
            self.logger.info(f"Using first available asset: {assets[0].get('name')} -> {download_url}")
            return download_url
        
        # Last resort: source code (this will show a user-friendly message)
        self.logger.info("No suitable assets found, falling back to source code")
        return release_info.get("zipball_url")

class UpdateManager(QObject):
    """Manages the update checking and installation process."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger("TidyCore")
        self.checker = UpdateChecker()
        self.current_update_info = None
        
        # Connect signals
        self.checker.update_available.connect(self._on_update_available)
        self.checker.no_update.connect(self._on_no_update)
        self.checker.error_occurred.connect(self._on_error)
    
    def check_for_updates(self, silent: bool = False):
        """Check for updates. If silent=True, only show notification if update is available."""
        self.silent_check = silent
        if not self.checker.isRunning():
            self.checker.start()
    
    def _on_update_available(self, update_info: Dict[str, Any]):
        """Handle when an update is available."""
        self.current_update_info = update_info
        self.logger.info(f"Update available: v{update_info['version']}")
        
        # Check if we have a valid download URL
        download_url = update_info.get('download_url')
        if not download_url:
            self.logger.error("No download URL available for update")
            if not getattr(self, 'silent_check', False):
                self._show_no_download_dialog(update_info)
            return
        
        # Show update dialog
        self._show_update_dialog(update_info)
    
    def _on_no_update(self):
        """Handle when no update is available."""
        self.logger.info("No updates available")
        if not getattr(self, 'silent_check', False):
            msg = QMessageBox()
            msg.setWindowTitle("TidyCore Update")
            msg.setText("You are running the latest version of TidyCore!")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.exec()
    
    def _on_error(self, error_message: str):
        """Handle update check errors."""
        self.logger.error(f"Update check error: {error_message}")
        if not getattr(self, 'silent_check', False):
            msg = QMessageBox()
            msg.setWindowTitle("Update Check Failed")
            msg.setText(f"Failed to check for updates:\\n{error_message}")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.exec()
    
    def _show_update_dialog(self, update_info: Dict[str, Any]):
        """Show the update available dialog."""
        # Use the beautiful UpdateDialog instead of simple QMessageBox
        try:
            from .update_dialog import UpdateDialog
            
            # Transform update_info to match UpdateDialog's expected format
            dialog_info = {
                "version": update_info['version'],
                "changelog": update_info['release_notes'],
                "published_at": update_info['published_at'],
                "size": self._get_asset_size_from_url(update_info.get('download_url', '')),
                "download_url": update_info.get('download_url')  # Include download URL
            }
            
            # Log for debugging
            self.logger.info(f"Creating UpdateDialog with info: {dialog_info}")
            
            dialog = UpdateDialog(dialog_info)
            
            # Store reference to dialog for progress updates
            self.current_dialog = dialog
            
            dialog.download_requested.connect(self._handle_download_request)
            dialog.exec()
            
        except ImportError:
            # Fallback to simple dialog if UpdateDialog is not available
            self._show_simple_update_dialog(update_info)
    
    def _show_simple_update_dialog(self, update_info: Dict[str, Any]):
        """Show simple update dialog as fallback."""
        msg = QMessageBox()
        msg.setWindowTitle("TidyCore Update Available")
        msg.setText(f"A new version of TidyCore is available!\\n\\n"
                   f"Current version: v{__version__}\\n"
                   f"Latest version: v{update_info['version']}")
        
        # Set detailed text with release notes
        if update_info['release_notes']:
            msg.setDetailedText(f"Release Notes:\\n{update_info['release_notes']}")
        
        msg.setIcon(QMessageBox.Icon.Information)
        
        # Add custom buttons
        update_button = msg.addButton("Update Now", QMessageBox.ButtonRole.AcceptRole)
        later_button = msg.addButton("Later", QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        
        if msg.clickedButton() == update_button:
            self._start_update_process()
    
    def _show_no_download_dialog(self, update_info: Dict[str, Any]):
        """Show dialog when no download URL is available."""
        msg = QMessageBox()
        msg.setWindowTitle("Update Available - Manual Download Required")
        msg.setText(f"A new version of TidyCore is available!\\n\\n"
                   f"Current version: v{__version__}\\n"
                   f"Latest version: v{update_info['version']}\\n\\n"
                   f"Automatic download is not available for this release.\\n"
                   f"Please download the update manually from GitHub.")
        
        # Set detailed text with release notes
        if update_info.get('release_notes'):
            msg.setDetailedText(f"Release Notes:\\n{update_info['release_notes']}")
        
        msg.setIcon(QMessageBox.Icon.Information)
        
        # Add custom buttons
        open_button = msg.addButton("Open GitHub Releases", QMessageBox.ButtonRole.AcceptRole)
        later_button = msg.addButton("Later", QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        
        if msg.clickedButton() == open_button:
            import webbrowser
            webbrowser.open("https://github.com/hei1sme/TidyCore/releases")

    def _get_asset_size_from_url(self, download_url: str) -> str:
        """Get asset size from download URL."""
        if not download_url or not REQUESTS_AVAILABLE:
            return "Unknown"
        
        try:
            # Make a HEAD request to get content length
            response = requests.head(download_url, timeout=5)
            if response.status_code == 200:
                size_bytes = int(response.headers.get('content-length', 0))
                return self._format_bytes(size_bytes)
        except:
            pass
        
        return "Unknown"
    
    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} TB"
    
    def _start_update_process(self):
        """Start the update process."""
        if not self.current_update_info:
            return
        
        download_url = self.current_update_info.get('download_url')
        if not download_url:
            QMessageBox.warning(None, "Update Error", "No download URL available for this update.")
            return
        
        # Use the threaded download approach instead of blocking download
        self.logger.info(f"Starting update process with URL: {download_url}")
        self._handle_download_request(download_url)
    
    def _handle_download_request(self, download_url: str):
        """Handle download request from UpdateDialog."""
        # Start download in a separate thread to avoid blocking the UI
        self.logger.info(f"Starting download from: {download_url}")
        
        # Create and start download thread
        self.download_thread = UpdateDownloadThread(download_url, self.logger)
        self.download_thread.progress_updated.connect(self._on_download_progress)
        self.download_thread.download_complete.connect(self._on_download_complete)
        self.download_thread.download_error.connect(self._on_download_error)
        
        # Connect progress updates to the dialog if it exists
        if hasattr(self, 'current_dialog') and self.current_dialog:
            self.download_thread.progress_updated.connect(self.current_dialog.update_progress)
            self.logger.info("Connected download progress to dialog")
        
        self.download_thread.start()
    
    def _on_download_progress(self, progress: int):
        """Handle download progress updates."""
        self.logger.info(f"Download progress: {progress}%")
    
    def _on_download_complete(self, file_path: str):
        """Handle successful download completion."""
        self.logger.info(f"Download completed: {file_path}")
        
        try:
            # Install the downloaded file
            if file_path.endswith('.exe'):
                self.logger.info("Installing executable update...")
                self._install_executable(Path(file_path))
            else:
                self.logger.info("Installing ZIP update...")
                self._install_from_zip(Path(file_path))
            
            self.logger.info("Installation completed successfully, showing restart dialog...")
            
            # Show restart dialog on main thread
            QTimer.singleShot(100, self._show_restart_dialog)
            
        except Exception as e:
            self.logger.error(f"Installation failed: {e}")
            import traceback
            self.logger.error(f"Installation traceback: {traceback.format_exc()}")
            QTimer.singleShot(100, lambda: self._show_error_dialog(f"Installation failed: {e}"))
    
    def _on_download_error(self, error_message: str):
        """Handle download errors."""
        self.logger.error(f"Download failed: {error_message}")
        QTimer.singleShot(100, lambda: self._show_error_dialog(f"Download failed: {error_message}"))
    
    def _install_executable(self, exe_file: Path):
        """Install an executable file."""
        current_exe = Path(sys.executable)
        backup_exe = current_exe.with_suffix('.exe.backup')
        
        # Create backup of current exe
        if current_exe.exists():
            if backup_exe.exists():
                backup_exe.unlink()
            current_exe.rename(backup_exe)
        
        # Move new exe into place
        shutil.move(str(exe_file), str(current_exe))
        self.logger.info("Executable update installed successfully")
    
    
    def _install_from_zip(self, zip_file: Path):
        """Install update from ZIP file."""
        try:
            self.logger.info(f"Installing update from ZIP: {zip_file}")
            
            # Create temporary extraction directory
            extract_dir = zip_file.parent / "extracted"
            extract_dir.mkdir(exist_ok=True)
            
            # Extract the ZIP file
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Find the executable file
            exe_files = list(extract_dir.rglob("*.exe"))
            if not exe_files:
                raise Exception("No executable found in update package")
            
            # Use the first executable found
            new_exe = exe_files[0]
            self.logger.info(f"Found executable: {new_exe}")
            
            # Install the executable
            self._install_executable(new_exe)
            
            # Clean up extraction directory
            shutil.rmtree(extract_dir, ignore_errors=True)
            
        except Exception as e:
            self.logger.error(f"Failed to install from ZIP: {e}")
            raise
    
    def _show_error_dialog(self, error_message: str):
        """Show error dialog."""
        msg = QMessageBox()
        msg.setWindowTitle("Update Error")
        msg.setText(f"An error occurred during the update process:\n\n{error_message}")
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.addButton("OK", QMessageBox.ButtonRole.AcceptRole)
        msg.exec()
    
    def _show_restart_dialog(self):
        """Show restart dialog."""
        self.logger.info("Showing restart dialog...")
        
        restart_msg = QMessageBox()
        restart_msg.setWindowTitle("Update Complete")
        
        restart_msg.setText("TidyCore has been updated successfully!\n\n"
                          "The application needs to restart to use the new version.\n"
                          "Click 'Restart Now' to close this instance and automatically restart.")
        
        restart_msg.setIcon(QMessageBox.Icon.Information)
        
        # Make sure the dialog is on top and visible
        restart_msg.setWindowFlags(restart_msg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        restart_button = restart_msg.addButton("Restart Now", QMessageBox.ButtonRole.AcceptRole)
        later_button = restart_msg.addButton("Restart Later", QMessageBox.ButtonRole.RejectRole)
        
        # Add a manual restart button for troubleshooting
        if hasattr(self, 'updated_exe_path') and self.updated_exe_path:
            manual_button = restart_msg.addButton("Show Installation Path", QMessageBox.ButtonRole.HelpRole)
        
        # Log the dialog creation
        self.logger.info("Restart dialog created with buttons: Restart Now, Restart Later")
        
        # Execute the dialog
        result = restart_msg.exec()
        
        self.logger.info(f"Restart dialog result: {result}")
        self.logger.info(f"Clicked button: {restart_msg.clickedButton().text() if restart_msg.clickedButton() else 'None'}")
        
        clicked_button = restart_msg.clickedButton()
        if clicked_button == restart_button:
            self.logger.info("User clicked 'Restart Now'")
            self._restart_application()
        elif hasattr(self, 'updated_exe_path') and clicked_button.text() == "Show Installation Path":
            self.logger.info("User clicked 'Show Installation Path'")
            self._show_installation_info()
        else:
            self.logger.info("User clicked 'Restart Later' or closed dialog")
    
    def _show_installation_info(self):
        """Show information about where the update was installed."""
        info_msg = QMessageBox()
        info_msg.setWindowTitle("Update Installation Info")
        
        if hasattr(self, 'updated_exe_path') and self.updated_exe_path:
            info_text = f"The updated TidyCore executable has been installed at:\n\n{self.updated_exe_path}\n\n"
            info_text += f"Working directory: {os.path.dirname(self.updated_exe_path)}\n\n"
            info_text += "You can manually start this executable if the automatic restart fails.\n\n"
            info_text += "If you encounter DLL errors, try:\n"
            info_text += "1. Running the Python version instead (python main.py)\n"
            info_text += "2. Installing Visual C++ Redistributables\n"
            info_text += "3. Checking if antivirus is blocking the executable"
        else:
            info_text = "No new executable was installed. The update was applied to the current installation."
        
        info_msg.setText(info_text)
        info_msg.setIcon(QMessageBox.Icon.Information)
        info_msg.addButton("OK", QMessageBox.ButtonRole.AcceptRole)
        info_msg.exec()

    def _restart_application(self):
        """Restart the application with 3-second delay."""
        try:
            self.logger.info("Starting application restart process...")
            self.logger.info(f"sys.frozen: {getattr(sys, 'frozen', False)}")
            self.logger.info(f"sys.executable: {sys.executable}")
            self.logger.info(f"sys.argv: {sys.argv}")
            self.logger.info(f"Current working directory: {os.getcwd()}")
            
            if getattr(sys, 'frozen', False):
                # Running as PyInstaller executable
                exe_path = sys.executable
                working_dir = os.path.dirname(exe_path)
                
                self.logger.info(f"Will restart executable: {exe_path}")
                self.logger.info(f"Working directory: {working_dir}")
                
                # Verify the executable exists
                if not os.path.exists(exe_path):
                    self.logger.error(f"Executable not found: {exe_path}")
                    
                    # Try to find TidyCore.exe in common locations
                    possible_paths = [
                        os.path.join(os.getcwd(), "TidyCore.exe"),
                        os.path.join(os.getcwd(), "release", "TidyCore-v1.0.0", "TidyCore.exe"),
                        os.path.join(os.getcwd(), "dist", "TidyCore.exe"),
                    ]
                    
                    for path in possible_paths:
                        if os.path.exists(path):
                            self.logger.info(f"Found alternative executable: {path}")
                            exe_path = path
                            working_dir = os.path.dirname(path)
                            break
                    else:
                        raise FileNotFoundError(f"Executable not found in any expected location: {possible_paths}")
                
                # Create a batch script for delayed restart
                self._create_delayed_restart_script(exe_path, working_dir)
                    
            else:
                # Running as Python script - check if we installed a new executable
                if hasattr(self, 'updated_exe_path') and os.path.exists(self.updated_exe_path):
                    # We have a new executable to run - this is for end users
                    exe_path = self.updated_exe_path
                    working_dir = os.path.dirname(exe_path)
                    
                    self.logger.info(f"Will restart new executable: {exe_path}")
                    self.logger.info(f"Working directory: {working_dir}")
                    
                    # Create restart script for new executable
                    self._create_delayed_restart_script(exe_path, working_dir)
                else:
                    # No new executable - this is a developer scenario
                    # Check if this looks like a development environment
                    if os.path.exists(os.path.join(os.getcwd(), "src")) and os.path.exists(os.path.join(os.getcwd(), "main.py")):
                        # Looks like development environment - restart as Python script
                        script_dir = os.getcwd()
                        main_py = os.path.join(script_dir, "main.py")
                        
                        self.logger.info(f"Development environment detected - will restart Python script: {main_py}")
                        self.logger.info(f"Script directory: {script_dir}")
                        
                        # Create restart script for Python
                        self._create_delayed_restart_script(sys.executable, script_dir, [sys.executable, main_py])
                    else:
                        # This shouldn't happen for regular users - show error
                        raise Exception("No executable update available and this doesn't appear to be a development environment. "
                                      "Please download TidyCore manually from the official website.")
            
            # Show countdown dialog
            self._show_restart_countdown_dialog()
            
            # Exit immediately after starting the delayed restart
            QTimer.singleShot(1000, self._force_exit)
            
        except Exception as e:
            self.logger.error(f"Failed to restart application: {e}")
            self.logger.error(f"Restart traceback: {traceback.format_exc()}")
            
            # Show error message with manual restart instructions
            restart_instructions = "Please close this application and manually start TidyCore again."
            if getattr(sys, 'frozen', False):
                restart_instructions += f"\nYou can find the executable at:\n{sys.executable}"
            else:
                restart_instructions += f"\nRun 'python main.py' from:\n{os.getcwd()}"
            
            QMessageBox.critical(None, "Restart Failed", 
                               f"Failed to restart TidyCore automatically.\n\n"
                               f"Error: {e}\n\n"
                               f"{restart_instructions}")
    
    def _create_delayed_restart_script(self, exe_path, working_dir, args=None):
        """Create a batch/shell script for delayed restart."""
        try:
            if sys.platform == 'win32':
                # Create Windows batch script
                script_path = os.path.join(tempfile.gettempdir(), "tidycore_restart.bat")
                
                # For PyInstaller executables, always use the exe path directly
                if getattr(sys, 'frozen', False):
                    # We're running as a PyInstaller executable
                    command = f'"{exe_path}"'
                    process_name = os.path.basename(exe_path)
                else:
                    # We're running as a Python script
                    if args is None:
                        command = f'"{exe_path}"'
                        process_name = os.path.basename(exe_path)
                    else:
                        command = f'"{args[0]}" ' + ' '.join(f'"{arg}"' for arg in args[1:])
                        process_name = os.path.basename(args[0])
                
                self.logger.info(f"Restart command: {command}")
                self.logger.info(f"Process name to monitor: {process_name}")
                
                script_content = f'''@echo off
echo TidyCore is updating and will restart in a moment...
echo Waiting for TidyCore to close...

REM Wait for the current TidyCore process to close
:wait_loop
tasklist /FI "IMAGENAME eq {process_name}" 2>NUL | find /I /N "{process_name}">NUL
if "%ERRORLEVEL%"=="0" (
    timeout /t 1 /nobreak >nul
    goto wait_loop
)

echo TidyCore process closed. Waiting 2 more seconds before restart...
timeout /t 2 /nobreak >nul

echo Starting updated TidyCore...
cd /d "{working_dir}"
start "" {command}

echo Cleaning up restart script...
del "%~f0"
'''
                
                with open(script_path, 'w') as f:
                    f.write(script_content)
                
                self.logger.info(f"Created restart script: {script_path}")
                
                # Execute the batch script
                subprocess.Popen([script_path], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
                self.logger.info("Restart script started")
                
            else:
                # Create shell script for Unix-like systems
                script_path = os.path.join(tempfile.gettempdir(), "tidycore_restart.sh")
                
                if args is None:
                    command = f'"{exe_path}"'
                else:
                    command = f'"{args[0]}" ' + ' '.join(f'"{arg}"' for arg in args[1:])
                
                # Get the process name to wait for it to close
                process_name = os.path.basename(exe_path)
                
                script_content = f'''#!/bin/bash
echo "TidyCore is updating and will restart in a moment..."
echo "Waiting for TidyCore to close..."

# Wait for the current TidyCore process to close
while pgrep -f "{process_name}" > /dev/null; do
    sleep 1
done

echo "TidyCore process closed. Waiting 2 more seconds before restart..."
sleep 2

echo "Starting updated TidyCore..."
cd "{working_dir}"
{command} &

echo "Cleaning up restart script..."
rm "$0"
'''
                
                with open(script_path, 'w') as f:
                    f.write(script_content)
                
                # Make script executable
                os.chmod(script_path, 0o755)
                
                self.logger.info(f"Created restart script: {script_path}")
                
                # Execute the shell script
                subprocess.Popen(['/bin/bash', script_path])
                self.logger.info("Restart script started")
                
        except Exception as e:
            self.logger.error(f"Failed to create restart script: {e}")
            raise
    
    def _show_restart_countdown_dialog(self):
        """Show a countdown dialog before restart."""
        msg = QMessageBox()
        msg.setWindowTitle("Restarting TidyCore")
        msg.setText("TidyCore has been updated successfully!\n\n"
                   "The application will close now and the updated version will start automatically.\n"
                   "A restart script is monitoring for the application to close completely.\n"
                   "Please wait...")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.NoButton)  # No buttons
        msg.setWindowFlags(msg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        self.logger.info("Showing restart countdown dialog")
        
        # Show the dialog briefly (it will auto-close when app exits)
        QTimer.singleShot(100, lambda: msg.show())
        QTimer.singleShot(200, lambda: msg.raise_())
        QTimer.singleShot(300, lambda: msg.activateWindow())

    def _force_exit(self):
        """Force exit the application after scheduling delayed restart."""
        try:
            self.logger.info("Forcing application exit...")
            
            # Get the QApplication instance
            app = QApplication.instance()
            if app:
                self.logger.info("Setting quit on last window closed to True")
                app.setQuitOnLastWindowClosed(True)
                
                # Close all windows
                self.logger.info("Closing all top level widgets")
                for widget in app.topLevelWidgets():
                    widget.close()
                
                # Force application quit
                self.logger.info("Calling QApplication.quit()")
                app.quit()
                
                # Give a moment for the quit signal to process
                QTimer.singleShot(500, lambda: self._hard_exit())
            else:
                self.logger.warning("No QApplication instance found, using sys.exit()")
                sys.exit(0)
                
        except Exception as e:
            self.logger.error(f"Error during force exit: {e}")
            # Last resort - hard exit
            self._hard_exit()
    
    def _hard_exit(self):
        """Perform a hard exit as last resort."""
        try:
            self.logger.info("Performing hard exit...")
            os._exit(0)
        except:
            # If even os._exit fails, there's nothing more we can do
            pass
    
    # ...existing code...
    
    def test_download_functionality(self):
        """Test the download functionality with a small test file."""
        self.logger.info("Testing download functionality...")
        
        # Use a small test file from a reliable source
        test_url = "https://httpbin.org/json"  # Small JSON response
        
        try:
            # Create and start download thread
            self.download_thread = UpdateDownloadThread(test_url, self.logger)
            self.download_thread.progress_updated.connect(
                lambda p: self.logger.info(f"Test download progress: {p}%")
            )
            self.download_thread.download_complete.connect(
                lambda f: self.logger.info(f"Test download completed: {f}")
            )
            self.download_thread.download_error.connect(
                lambda e: self.logger.error(f"Test download failed: {e}")
            )
            
            self.download_thread.start()
            self.logger.info("Test download started...")
            
        except Exception as e:
            self.logger.error(f"Failed to start test download: {e}")
    
    def test_restart_dialog(self):
        """Test the restart dialog functionality."""
        self.logger.info("Testing restart dialog...")
        try:
            self._show_restart_dialog()
        except Exception as e:
            self.logger.error(f"Failed to show restart dialog: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Test functionality methods removed as requested
    # Users can test restart functionality by performing an actual update

    # ...existing code...

# Global instance with robust error handling
update_manager = None

def get_update_manager():
    """Get the update manager instance, creating it if necessary."""
    global update_manager
    if update_manager is None:
        try:
            logger = logging.getLogger("TidyCore")
            logger.info("Creating UpdateManager instance...")
            update_manager = UpdateManager()
            logger.info("UpdateManager instance created successfully")
        except Exception as e:
            logger = logging.getLogger("TidyCore")
            logger.error(f"Failed to create update_manager instance: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            logger.error(f"Update functionality will be disabled")
            # Create a dummy object to prevent attribute errors
            class DummyUpdateManager:
                def __getattr__(self, name):
                    def dummy_method(*args, **kwargs):
                        logger.warning(f"UpdateManager method '{name}' called but UpdateManager is disabled")
                        pass
                    return dummy_method
            update_manager = DummyUpdateManager()
    return update_manager

# Try to create the instance immediately
try:
    logger = logging.getLogger("TidyCore")
    logger.info("Attempting to create UpdateManager during module import...")
    if PYSIDE_AVAILABLE:
        update_manager = UpdateManager()
        logger.info("UpdateManager created successfully during import")
    else:
        logger.warning("PySide6 not available, UpdateManager will be disabled")
        # Create dummy manager
        class DummyUpdateManager:
            def __getattr__(self, name):
                def dummy_method(*args, **kwargs):
                    pass
                return dummy_method
        update_manager = DummyUpdateManager()
except Exception as e:
    logger = logging.getLogger("TidyCore")
    logger.error(f"Failed to create update_manager instance during import: {e}")
    logger.error(f"Import traceback: {traceback.format_exc()}")
    # Set to None - will be created on first access via get_update_manager()
    update_manager = None

# Ensure the UpdateManager class exists even if there are import issues
if not PYSIDE_AVAILABLE:
    # Create a dummy UpdateManager if PySide6 is not available
    class UpdateManager:
        def __init__(self, parent=None):
            pass
        def __getattr__(self, name):
            def dummy_method(*args, **kwargs):
                pass
            return dummy_method
