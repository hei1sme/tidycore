# Deployment Guide for TidyCore

## 🚀 Creating a New Release

### Step 1: Prepare the Release

1. **Update version number:**
   ```bash
   python scripts/manage_version.py patch  # For bug fixes
   python scripts/manage_version.py minor  # For new features
   python scripts/manage_version.py major  # For breaking changes
   ```

2. **Test the application:**
   ```bash
   python main.py
   # Test all features thoroughly
   ```

3. **Update documentation:**
   - Update `README.md` if needed
   - Update `CHANGELOG.md` (create if doesn't exist)
   - Review `RELEASE_NOTES_TEMPLATE.md`

### Step 2: Build and Test Executable

1. **Build the executable:**
   ```bash
   python scripts/build_release.py
   ```

2. **Test the built executable:**
   ```bash
   cd release
   ./TidyCore.exe
   # Test all functionality
   ```

### Step 3: Commit and Tag

1. **Commit changes:**
   ```bash
   git add .
   git commit -m "Release v1.0.0: Add database integration and update system"
   ```

2. **Create and push tag:**
   ```bash
   git tag v1.0.0
   git push origin main
   git push origin v1.0.0
   ```

### Step 4: GitHub Release (Automatic)

The GitHub Actions workflow will automatically:
- Build the Windows executable
- Create release notes from template
- Upload the release package
- Publish the GitHub release

### Step 5: Manual Release (if needed)

If automatic release fails:

1. **Go to GitHub releases page:**
   - Navigate to `https://github.com/hei1sme/TidyCore/releases`
   - Click "Create a new release"

2. **Fill in release details:**
   - Tag version: `v1.0.0`
   - Release title: `TidyCore v1.0.0`
   - Description: Copy from `RELEASE_NOTES_TEMPLATE.md`

3. **Upload assets:**
   - Upload `TidyCore-v1.0.0-Windows.zip`
   - Include any additional files

## 📦 Distribution Checklist

### Before Release
- [ ] All tests pass
- [ ] Version number updated
- [ ] Documentation updated
- [ ] Executable builds successfully
- [ ] Manual testing completed
- [ ] Release notes prepared

### After Release
- [ ] GitHub release created
- [ ] Release announced (if applicable)
- [ ] Documentation updated
- [ ] Next version planning

## 🔄 Continuous Integration

### GitHub Actions Workflow

The workflow in `.github/workflows/release.yml` automatically:

1. **Triggers on:**
   - New version tags (`v*`)
   - Manual workflow dispatch

2. **Build process:**
   - Sets up Python 3.10
   - Installs dependencies
   - Runs build script
   - Creates release archive

3. **Release process:**
   - Generates release notes
   - Creates GitHub release
   - Uploads build artifacts

### Local Development Workflow

1. **Development:**
   ```bash
   git checkout -b feature/new-feature
   # Make changes
   git commit -m "Add new feature"
   git push origin feature/new-feature
   ```

2. **Testing:**
   ```bash
   python main.py  # Test locally
   python scripts/build_release.py  # Test build
   ```

3. **Release preparation:**
   ```bash
   git checkout main
   git merge feature/new-feature
   python scripts/manage_version.py minor
   git commit -m "Bump version for release"
   git tag v1.1.0
   git push origin main --tags
   ```

## 🛠️ Build Configuration

### PyInstaller Options

The build script uses these PyInstaller options:
- `--onefile`: Single executable file
- `--windowed`: No console window
- `--icon`: Application icon
- `--add-data`: Include additional files
- `--hidden-import`: Ensure all dependencies are included

### Customization

To modify the build:

1. **Edit `scripts/build_release.py`:**
   - Modify PyInstaller command
   - Add/remove included files
   - Change output directory

2. **Update workflow:**
   - Edit `.github/workflows/release.yml`
   - Modify build steps
   - Add additional platforms

## 📋 Release Management

### Version Numbering

Using semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Types

1. **Stable releases**: `v1.0.0`, `v1.1.0`, `v2.0.0`
2. **Pre-releases**: `v1.0.0-beta`, `v1.0.0-rc1`
3. **Development**: Use branch names for features

### Changelog Management

Maintain a `CHANGELOG.md` file with:
- Version numbers and dates
- Added features
- Changed functionality
- Deprecated features
- Removed features
- Fixed bugs
- Security updates
