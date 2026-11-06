"""Build a local Windows artifact without killing apps or deleting old builds."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import platform

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from tidycore import __version__


def main():
    if sys.platform != 'win32' or sys.prefix == sys.base_prefix:
        raise SystemExit('Build on native Windows using the project .venv interpreter.')
    run = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    work = ROOT / 'build' / run
    dist = ROOT / 'dist' / run
    release = ROOT / 'release' / f'TidyCore-v{__version__}-Windows-{run}'
    for path in (work, dist, release):
        path.resolve().relative_to(ROOT)
        path.mkdir(parents=True, exist_ok=False)
    # Render the repo-native vector icon at Windows icon resolutions.
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    from PIL import Image
    image = QImage(256, 256, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer = QSvgRenderer(str(ROOT / 'assets' / 'tidycore.svg'))
    renderer.render(painter)
    painter.end()
    png = work / 'tidycore.png'
    image.save(str(png))
    icon = work / 'tidycore.ico'
    with Image.open(png) as source:
        source.save(icon, sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
    version_file = work / 'windows-version.txt'
    version_tuple = tuple(int(part) for part in __version__.split('.')) + (0,)
    strings = {'CompanyName':'TidyCore','FileDescription':'TidyCore file organizer',
               'FileVersion':__version__,'InternalName':'TidyCore','OriginalFilename':'TidyCore.exe',
               'ProductName':'TidyCore','ProductVersion':__version__,
               'LegalCopyright':'TidyCore contributors. MIT License.'}
    entries = ','.join(f'StringStruct({key!r},{value!r})' for key,value in strings.items())
    version_file.write_text(
        f"VSVersionInfo(ffi=FixedFileInfo(filevers={version_tuple!r},prodvers={version_tuple!r},mask=0x3f,flags=0,OS=0x40004,fileType=1,subtype=0,date=(0,0)),"
        f"kids=[StringFileInfo([StringTable('040904B0',[{entries}])]),VarFileInfo([VarStruct('Translation',[1033,1200])])])",
        encoding='utf-8')
    command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onefile', '--windowed',
               '--name=TidyCore', '--noupx', f'--icon={icon}',
               f'--version-file={version_file}',
               f'--workpath={work / "pyinstaller"}', f'--specpath={work}', f'--distpath={dist}',
               f'--add-data={ROOT / "config" / "config.json"};config',
               f'--add-data={ROOT / "assets" / "tidycore.svg"};assets',
               str(ROOT / 'main.py')]
    log = work / 'build.log'
    print(f'Building with {sys.executable}\nLog: {log}', flush=True)
    with log.open('w', encoding='utf-8') as handle:
        result = subprocess.run(command, cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT)
    if result.returncode:
        print(log.read_text(encoding='utf-8')[-12000:])
        return result.returncode
    executable = release / 'TidyCore.exe'
    shutil.copy2(dist / 'TidyCore.exe', executable)
    for name in ('README.md', 'LICENSE', 'DESIGN.md'):
        shutil.copy2(ROOT / name, release / name)
    shutil.copytree(ROOT / 'docs', release / 'docs',ignore=shutil.ignore_patterns('evidence'))
    if (ROOT / 'assets' / 'screenshots').exists():
        shutil.copytree(ROOT / 'assets' / 'screenshots',release / 'assets' / 'screenshots')
    with executable.open('rb') as handle:
        digest = hashlib.file_digest(handle, 'sha256').hexdigest()
    inputs = [ROOT/'main.py', *sorted((ROOT/'src').rglob('*.py')),
              ROOT/'config/config.json', ROOT/'assets/tidycore.svg',ROOT/'requirements.txt']
    source_hashes = {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}
    manifest = {'version': __version__, 'built_at': datetime.now().astimezone().isoformat(),
                'python': platform.python_version(), 'platform': platform.system(),
                'sha256': digest, 'executable': 'TidyCore.exe',
                'build_command': '.venv\\Scripts\\python.exe scripts/build_release.py',
                'source_sha256': source_hashes}
    (release / 'BUILD.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (release / 'SHA256SUMS.txt').write_text(f'{digest}  TidyCore.exe\n', encoding='utf-8')
    archive = shutil.make_archive(str(release), 'zip', release)
    print(f'Executable: {executable}\nArchive: {archive}\nSHA256: {digest}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
