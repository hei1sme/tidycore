# Runtime hook for unicodedata
# This ensures unicodedata is properly loaded at runtime

import sys
import os

# Add the DLLs directory to the path for PyInstaller bundles
if hasattr(sys, '_MEIPASS'):
    # Running in PyInstaller bundle
    dlls_path = os.path.join(sys._MEIPASS, 'DLLs')
    if os.path.exists(dlls_path) and dlls_path not in sys.path:
        sys.path.insert(0, dlls_path)

# Preload unicodedata to avoid runtime issues
try:
    import unicodedata
    # Force initialization by using a simple operation
    unicodedata.name('A', 'UNKNOWN')
    print("✓ unicodedata loaded successfully")
except ImportError as e:
    print(f"✗ Failed to import unicodedata: {e}")
    # Try alternative loading methods
    try:
        import importlib.util
        spec = importlib.util.find_spec('unicodedata')
        if spec:
            unicodedata = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(unicodedata)
            print("✓ unicodedata loaded via importlib")
    except Exception as e2:
        print(f"✗ Alternative loading failed: {e2}")
except Exception as e:
    print(f"✗ Error initializing unicodedata: {e}")

# Also ensure encodings are available
try:
    import encodings
    import encodings.idna
    import encodings.utf_8
    import encodings.ascii
    print("✓ encodings loaded successfully")
except ImportError as e:
    print(f"✗ Failed to import encodings: {e}")
