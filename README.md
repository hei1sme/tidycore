# TidyCore v1.0.0

<div align="center">

**A smart, modern, and configurable file organization utility that automatically tidies up your folders.**

![TidyCore Dashboard Screenshot](https://raw.githubusercontent.com/hei1sme/TidyCore/main/assets/dashboard.png)
_The TidyCore Dashboard: At-a-glance monitoring of all file operations._

</div>

---

TidyCore is a desktop application designed to bring order to your most cluttered folders, like "Downloads." It runs silently in the background, watching for new files and automatically moving them into categorized subdirectories based on a powerful and fully customizable set of rules.

Built with a modern user interface and a robust backend engine, TidyCore is the "set it and forget it" solution for maintaining a clean digital workspace.

## ✨ Features

*   **Automatic & Real-time Organization:** Runs as a background utility, watching a target folder for new or modified files and organizing them instantly.
*   **Intelligent & Safe:** Implements a cooldown period to safely handle large files and in-progress downloads (`.crdownload`, `.tmp`) without moving corrupted data.
*   **Smart Folder Categorization:** Can intelligently scan inside new folders to determine their dominant content type and sort them accordingly.
*   **Powerful Rules Engine:** Comes with sensible defaults but gives you full control to edit, add, and create complex nested rules via an intuitive graphical editor.
*   **Modern Dashboard:** A sleek, real-time dashboard to monitor activity, view statistics, and see a live breakdown of organized files in a donut chart.
*   **User-Trust Features:** The "Recent Folder Decisions" panel shows you exactly which folders were moved and allows you to **Undo** the action or **Ignore** the folder in the future with a single click.
*   **System Tray Integration:** Hides to the system tray for unobtrusive background operation. A right-click menu provides quick access to the dashboard and exit controls.
*   **Startup on Boot:** Can be configured to launch automatically when you log in to your computer.

## 🚀 Getting Started

### Installation

No complex installation required! TidyCore is a portable application.

1.  **Download the latest release:** Go to the [**TidyCore Releases Page**](https://github.com/hei1sme/TidyCore/releases) on GitHub.
2.  Download the `TidyCore-v1.0.0-Windows.zip` file from the latest release.
3.  **Extract the archive:** Right-click the downloaded `.zip` file and select "Extract All..." to a location of your choice (e.g., your Desktop or `C:\Program Files`).
4.  **Run the application:** Open the extracted `TidyCore` folder and double-click `TidyCore.exe`.

That's it! TidyCore will start, and its icon will appear in your system tray.

### First-Time Use

On first launch, TidyCore will automatically detect your user's **Downloads** folder and begin watching it. You can change the target folder and all other settings by opening the dashboard from the system tray icon and navigating to the **Settings** page.

> **Note:** On Windows, you may see a "Windows protected your PC" SmartScreen prompt. This is because the application is not code-signed. Click **"More info"** and then **"Run anyway"** to proceed.

## 🖼️ Screenshots

<div align="center">

**The fully-featured Settings page, giving you granular control over all rules.**
![TidyCore Settings Screenshot](https://raw.githubusercontent.com/hei1sme/TidyCore/main/assets/settings.png)

</div>

## 🛠️ Built With

TidyCore was built with a modern Python stack:

*   **Backend:**
    *   [Python 3](https://www.python.org/)
    *   [Watchdog](https://github.com/gorakhargosh/watchdog) - For monitoring filesystem events.
*   **Frontend (GUI):**
    *   [PySide6 (Qt for Python)](https://www.qt.io/qt-for-python) - For the modern, cross-platform user interface.
    *   [QTAwesome](https://github.com/spyder-ide/qtawesome) - For high-quality icons.
    *   [PyQtGraph](https://www.pyqtgraph.org/) - For rendering beautiful, real-time charts.
*   **Packaging & Distribution:**
    *   [PyInstaller](https://www.pyinstaller.org/) - For bundling the application into a standalone executable.

## 👤 About the Creator

This project was developed by **Le Nguyen Gia Hung (hei)**.

I am a second-year AI Major at FPT University and the founder of [SpeedyLabX](https://github.com/SpeedyLabX), a student-led research group. I am passionate about building practical, data-driven solutions to real-world challenges.

<p align="center">
  <a href="mailto:heiontheway@gmail.com">
    <img src="https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white" alt="Email"/>
  </a>
  <a href="https://linkedin.com/in/le-nguyen-gia-hung" target="_blank">
    <img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn"/>
  </a>
</p>

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.