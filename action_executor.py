"""
Action Executor Module using PyAutoGUI
Executes system-level actions: mouse, keyboard, voice, and accessibility features
for Multimodal Gesture and Voice HCI System
"""

import pyautogui
import time
import platform
import subprocess
import webbrowser
import os
import datetime
import pyttsx3


class ActionExecutor:
    def __init__(self):
        """Initialize action executor"""
        pyautogui.PAUSE = 0.05
        pyautogui.FAILSAFE = True
        self.os_type = platform.system()

        # Text-to-Speech for accessibility
        self.engine = pyttsx3.init()
        self.voice_typing = False  # Tracks dictation mode

        # --- Action map (gesture + voice) ---
        self.action_map = {
            # Mouse Actions
            'click': self.left_click,
            'left_click': self.left_click,
            'right_click': self.right_click,
            'double_click': self.double_click,
            'middle_click': self.middle_click,
            'scroll_up': self.scroll_up,
            'scroll_down': self.scroll_down,
            'move_cursor': self.move_cursor,

            # Keyboard Actions
            'press_enter': lambda: self.press_key('enter'),
            'press_space': lambda: self.press_key('space'),
            'press_tab': lambda: self.press_key('tab'),
            'press_escape': lambda: self.press_key('escape'),
            'press_delete': lambda: self.press_key('delete'),
            'press_backspace': lambda: self.press_key('backspace'),

            'copy': lambda: self.hotkey('ctrl', 'c'),
            'paste': lambda: self.hotkey('ctrl', 'v'),
            'cut': lambda: self.hotkey('ctrl', 'x'),
            'undo': lambda: self.hotkey('ctrl', 'z'),
            'redo': lambda: self.hotkey('ctrl', 'y'),
            'select_all': lambda: self.hotkey('ctrl', 'a'),
            'save': lambda: self.hotkey('ctrl', 's'),

            # Window Management
            'minimize_window': self.minimize_window,
            'maximize_window': self.maximize_window,
            'close_window': self.close_window,
            'switch_window': self.switch_window,
            'new_window': lambda: self.hotkey('ctrl', 'n'),
            'refresh': lambda: self.press_key('f5'),

            # Tabs & Browser Navigation
            'new_tab': lambda: self.hotkey('ctrl', 't'),
            'close_tab': lambda: self.hotkey('ctrl', 'w'),
            'next_tab': lambda: self.hotkey('ctrl', 'tab'),
            'previous_tab': lambda: self.hotkey('ctrl', 'shift', 'tab'),

            # Applications
            'open_browser': self.open_browser,
            'close_browser': self.close_browser,
            'open_file_explorer': self.open_file_explorer,
            'open_notepad': self.open_notepad,
            'open_settings': self.open_settings,
            'open_mail': self.open_mail,

            # System Actions
            'screenshot': self.take_screenshot,
            'lock_screen': self.lock_screen,
            'shutdown': self.shutdown,
            'restart': self.restart,

            # Volume & Brightness
            'volume_up': self.volume_up,
            'volume_down': self.volume_down,
            'volume_mute': self.volume_mute,
            'brightness_up': self.brightness_up,
            'brightness_down': self.brightness_down,

            # Zoom & Accessibility
            'zoom_in': self.zoom_in,
            'zoom_out': self.zoom_out,
            'read_screen': self.read_screen,
            'tell_time': self.tell_time,
            'tell_date': self.tell_date,

            # Dictation / Voice Typing
            'start_voice_typing': self.start_voice_typing,
            'stop_voice_typing': self.stop_voice_typing,

            # Special Actions
            'toggle_cursor': self.toggle_cursor
        }

    # ============================================================
    # ----------------------- Core Executor ----------------------
    # ============================================================
    def execute(self, action_name, params=None):
        """Execute an action by name"""
        if not action_name:
            return False

        action_name = action_name.lower().replace(' ', '_')
        action_func = self.action_map.get(action_name)

        if action_func:
            try:
                # Toggle cursor handled elsewhere
                if action_name == 'toggle_cursor':
                    return True

                # Handle dynamic params (like move_cursor)
                if params:
                    action_func(**params)
                else:
                    action_func()

                print(f"✅ Executed action: {action_name}")
                return True
            except Exception as e:
                print(f"❌ Error executing action '{action_name}': {e}")
                return False
        else:
            print(f"⚠️ Unknown action: {action_name}")
            return False

    # ============================================================
    # ------------------------- Mouse ----------------------------
    # ============================================================
    def left_click(self): pyautogui.click()
    def right_click(self): pyautogui.rightClick()
    def double_click(self): pyautogui.doubleClick()
    def middle_click(self): pyautogui.middleClick()
    def scroll_up(self, amount=3): pyautogui.scroll(amount * 100)
    def scroll_down(self, amount=3): pyautogui.scroll(-amount * 100)

    def move_cursor(self, x=None, y=None):
        """Move cursor — controlled externally via gesture coordinates"""
        if x is not None and y is not None:
            pyautogui.moveTo(x, y)

    # ============================================================
    # ----------------------- Keyboard ---------------------------
    # ============================================================
    def press_key(self, key): pyautogui.press(key)
    def hotkey(self, *keys): pyautogui.hotkey(*keys)
    def type_text(self, text): pyautogui.write(text, interval=0.05)

    # ============================================================
    # ------------------ Window / System Mgmt --------------------
    # ============================================================
    def minimize_window(self):
        if self.os_type == 'Windows': self.hotkey('win', 'down')
        elif self.os_type == 'Darwin': self.hotkey('command', 'm')
        else: self.hotkey('super', 'h')

    def maximize_window(self):
        if self.os_type == 'Windows': self.hotkey('win', 'up')
        elif self.os_type == 'Darwin': self.hotkey('f')
        else: self.hotkey('super', 'up')

    def close_window(self):
        if self.os_type == 'Windows': self.hotkey('alt', 'f4')
        elif self.os_type == 'Darwin': self.hotkey('command', 'w')
        else: self.hotkey('alt', 'f4')

    def switch_window(self):
        if self.os_type in ['Windows', 'Linux']: self.hotkey('alt', 'tab')
        elif self.os_type == 'Darwin': self.hotkey('command', 'tab')

    # ============================================================
    # ---------------------- Applications ------------------------
    # ============================================================
    def open_browser(self): webbrowser.open("https://google.com")

    def close_browser(self):
        """Close browser (supports Chrome/Edge)"""
        try:
            if self.os_type == 'Windows':
                os.system("taskkill /IM chrome.exe /F")
                os.system("taskkill /IM msedge.exe /F")
            elif self.os_type == 'Linux':
                os.system("pkill chrome")
            else:
                os.system("osascript -e 'quit app \"Google Chrome\"'")
        except Exception as e:
            print(f"Browser close failed: {e}")

    def open_file_explorer(self):
        if self.os_type == 'Windows': self.hotkey('win', 'e')
        elif self.os_type == 'Darwin': subprocess.Popen(['open', '/'])
        else: subprocess.Popen(['xdg-open', '/home'])

    def open_notepad(self):
        if self.os_type == 'Windows': subprocess.Popen(['notepad.exe'])
        elif self.os_type == 'Darwin': subprocess.Popen(['open', '-a', 'TextEdit'])
        else: subprocess.Popen(['gedit'])

    def open_settings(self):
        if self.os_type == 'Windows': subprocess.Popen('start ms-settings:', shell=True)
        elif self.os_type == 'Darwin': subprocess.Popen(['open', '-a', 'System Settings'])
        else: subprocess.Popen(['gnome-control-center'])

    def open_mail(self):
        """Open Gmail in browser"""
        webbrowser.open("https://mail.google.com")

    # ============================================================
    # ------------------- System-Level Actions -------------------
    # ============================================================
    def take_screenshot(self):
        filename = f"screenshot_{time.strftime('%Y%m%d-%H%M%S')}.png"
        pyautogui.screenshot(filename)
        self.engine.say("Screenshot taken")
        self.engine.runAndWait()
        print(f"📸 Saved {filename}")

    def lock_screen(self):
        if self.os_type == 'Windows': self.hotkey('win', 'l')
        elif self.os_type == 'Darwin': self.hotkey('command', 'control', 'q')
        else: self.hotkey('super', 'l')

    def shutdown(self):
        if self.os_type == 'Windows': os.system("shutdown /s /t 1")
        elif self.os_type == 'Linux': os.system("shutdown now")
        else: os.system("osascript -e 'tell app \"System Events\" to shut down'")

    def restart(self):
        if self.os_type == 'Windows': os.system("shutdown /r /t 1")
        elif self.os_type == 'Linux': os.system("reboot")
        else: os.system("osascript -e 'tell app \"System Events\" to restart'")

    # ============================================================
    # ---------------- Volume & Brightness -----------------------
    # ============================================================
    def volume_up(self): pyautogui.press('volumeup')
    def volume_down(self): pyautogui.press('volumedown')
    def volume_mute(self): pyautogui.press('volumemute')

    def brightness_up(self):
        try: pyautogui.press('brightnessup')
        except: print("Brightness control not supported.")

    def brightness_down(self):
        try: pyautogui.press('brightnessdown')
        except: print("Brightness control not supported.")

    # ============================================================
    # -------------------- Accessibility -------------------------
    # ============================================================
    def zoom_in(self): pyautogui.hotkey('ctrl', '+')
    def zoom_out(self): pyautogui.hotkey('ctrl', '-')

    def read_screen(self):
        """Placeholder for text-to-speech screen reading"""
        self.engine.say("Screen reading feature not fully implemented yet.")
        self.engine.runAndWait()

    def tell_time(self):
        now = datetime.datetime.now().strftime("%I:%M %p")
        self.engine.say(f"The time is {now}")
        self.engine.runAndWait()

    def tell_date(self):
        today = datetime.date.today().strftime("%B %d, %Y")
        self.engine.say(f"Today is {today}")
        self.engine.runAndWait()

    # ============================================================
    # ------------------- Dictation Mode -------------------------
    # ============================================================
    def start_voice_typing(self):
        """Activate voice typing mode"""
        self.voice_typing = True
        self.engine.say("Voice typing enabled. Speak now.")
        self.engine.runAndWait()
        print("🎙️ Voice typing started")

    def stop_voice_typing(self):
        """Stop voice typing mode"""
        self.voice_typing = False
        self.engine.say("Voice typing stopped.")
        self.engine.runAndWait()
        print("🛑 Voice typing stopped")

    # ============================================================
    # --------------------- Special ------------------------------
    # ============================================================
    def toggle_cursor(self):
        """Handled externally in app.py"""
        pass
