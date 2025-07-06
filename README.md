# TidyCore v2.0.0

<div align="center">

**A smart, modern, and configurable file organization utility that automatically tidies up your folders.**

![TidyCore Dashboard Screenshot](https://raw.githubusercontent.com/hei1sme/TidyCore/main/assets/dashboard.png)
_The TidyCore Dashboard: At-a-glance monitoring of all file operations._

[![Release](https://img.shields.io/github/release/hei1sme/TidyCore.svg)](https://github.com/hei1sme/TidyCore/releases)
[![License](https://img.shields.io/github/license/hei1sme/TidyCore.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/hei1sme/TidyCore/releases)

</div>

---

TidyCore is a desktop application designed to bring order to your most cluttered folders, like "Downloads." It runs silently in the background, watching for new files and automatically moving them into categorized subdirectories based on a powerful and fully customizable set of rules.

Built with a modern user interface and a robust backend engine, TidyCore is the "set it and forget it" solution for maintaining a clean digital workspace.

## 🎉 What's New in v2.0.0

### 🏗️ **Professional Project Structure**
- **Modern Python Package Layout**: Reorganized with `src/` structure following industry best practices
- **Better Developer Experience**: Clear separation of source code, configuration, documentation, and scripts
- **Enhanced Maintainability**: Professional folder organization for easier contribution and development

### 💾 **Persistent Statistics Database**
- **SQLite Integration**: All statistics now persist between application restarts
- **Historical Data**: Track your file organization history over time
- **Performance Optimized**: Fast database queries for real-time dashboard updates

### 🔄 **Intelligent Auto-Update System**
- **Background Checking**: Silent update checks with non-intrusive notifications
- **One-Click Updates**: Download and install updates with progress tracking
- **Smart Versioning**: Automatic version comparison and update notifications
- **Manual Control**: Option to check for updates manually from system tray

### 🎨 **Enhanced Modern UI**
- **Dark Theme Excellence**: Professional dark theme with gradient backgrounds
- **Improved Performance**: Better memory management and smoother animations
- **Enhanced Accessibility**: Better contrast and readable typography
- **Responsive Design**: Adapts beautifully to different window sizes

## ✨ Core Features

- **Automatic & Real-time Organization:** Runs as a background utility, watching a target folder for new or modified files and organizing them instantly.
- **Intelligent & Safe:** Implements a cooldown period to safely handle large files and in-progress downloads (`.crdownload`, `.tmp`) without moving corrupted data.
- **Smart Folder Categorization:** Can intelligently scan inside new folders to determine their dominant content type and sort them accordingly.
- **Powerful Rules Engine:** Comes with sensible defaults but gives you full control to edit, add, and create complex nested rules via an intuitive graphical editor.
- **Modern Dashboard:** A sleek, real-time dashboard to monitor activity, view statistics, and see a live breakdown of organized files in a donut chart.
- **User-Trust Features:** The "Recent Folder Decisions" panel shows you exactly which folders were moved and allows you to **Undo** the action or **Ignore** the folder in the future with a single click.
- **System Tray Integration:** Hides to the system tray for unobtrusive background operation. A right-click menu provides quick access to the dashboard and exit controls.
- **Startup on Boot:** Can be configured to launch automatically when you log in to your computer.

## 🚀 Getting Started

### Quick Installation (Recommended)

TidyCore is a portable application - no complex installation required!

1. **Download the latest release:** Go to the [**TidyCore Releases Page**](https://github.com/hei1sme/TidyCore/releases) on GitHub.
2. Download the `TidyCore-v2.0.0-Windows.zip` file from the latest release.
3. **Extract the archive:** Right-click the downloaded `.zip` file and select "Extract All..." to a location of your choice (e.g., your Desktop or `C:\Program Files`).
4. **Run the application:** Open the extracted `TidyCore` folder and double-click `TidyCore.exe`.

That's it! TidyCore will start, and its icon will appear in your system tray.

### Development Installation

For developers who want to run from source or contribute:

```bash
# Clone the repository
git clone https://github.com/hei1sme/TidyCore.git
cd TidyCore

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### First-Time Setup

On first launch, TidyCore will automatically detect your user's **Downloads** folder and begin watching it. You can change the target folder and all other settings by opening the dashboard from the system tray icon and navigating to the **Settings** page.

> **Note:** On Windows, you may see a "Windows protected your PC" SmartScreen prompt. This is because the application is not code-signed. Click **"More info"** and then **"Run anyway"** to proceed.

## 🖼️ Screenshots

<div align="center">

**The fully-featured Settings page, giving you granular control over all rules.**
![TidyCore Settings Screenshot](https://raw.githubusercontent.com/hei1sme/TidyCore/main/assets/settings.png)

</div>

## 🛠️ Built With

TidyCore was built with a modern Python stack:

### Backend Technologies

- **[Python 3.8+](https://www.python.org/)** - Core programming language
- **[Watchdog](https://github.com/gorakhargosh/watchdog)** - File system event monitoring
- **[SQLite](https://sqlite.org/)** - Embedded database for statistics
- **[Requests](https://requests.readthedocs.io/)** - HTTP client for auto-updates

### Frontend (GUI)

- **[PySide6 (Qt for Python)](https://www.qt.io/qt-for-python)** - Modern, cross-platform user interface
- **[QTAwesome](https://github.com/spyder-ide/qtawesome)** - High-quality vector icons
- **[PyQtGraph](https://www.pyqtgraph.org/)** - Beautiful, real-time charts and visualizations

### Build & Distribution

- **[PyInstaller](https://www.pyinstaller.org/)** - Standalone executable bundling
- **[GitHub Actions](https://github.com/features/actions)** - Automated CI/CD pipeline
- **Professional Project Structure** - Modern `src/` layout following Python best practices

## 📊 Project Structure

```text
TidyCore/
├── src/tidycore/          # Source code package
├── config/                # Configuration files
├── scripts/               # Build and utility scripts
├── docs/                  # Documentation
├── assets/                # Screenshots and media
└── .github/workflows/     # CI/CD automation
```

For detailed information about the project structure, see [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md).

## 📈 Performance & Statistics

- **Lightweight**: Small memory footprint (~50MB RAM usage)
- **Fast**: Real-time file processing with configurable cooldown
- **Reliable**: Comprehensive error handling and logging
- **Persistent**: SQLite database preserves statistics across restarts
- **Scalable**: Handles large directories efficiently

## 🔧 Configuration

TidyCore is highly configurable with support for:

- **Custom File Rules**: Define your own categorization rules
- **Flexible Folder Handling**: Smart scan, move to others, or ignore
- **Cooldown Periods**: Adjustable wait times for file processing
- **Ignore Lists**: Exclude specific files or extensions
- **Update Settings**: Control automatic update behavior

## 🚀 Advanced Features

### Auto-Update System

- **Silent Background Checks**: Non-intrusive update notifications
- **One-Click Installation**: Download and install updates seamlessly
- **Manual Control**: Check for updates on demand from system tray
- **Version Intelligence**: Smart comparison and compatibility checking

### Database Integration

- **Persistent Statistics**: Track file organization history
- **Performance Metrics**: Monitor processing speed and efficiency
- **Historical Analysis**: View trends over time
- **Data Integrity**: Automatic backup and recovery

### Professional Architecture

- **Modular Design**: Clean separation of concerns
- **Plugin Ready**: Extensible architecture for future enhancements
- **Cross-Platform**: Windows, Linux, and macOS support
- **Developer Friendly**: Well-documented code and clear structure

## 👤 About the Creator

This project was developed by **Le Nguyen Gia Hung (hei)**.

I am a second-year AI Major at FPT University and the founder of [SpeedyLabX](https://github.com/SpeedyLabX), a student-led research group. I am passionate about building practical, data-driven solutions to real-world challenges.

**Connect with me:**

[![Email](https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:heiontheway@gmail.com)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/le-nguyen-gia-hung)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/hei1sme)

## 📖 Documentation

- **[Installation Guide](docs/INSTALLATION.md)** - Detailed installation instructions
- **[Project Structure](docs/PROJECT_STRUCTURE.md)** - Understanding the codebase
- **[Development Guide](docs/DEVELOPMENT_SUMMARY.md)** - For contributors
- **[Changelog](docs/CHANGELOG.md)** - Version history and updates

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 🐛 Support

- **Issues**: [GitHub Issues](https://github.com/hei1sme/TidyCore/issues)
- **Discussions**: [GitHub Discussions](https://github.com/hei1sme/TidyCore/discussions)
- **Email**: [heiontheway@gmail.com](mailto:heiontheway@gmail.com)

## ⭐ Show Your Support

If you find TidyCore helpful, please consider giving it a star on GitHub! It helps others discover the project and motivates continued development.

[![GitHub stars](https://img.shields.io/github/stars/hei1sme/TidyCore.svg?style=social&label=Star)](https://github.com/hei1sme/TidyCore)

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Made with ❤️ for a cleaner digital workspace**

</div>