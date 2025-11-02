```markdown
# Gesture and Voice-Based Human-Computer Interaction (HCI) System

### Accessibility-Focused Assistive AI for People with Physical Disabilities

---

## 🏷️ Badges

![Python](https://img.shields.io/badge/Python-3.10-blue.svg)
![Flask](https://img.shields.io/badge/Flask-Framework-black.svg)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Hand_Tracking-orange.svg)
![Vosk](https://img.shields.io/badge/Vosk-Offline_STT-brightgreen.svg)
![PyAutoGUI](https://img.shields.io/badge/PyAutoGUI-Automation-yellow.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

---

## 🧠 Overview

The Gesture and Voice-Based Human-Computer Interaction (HCI) System is an assistive technology designed to empower individuals with physical disabilities by enabling seamless computer interaction without relying on a keyboard or mouse.

It combines gesture recognition and offline voice command processing to allow customizable, private, and efficient accessibility. Users can map gestures to actions, train new gestures, and control the computer using offline voice recognition — ensuring functionality even without internet connectivity.

---

## 🌟 Key Highlights

- Gesture control for performing computer actions  
- Voice command support for hands-free operation  
- Customizable gesture-action mappings  
- Ability to add and train new gestures  
- Fully offline operation for privacy and accessibility  
- Intuitive and user-friendly interface for every user  

---

## 🧩 System Architecture

```
gesture-voice-hci/
│
├── app.py                     # Main Flask application (central controller)
├── gesture_recognition.py     # Handles hand gesture detection and classification
├── voice_recognition.py       # Offline speech-to-text processing using Vosk
├── action_executor.py         # Executes system actions mapped to gestures/voice
├── config.json                # Stores user settings and gesture mappings
├── requirements.txt           # All dependencies
│
├── templates/
│   └── index.html             # Web interface
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── models/
│       ├── vosk-model/             # Vosk offline model
│       └── gesture_recognizer.task # Pretrained MediaPipe model
│
└── README.md
```

---

## ⚙️ Installation Guide

### 1. Prerequisites

Ensure Python 3.10 is installed (MediaPipe supports Python 3.9–3.11).  
Then open your terminal and follow:

```
py -3.10 -m venv venv
venv\Scripts\activate
```

### 2. Install Required Packages

```
pip install flask flask-socketio flask-cors opencv-python mediapipe pyautogui eventlet vosk sounddevice numpy pyttsx3
```

Alternatively, install all dependencies using:

```
pip install -r requirements.txt
```

### 3. Download the Vosk Model

Download **vosk-model-small-en-us-0.15** from [Vosk Models](https://alphacephei.com/vosk/models).  
Extract and place it inside:

```
static/models/vosk-model/
```

---

## 🚀 Running the Application

```
python app.py
```

Then open the browser and access:

```
http://127.0.0.1:5000/
```

---

## 🧩 System Workflow

![System Architecture Preview](https://via.placeholder.com/900x400.png?text=System+Architecture+Overview)
*Description: Flow diagram showing gesture and voice input connected to Flask backend, then action execution module.*

---

## 🖐️ Gesture Recognition Module

### How It Works

1. Captures 21 hand landmarks using MediaPipe.  
2. Normalizes, translates, scales, and flattens coordinates.  
3. Classifies using predefined and custom gestures stored locally.  
4. Custom gestures are compared via Mean Squared Error (MSE).  

When a gesture is shown:
- The system computes MSE for each template.
- The gesture with the lowest value (< 0.08) is selected.

### Training New Gestures

1. Capture multiple samples.  
2. Average all landmark arrays:  
   ```
   gesture_name = [flattened normalized landmark array]
   ```
3. Store for matching future gestures.

---

## 🎙️ Voice Recognition Module

### Process Flow

- Audio input captured using the sounddevice library.  
- Speech converted to text using Vosk offline STT.  
- Commands passed to the Action Executor.  
- Voice feedback provided through pyttsx3 (TTS).  

This enables fully offline speech-based system control.

---

## ⚡ Action Executor Module

### Description

Handles execution of computer-level tasks such as mouse actions, keyboard shortcuts, application launch, accessibility tools, and voice typing.

| Category | Example Actions | Tools Used |
|-----------|-----------------|-------------|
| Mouse | click, scroll, move_cursor | PyAutoGUI |
| Keyboard | copy, paste, type_text | PyAutoGUI |
| System | shutdown, lock_screen | OS/System |
| Apps | open_browser, open_notepad | subprocess/webbrowser |
| Accessibility | tell_time, read_screen | pyttsx3 |
| Voice Typing | start/stop dictation | pyttsx3 + PyAutoGUI |

**Flow:**  
Gesture or voice command → recognized action → system executes via ActionExecutor.

---

## 🌐 Flask Backend (app.py)

### Responsibilities

- Runs Flask webserver and UI  
- Manages real-time communication via Flask-SocketIO  
- Runs gesture and voice recognition loops  
- Executes mapped actions  
- Provides REST API endpoints for configuration and gesture management  
- Maintains user gesture library and mappings  

### Why Socket.IO?

Provides two-way, real-time communication between browser and backend for instant updates.

---

## 🔗 API Endpoints

| Route | Method | Purpose |
|--------|---------|----------|
| `/` | GET | Load web interface |
| `/api/config` | GET | Retrieve config JSON |
| `/api/config/settings` | POST | Update camera/voice settings |
| `/api/actions` | GET | List available system actions |
| `/api/gestures` | POST | Update gesture-action mappings |
| `/api/voice` | POST | Update voice-action mappings |
| `/api/learn_gesture` | POST | Start learning new gesture |
| `/api/gesture/delete` | POST | Delete custom gesture |

---

## 💻 Frontend (main.js & index.html)

- Handles all user interactions, buttons, and configuration inputs  
- Connects via Socket.IO for real-time updates  
- Fetches and posts API requests for gestures, voice, and settings  
- Dynamically updates the video feed and gesture list on-screen  

| Feature | Frontend Call | Backend Action |
|----------|----------------|----------------|
| Start Gesture | socket.emit("start_gesture") | Begins recognition loop |
| Stop Gesture | socket.emit("stop_gesture") | Stops recognition |
| Start Voice | socket.emit("start_voice") | Starts Vosk recognition |
| Stop Voice | socket.emit("stop_voice") | Stops recognition |
| Learn Gesture | POST /api/learn_gesture | Activates training mode |
| Delete Gesture | POST /api/gesture/delete | Removes mapping |
| Save Config | POST /api/config/settings | Saves updated config |
| Get Config | GET /api/config | Returns settings JSON |

---

## 🎞️ Demonstration Preview

### Installation and Setup Preview
![Installation Preview](https://via.placeholder.com/900x400.png?text=Installation+and+Running+Demo)
*Description: Screenshot showing terminal with Flask server running and localhost open on browser.*

### Gesture and Voice Demo
![Demo Image](https://via.placeholder.com/900x400.png?text=Real-Time+Gesture+%26+Voice+Control)
*Description: Example scene where user performs a gesture and the system triggers corresponding computer action.*

---

## 🧠 Concept Flow Summary

1. Gesture Recognizer captures real-time hand input.  
2. Voice Recognizer processes speech commands.  
3. Action Executor performs mapped system actions.  
4. Flask server and Socket.IO connect backend to frontend dynamically.  
5. Interface updates continuously for accessibility feedback.

---

## 🔒 Advantages

- Completely offline operation for unmatched privacy.  
- Custom gestures and voice command mappings per user.  
- Real-time assistive interaction.  
- Cross-platform support with minimal setup.  
- Light, modular, and easily extensible architecture.

---

## 🧾 Future Enhancements

- Integration with eye-tracking and facial expression recognition.  
- Multilingual voice recognition model.  
- Gesture cloud backup and sharing support.  
- AI-based adaptive gesture-learning system.

---

## 🧑‍💻 Contributors

Developed by a Final Year B.Tech Computer Science Engineering student at VIT.  
Focus areas include Human-Computer Interaction, Computer Vision, and Assistive Systems Engineering.

---

## 🧩 License

This project is released under the MIT License.  
Feel free to modify and enhance for educational or assistive technology purposes.

---
```
