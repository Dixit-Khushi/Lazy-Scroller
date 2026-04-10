# 🖐️ Lazy Scroller

**A Next-Gen Hand Tracking Interface for Control**

Lazy Scroller is a standalone Python application that transforms your hand movements into digital actions. Control your computer's mouse and scroll through pages without touching a mouse or keyboard.

---

## ✨ Features

- **Cursor Control**: Move your hand to control the mouse cursor.
- **Click**: Quick pinch gesture to click on items.
- **Scroll**: Pinch and move your hand up/down to scroll continuously.

---

## ⚡ Quick Start (Windows)

1. Ensure **Python** is installed and on your system's PATH.
2. Double-click the `run_app.bat` file to automatically install dependencies and launch the exact experience.
3. Allow camera permissions if prompted. 
4. Move your hands! Press `q` in the terminal or cv2 window to quit.

---

## ️ Controls

| Action | Gesture |
| :--- | :--- |
| **Move Cursor** | Open Hand |
| **Scroll Page** | Pinch (Index+Thumb) & Move Up/Down |
| **Left Click** | Quick Pinch (Tap) |

---

## 🔧 Technical Details

Powered by **Python**, **OpenCV**, **MediaPipe** (Tasks API), and **PyAutoGUI**.

### Manual Run

```bash
# Install Dependencies
pip install -r requirements.txt

# Run the Application
python Scrollerr.py
```
