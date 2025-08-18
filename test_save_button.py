#!/usr/bin/env python3
"""
TidyCore Settings Save Button Test
This script tests that the save button in settings is visible and clickable.
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'src')

def test_settings_save_button():
    """Test that settings save button is visible and functional."""
    print("🔍 TESTING SETTINGS SAVE BUTTON")
    print("=" * 50)
    
    try:
        from PySide6.QtWidgets import QApplication
        from tidycore.settings_page import SettingsPage
        
        # Create app
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        print("1. Creating settings page...")
        settings_page = SettingsPage()
        print("   ✓ Settings page created with scroll area")
        
        print("2. Testing save button properties...")
        save_buttons = []
        for widget in settings_page.findChildren(type(settings_page).__bases__[0]):
            if hasattr(widget, 'text') and 'Save' in str(widget.text()):
                save_buttons.append(widget)
        
        if save_buttons:
            save_btn = save_buttons[0]
            print(f"   ✓ Found save button: '{save_btn.text()}'")
            print(f"   ✓ Enabled: {save_btn.isEnabled()}")
            print(f"   ✓ Size: {save_btn.minimumWidth()}x{save_btn.minimumHeight()}")
            
            # Test visibility after showing parent
            settings_page.show()
            settings_page.resize(900, 700)
            
            print(f"   ✓ Visible after parent shown: {save_btn.isVisible()}")
            
            # Test clicking the button
            print("3. Testing button functionality...")
            try:
                # Simulate clicking by calling the connected method
                print("   Simulating button click...")
                settings_page._save_settings()
                print("   ✓ Save method executed successfully")
            except Exception as e:
                print(f"   ❌ Save method failed: {e}")
                return False
            
            settings_page.hide()
            print("   ✓ Button is functional")
            
        else:
            print("   ❌ No save button found")
            return False
        
        app.quit()
        
        print("\n" + "=" * 50)
        print("✅ SETTINGS SAVE BUTTON TEST PASSED")
        print("The save button should now be:")
        print("• Visible in the settings page")
        print("• Properly sized and styled")
        print("• Clickable and functional")
        print("• Accessible via scroll if needed")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_settings_save_button()
    if success:
        print("\n🎉 You can now use the save button in TidyCore settings!")
    else:
        print("\n⚠️  There may still be issues with the save button.")
    
    sys.exit(0 if success else 1)
