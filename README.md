# 🖐️ HandGesture Studio

**A Next-Gen Hand Tracking Interface for Creativity & Control**

HandGesture Studio is a modern web-based application that transforms your hand movements into digital actions. Draw in the air, manipulate 3D objects, or control your computer—all without touching a mouse or keyboard.

---

## ✨ Features

### 1. **Air Drawing**
- A pristine, infinite canvas for freehand drawing.
- **Gesture**: Pinch your index finger and thumb to draw. Release to hover.
- **Tech**: HTML5 Canvas powered by real-time hand tracking.

### 2. **Hand Scroller (Utility Mode)**
- Control your entire OS with simple gestures.
- **Scroll**: Move your hand up/down to scroll content.
- **Click**: Quick pinch gesture to click.
- **Cursor**: Open hand to move the mouse cursor.

### 3. **3D Drawing**
- Interact with a 3D environment.
- **Visuals**: Powered by Three.js for immersive graphics.
- **Control**: Rotate and manipulate objects in 3D space.

---

## ⚡ Quick Start (Windows)

We've made it incredibly easy to start. No complicated installation required (if Python is installed).

1.  **Double-click** the `run_handgesture.bat` file.
2.  The application will launch in your default web browser at `http://localhost:8000`.
3.  Grant camera permissions when prompted.

---

## �️ Usage Guide

### The Hub
The main menu allows you to switch between modes seamlessly. Just click on the card for the mode you want to enter.

### Controls
| Mode | Gesture | Action |
| :--- | :--- | :--- |
| **All** | **Open Hand** | Move Cursor / Tracking Active |
| **Air Draw** | **Pinch (Index+Thumb)** | Draw on Canvas |
| **Scroller** | **Pinch & Move Up/Down** | Scroll Page |
| **Scroller** | **Quick Pinch (Tap)** | Left Click |
| **3D Draw** | **Pinch & Rotate** | Rotate 3D Object |

---

## 🔧 Technical Details

This project uses a hybrid architecture:
-   **Backend**: Python (FastAPI) handles the heavy lifting of Computer Vision using MediaPipe.
-   **Frontend**: React + Three.js + TailwindCSS (served via CDN) for a responsive, modern UI.
-   **Communication**: WebSocket connection streams hand landmarks in real-time (60 FPS).

### Requirements
-   Python 3.8+
-   Webcam

### Manual Installation
If you prefer identifying the magic yourself:

```bash
# 1. Install Dependencies
pip install fastapi uvicorn websockets mediapipe opencv-python pyautogui

# 2. Run the Server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📂 Legacy Version
 Looking for the original standalone Python script? It's still here!
-   Run `python Scrollerr.py` to use the legacy version.
-   See `OLD_README.md` (if renamed) or previous commits for details.

---

*Built with ❤️ using Python & React.*
