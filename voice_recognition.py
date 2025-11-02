"""
Voice Recognition Module using Vosk (Offline)
Captures microphone audio and recognizes speech without internet
"""

import json
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer

class VoiceRecognizer:
    def __init__(self, model_path='static/models/vosk-model', sample_rate=16000, config=None):
        """Initialize Vosk voice recognizer"""
        
        try:
            print(f"Loading Vosk model from: {model_path}")
            self.model = Model(model_path)
            print("Vosk model loaded successfully")
        except Exception as e:
            raise Exception(f"Failed to load Vosk model: {e}. "
                          f"Please download from https://alphacephei.com/vosk/models")
        
        self.sample_rate = sample_rate
        self.config = config or {}
        self.recognizer = KaldiRecognizer(self.model, sample_rate)
        self.audio_queue = queue.Queue()
        
        self.stream = sd.RawInputStream(
            samplerate=sample_rate,
            blocksize=8000,
            dtype='int16',
            channels=1,
            callback=self._audio_callback
        )
        self.stream.start()
        self.running = True
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream"""
        if status:
            print(f"Audio stream status: {status}")
        self.audio_queue.put(bytes(indata))
    
    def recognize(self):
        """Recognize speech from microphone"""
        if not self.running:
            return None
        
        try:
            if not self.audio_queue.empty():
                data = self.audio_queue.get_nowait()
                
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '')
                    
                    if text:
                        return {
                            'text': text,
                            'confidence': 1.0,
                            'final': True
                        }
                else:
                    partial = json.loads(self.recognizer.PartialResult())
                    partial_text = partial.get('partial', '')
                    
                    if partial_text:
                        return {
                            'text': partial_text,
                            'confidence': 0.5,
                            'final': False
                        }
        
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Error in voice recognition: {e}")
        
        return None
    
    def stop(self):
        """Stop the recognizer and release resources"""
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()