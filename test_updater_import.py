#!/usr/bin/env python3
"""
Test script to check if the updater module can be imported properly.
This helps debug import issues before building with PyInstaller.
"""

import sys
import logging
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TidyCore")

def test_import():
    """Test importing the updater module and its components."""
    print("=" * 60)
    print("Testing updater module import...")
    print("=" * 60)
    
    try:
        print("1. Importing updater module...")
        from src.tidycore import updater
        print("   ✓ updater module imported successfully")
        
        print("2. Checking for update_manager...")
        if hasattr(updater, 'update_manager'):
            print("   ✓ update_manager found in module")
            
            if updater.update_manager is not None:
                print("   ✓ update_manager is not None")
                print(f"   ✓ update_manager type: {type(updater.update_manager)}")
                
                # Test a method call
                try:
                    # This should not raise an exception
                    updater.update_manager.check_for_updates
                    print("   ✓ update_manager has check_for_updates method")
                except AttributeError as e:
                    print(f"   ✗ update_manager missing method: {e}")
                    
            else:
                print("   ✗ update_manager is None")
        else:
            print("   ✗ update_manager not found in module")
            
        print("3. Testing direct import...")
        from src.tidycore.updater import update_manager
        print("   ✓ Direct import of update_manager successful")
        print(f"   ✓ Direct import type: {type(update_manager)}")
        
        print("4. Testing UpdateManager class...")
        from src.tidycore.updater import UpdateManager
        print("   ✓ UpdateManager class imported successfully")
        
        print("5. Testing get_update_manager function...")
        if hasattr(updater, 'get_update_manager'):
            manager = updater.get_update_manager()
            print("   ✓ get_update_manager function works")
            print(f"   ✓ get_update_manager returns: {type(manager)}")
        else:
            print("   ✗ get_update_manager function not found")
            
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED - Module should work in PyInstaller build")
        print("=" * 60)
        return True
        
    except ImportError as e:
        print(f"   ✗ Import failed: {e}")
        import traceback
        print("   Traceback:")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        import traceback
        print("   Traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_import()
    sys.exit(0 if success else 1)
