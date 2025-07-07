# Hook for unicodedata module
# This ensures unicodedata is properly bundled with PyInstaller

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_dynamic_libs

# Collect all unicodedata components
datas, binaries, hiddenimports = collect_all('unicodedata')

# Explicitly collect data files
unicodedata_datas = collect_data_files('unicodedata')
if unicodedata_datas:
    datas.extend(unicodedata_datas)

# Collect any dynamic libraries
unicodedata_libs = collect_dynamic_libs('unicodedata')
if unicodedata_libs:
    binaries.extend(unicodedata_libs)

# Add to hidden imports
hiddenimports += ['unicodedata']
