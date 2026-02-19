import cv2
import mediapipe as mp
import pyautogui
import time
import os
import urllib.request
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# 1. Download Model if missing
model_path = 'hand_landmarker.task'
if not os.path.exists(model_path):
    print(f"Model file {model_path} not found. Downloading...")
    url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
    try:
        urllib.request.urlretrieve(url, model_path)
        print("Download complete.")
    except Exception as e:
        print(f"Failed to download model: {e}")
        exit()

# 2. Initialize HandLandmarker
base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5
)
detector = vision.HandLandmarker.create_from_options(options)

# 3. Setup Webcam
cap = cv2.VideoCapture(0)

# Variables
prev_y = 0
prev_x = 0
movement_accumulator = 0

scroll_threshold = 0.02  # Accumulated 2% of screen height triggers scroll
scroll_speed = -100 # Pixels (negative = down)
start_time = time.time()
is_pinched = False
pinch_start_time = 0
last_click_time = 0 
# Smoothing variables (will be initialized in loop if needed, but good to have)
prev_screen_x, prev_screen_y = 0, 0

print("Lazy Scroller 2.0 (Tasks API) Started.")
print("Move hand UP to scroll DOWN. Press 'q' to quit.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Empty frame.")
        continue

    # Flip and convert
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Create MP Image
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    
    # Timestamp calculation (ms)
    timestamp_ms = int((time.time() - start_time) * 1000)
    
    # Detect
    detection_result = detector.detect_for_video(mp_image, timestamp_ms)
    
    # Visualization (Custom drawing needed as mp_drawing works with proto, result is object)
    # We will just draw a circle on the tip for simplicity
    
    if detection_result.hand_landmarks:
        for hand_landmarks in detection_result.hand_landmarks:
            # Get Index Finger Tip (8) and Thumb Tip (4)
            index_tip = hand_landmarks[8]
            thumb_tip = hand_landmarks[4]
            
            # Coordinates are normalized [0, 1]
            h, w, c = frame.shape
            ix, iy = int(index_tip.x * w), int(index_tip.y * h)
            tx, ty = int(thumb_tip.x * w), int(thumb_tip.y * h)
            
            # Calculate Current Y Position (Midpoint Normalized)
            curr_y = (index_tip.y + thumb_tip.y) / 2
            curr_x = (index_tip.x + thumb_tip.x) / 2
            
            # Calculate Distance between Index and Thumb
            distance = ((ix - tx)**2 + (iy - ty)**2)**0.5
            
            # Draw Tips
            cv2.circle(frame, (ix, iy), 10, (255, 0, 255), cv2.FILLED)
            cv2.circle(frame, (tx, ty), 10, (255, 0, 255), cv2.FILLED)
            
            # Logic: Pinch Detection with Hysteresis
            # distance is in pixels (approx)
            
            # Define thresholds
            enter_pinch_dist = 40  # Must be closer than this to START
            exit_pinch_dist = 60   # Must be further than this to STOP
            
            if not is_pinched:
                # FREEZE CURSOR after a click to allow Double Click
                # Increased to 1.0s to give user more time
                if time.time() - last_click_time < 1.0:
                     cv2.putText(frame, "Cursor Frozen (Double Tap Now)", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                     # pass means we don't update cursor position, effectively freezing it.
                else: 
                    if distance < enter_pinch_dist:
                        is_pinched = True
                        pinch_start_time = time.time() # Start grace period
                        prev_y = curr_y # Anchor vertical
                        prev_x = curr_x # Anchor horizontal
                    
                    # DEAD ZONE (Clutch) Logic
                    # If distance is between Pinch and Open, do NOTHING.
                    # This allows user to "declutch" and move hand back without moving cursor.
                    elif distance < 100: # 40 to 100 is Dead Zone
                        cv2.putText(frame, "NEUTRAL (Relaxed)", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                        # pass - No cursor movement
                        pass
                        
                    else:
                        # CURSOR MOVEMENT (Hand Fully Open, > 100px)
                        cv2.putText(frame, "CURSOR ACTIVE", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        
                        # Map Index Finger coordinates to Screen
                        screen_w, screen_h = pyautogui.size()
                        
                        # Optional: Add margins to make reaching edges easier
                        margin = 0.1 # 10% margin on sides
                        
                        mapped_x = (index_tip.x - margin) / (1 - 2*margin)
                        mapped_y = (index_tip.y - margin) / (1 - 2*margin)
                        
                        mapped_x = max(0, min(1, mapped_x))
                        mapped_y = max(0, min(1, mapped_y))
                        
                        target_x = int(mapped_x * screen_w)
                        target_y = int(mapped_y * screen_h)
                        
                        # FAILSAFE: Disable corner failsafe effectively
                        pyautogui.FAILSAFE = False 
                        
                        # Smoothing (Weighted Average)
                        if 'prev_screen_x' not in locals():
                            prev_screen_x, prev_screen_y = target_x, target_y
                        
                        # Dynamic Smoothing: Move faster if distance is large (snap), smoother if small (precision)
                        dist_move = ((target_x - prev_screen_x)**2 + (target_y - prev_screen_y)**2)**0.5
                        
                        # 1. Deadzone: If movement is tiny (jitter), ignore it.
                        if dist_move < 3:
                            curr_screen_x, curr_screen_y = prev_screen_x, prev_screen_y
                        else:
                            # 2. Dynamic Alpha: 
                            # Slow movement -> Low Alpha (High smoothing)
                            # Fast movement -> High Alpha (Low smoothing, responsive)
                            
                            # Base alpha 0.15 is smoother than 0.1 for start, max 0.8 for fast.
                            alpha = 0.15 + (min(dist_move, 200) / 200) * 0.65
                            
                            curr_screen_x = prev_screen_x + (target_x - prev_screen_x) * alpha
                            curr_screen_y = prev_screen_y + (target_y - prev_screen_y) * alpha
                        
                        pyautogui.moveTo(curr_screen_x, curr_screen_y)
                        prev_screen_x, prev_screen_y = curr_screen_x, curr_screen_y
                    
            else:
                # PINCHED STATE
                if distance > exit_pinch_dist:
                    is_pinched = False
                    
                    # CHECK FOR CLICK (Tap)
                    pinch_duration = time.time() - pinch_start_time
                    if pinch_duration < 0.3: # Quick tap
                        pyautogui.click()
                        last_click_time = time.time() # Start freeze timer for double click
                        cv2.putText(frame, "CLICK!", (int(ix), int(iy)), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                    
                    prev_y = 0 # Reset anchor
                    prev_x = 0
                    movement_accumulator = 0

            
            # Visualization of Thresholds
            color = (0, 255, 0) if is_pinched else (0, 0, 255)
            cv2.line(frame, (ix, iy), (tx, ty), color, 3)
            # cv2.putText(frame, f"Dist: {int(distance)}", (int(ix+20), int(iy)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            if is_pinched:
                # GRACE PERIOD: Ignore movement for x seconds after grab to prevent "jump"
                if time.time() - pinch_start_time < 0.3:
                    cv2.putText(frame, "Stabilizing...", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                    prev_y = curr_y # Reset anchors
                    prev_x = curr_x
                else:
                    cv2.putText(frame, "SCROLL MODE", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                    # VERTICAL SCROLL - Proportional (Smooth)
                    diff_y = prev_y - curr_y 
                    
                    # 1. Noise Gate: Ignore tiny jitters
                    if abs(diff_y) > 0.001: 
                        # 2. Sensitivity Factor: Multiplier to convert hand movement (0.0-1.0) to scroll units 
                        # Tuning: 5000 seems to be a good starting point for Windows (where ~120 is one click)
                        # Higher = Faster/More sensitive
                        SCROLL_SENSITIVITY = 5000 
                        
                        target_scroll = diff_y * SCROLL_SENSITIVITY
                        movement_accumulator += target_scroll
                        
                        # 3. Apply Scroll: Trigger when we have enough accumulated movement
                        # Windows standard click is often 120. PyAutoGUI handles integers.
                        # Using 30 as a "step" allows smoother updates than waiting for 100.
                        step_size = 30
                        
                        if abs(movement_accumulator) >= step_size:
                            scroll_amount = int(movement_accumulator)
                            
                            # Note: Hand UP (Positive diff_y) -> Scroll DOWN (Negative Value)
                            # Hand DOWN (Negative diff_y) -> Scroll UP (Positive Value)
                            # But wait, diff_y = prev - curr. 
                            # If Hand Moves UP: prev > curr (since 0 is top), result POSITIVE. 
                            # We want PAGE to go DOWN -> Scroll value NEGATIVE.
                            # So we invert the sign.
                            
                            pyautogui.scroll(-scroll_amount) 
                            
                            # Update Visuals
                            if scroll_amount > 0: # Hand moved UP, Scroll DOWN
                                cv2.putText(frame, "SCROLL DOWN", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                            else:
                                cv2.putText(frame, "SCROLL UP", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                                
                            # Subtract the used amount, keeping the remainder (sub_pixel precision)
                            movement_accumulator -= scroll_amount 
                    

                    
                    prev_y = curr_y
                    prev_x = curr_x
            else:
                 cv2.putText(frame, "Cursor Mode (Pinch to Scroll/Click)", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
    cv2.imshow('Lazy Scroller', frame)
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()