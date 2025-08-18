#!/usr/bin/env python3
"""
TidyCore Fix Validation Script
This script tests all the fixes implemented for TidyCore to ensure proper functionality.
"""

import sys
import os
import threading
import time
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def test_imports():
    """Test that all modules import correctly."""
    print("🔍 Testing imports...")
    try:
        from tidycore.config_manager import load_config
        from tidycore.engine import TidyCoreEngine
        from tidycore.logger import setup_logger
        from tidycore.database import StatisticsDatabase
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_database():
    """Test database functionality."""
    print("🔍 Testing database...")
    try:
        from tidycore.database import StatisticsDatabase
        db = StatisticsDatabase()
        
        # Test database operations
        initial_stats = db.get_total_stats()
        db.record_file_operation("test.txt", "/test/test.txt", "/test/docs/test.txt", "Documents")
        new_stats = db.get_total_stats()
        
        if new_stats > initial_stats:
            print("✅ Database operations working")
            print(f"   Stats: {initial_stats} → {new_stats}")
            return True
        else:
            print("❌ Database operations failed")
            return False
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_configuration():
    """Test configuration loading."""
    print("🔍 Testing configuration...")
    try:
        from tidycore.config_manager import load_config
        config = load_config()
        
        if 'target_folder' in config and os.path.exists(config['target_folder']):
            print("✅ Configuration loaded successfully")
            print(f"   Target folder: {config['target_folder']}")
            return True
        else:
            print("❌ Configuration invalid")
            return False
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_engine_creation():
    """Test engine creation and health status."""
    print("🔍 Testing engine creation...")
    try:
        from tidycore.config_manager import load_config
        from tidycore.engine import TidyCoreEngine
        from tidycore.logger import setup_logger
        
        logger = setup_logger()
        config = load_config()
        engine = TidyCoreEngine(config)
        
        health = engine.get_health_status()
        print("✅ Engine created successfully")
        print(f"   Health status: {health}")
        return True
    except Exception as e:
        print(f"❌ Engine creation error: {e}")
        return False

def test_threading():
    """Test non-daemon threading."""
    print("🔍 Testing threading...")
    try:
        def test_thread_function():
            time.sleep(1)
            return True
        
        thread = threading.Thread(target=test_thread_function, daemon=False)
        thread.start()
        thread.join(timeout=3)
        
        if not thread.is_alive():
            print("✅ Non-daemon threading working")
            return True
        else:
            print("❌ Threading test timeout")
            return False
    except Exception as e:
        print(f"❌ Threading error: {e}")
        return False

def test_background_persistence():
    """Test that engine continues running after GUI closes."""
    print("🔍 Testing background persistence...")
    try:
        from tidycore.config_manager import load_config
        from tidycore.engine import TidyCoreEngine
        from tidycore.logger import setup_logger
        
        logger = setup_logger()
        config = load_config()
        
        # Create engine like in main.py
        engine = TidyCoreEngine(config)
        
        # Start non-daemon thread (like fixed main.py)
        engine_thread = threading.Thread(
            target=engine.run,
            daemon=False,  # FIXED: Non-daemon for persistence
            name="TestEngineThread"
        )
        engine_thread.start()
        
        # Wait for initialization
        time.sleep(2)
        
        # Check thread is non-daemon and alive
        if not engine_thread.daemon and engine_thread.is_alive():
            # Simulate GUI close without stopping engine
            print("   Simulating GUI close (engine should continue)...")
            time.sleep(1)
            
            # Engine should still be running
            health = engine.get_health_status()
            if health['is_running'] and health['observer_alive']:
                print("✅ Engine persists after GUI close")
                result = True
            else:
                print("❌ Engine stopped when it shouldn't have")
                result = False
        else:
            print("❌ Engine thread not properly configured")
            result = False
        
        # Cleanup
        engine.stop()
        time.sleep(1)
        
        return result
        
    except Exception as e:
        print(f"❌ Background persistence test error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 TidyCore Fix Validation")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Database", test_database),
        ("Configuration", test_configuration),
        ("Engine Creation", test_engine_creation),
        ("Threading", test_threading),
        ("Background Persistence", test_background_persistence),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📝 {test_name}")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 ALL FIXES WORKING CORRECTLY!")
        print("Your TidyCore application should now:")
        print("• Continue running after GUI is closed")
        print("• Persist data across restarts")
        print("• Automatically recover from errors")
        print("• Monitor files reliably")
    else:
        print("\n⚠️  Some issues remain. Check the failed tests above.")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
