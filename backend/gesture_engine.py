import cv2
import mediapipe as mp
import time
import os
import urllib.request
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

class GestureEngine:
    def __init__(self, model_path=None):
        if model_path is None:
            # Default to looking in the same directory as this file
            model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hand_landmarker.task')
        
        self.model_path = model_path
        self.ensure_model_exists()
        
        base_options = python.BaseOptions(model_asset_path=self.model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        self.start_time = time.time()
        
        # State variables
        self.is_pinched = False
        self.pinch_start_time = 0
        self.prev_y = 0
        self.prev_x = 0
        self.movement_accumulator = 0
        self.last_click_time = 0
        
        # Smoothing State
        self.prev_cursor_x = 0
        self.prev_cursor_y = 0
        self.smoothing_factor = 0.5 # Lower = smoother but more lag
        
        # Output State
        self.current_state = {
            "landmarks": [],
            "gesture": "NONE",
            "cursor": {"x": 0, "y": 0},
            "scroll_delta": 0,
            "is_pinched": False
        }

    def ensure_model_exists(self):
        if not os.path.exists(self.model_path):
            print(f"Model file {self.model_path} not found. Downloading...")
            url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
            try:
                urllib.request.urlretrieve(url, self.model_path)
                print("Download complete.")
            except Exception as e:
                print(f"Failed to download model: {e}")

    def process_frame(self, frame):
        # 1. Convert Frame
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = int((time.time() - self.start_time) * 1000)

        # 2. Detect
        detection_result = self.detector.detect_for_video(mp_image, timestamp_ms)
        
        # 3. Process Results
        gesture_data = self._analyze_landmarks(detection_result, frame.shape)
        return gesture_data

    def _analyze_landmarks(self, detection_result, frame_shape):
        h, w, c = frame_shape
        landmarks_list = []
        
        if not detection_result.hand_landmarks:
            return None

        hand_landmarks = detection_result.hand_landmarks[0] # Single hand
        
        # Convert to list of dicts for JSON serialization
        for lm in hand_landmarks:
            landmarks_list.append({"x": lm.x, "y": lm.y, "z": lm.z})

        # Keypoints
        index_tip = hand_landmarks[8]
        thumb_tip = hand_landmarks[4]
        
        # Coordinates
        ix, iy = index_tip.x * w, index_tip.y * h
        tx, ty = thumb_tip.x * w, thumb_tip.y * h
        
        # Distance (Pinch)
        distance = ((ix - tx)**2 + (iy - ty)**2)**0.5
        
        # Thresholds
        ENTER_PINCH = 40
        EXIT_PINCH = 60
        
        # State Update
        scroll_delta = 0
        click_triggered = False
        
        # --- LOGIC PORTED FROM Scrollerr.py ---
        curr_y = (index_tip.y + thumb_tip.y) / 2
        curr_x = (index_tip.x + thumb_tip.x) / 2
        
        # ALWAYS Update Cursor (Critical for Drawing/Dragging)
        # Map safely with margins
        margin = 0.1
        mapped_x = (index_tip.x - margin) / (1 - 2*margin)
        mapped_y = (index_tip.y - margin) / (1 - 2*margin)
        mapped_x = max(0, min(1, mapped_x))
        mapped_y = max(0, min(1, mapped_y))
        
        # Apply Smoothing (Low Pass Filter)
        # New = Old + (Target - Old) * Alpha
        smooth_x = self.prev_cursor_x + (mapped_x - self.prev_cursor_x) * self.smoothing_factor
        smooth_y = self.prev_cursor_y + (mapped_y - self.prev_cursor_y) * self.smoothing_factor
        
        self.prev_cursor_x = smooth_x
        self.prev_cursor_y = smooth_y
        
        self.current_state["cursor"] = {"x": smooth_x, "y": smooth_y}
        
        if not self.is_pinched:
            if distance < ENTER_PINCH:
                self.is_pinched = True
                self.pinch_start_time = time.time()
                self.prev_y = curr_y
                self.prev_x = curr_x

        else: # Pinched
            if distance > EXIT_PINCH:
                self.is_pinched = False
                # Check Click
                if (time.time() - self.pinch_start_time) < 0.3:
                    click_triggered = True
                
                # Reset
                self.movement_accumulator = 0
            else:
                # Scroll Logic
                # Wait for stabilization
                if (time.time() - self.pinch_start_time) > 0.3:
                    diff_y = self.prev_y - curr_y
                    if abs(diff_y) > 0.001:
                        SCROLL_SENSITIVITY = 5000
                        target_scroll = diff_y * SCROLL_SENSITIVITY
                        self.movement_accumulator += target_scroll
                        
                        step_size = 30
                        if abs(self.movement_accumulator) >= step_size:
                            scroll_amount = int(self.movement_accumulator)
                            scroll_delta = -scroll_amount # Invert for natural scroll
                            self.movement_accumulator -= scroll_amount
                    
                    self.prev_y = curr_y
                    self.prev_x = curr_x

        self.current_state["landmarks"] = landmarks_list
        self.current_state["is_pinched"] = self.is_pinched
        self.current_state["scroll_delta"] = scroll_delta
        self.current_state["click_triggered"] = click_triggered
        
        return self.current_state
