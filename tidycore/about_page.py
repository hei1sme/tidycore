# tidycore/about_page.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QScrollArea
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl

# Import the version from our new __init__.py
from tidycore import __version__

class AboutPage(QWidget):
    """The 'About' page for the TidyCore application."""
    def __init__(self, parent=None):
        super().__init__(parent)

        # --- Main Layout with Scroll Area ---
        # This ensures the content is scrollable if the window is small
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)
        
        layout = QVBoxLayout(content_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(20)
        
        # --- App Info Section ---
        app_info_box = self._create_app_info_section()
        
        # --- Creator Info Section ---
        creator_info_box = self._create_creator_info_section()

        layout.addWidget(app_info_box)
        layout.addWidget(creator_info_box)

    def _create_app_info_section(self) -> QGroupBox:
        box = QGroupBox("About TidyCore")
        layout = QVBoxLayout(box)

        # App Name and Version
        title_text = f"<h1>TidyCore</h1><h3>Version {__version__}</h3>"
        title_label = QLabel(title_text)
        
        # Description
        description_text = """
        <p>A smart, modern, and configurable file organization utility that automatically
        tidies up your folders. TidyCore runs silently in the background, watching for 
        new files and moving them according to a set of customizable rules.</p>
        """
        description_label = QLabel(description_text)
        description_label.setWordWrap(True)

        # Acknowledgements
        credits_text = """
        <p><b>Built with:</b> Python, PySide6 (Qt for Python), Watchdog, and QTAwesome.<br>
        <b>License:</b> MIT License</p>
        <p>This project is open source. Feel free to contribute!</p>
        """
        credits_label = QLabel(credits_text)
        credits_label.setWordWrap(True)
        # --- Making the GitHub link clickable ---
        # Note: You'll need to replace the URL with your actual TidyCore repo URL
        github_link = "<a href='https://github.com/hei1sme/TidyCore' style='color: #7aa2f7;'>View Project on GitHub</a>"
        github_label = QLabel(github_link)
        github_label.setOpenExternalLinks(True) # Best way to open web links

        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addWidget(credits_label)
        layout.addWidget(github_label)
        
        return box

    def _create_creator_info_section(self) -> QGroupBox:
        box = QGroupBox("About the Creator")
        layout = QVBoxLayout(box)
        
        # Your profile content, formatted with basic HTML
        profile_text = """
        <h2>Le Nguyen Gia Hung (hei)</h2>
        <p><i>A Second-Year AI Major, Researcher, and Founder at FPT University.</i></p>
        <p>Deeply fascinated by the world of Artificial Intelligence, I co-founded 
        <b>SpeedyLabX</b>, a student-led research group dedicated to solving complex 
        problems with AI. As Founder and Lead Researcher, I am currently spearheading our 
        primary research initiative: "Proactive Air Quality Forecasting and Health Alert System for Melbourne,"
        with the goal of submission to the AJCAI 2025 conference.</p>
        """
        profile_label = QLabel(profile_text)
        profile_label.setWordWrap(True) # Important for text to wrap nicely

        # Links Section
        links_text = """
        <p><b>Connect with me:</b><br>
        <a href='https://linkedin.com/in/le-nguyen-gia-hung' style='color: #7aa2f7;'>LinkedIn</a> | 
        <a href='mailto:heiontheway@gmail.com' style='color: #7aa2f7;'>Email</a> |
        <a href='https://github.com/hei1sme' style='color: #7aa2f7;'>GitHub Profile</a>
        </p>
        """
        links_label = QLabel(links_text)
        links_label.setOpenExternalLinks(True)

        layout.addWidget(profile_label)
        layout.addWidget(links_label)

        return box