# TidyCore Project Structure

## Overview

This document describes the organized folder structure of the TidyCore project, designed for professional GitHub presentation while maintaining all functionality.

## Directory Structure

```text
TidyCore/
├── 📁 .github/               # GitHub Actions workflows
│   └── workflows/
│       └── release.yml       # Automated release pipeline
├── 📁 src/                   # Source code
│   └── tidycore/             # Main application package
│       ├── __init__.py       # Package initialization and version
│       ├── gui.py            # Main GUI components and dashboard
│       ├── engine.py         # File organization engine
│       ├── config_manager.py # Configuration management
│       ├── database.py       # Statistics database (SQLite)
│       ├── updater.py        # Auto-update functionality
│       ├── update_manager.py # Additional update logic
│       ├── update_dialog.py  # Update notification UI
│       ├── settings_page.py  # Settings configuration interface
│       ├── about_page.py     # About page with version info
│       ├── pie_chart_widget.py # Statistics visualization
│       ├── folder_decision_widget.py # Undo/Ignore functionality
│       ├── signals.py        # Qt signal definitions
│       ├── logger.py         # Logging configuration
│       ├── utils.py          # Utility functions
│       └── startup_manager.py # Startup configuration
├── 📁 config/               # Configuration files
│   └── config.json          # Default application configuration
├── 📁 scripts/              # Build and utility scripts
│   ├── build_release.py     # Release build script
│   └── manage_version.py    # Version management utility
├── 📁 docs/                 # Documentation
│   ├── CHANGELOG.md         # Version history
│   ├── INSTALLATION.md      # Installation guide
│   ├── DEPLOYMENT.md        # Deployment instructions
│   ├── DEVELOPMENT_SUMMARY.md # Development summary
│   ├── RELEASE_NOTES_TEMPLATE.md # Release notes template
│   ├── RELEASE_WORKFLOW.md  # Release process
│   └── PROJECT_STRUCTURE.md # This file
├── 📁 assets/               # Static assets (for documentation)
│   ├── dashboard.png        # Dashboard screenshot
│   └── settings.png         # Settings screenshot
├── 📁 build/                # Build artifacts (gitignored)
├── 📁 dist/                 # Distribution files (gitignored)
├── 📁 release/              # Release packages (gitignored)
├── 📄 main.py               # Application entry point
├── 📄 requirements.txt      # Python dependencies
├── 📄 README.md             # Project overview and usage
├── 📄 LICENSE               # MIT License
├── 📄 .gitignore            # Git ignore rules
├── 📄 icon.png              # Application icon
├── 📄 tidycore.log          # Application logs (gitignored)
├── 📄 tidycore_stats.db     # Statistics database (gitignored)
└── 📄 TidyCore.spec         # PyInstaller specification
```

## Directory Descriptions

### `/src/` - Source Code

Contains all application source code following Python packaging best practices:

- **tidycore/**: Main application package with all modules
- Organized by functionality (GUI, engine, database, etc.)
- Uses relative imports for clean module structure

### `/config/` - Configuration

Stores configuration files that can be modified by users:

- **config.json**: Default application settings and file organization rules
- Separated from source code for easy access and modification

### `/scripts/` - Build & Utility Scripts

Development and deployment scripts:

- **build_release.py**: Automated release building with PyInstaller
- **manage_version.py**: Version management and tagging utility

### `/docs/` - Documentation

All documentation files organized for easy access:

- Installation guides, deployment instructions, and development notes
- Release templates and workflow documentation
- Keeps the root directory clean

### `/assets/` - Static Assets

Images and resources used in documentation:

- Screenshots for README and documentation
- Not included in the final executable (documentation only)

### `/.github/` - GitHub Configuration

GitHub-specific configuration:

- **workflows/**: CI/CD automation for releases
- Issue templates and other GitHub features

## Key Benefits

### 1. **Professional Appearance**

- Clean, organized structure following industry standards
- Easy navigation for contributors and users
- Clear separation of concerns

### 2. **Maintainability**

- Source code isolated in `/src/` directory
- Configuration separate from code
- Documentation centralized in `/docs/`

### 3. **Build Process**

- Updated build script handles new structure automatically
- PyInstaller configuration adjusted for new paths
- Release process unchanged for end users

### 4. **Development Workflow**

- Follows Python packaging conventions
- Easy to set up development environment
- Clear import structure with relative imports

## Import Structure

### Main Entry Point

```python
# main.py
from src.tidycore.gui import TidyCoreGUI
from src.tidycore.engine import TidyCoreEngine
from src.tidycore.config_manager import load_config
```

### Internal Module Imports

```python
# Within tidycore package
from .signals import signals
from .database import statistics_db
from .config_manager import ConfigManager
```

## Build Process Updates

The build script (`scripts/build_release.py`) has been updated to:

1. Work from the project root directory
2. Include the config directory in the build
3. Use the correct source paths for PyInstaller
4. Maintain all functionality while using the new structure

## Backward Compatibility

- All functionality preserved
- End-user experience unchanged
- Configuration files automatically located
- Release packages contain all necessary files

This structure provides better organization, maintainability, and professional presentation while ensuring all existing functionality continues to work seamlessly.

- Clear separation of concerns
- Better maintainability
- Professional GitHub appearance
- Easy navigation for contributors
- Standard Python package layout
