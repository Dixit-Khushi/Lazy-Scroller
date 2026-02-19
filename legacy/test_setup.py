import sys
import importlib.util

def check_import(module_name, display_name=None):
    if display_name is None:
        display_name = module_name
    
    print(f"Checking {display_name}...", end=" ")
    try:
        if module_name == "opencv-python":
            import cv2
            print(f"✅ Found (cv2 version: {cv2.__version__})")
        else:
            lib = importlib.import_module(module_name)
            version = getattr(lib, '__version__', 'unknown')
            print(f"✅ Found (version: {version})")
    except ImportError:
        print(f"❌ MISSING! Please run: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    return True

print("--- Verifying Environment ---")
all_good = True
all_good &= check_import("mediapipe")
all_good &= check_import("pyautogui")
all_good &= check_import("opencv-python", "OpenCV")

if all_good:
    print("\n🎉 All requirements are satisfied! You are ready to scroll.")
else:
    print("\n⚠️  Some requirements are missing.")
