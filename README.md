

-----

# Gesture and Voice-Based HCI System for the Disabled Population

An innovative assistive technology designed to empower individuals with physical disabilities by enabling seamless computer interaction without the need for traditional input devices like a keyboard or mouse.

This system combines gesture recognition and offline voice command processing to perform various actions efficiently. Users can customize actions for predefined gestures and also add new gestures to suit their personal preferences. The system features a user-friendly interface that ensures ease of use and accessibility for all users.

By running completely offline, it ensures privacy, reliability, and independence from internet connectivity, making it ideal for real-world use in assistive environments.

## 🌟 Key Highlights

  * **Gesture Control:** Perform computer actions using hand movements.
  * **Voice Commands:** Execute tasks hands-free with offline voice recognition.
  * **Fully Customizable:** Easily map gestures and voice commands to specific actions.
  * **Learn New Gestures:** Train the system to recognize new, user-defined gestures.
  * **100% Offline:** All processing is done locally. No internet connection is required, ensuring privacy and reliability.
  * **Intuitive UI:** A user-friendly web interface for configuration and management.

-----

## 🏛️ System Architecture

The system operates on a decoupled, real-time architecture orchestrated by a Flask-SocketIO backend. All components run locally on the user's machine.

1.  **Input Layer:** The **Camera (OpenCV)** and **Microphone (Sounddevice)** capture raw video and audio streams.
2.  **Recognition Layer:**
      * Video is processed by the **Gesture Recognizer** (MediaPipe) to identify hand landmarks and classify gestures.
      * Audio is processed by the **Voice Recognizer** (Vosk) to transcribe speech to text.
3.  **Core Logic (`app.py`):** The main Flask server receives recognized gestures and text. It consults the `config.json` file to find the corresponding action.
4.  **Execution Layer (`action_executor.py`):** This module receives the action name (e.g., "click", "open\_browser") from the core logic and uses tools like PyAutoGUI to simulate mouse/keyboard inputs or run system commands.
5.  **Frontend (Web Interface):** A browser-based UI (HTML/CSS/JS) communicates with the Flask server via Socket.IO for real-time status updates and via HTTP API for configuration.

-----

## 🛠️ Technology Stack

  * **Backend:** Flask, Flask-SocketIO, Eventlet
  * **Gesture Recognition:** MediaPipe, OpenCV, NumPy
  * **Voice Recognition:** Vosk, Sounddevice
  * **System Control:** PyAutoGUI, pyttsx3, subprocess
  * **Frontend:** HTML, CSS, JavaScript (using Socket.IO client & Fetch API)

-----

## 🚀 Setup and Installation

### 1\. Prerequisites

  * **Python 3.10** (MediaPipe supports Python 3.9-3.11).
  * Make sure Python and `pip` are added to your system's PATH.

### 2\. Create Virtual Environment

Open your terminal in the project directory and run the following commands:

```bash
# Create a virtual environment named 'venv'
py -3.10 -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate
```

### 3\. Install Dependencies

With your virtual environment activated, install all the required Python packages:

```bash
pip install flask flask-socketio flask-cors opencv-python mediapipe pyautogui eventlet vosk sounddevice numpy pyttsx3
```

### 4\. Download Offline Voice Model (Vosk)

This system uses an offline model for voice recognition to ensure privacy.

