"""
Main Flask Application for Real Gesture and Voice HCI System
Handles web server, WebSocket connections, and coordinates all modules
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import cv2
import base64
import json
import threading
import time
import eventlet
eventlet.monkey_patch() 

import pyautogui
from gesture_recognition import GestureRecognizer 
from voice_recognition import VoiceRecognizer
from action_executor import ActionExecutor

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'gesture-voice-hci-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Initialize modules
action_executor = ActionExecutor()
gesture_recognizer = None
voice_recognizer = None

SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()

# Global state
app_state = {
    'gesture_enabled': False,
    'voice_enabled': False,
    'camera_active': False,
    'cursor_enabled': False,
    'last_gesture': None,
    'last_command': None,
    'statistics': {
        'gestures_recognized': 0,
        'commands_recognized': 0,
        'actions_executed': 0
    }
}

# --- MODIFIED: State for Learning Gestures ---
config_lock = threading.Lock()
learning_mode = False
new_gesture_name = None
learning_status = {"status": "idle", "message": ""}
learning_samples = []
TARGET_SAMPLES = 30 # Set to 30 for speed, you can change this to 50
# --- END MODIFIED ---


# --- Configuration Management (Unchanged) ---
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("config.json not found, creating a default one.")
        default_config = get_default_config()
        save_config(default_config)
        return default_config
    except json.JSONDecodeError:
        print("Error reading config.json, it might be corrupted. Using default.")
        return get_default_config()

def save_config(new_config):
    global config
    try:
        with open('config.json', 'w') as f:
            json.dump(new_config, f, indent=2)
        config = new_config 
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_default_config():
    return {
        "settings": { "camera_index": 0, "camera_width": 640, "camera_height": 480, "gesture_cooldown": 0.5, "voice_cooldown": 0.5, "voice_sample_rate": 16000 },
        "gestures": { "Thumb_Up": { "name": "Thumbs Up", "action": "click" } },
        "voice_commands": { "click": { "command": "click", "action": "click" } },
        "custom_gesture_data": {}
    }

config = load_config()

# --- HTTP Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/api/config', methods=['GET'])
def get_config_api():
    return jsonify(config)

@app.route('/api/config/settings', methods=['POST'])
def update_settings():
    global config
    try:
        new_settings = request.json.get('settings')
        if new_settings:
            with config_lock:
                config['settings'].update(new_settings)
                save_config(config)
            
            if app_state['gesture_enabled']:
                handle_stop_gesture()
                socketio.sleep(0.5) 
                handle_start_gesture()
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'No settings found in request'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/actions', methods=['GET'])
def get_actions():
    action_list = list(action_executor.action_map.keys())
    return jsonify(action_list)

@app.route('/api/gestures', methods=['POST'])
def update_gestures():
    global config
    try:
        new_gestures = request.json
        with config_lock:
            for gesture_name, action_name in new_gestures.items():
                if gesture_name in config['gestures']:
                    config['gestures'][gesture_name]['action'] = action_name if action_name != "null" else None
                else:
                    config['gestures'][gesture_name] = {"name": gesture_name, "action": action_name if action_name != "null" else None}
            
            if save_config(config):
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Failed to save config'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/voice', methods=['POST'])
def update_voice_commands():
    global config
    try:
        new_commands = request.json
        with config_lock:
            for command_key, action_name in new_commands.items():
                if command_key in config['voice_commands']:
                    config['voice_commands'][command_key]['action'] = action_name if action_name != "null" else None
            
            if save_config(config):
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Failed to save config'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# --- MODIFIED: Routes for Learning Gestures ---
@app.route('/api/learn_gesture', methods=['POST'])
def learn_gesture_route():
    global learning_mode, new_gesture_name, learning_status, config, learning_samples
    
    data = request.json
    gesture_name = data.get('name')
    
    if not gesture_name:
        return jsonify({"status": "error", "message": "Gesture name is required."}), 400
    
    with config_lock:
        if gesture_name in config['gestures'] or gesture_name in config['custom_gesture_data']:
            return jsonify({"status": "error", "message": "This name is already used. Please choose another."}), 400

    learning_mode = True
    new_gesture_name = gesture_name
    learning_samples = [] # Reset sample list
    learning_status = {"status": "learning", "message": f"Learning '{gesture_name}'. Go to Dashboard and hold pose..."}
    
    print(f"Starting to learn gesture: {gesture_name}")
    return jsonify(learning_status)

@app.route('/api/get_learning_status', methods=['GET'])
def get_learning_status():
    global learning_status
    return jsonify(learning_status)

# --- NEW: Route for Deleting Gestures ---
@app.route('/api/gesture/delete', methods=['POST'])
def delete_gesture():
    global config
    data = request.json
    gesture_name = data.get('name')
    
    if not gesture_name:
        return jsonify({'success': False, 'error': 'No gesture name provided.'}), 400
    
    with config_lock:
        config = load_config() # Load fresh config
        
        # Check if it's a built-in gesture (cannot be deleted)
        if gesture_name in config['gestures'] and config['gestures'][gesture_name]['name'] != gesture_name:
            return jsonify({'success': False, 'error': 'Cannot delete a built-in gesture.'}), 400
        
        # Delete from both mappings and data
        deleted_from_gestures = config['gestures'].pop(gesture_name, None)
        deleted_from_data = config['custom_gesture_data'].pop(gesture_name, None)
        
        if deleted_from_gestures is None and deleted_from_data is None:
            return jsonify({'success': False, 'error': 'Gesture not found.'}), 404

        if save_config(config):
            print(f"Deleted custom gesture: {gesture_name}")
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to save config after deletion.'}), 500
# --- END NEW ---


# --- Socket.IO Events (handle_start_gesture is modified) ---
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('status', {
        'gesture_enabled': app_state['gesture_enabled'],
        'voice_enabled': app_state['voice_enabled']
    })

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('start_gesture')
def handle_start_gesture():
    global gesture_recognizer, app_state
    try:
        if not app_state['gesture_enabled']:
            with config_lock:
                current_config = load_config() # Load fresh config for recognizer
                camera_index = current_config['settings']['camera_index']
                width = current_config['settings']['camera_width']
                height = current_config['settings']['camera_height']
            
            gesture_recognizer = GestureRecognizer(
                camera_index=camera_index, width=width, height=height, config=current_config
            )
            app_state['gesture_enabled'] = True
            app_state['camera_active'] = True
            socketio.start_background_task(target=gesture_loop)
            emit('gesture_status', {'message': 'Gesture recognition started'})
    except Exception as e:
        print(f"Error starting gesture recognition: {e}")
        emit('error', {'message': f'Failed to start gesture recognition: {str(e)}'})

@socketio.on('stop_gesture')
def handle_stop_gesture():
    global gesture_recognizer, app_state, learning_mode, learning_samples
    app_state['gesture_enabled'] = False
    app_state['cursor_enabled'] = False
    learning_mode = False # Stop learning
    learning_samples = [] # Clear samples
    if gesture_recognizer:
        gesture_recognizer.stop()
        gesture_recognizer = None
    emit('gesture_status', {'message': 'Gesture recognition stopped'})

@socketio.on('start_voice')
def handle_start_voice():
    # (Unchanged)
    global voice_recognizer, app_state
    try:
        if not app_state['voice_enabled']:
            with config_lock:
                current_config = load_config()
                model_path = 'static/models/vosk-model'
                sample_rate = current_config['settings']['voice_sample_rate']
            
            voice_recognizer = VoiceRecognizer(
                model_path=model_path, sample_rate=sample_rate, config=current_config
            )
            app_state['voice_enabled'] = True
            socketio.start_background_task(target=voice_loop)
            emit('voice_status', {'message': 'Voice recognition started'})
    except Exception as e:
        print(f"Error starting voice recognition: {e}")
        emit('error', {'message': f'Failed to start voice recognition: {str(e)}'})

@socketio.on('stop_voice')
def handle_stop_voice():
    # (Unchanged)
    global voice_recognizer, app_state
    app_state['voice_enabled'] = False
    if voice_recognizer:
        voice_recognizer.stop()
        voice_recognizer = None
    emit('voice_status', {'message': 'Voice recognition stopped'})


# --- HEAVILY MODIFIED: Background Loops ---

def gesture_loop():
    """
    Main loop for gesture recognition.
    MODIFIED to support sample-based learning.
    """
    global gesture_recognizer, app_state, config
    global learning_mode, new_gesture_name, learning_status, learning_samples
    
    last_gesture_time = 0
    with config_lock:
        cooldown = config['settings']['gesture_cooldown']
    prev_x, prev_y = 0, 0
    smoothing = 0.7 

    while app_state['gesture_enabled']:
        try:
            if gesture_recognizer is None: break
            
            frame, gesture_result, landmarks_result = gesture_recognizer.process_frame()
            
            if frame is None:
                socketio.sleep(0.1)
                continue
            
            # --- LEARNING MODE LOGIC ---
            if learning_mode:
                status_msg = ""
                if landmarks_result:
                    # 1. Check for conflict with BUILT-IN gestures
                    if gesture_result and gesture_result['gesture'] != 'None':
                        status_msg = f"Conflict: Too similar to '{gesture_result['gesture']}'. Try a different pose."
                        learning_status = {"status": "error", "message": status_msg}
                        learning_samples = [] # Reset samples on conflict
                        cv2.putText(frame, status_msg, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    # 2. No conflict, collect sample
                    else:
                        normalized_landmarks = gesture_recognizer.normalize_landmarks(landmarks_result[0])
                        learning_samples.append(normalized_landmarks)
                        
                        sample_count = len(learning_samples)
                        status_msg = f"Hold still... ({sample_count}/{TARGET_SAMPLES})"
                        learning_status["message"] = status_msg # Update polling status
                        cv2.putText(frame, status_msg, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

                        # 3. Check if we are done collecting
                        if sample_count >= TARGET_SAMPLES:
                            print(f"Collected {sample_count} samples. Averaging and saving...")
                            result = gesture_recognizer.save_averaged_template(learning_samples, new_gesture_name)
                            
                            if result["status"] == "success":
                                with config_lock:
                                    config['gestures'][new_gesture_name] = {"name": new_gesture_name, "action": None}
                                    save_config(config)
                                learning_status = {"status": "success", "message": result["message"]}
                                print(f"Successfully learned: {new_gesture_name}")
                            
                            else:
                                # Failed (e.g., too similar to custom gesture)
                                learning_status = {"status": "error", "message": result["message"]}
                                print(f"Failed to learn: {result['message']}")

                            # Reset learning mode
                            learning_mode = False
                            new_gesture_name = None
                            learning_samples = []
                
                else:
                    # No hand detected
                    status_msg = learning_status["message"]
                    cv2.putText(frame, status_msg, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 150, 255), 2)

            # --- NORMAL OPERATION LOGIC (NOW IN 'ELSE') ---
            else:
                if app_state['cursor_enabled'] and landmarks_result:
                    try:
                        index_finger_tip = landmarks_result[0][8] 
                        x = int(index_finger_tip.x * SCREEN_WIDTH)
                        y = int(index_finger_tip.y * SCREEN_HEIGHT)
                        smooth_x = int(prev_x + (x - prev_x) * (1 - smoothing))
                        smooth_y = int(prev_y + (y - prev_y) * (1 - smoothing))
                        pyautogui.moveTo(smooth_x, smooth_y)
                        prev_x, prev_y = smooth_x, smooth_y
                    except Exception as e:
                        pass 
                
                if gesture_result and gesture_result['gesture']:
                    current_time = time.time()
                    gesture_name = gesture_result['gesture']
                    
                    if (current_time - last_gesture_time >= cooldown) and (gesture_name != 'None'):
                        confidence = gesture_result['confidence']
                        action = get_gesture_action(gesture_name) 
                        
                        if action == 'toggle_cursor':
                            app_state['cursor_enabled'] = not app_state['cursor_enabled']
                            cursor_status = "ON" if app_state['cursor_enabled'] else "OFF"
                            print(f"Cursor Mode Toggled: {cursor_status}")
                            socketio.emit('gesture_recognized', {
                                'gesture': gesture_name, 'confidence': confidence, 'action': f'Cursor Mode {cursor_status}'
                            })
                            app_state['statistics']['gestures_recognized'] += 1
                        
                        elif action and not app_state['cursor_enabled']:
                            success = action_executor.execute(action)
                            if success:
                                app_state['statistics']['actions_executed'] += 1
                            socketio.emit('gesture_recognized', {
                                'gesture': gesture_name, 'confidence': confidence, 'action': action
                            })
                            app_state['statistics']['gestures_recognized'] += 1
                        
                        last_gesture_time = current_time

            # --- ENDIF learning_mode ---
            
            _, buffer = cv2.imencode('.jpg', frame)
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            socketio.emit('video_frame', {'frame': jpg_as_text})
            
            socketio.sleep(0.01)
            
        except Exception as e:
            print(f"Error in gesture loop: {e}")
            app_state['gesture_enabled'] = False 

    print("Gesture loop stopped.")


def voice_loop():
    # (Unchanged)
    global voice_recognizer, app_state
    
    with config_lock:
        cooldown = load_config()['settings']['voice_cooldown']
        
    last_command_time = 0
    
    while app_state['voice_enabled']:
        try:
            if voice_recognizer is None: break
            result = voice_recognizer.recognize()
            
            if result and result.get('text') and result.get('final', True):
                current_time = time.time()
                
                if current_time - last_command_time >= cooldown:
                    command_text = result['text']
                    app_state['statistics']['commands_recognized'] += 1
                    action = get_voice_action_robust(command_text)
                    
                    if action:
                        success = action_executor.execute(action)
                        if success:
                            app_state['statistics']['actions_executed'] += 1
                    
                    socketio.emit('voice_recognized', {
                        'text': command_text,
                        'confidence': result.get('confidence', 1.0),
                        'action': action or 'None'
                    })
                    last_command_time = current_time
            
            socketio.sleep(0.1)
        except Exception as e:
            print(f"Error in voice loop: {e}")

    print("Voice loop stopped.")


# --- Action Mapping (Unchanged) ---
def get_gesture_action(gesture_name):
    with config_lock:
        if gesture_name in config.get('gestures', {}):
            return config['gestures'][gesture_name].get('action')
    return None

def get_voice_action_robust(spoken_text):
    spoken_text = spoken_text.lower().strip()
    if not spoken_text:
        return None

    spoken_words = set(spoken_text.split())
    best_match_action = None
    highest_match_count = 0

    with config_lock:
        commands = config.get('voice_commands', {}).values()
    
    for cmd_data in commands:
        command_to_check = cmd_data.get('command', '').lower()
        if not command_to_check:
            continue
        command_words = command_to_check.split()
        if all(word in spoken_words for word in command_words):
            if len(command_words) > highest_match_count:
                highest_match_count = len(command_words)
                best_match_action = cmd_data.get('action')
    return best_match_action

if __name__ == '__main__':
    print("="*60)
    print("Gesture and Voice HCI System - Starting...")
    print("="*60)
    print(f"Server will run on: http://127.0.0.1:5000")
    print("Open this URL in your browser.")
    print("Press Ctrl+C to stop")
    print("="*60)
    
    socketio.run(app, host='127.0.0.1', port=5000, debug=False, use_reloader=False)