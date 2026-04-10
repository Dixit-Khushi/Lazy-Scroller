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
prev_y = None
prev_x = None
movement_accumulator = 0.0
smooth_y = None          # EMA-filtered Y for smooth scrolling
EMA_ALPHA = 0.15         # Lower = smoother but more lag (0.1–0.4 is good)
start_time = time.time()
is_pinched = False
pinch_start_time = 0
last_click_time = 0
# Cursor smoothing variables
prev_screen_x, prev_screen_y = None, None

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
            
            # Define thresholds — tight so scroll only fires when fingers TOUCH
            enter_pinch_dist = 18  # Fingers must nearly touch to START scroll
            exit_pinch_dist = 32   # Must open this far to STOP scroll
            
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
                        if prev_screen_x is None:
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
                # GRACE PERIOD: stabilise anchor before scrolling starts
                if time.time() - pinch_start_time < 0.25:
                    cv2.putText(frame, "Stabilizing...", (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                    # Reset EMA and anchor to current position
                    smooth_y = curr_y
                    prev_y = curr_y
                    prev_x = curr_x
                else:
                    cv2.putText(frame, "SCROLL MODE", (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                    # --- EMA filter on Y to kill jitter ---
                    if smooth_y is None:
                        smooth_y = curr_y
                    else:
                        smooth_y = EMA_ALPHA * curr_y + (1 - EMA_ALPHA) * smooth_y

                    # Diff against previous EMA-smoothed position
                    if prev_y is None:
                        prev_y = smooth_y

                    diff_y = prev_y - smooth_y  # +ve = hand moved UP = scroll DOWN

                    # Noise gate: ignore sub-pixel hand tremor
                    if abs(diff_y) > 0.0005:
                        # Sensitivity (tune this number up/down)
                        SCROLL_SENSITIVITY = 4000
                        movement_accumulator += diff_y * SCROLL_SENSITIVITY

                        # Fire scroll every 1 unit — tiny, continuous steps = buttery smooth
                        if abs(movement_accumulator) >= 1:
                            scroll_amount = int(movement_accumulator)
                            pyautogui.scroll(-scroll_amount)
                            movement_accumulator -= scroll_amount

                            if scroll_amount > 0:
                                cv2.putText(frame, "SCROLL DOWN v", (50, 50),
                                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                            else:
                                cv2.putText(frame, "SCROLL UP ^", (50, 50),
                                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                    prev_y = smooth_y
                    prev_x = curr_x
            else:
                smooth_y = None   # Reset EMA when not pinched
                prev_y = None
                cv2.putText(frame, "Open hand — Pinch fingers to Scroll", (50, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                
    cv2.imshow('Lazy Scroller', frame)
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()