# Changelog

All notable changes to TidyCore will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2025-07-07

### Added
- 🏗️ **Professional Project Structure**: Complete reorganization following modern Python standards
  - Modern `src/` package layout with proper separation of concerns
  - Centralized documentation in `docs/` directory
  - Organized configuration files in `config/` directory
  - Build and utility scripts in `scripts/` directory
- 💾 **Persistent Statistics Database**: SQLite integration for persistent data storage
  - Historical file organization tracking
  - Performance metrics and analytics
  - Category breakdown and trend analysis
  - Automatic backup and recovery mechanisms
- 🔄 **Intelligent Auto-Update System**: Advanced update management
  - Silent background update checking
  - Modern notification dialogs with release notes
  - One-click download and installation
  - Manual update check from system tray
- 📖 **Comprehensive Documentation**: Professional documentation suite
  - Detailed project structure guide
  - Enhanced installation instructions
  - Developer contribution guidelines
  - Complete API documentation
- 🎨 **Enhanced UI Performance**: Improved visual design and responsiveness
  - Better memory management and resource usage
  - Smoother animations and transitions
  - Enhanced accessibility and readability
  - Optimized rendering performance

### Changed
- 🔧 **Import Structure**: Updated to use modern Python import patterns
  - Main entry point imports from `src.tidycore`
  - Internal modules use relative imports
  - Clean separation between packages
- 📦 **Build System**: Enhanced build process for new structure
  - Updated PyInstaller configuration
  - Modified GitHub Actions workflow
  - Improved release packaging
  - Better error handling in build scripts
- ⚙️ **Configuration Management**: Centralized configuration handling
  - Config files moved to dedicated directory
  - Enhanced validation and error reporting
  - Backward compatibility maintained
  - Automatic migration for existing setups
- 📊 **Statistics System**: Upgraded from in-memory to persistent storage
  - SQLite database replaces temporary counters
  - Historical data preservation
  - Performance optimized queries
  - Enhanced data integrity

### Technical
- **Architecture**: Modern Python package structure with `src/` layout
- **Database**: SQLite integration for persistent statistics
- **Updates**: GitHub API integration with intelligent version management
- **Build**: Enhanced PyInstaller configuration for new structure
- **Documentation**: Comprehensive project documentation and guides
- **Performance**: Optimized memory usage and rendering efficiency
- **Compatibility**: Seamless upgrade path from v1.x.x

### Migration Notes
- All existing configurations automatically detected and preserved
- Statistics data enhanced with persistent storage
- No user action required for upgrade
- Release packages maintain identical functionality

## [1.0.0] - 2025-07-06

### Added
- 🎨 **Modern Dark Theme UI**: Complete redesign with gradient backgrounds, card-style layouts, and modern color scheme
- 📊 **Enhanced Dashboard**: Large, color-coded statistics display with real-time updates
- 🎯 **Interactive Sidebar Navigation**: Active page indicators and modern button styling
- 📈 **Real-time Activity Feed**: Color-coded messages with timestamps and clear button
- 🥧 **Improved Pie Chart**: Interactive legend with progress bars and hover effects
- 💾 **Database Integration**: SQLite database for persistent statistics tracking
- 🔄 **Auto-Update System**: Background update checking with modern notification dialogs
- 🖥️ **System Tray Integration**: Right-click menu with update check option
- 🚀 **Enhanced Performance**: Better memory management and file processing
- 🔧 **Robust Error Handling**: Comprehensive logging and error recovery

### Changed
- 🎨 Updated all UI components with modern styling and improved spacing
- 📊 Statistics now persist between application restarts
- 🔄 Update notifications are now non-intrusive and user-friendly
- 🖼️ Window layout optimized for better content organization

### Fixed
- 🐛 Improved file processing stability and conflict resolution
- 🔧 Better handling of network errors in update system
- 📏 Fixed window sizing and layout responsiveness
- 🔄 Enhanced cooldown system for file processing

### Technical
- Built with PySide6 (Qt 6) for modern UI framework
- SQLite database integration for statistics
- GitHub API integration for automatic updates
- PyInstaller for standalone executable builds
- Comprehensive error handling and logging system

## [0.9.0] - Previous Version
### Added
- Basic file organization functionality
- Simple GUI interface
- Configuration management
- File watching capabilities

---

## Release Notes Format

Each release follows this structure:
- **Added**: New features
- **Changed**: Changes in existing functionality  
- **Deprecated**: Soon-to-be removed features
- **Removed**: Now removed features
- **Fixed**: Bug fixes
- **Security**: Vulnerability fixes
