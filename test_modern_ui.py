#!/usr/bin/env python3
"""
Test script to demonstrate the modernized TidyCore UI.
"""

import sys
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

def test_modern_ui():
    """Test function to demonstrate the modern UI styling."""
    print("🎨 Testing TidyCore Modern UI")
    print("="*50)
    
    # Import here to avoid issues
    from src.tidycore.gui import TidyCoreGUI
    from src.tidycore.engine import TidyCoreEngine
    
    app = QApplication(sys.argv)
    
    # Create a mock engine for testing
    class MockEngine:
        def __init__(self):
            self.running = True
            self.paused = False
        
        def is_running(self):
            return self.running
        
        def is_paused(self):
            return self.paused
        
        def pause(self):
            self.paused = True
            print("📊 Engine paused")
        
        def resume(self):
            self.paused = False
            print("▶️ Engine resumed")
        
        def get_health_status(self):
            return {
                'status': 'running',
                'observer_status': 'active',
                'last_heartbeat': time.time(),
                'processed_files': 42,
                'errors': 0
            }
    
    # Create the GUI with mock engine
    engine = MockEngine()
    gui = TidyCoreGUI(engine, app)
    gui.show()
    
    # Update the status to show modern styling
    gui.update_engine_status()
    
    print("✅ Modern UI Features Applied:")
    print("   • Enhanced sidebar with gradients and rounded corners")
    print("   • Professional button styling with hover effects") 
    print("   • Modern content area with light theme")
    print("   • Improved typography and spacing")
    print("   • Professional color scheme (blues, grays)")
    print("   • Enhanced group boxes with styled titles")
    print("   • Modern input fields and form controls")
    print("\n🚀 UI is now running with modern professional styling!")
    print("   Close the window to exit the test.")
    
    # Run the event loop
    app.exec()

if __name__ == "__main__":
    test_modern_ui()
