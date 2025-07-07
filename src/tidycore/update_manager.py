# tidycore/update_manager.py
import requests
import logging
import json
import threading
import zipfile
import tempfile
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Callable
from packaging import version
from .utils import get_absolute_path

class UpdateManager:
    """Handles checking for updates and auto-updating the application."""
    
    def __init__(self, current_version: str = "1.0.0"):
        self.current_version = current_version
        self.logger = logging.getLogger("TidyCore.UpdateManager")
        self.github_api_url = "https://api.github.com/repos/hei1sme/TidyCore/releases/latest"
        self.update_callback: Optional[Callable] = None
        self.auto_check_enabled = True
        
    def set_update_callback(self, callback: Callable):
        """Set callback function to notify GUI of update status."""
        self.update_callback = callback
    
    def check_for_updates_async(self):
        """Check for updates in a background thread."""
        if not self.auto_check_enabled:
            return
            
        thread = threading.Thread(target=self._check_for_updates, daemon=True)
        thread.start()
    
    def _check_for_updates(self):
        """Internal method to check for updates."""
        try:
            self.logger.info("Checking for updates...")
            
            # GitHub API request with timeout
            response = requests.get(self.github_api_url, timeout=10)
            response.raise_for_status()
            
            release_data = response.json()
            latest_version = release_data["tag_name"].lstrip("v")
            
            if version.parse(latest_version) > version.parse(self.current_version):
                update_info = {
                    "available": True,
                    "version": latest_version,
                    "url": release_data["html_url"],
                    "download_url": self._get_download_url(release_data),
                    "changelog": release_data.get("body", "No changelog available"),
                    "published_at": release_data.get("published_at", ""),
                    "size": self._get_asset_size(release_data)
                }
                
                self.logger.info(f"Update available: v{latest_version}")
                if self.update_callback:
                    self.update_callback(update_info)
            else:
                self.logger.info("Application is up to date")
                if self.update_callback:
                    self.update_callback({"available": False})
                    
        except requests.RequestException as e:
            self.logger.warning(f"Failed to check for updates: {e}")
            if self.update_callback:
                self.update_callback({"error": str(e)})
        except Exception as e:
            self.logger.error(f"Update check error: {e}")
            if self.update_callback:
                self.update_callback({"error": str(e)})
    
    def _get_download_url(self, release_data: Dict) -> Optional[str]:
        """Get the appropriate download URL for the current platform."""
        assets = release_data.get("assets", [])
        
        # Log available assets for debugging
        self.logger.info(f"Available assets: {[asset.get('name', 'Unknown') for asset in assets]}")
        
        # Determine platform-specific filename
        import platform
        system = platform.system().lower()
        
        if system == "windows":
            # More comprehensive patterns for Windows
            patterns = ["windows", "win"]
        elif system == "darwin":
            patterns = ["macos", "mac", "darwin"]
        else:
            patterns = ["linux"]
        
        # First priority: Look for platform-specific executable
        for asset in assets:
            name = asset.get("name", "").lower()
            for pattern in patterns:
                if pattern in name and (".exe" in name or ".zip" in name):
                    self.logger.info(f"Found platform-specific asset: {asset.get('name')}")
                    return asset.get("browser_download_url")
        
        # Second priority: Look for any zip or exe file
        for asset in assets:
            name = asset.get("name", "").lower()
            if ".zip" in name or ".exe" in name:
                self.logger.info(f"Found executable/zip asset: {asset.get('name')}")
                return asset.get("browser_download_url")
        
        # Third priority: Look for any binary asset (not source code)
        for asset in assets:
            name = asset.get("name", "").lower()
            if not any(src in name for src in ["source", "src", "tar.gz", ".tar"]):
                self.logger.info(f"Found binary asset: {asset.get('name')}")
                return asset.get("browser_download_url")
        
        # Fallback to first asset
        if assets:
            self.logger.info(f"Using first available asset: {assets[0].get('name')}")
            return assets[0].get("browser_download_url")
        
        self.logger.info("No assets found")
        return None
    
    def _get_asset_size(self, release_data: Dict) -> str:
        """Get the size of the main asset."""
        assets = release_data.get("assets", [])
        if assets:
            size_bytes = assets[0].get("size", 0)
            return self._format_bytes(size_bytes)
        return "Unknown"
    
    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} TB"
    
    def download_and_install_update(self, download_url: str, progress_callback: Optional[Callable] = None):
        """Download and install the update."""
        thread = threading.Thread(
            target=self._download_and_install,
            args=(download_url, progress_callback),
            daemon=True
        )
        thread.start()
    
    def _download_and_install(self, download_url: str, progress_callback: Optional[Callable] = None):
        """Internal method to download and install update."""
        try:
            self.logger.info(f"Downloading update from: {download_url}")
            
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                download_path = temp_path / "update.zip"
                
                # Download with progress
                response = requests.get(download_url, stream=True)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(download_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if progress_callback and total_size > 0:
                                progress = (downloaded / total_size) * 100
                                progress_callback(progress)
                
                self.logger.info("Download completed, extracting...")
                
                # Extract update
                extract_path = temp_path / "extracted"
                extract_path.mkdir()
                
                with zipfile.ZipFile(download_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                
                # Find the executable
                exe_files = list(extract_path.rglob("*.exe"))
                if not exe_files:
                    raise Exception("No executable found in update package")
                
                new_exe = exe_files[0]
                current_exe = Path(sys.executable)
                
                # Create update script
                self._create_update_script(new_exe, current_exe)
                
                self.logger.info("Update ready to install. Restart required.")
                if progress_callback:
                    progress_callback(100)
                    
        except Exception as e:
            self.logger.error(f"Update installation failed: {e}")
            if progress_callback:
                progress_callback(-1)  # Error indicator
    
    def _create_update_script(self, new_exe: Path, current_exe: Path):
        """Create a script to replace the current executable."""
        script_content = f"""
@echo off
timeout /t 2 /nobreak > nul
taskkill /f /im "TidyCore.exe" 2>nul
timeout /t 1 /nobreak > nul
copy /y "{new_exe}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
"""
        
        script_path = current_exe.parent / "update_tidycore.bat"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make script executable and run it
        subprocess.Popen([str(script_path)], shell=True)
    
    def enable_auto_check(self, enabled: bool):
        """Enable or disable automatic update checking."""
        self.auto_check_enabled = enabled
        self.logger.info(f"Auto-update check {'enabled' if enabled else 'disabled'}")


# Global update manager instance
update_manager = UpdateManager()