1.  Go to the Vosk models page: [https://alphacephei.com/vosk/models](https://alphacephei.com/vosk/models)
2.  Download the **`vosk-model-small-en-us-0.15`** model.
3.  Extract the downloaded ZIP file.
4.  You will get a folder (e.g., `vosk-model-small-en-us-0.15`). **Rename this folder to exactly `vosk-model`**.
5.  Place this `vosk-model` folder inside the `static/models/` directory. The final path should be `static/models/vosk-model/`.

-----

## ▶️ How to Run the System

1.  Ensure your virtual environment is **activated**:
    ```bash
    venv\Scripts\activate
    ```
2.  Run the main application:
    ```bash
    python app.py
    ```
3.  Open your web browser and navigate to:
    ```
    http://127.0.0.1:5000
    ```
4.  Use the web interface to start the gesture and voice modules, customize mappings, and train new gestures.

-----

## ⚙️ How It Works

The system is broken down into several key Python modules.

### 1\. The Central Brain (`app.py`)

This is the main Flask application that:

  * 🌐 Runs the Flask web server to provide the `index.html` interface.
  * 🔁 Uses **Flask-SocketIO** for real-time, two-way communication between the frontend (browser) and backend (server).
  * 🎥 Manages the gesture recognition loop (`GestureRecognizer`).
  * 🎙️ Manages the voice recognition thread (`VoiceRecognizer`).
  * ⚡ Connects recognized commands to the `ActionExecutor`.
  * 🧩 Provides API endpoints for saving/loading configurations (`config.json`).

### 2\. Gesture Recognition (`gesture_recognition.py`)

This module uses **MediaPipe** to detect 21 hand landmarks from the camera feed.

#### Predefined Gestures

The system uses a pre-trained MediaPipe model (`gesture_recognizer.task`) to recognize common gestures (like *Click*, *Fist*, *Open\_Palm*) immediately.

#### New (Custom) Gestures

When a user trains a new gesture, a custom normalization and matching process is used:

1.  **Input:** The 21 hand landmarks (x, y, z) are captured.

2.  **Reference Points:** The wrist (landmark 0) and middle finger base (landmark 9) are used as references.

3.  **Translation:** All landmarks are moved so the wrist becomes the origin (0, 0, 0).

4.  **Scaling:** The distance between the wrist and middle finger base is used to normalize the hand size.

5.  **Flatten Array:** The 21 normalized landmarks are flattened into a single 1D array.

6.  **Training:** The system averages this flattened array over several samples and saves it as a template in `config.json`.

7.  **Recognition:** To recognize a custom gesture, the system calculates the **Mean Squared Error (MSE)** between the current (live) flattened array and all saved gesture templates.

    $$\text{MSE} = \frac{1}{n} \sum_{i=1}^{n} (Y_{\text{input}} - Y_{\text{template}})^2$$

    The gesture with the smallest MSE is chosen, but only if it's below a set threshold (e.g., `0.08`) to prevent false positives.

### 3\. Voice Recognition (`voice_recognition.py`)

  * Uses `sounddevice` to capture live audio from the microphone.
  * Feeds the audio stream directly into the offline **Vosk** model.
  * Vosk performs speech-to-text and returns the recognized command as a string.

### 4\. Action Executor (`action_executor.py`)

This module is the "hands" of the system. It receives an action name (e.g., `"click"`, `"copy"`) and performs the task on the host computer.

| Category | Example Actions | Tools Used |
| :--- | :--- | :--- |
| **Mouse** | `click`, `scroll`, `move_cursor` | `pyautogui` |
| **Keyboard** | `copy`, `paste`, `type_text` | `pyautogui` |
| **System** | `shutdown`, `lock_screen` | `os` / `subprocess` |
| **Apps** | `open_browser`, `open_notepad` | `subprocess`, `webbrowser` |
| **Accessibility**| `tell_time`, `read_screen` | `pyttsx3` |
| **Voice Typing**| `start/stop dictation` | `pyttsx3` + `pyautogui` |

### 5\. Frontend (`templates/index.html`, `static/js/main.js`)

The user interface is a web page built with **HTML** and **CSS**. All interactivity is powered by **JavaScript** (`main.js`).

  * Manages all frontend interactions (button clicks, toggles, tabs).
  * Connects to the backend via **Socket.IO** for real-time status updates (e.g., "Gesture Detected: *Click*").
  * Uses the **Fetch API** to send and receive data from the Flask API endpoints (e.g., saving new gesture mappings).
  * Dynamically updates the UI based on data received from the backend.

-----

## 📁 Project Structure

```
gesture-voice-hci/
│
├── app.py                  # Main Flask application (backend)
├── gesture_recognition.py  # Module for gesture detection logic
├── voice_recognition.py    # Module for voice command processing
├── action_executor.py      # Module for executing system actions
├── config.json             # Stores user settings, gestures, and mappings
├── requirements.txt        # Python dependencies
│
├── templates/
│   └── index.html          # Frontend web page (UI)
│
├── static/
│   ├── css/
│   │   └── style.css       # Styles for the UI
│   ├── js/
│   │   └── main.js         # Frontend JavaScript logic
│   └── models/
│       ├── vosk-model/     # (Place downloaded Vosk model here)
│       └── gesture_recognizer.task # Pre-trained MediaPipe gesture model
│
└── README.md               # This file
```

-----

## 🔌 Backend API & Real-time Events

### HTTP API Endpoints (`app.py`)

These are used for configuration and saving.

| Route | Method | Purpose |
| :--- | :--- | :--- |
| `/` | `GET` | Loads the web interface (`index.html`). |
| `/api/config` | `GET` | Returns the current `config.json` to the frontend. |
| `/api/config/settings` | `POST` | Updates camera/voice settings in `config.json`. |
| `/api/actions` | `GET` | Returns a list of all available system actions. |
| `/api/gestures` | `POST` | Updates the gesture-to-action mappings. |
| `/api/voice` | `POST` | Updates the voice-to-action mappings. |
| `/api/learn_gesture` | `POST` | Tells the backend to start learning a new gesture. |
| `/api/gesture/delete`| `POST` | Deletes a custom gesture from `config.json`. |

### Socket.IO Events (`main.js` & `app.py`)

These are used for real-time control and status updates.

| Feature | Frontend (`main.js`) | Backend (`app.py`) |
| :--- | :--- | :--- |
| **Start Gesture** | `socket.emit("start_gesture")` | Starts the gesture recognition loop. |
| **Stop Gesture** | `socket.emit("stop_gesture")` | Stops the gesture recognition loop. |
| **Start Voice** | `socket.emit("start_voice")` | Starts the voice recognition thread. |
| **Stop Voice** | `socket.emit("stop_voice")` | Stops the voice recognition thread. |
| **Video Feed** | `socket.on("video_feed", ...)` | `socket.emit("video_feed", ...)` (Sends image) |
| **Status Update**| `socket.on("status", ...)` | `socket.emit("status", ...)` (Sends log message) |

-----

## 🧑‍💻 Contributors

Developed by a Final Year B.Tech Computer Science Engineering student at VIT.

Focus areas: Human-Computer Interaction, Computer Vision, and Assistive Systems Engineering.

-----

## 🔮 Future Scope

  * **Eye-Tracking Integration:** Add eye-gaze tracking as another input method for mouse control.
  * **Expanded Language Support:** Integrate more Vosk models for non-English languages.
  * **Head Gesture Recognition:** Include head movements (nod, shake) as triggers for actions.
  * **Context-Aware Actions:** Develop a model that suggests actions based on the application currently in focus.
  * **Cross-Platform Executable:** Package the application (using PyInstaller or similar) into a single executable file for easier distribution.

-----

