# TidyCore Installation Guide

## 📦 Quick Installation (Recommended)

### For Windows Users

1. **Download the Latest Release**
   - Go to the [TidyCore Releases Page](https://github.com/hei1sme/TidyCore/releases)
   - Download `TidyCore-v{version}-Windows.zip`

2. **Extract and Run**
   ```
   1. Right-click the downloaded ZIP file
   2. Select "Extract All..."
   3. Choose your installation location (e.g., C:\Program Files\TidyCore)
   4. Open the extracted folder
   5. Double-click TidyCore.exe to start
   ```

3. **First Launch**
   - TidyCore will start and appear in your system tray
   - Right-click the tray icon and select "Show Dashboard"
   - Configure your target folder in Settings

## 🔧 Development Installation

### Prerequisites
- Python 3.8 or higher
- Git (for cloning the repository)

### Step-by-Step Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/hei1sme/TidyCore.git
   cd TidyCore
   ```

2. **Create Virtual Environment (Recommended)**
   ```bash
   python -m venv tidycore_env
   
   # On Windows:
   tidycore_env\Scripts\activate
   
   # On macOS/Linux:
   source tidycore_env/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run TidyCore**
   ```bash
   python main.py
   ```

## 🏗️ Building from Source

### Build Executable

1. **Install PyInstaller**
   ```bash
   pip install pyinstaller
   ```

2. **Run Build Script**
   ```bash
   python build.py
   ```

3. **Find Your Executable**
   - Built executable will be in `release/TidyCore/`
   - ZIP distribution will be in `release/`

### Manual PyInstaller Command
```bash
pyinstaller --name=TidyCore --onedir --windowed --icon=icon.png \
  --add-data="icon.png;." --add-data="assets;assets" \
  --add-data="config.json;." main.py
```

## 🚀 Startup Configuration

### Windows Startup

1. **Using Task Scheduler (Recommended)**
   ```
   1. Press Win + R, type "taskschd.msc"
   2. Click "Create Basic Task"
   3. Name: "TidyCore Startup"
   4. Trigger: "When I log on"
   5. Action: "Start a program"
   6. Program: Path to TidyCore.exe
   7. Check "Run with highest privileges"
   ```

2. **Using Startup Folder**
   ```
   1. Press Win + R, type "shell:startup"
   2. Create a shortcut to TidyCore.exe in this folder
   ```

### macOS Startup

1. **System Preferences Method**
   ```
   1. Open System Preferences
   2. Go to Users & Groups
   3. Select your user account
   4. Click "Login Items" tab
   5. Add TidyCore application
   ```

### Linux Startup

1. **Using Autostart**
   ```bash
   # Create desktop entry
   mkdir -p ~/.config/autostart
   cat > ~/.config/autostart/tidycore.desktop << EOF
   [Desktop Entry]
   Type=Application
   Name=TidyCore
   Exec=/path/to/TidyCore
   Hidden=false
   NoDisplay=false
   X-GNOME-Autostart-enabled=true
   EOF
   ```

## 🔧 Configuration

### Initial Setup

1. **Target Folder**
   - Set the folder you want TidyCore to monitor
   - Default: Downloads folder
   - Recommended: Create a "Drop Zone" folder

2. **File Categories**
   - Review and customize file type rules
   - Add new categories as needed
   - Set up sub-categories for better organization

3. **Folder Handling**
   - Choose how to handle folders:
     - Smart Scan: Analyze folder contents
     - Move to Others: Move all folders to "Others"
     - Ignore: Don't process folders

### Advanced Configuration

1. **Cooldown Period**
   - Adjust the wait time before processing files
   - Useful for large file downloads
   - Default: 5 seconds

2. **Ignore List**
   - Add file names or extensions to ignore
   - System files are automatically ignored
   - Use for temporary files or specific applications

## 🛠️ Troubleshooting

### Common Issues

1. **Application Won't Start**
   ```
   - Check if all dependencies are installed
   - Verify Python version (3.8+)
   - Run from command line to see error messages
   ```

2. **Files Not Being Organized**
   ```
   - Check if TidyCore is running (system tray icon)
   - Verify target folder permissions
   - Check if files match configured rules
   ```

3. **Update Check Fails**
   ```
   - Check internet connection
   - Verify firewall settings
   - Try manual update check from tray menu
   ```

4. **Windows SmartScreen Warning**
   ```
   - This is normal for unsigned executables
   - Click "More info" then "Run anyway"
   - Consider adding TidyCore to Windows Defender exclusions
   ```

### Log Files

- **Location**: `tidycore.log` in the application directory
- **Content**: Detailed application logs and error messages
- **Use**: For debugging and troubleshooting issues

### Getting Help

1. **Documentation**: Check the [README.md](README.md) file
2. **Issues**: Report bugs on [GitHub Issues](https://github.com/hei1sme/TidyCore/issues)
3. **Discussions**: Join the community discussion
4. **Contact**: Email the developer at heiontheway@gmail.com

## 🔄 Updating TidyCore

### Automatic Updates (Recommended)
- TidyCore checks for updates automatically on startup
- Update notifications appear when new versions are available
- Use "Check for Updates" from the system tray menu

### Manual Updates
1. Download the latest release from GitHub
2. Close TidyCore completely
3. Replace the old files with new ones
4. Start TidyCore again
5. Your configuration and data will be preserved

## 🗑️ Uninstalling TidyCore

### Portable Installation
1. Close TidyCore completely
2. Delete the TidyCore folder
3. Remove any shortcuts you created

### Remove User Data (Optional)
- Configuration files are stored in the application folder
- Log files: Delete `tidycore.log`
- Database: Delete `statistics.db` if you don't want to keep statistics

## 📊 Performance Tips

1. **Monitor Moderate Folders**
   - Avoid monitoring very large directories
   - Use subdirectories for better performance

2. **Adjust Cooldown Period**
   - Increase for slow storage devices
   - Decrease for faster SSDs

3. **Regular Maintenance**
   - Clear log files occasionally
   - Review and update ignore lists
   - Clean up processed files periodically
