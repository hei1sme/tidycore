# TidyCore Release Workflow

## 🔄 Complete Release Process

### 1. Pre-Release Checklist
- [ ] All features tested and working
- [ ] Update version number in `tidycore/__init__.py`
- [ ] Update CHANGELOG.md with new features/fixes
- [ ] Run full test suite
- [ ] Check all dependencies in requirements.txt
- [ ] Update README.md if needed

### 2. Version Numbering (Semantic Versioning)
- **Major version (X.0.0)**: Breaking changes, major new features
- **Minor version (1.X.0)**: New features, backwards compatible
- **Patch version (1.0.X)**: Bug fixes, small improvements

### 3. Build Process
```bash
# 1. Clean previous builds
rm -rf build/ dist/

# 2. Build executable with PyInstaller
python -m PyInstaller TidyCore.spec

# 3. Test the built executable
./dist/TidyCore/TidyCore.exe

# 4. Create release package
cd dist/
zip -r TidyCore-v{version}-Windows.zip TidyCore/
```

### 4. Git Workflow
```bash
# 1. Commit all changes
git add .
git commit -m "Release v{version}: Add feature descriptions"

# 2. Create and push version tag
git tag -a v{version} -m "Release version {version}"
git push origin main
git push origin v{version}
```

### 5. GitHub Release
1. Go to GitHub repository → Releases
2. Click "Create a new release"
3. Choose the version tag you just created
4. Fill in release title: "TidyCore v{version}"
5. Add release notes (copy from CHANGELOG.md)
6. Upload the built zip file
7. Mark as "Latest release" if it's stable
8. Publish release

### 6. Post-Release
- [ ] Update project documentation
- [ ] Announce on social media/forums
- [ ] Monitor for user feedback and bug reports
- [ ] Plan next version features

## 🛠️ Automation Scripts

### build_release.py
```python
#!/usr/bin/env python3
import subprocess
import shutil
import os
from pathlib import Path

def build_release(version):
    print(f"Building TidyCore v{version}...")
    
    # Clean build directory
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # Build with PyInstaller
    subprocess.run(["python", "-m", "PyInstaller", "TidyCore.spec"], check=True)
    
    # Create release zip
    shutil.make_archive(f"TidyCore-v{version}-Windows", "zip", "dist/TidyCore")
    
    print(f"Release package created: TidyCore-v{version}-Windows.zip")

if __name__ == "__main__":
    from tidycore import __version__
    build_release(__version__)
```

## 📝 Release Notes Template
See `RELEASE_NOTES_TEMPLATE.md` for the standard format.

## 🔧 CI/CD Setup (Optional)
For automated builds, you can set up GitHub Actions to:
- Build releases automatically on tag push
- Run tests before building
- Upload release assets automatically
