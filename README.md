# 🖐️ Lazy Scroller - The Ultimate Hand Gesture Control

**Scroll like a Jedi. Because clicking is too much work.**

## 🧐 What is this?
Lazy Scroller is a Python application that lets you scroll through websites, documents, and social media feeds using just your hand gestures. No mouse, no trackpad, just you waving at your webcam.

It uses computer vision to track your hand and translates your movements into smooth scrolling actions.

## 🎯 Who is this for?
- **Lazy People**: Why move your arm to the mouse when you can just twitch your fingers?
- **Show-offs**: Impress your friends by controlling your computer like Tony Stark.
- **Multitaskers**: Eating a burger? Scroll with your clean hand while holding the burger with the other.

## 🛠️ How it's made
This project is built using:
- **Python**: The magic behind the curtain.
- **OpenCV**: Eyes of the operation (Webcam access).
- **MediaPipe**: The brain that understands hands (Google's ML solution).
- **PyAutoGUI**: The worker that actually scrolls the screen.

## ⚡ Quick Start (Windows)
**Don't want to type commands?**
1. Double-click the **`run_app.bat`** file.
2. It will automatically check for changes, install what's needed, and start the app.
3. Enjoy!

## 🚀 How to use it (Manual Setup)

Want to run this on your machine? Follow these steps:

### Prerequisites
Make sure you have Python installed.

### 1. Clone or Download
Download this folder to your computer.

### 2. Install Dependencies
Open your terminal/command prompt in the project folder and run:
```bash
pip install -r requirements.txt
```

### 3. Run it!
Make sure your webcam is ready, then run:
```bash
python Scrollerr.py
```

### 4. Controls
- **Cursor Active (Hand Open)**: Spread fingers wide (> 100 distance) to move cursor.
- **Neutral / Reset (Relaxed)**: Relax fingers (Semi-open) to stop cursor. Use this to move your hand back without moving the mouse.
- **Scroll Mode (Pinch)**: Pinch Thumb + Index (< 40 distance) to Scroll.
- **Scroll Up/Down/Left/Right**: Move your hand while pinching to scroll in any direction.
- **Click (Tap)**: Quickly Pinch and Release (like a tap) to Click. 
- **Double Click**: Tap twice quickly. (Cursor freezes for 1 second after a click to make this easier).
- **'q' Key**: Quit the app.

---
*Made with ❤️ and Python.*
