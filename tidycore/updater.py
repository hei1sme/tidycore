# tidycore/updater.py
import requests
import json
import logging
import subprocess
import sys
import os
import tempfile
import zipfile
from pathlib import Path
from packaging import version
from typing import Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import QMessageBox, QPushButton

from tidycore import __version__
from tidycore.utils import get_absolute_path

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
                
        except requests.RequestException as e:
            self.error_occurred.emit(f"Network error: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"Update check failed: {str(e)}")
    
    def _get_download_url(self, release_info: Dict[str, Any]) -> Optional[str]:
        """Extract the appropriate download URL for the current platform."""
        assets = release_info.get("assets", [])
        
        # Look for Windows executable first
        for asset in assets:
            name = asset.get("name", "").lower()
            if sys.platform == "win32" and (".exe" in name or "windows" in name):
                return asset.get("browser_download_url")
        
        # Fallback to source code
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
    
    def _start_update_process(self):
        """Start the update process."""
        if not self.current_update_info:
            return
        
        download_url = self.current_update_info.get('download_url')
        if not download_url:
            QMessageBox.warning(None, "Update Error", "No download URL available for this update.")
            return
        
        # Show progress dialog and start download
        progress_msg = QMessageBox()
        progress_msg.setWindowTitle("Updating TidyCore")
        progress_msg.setText("Downloading update...\\nThis may take a few minutes.")
        progress_msg.setStandardButtons(QMessageBox.StandardButton.NoButton)
        progress_msg.show()
        
        try:
            self._download_and_install_update(download_url)
            progress_msg.close()
            
            # Show restart dialog
            restart_msg = QMessageBox()
            restart_msg.setWindowTitle("Update Complete")
            restart_msg.setText("Update downloaded successfully!\\n\\n"
                              "TidyCore will now restart to complete the update.")
            restart_msg.setIcon(QMessageBox.Icon.Information)
            restart_button = restart_msg.addButton("Restart Now", QMessageBox.ButtonRole.AcceptRole)
            later_button = restart_msg.addButton("Restart Later", QMessageBox.ButtonRole.RejectRole)
            
            restart_msg.exec()
            
            if restart_msg.clickedButton() == restart_button:
                self._restart_application()
                
        except Exception as e:
            progress_msg.close()
            QMessageBox.critical(None, "Update Failed", f"Failed to update TidyCore:\\n{str(e)}")
    
    def _download_and_install_update(self, download_url: str):
        """Download and install the update."""
        # Create temp directory
        temp_dir = tempfile.mkdtemp(prefix="tidycore_update_")
        
        try:
            # Download the update
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Determine file extension
            if download_url.endswith('.exe'):
                update_file = Path(temp_dir) / "TidyCore_update.exe"
            else:
                update_file = Path(temp_dir) / "update.zip"
            
            # Save downloaded file
            with open(update_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # If it's an executable, move it to replace current exe
            if update_file.suffix == '.exe':
                current_exe = Path(sys.executable)
                backup_exe = current_exe.with_suffix('.exe.backup')
                
                # Create backup of current exe
                if current_exe.exists():
                    current_exe.rename(backup_exe)
                
                # Move new exe into place
                update_file.rename(current_exe)
                
                self.logger.info("Update installed successfully")
            else:
                # Handle zip file update (source code)
                self._install_from_zip(update_file)
                
        finally:
            # Clean up temp directory
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _install_from_zip(self, zip_file: Path):
        """Install update from zip file (for source distributions)."""
        # This is a simplified implementation
        # In practice, you might want more sophisticated handling
        self.logger.info("Zip-based updates not fully implemented yet")
        raise NotImplementedError("Zip-based updates require manual installation")
    
    def _restart_application(self):
        """Restart the application."""
        try:
            if getattr(sys, 'frozen', False):
                # Running as executable
                subprocess.Popen([sys.executable])
            else:
                # Running as script
                subprocess.Popen([sys.executable] + sys.argv)
            
            # Exit current instance
            sys.exit(0)
            
        except Exception as e:
            self.logger.error(f"Failed to restart application: {e}")
            QMessageBox.critical(None, "Restart Failed", 
                               f"Failed to restart automatically.\\n"
                               f"Please restart TidyCore manually.\\n\\nError: {e}")

# Global instance
update_manager = UpdateManager()
