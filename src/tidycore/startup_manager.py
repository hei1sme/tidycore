# tidycore/startup_manager.py
import sys
import os

if sys.platform == 'win32':
    import winreg

class StartupManager:
    """Manages adding/removing the application from OS startup."""

    def __init__(self, app_name: str, app_path: str):
        """
        Initializes the manager.
        Args:
            app_name: The name for the startup entry (e.g., "TidyCore").
            app_path: The full path to the executable to run on startup.
        """
        self.app_name = app_name
        self.app_path = app_path
        self.is_windows = (sys.platform == 'win32')
        
        if self.is_windows:
            # The registry key for current user startup programs
            self.registry_key = winreg.HKEY_CURRENT_USER
            self.run_key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

    def is_enabled(self) -> bool:
        """Checks if the application is currently set to run on startup."""
        if not self.is_windows:
            return False # Not implemented for other OS yet

        try:
            with winreg.OpenKey(self.registry_key, self.run_key_path, 0, winreg.KEY_READ) as key:
                # Try to read the value. If it exists, it's enabled.
                winreg.QueryValueEx(key, self.app_name)
            return True
        except FileNotFoundError:
            # The key/value doesn't exist, so it's not enabled.
            return False
        except Exception:
            # Handle other potential errors gracefully
            return False

    def enable(self):
        """Adds the application to startup."""
        if not self.is_windows:
            print("Startup management is only implemented for Windows.")
            return

        try:
            with winreg.OpenKey(self.registry_key, self.run_key_path, 0, winreg.KEY_WRITE) as key:
                # Set the value: The name is our app name, the data is the path.
                # The path must be enclosed in quotes if it contains spaces.
                winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, f'"{self.app_path}"')
        except Exception as e:
            print(f"Error enabling startup: {e}")

    def disable(self):
        """Removes the application from startup."""
        if not self.is_windows:
            return

        try:
            with winreg.OpenKey(self.registry_key, self.run_key_path, 0, winreg.KEY_WRITE) as key:
                # Simply delete the value with our app's name.
                winreg.DeleteValue(key, self.app_name)
        except FileNotFoundError:
            # It's already disabled, no need to do anything.
            pass
        except Exception as e:
            print(f"Error disabling startup: {e}")

# --- NEW, SIMPLER LOGIC FOR APPLICATION_PATH ---
def get_application_path():
    """Determines the correct path to execute for startup."""
    if getattr(sys, 'frozen', False):
        # We are running in a bundle (packaged with PyInstaller).
        # The path is simply sys.executable.
        return sys.executable
    else:
        # We are running as a script.
        # The command should be 'path/to/python.exe path/to/main.py'.
        main_script_path = os.path.abspath("main.py")
        return f'"{sys.executable}" "{main_script_path}"'

# Create a single instance to be used by the app
startup_manager = StartupManager(app_name="TidyCore", app_path=get_application_path())