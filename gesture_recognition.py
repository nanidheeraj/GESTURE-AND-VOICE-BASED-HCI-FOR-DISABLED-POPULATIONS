"""
Gesture Recognition Module using MediaPipe GestureRecognizer Task
Detects hand landmarks and recognizes 25+ built-in static/dynamic gestures
AND supports learning/recognizing new custom gestures.
"""

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.framework.formats import landmark_pb2
import numpy as np
import time
import json

# Helper functions for drawing
_MARGIN = 10  # pixels
_ROW_SIZE = 10  # pixels
_FONT_SIZE = 1
_FONT_THICKNESS = 1
_TEXT_COLOR = (0, 255, 0)  # Green
_CUSTOM_GESTURE_COLOR = (0, 255, 255) # Yellow for custom gestures

class GestureRecognizer:
    def __init__(self, camera_index=0, width=640, height=480, config=None):
        """Initialize gesture recognizer with MediaPipe GestureRecognizer Task"""
        
        self.width = width
        self.height = height
        self.cap = cv2.VideoCapture(camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        self.config_data = config or {}
        self.running = True

        # --- Load custom gesture data ---
        self.config_path = 'config.json' 
        self.recognition_threshold = 0.08 # Tune this sensitivity
        self.custom_gestures = self._load_custom_gestures()
        
        # Initialize MediaPipe Gesture Recognizer
        try:
            model_path = 'static/models/gesture_recognizer.task'
            BaseOptions = mp.tasks.BaseOptions
            GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
            VisionRunningMode = mp.tasks.vision.RunningMode

            options = GestureRecognizerOptions(
                base_options=BaseOptions(model_asset_path=model_path),
                running_mode=VisionRunningMode.VIDEO,
                num_hands=1,
                min_hand_detection_confidence=0.5,
                min_hand_presence_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.recognizer = vision.GestureRecognizer.create_from_options(options)
            print("MediaPipe GestureRecognizer model loaded successfully.")
        except Exception as e:
            raise Exception(f"Failed to load GestureRecognizer model: {e}. "
                            f"Make sure 'static/models/gesture_recognizer.task' exists.")
        
        self.frame_timestamp_ms = 0

    def _load_custom_gestures(self):
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            return config.get('custom_gesture_data', {})
        except FileNotFoundError:
            print("config.json not found, starting with no custom gestures.")
            return {}
        except Exception as e:
            print(f"Error loading custom gestures: {e}")
            return {}

    def _save_custom_gestures(self):
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            config['custom_gesture_data'] = self.custom_gestures
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print("Custom gestures saved.")
        except Exception as e:
            print(f"Error saving custom gestures: {e}")

    # --- MODIFIED: Renamed from _normalize_landmarks to be public ---
    def normalize_landmarks(self, landmarks):
        """
        Normalizes landmarks based on wrist (0) and middle finger MCP (9).
        Input: list of landmark_pb2.NormalizedLandmark
        """
        if not landmarks:
            return np.array([])
            
        landmarks_np = np.array([[lm.x, lm.y] for lm in landmarks])
        
        wrist = landmarks_np[0]
        mcp_middle = landmarks_np[9]

        scale = np.linalg.norm(mcp_middle - wrist)
        if scale == 0:
            scale = 1 

        normalized = (landmarks_np - wrist) / scale
        return normalized.flatten()

    def _calculate_distance(self, template1, template2):
        """Calculates the mean squared error between two normalized landmark templates."""
        if template1.shape != template2.shape:
            return float('inf')
        return np.sum((template1 - template2)**2) / len(template1)

    # --- NEW: Method to save an averaged template from many samples ---
    def save_averaged_template(self, samples_list, new_gesture_name):
        """
        Averages a list of collected samples and saves the resulting template.
        """
        if not samples_list:
            return {"status": "error", "message": "No samples collected."}
        
        try:
            # Calculate average template from all collected samples
            avg_template = np.mean(samples_list, axis=0)
            
            # Check for conflicts with existing *custom* gestures
            for name, template_data in self.custom_gestures.items():
                saved_template = np.array(template_data)
                distance = self._calculate_distance(avg_template, saved_template)
                if distance < self.recognition_threshold:
                     return {"status": "error", "message": f"Pose is too similar to your existing gesture '{name}'."}

            # Save the new averaged template
            self.custom_gestures[new_gesture_name] = avg_template.tolist()
            self._save_custom_gestures()
            
            return {"status": "success", "message": f"Successfully learned '{new_gesture_name}'."}
        except Exception as e:
            print(f"Error in save_averaged_template: {e}")
            return {"status": "error", "message": "An error occurred during saving."}


    # --- DELETED: The old learn_new_gesture method is removed ---

    def _recognize_custom(self, hand_landmarks):
        """
        Recognizes custom gestures by comparing to saved templates.
        Input: list of landmark_pb2.NormalizedLandmark
        """
        if not self.custom_gestures:
            return None
            
        try:
            live_template = self.normalize_landmarks(hand_landmarks) # Use public method
            
            min_dist = float('inf')
            best_match = None

            for name, template_data in self.custom_gestures.items():
                saved_template = np.array(template_data)
                distance = self._calculate_distance(live_template, saved_template)
                
                if distance < min_dist and distance < self.recognition_threshold:
                    min_dist = distance
                    best_match = name
            
            if best_match:
                return {
                    'gesture': best_match,
                    'confidence': 1.0 - (min_dist / self.recognition_threshold),
                    'handedness': 'Unknown'
                }
            return None
        except Exception as e:
            return None

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        if hasattr(self, 'recognizer'):
            self.recognizer.close()
            
    def process_frame(self):
        """Process a single frame and return frame with gesture result"""
        if not self.cap.isOpened():
            return None, None, None
            
        ret, frame = self.cap.read()
        if not ret:
            return None, None, None
            
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        self.frame_timestamp_ms = int(time.time() * 1000)

        try:
            recognition_result = self.recognizer.recognize_for_video(
                mp_image, 
                self.frame_timestamp_ms
            )
        except Exception as e:
            print(f"Error during recognition: {e}")
            return frame, None, None

        gesture_result = None
        landmarks_result = None
        annotated_image = frame.copy()
        
        if recognition_result.hand_landmarks:
            landmarks_result = recognition_result.hand_landmarks
            
            top_gesture = None
            text_color = _TEXT_COLOR
            
            if recognition_result.gestures and recognition_result.gestures[0]:
                top_gesture = recognition_result.gestures[0][0]
            
            if not top_gesture or top_gesture.category_name == 'None':
                custom_result = self._recognize_custom(landmarks_result[0])
                if custom_result:
                    gesture_result = custom_result
                    text_color = _CUSTOM_GESTURE_COLOR
                elif top_gesture:
                    gesture_result = {
                        'gesture': top_gesture.category_name,
                        'confidence': top_gesture.score,
                        'handedness': recognition_result.handedness[0][0].display_name
                    }
            else:
                gesture_result = {
                    'gesture': top_gesture.category_name,
                    'confidence': top_gesture.score,
                    'handedness': recognition_result.handedness[0][0].display_name
                }
                
            hand_landmarks = landmarks_result[0]
            self.draw_landmarks_on_image(annotated_image, hand_landmarks)
            
            if gesture_result:
                x_min = min([lm.x for lm in hand_landmarks]) * self.width
                y_min = min([lm.y for lm in hand_landmarks]) * self.height
                text_x = int(x_min) - _MARGIN
                text_y = int(y_min) - _MARGIN
                cv2.putText(annotated_image, f"{gesture_result['gesture']} ({gesture_result['confidence']:.2f})",
                            (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX,
                            _FONT_SIZE, text_color, _FONT_THICKNESS, cv2.LINE_AA)
            
        return annotated_image, gesture_result, landmarks_result

    def draw_landmarks_on_image(self, rgb_image, hand_landmarks):
        hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
        hand_landmarks_proto.landmark.extend([
            landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) 
            for landmark in hand_landmarks
        ])
        
        mp.solutions.drawing_utils.draw_landmarks(
            rgb_image,
            hand_landmarks_proto,
            mp.solutions.hands.HAND_CONNECTIONS,
            mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
            mp.solutions.drawing_styles.get_default_hand_connections_style()
        )