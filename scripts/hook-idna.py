# Hook for idna module
# This ensures idna and its data files are properly bundled with PyInstaller

from PyInstaller.utils.hooks import collect_all, collect_data_files

# Collect all idna components
datas, binaries, hiddenimports = collect_all('idna')

# Add specific idna modules that are often missed
hiddenimports += [
    'idna.core',
    'idna.idnadata', 
    'idna.uts46data',
    'idna.package_data'
]

# Collect idna data files explicitly
try:
    import idna
    import os
    idna_path = os.path.dirname(idna.__file__)
    
    # Add data files from idna package
    for data_file in ['idnadata', 'uts46data']:
        data_path = os.path.join(idna_path, data_file + '.py')
        if os.path.exists(data_path):
            datas.append((data_path, 'idna'))
except ImportError:
    pass
