import speech_recognition as sr
import pyttsx3
from utils import log

class SpeechEngine:
    """
    Manages Text-To-Speech (TTS) operations.
    Should be instantiated and run inside the assistant background thread
    to avoid COM threading model collisions on Windows.
    """
    def __init__(self):
        log("SpeechEngine", "Initializing pyttsx3 TTS engine...")
        try:
            self.engine = pyttsx3.init()
            # Set standard rate (default is 200, 175-180 is usually more natural)
            self.engine.setProperty('rate', 175)
            
            # Select voice: prefer a female or clean voice if available, otherwise default
            voices = self.engine.getProperty('voices')
            if voices:
                # Try to find a female voice (usually voice index 1 on Windows)
                chosen_voice = voices[0]
                for v in voices:
                    if "female" in v.name.lower() or "zira" in v.name.lower():
                        chosen_voice = v
                        break
                self.engine.setProperty('voice', chosen_voice.id)
                log("SpeechEngine", f"Selected voice: {chosen_voice.name}")
        except Exception as e:
            log("SpeechEngine", f"Failed to initialize TTS engine: {e}")
            self.engine = None

    def speak(self, text: str) -> None:
        """
        Synthesizes speech for the provided text.
        Blocks until speaking is done.
        """
        if not self.engine:
            log("SpeechEngine", "TTS Engine not available. Speech skipped.")
            return
        
        log("SpeechEngine", f"Speaking: '{text}'")
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            log("SpeechEngine", f"Error during speaking: {e}")


class SpeechListener:
    """
    Manages Speech-To-Text (STT) operations via speech_recognition.
    """
    def __init__(self):
        log("SpeechListener", "Initializing speech recognizer...")
        self.recognizer = sr.Recognizer()
        
        # Fine-tune recognizer parameters for better responsiveness
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8  # seconds of silence before considering a phrase complete
        
        self.mic = None
        self.mic_available = False
        
        # Attempt to initialize the microphone
        try:
            # We list microphones to check if any are present
            mics = sr.Microphone.list_microphone_names()
            if not mics:
                log("SpeechListener", "No microphone devices found on this system.")
            else:
                self.mic = sr.Microphone()
                self.mic_available = True
                log("SpeechListener", "Microphone initialized successfully.")
        except Exception as e:
            log("SpeechListener", f"Microphone initialization failed (possibly PyAudio missing): {e}")

    def adjust_for_ambient_noise(self) -> None:
        """
        Adjusts the recognizer's energy threshold based on ambient room noise.
        """
        if not self.mic_available or not self.mic:
            log("SpeechListener", "Cannot adjust for ambient noise: Microphone not available.")
            return
            
        log("SpeechListener", "Calibrating microphone for ambient noise... (1 second)")
        try:
            with self.mic as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
            log("SpeechListener", f"Calibration complete. Energy threshold set to: {self.recognizer.energy_threshold}")
        except Exception as e:
            log("SpeechListener", f"Error during ambient noise adjustment: {e}")

    def listen(self, timeout: float = None, phrase_time_limit: float = None) -> str:
        """
        Listens to the microphone and returns the transcribed text.
        Returns an empty string if:
          - Microphone is unavailable
          - Timeout occurs
          - Speech was not understood
          - Network/API errors occur
        """
        if not self.mic_available or not self.mic:
            return ""

        try:
            with self.mic as source:
                # Listen for sound
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            
            log("SpeechListener", "Transcribing speech...")
            # Use Google Web Speech API (free, built-in, doesn't require keys)
            text = self.recognizer.recognize_google(audio)
            return text
            
        except sr.WaitTimeoutError:
            # No audio spoken within timeout duration
            return ""
        except sr.UnknownValueError:
            # Recognizer could not understand the audio
            log("SpeechListener", "Google Speech Recognition could not understand audio.")
            return ""
        except sr.RequestError as e:
            log("SpeechListener", f"Google Speech Recognition service error: {e}")
            return ""
        except Exception as e:
            log("SpeechListener", f"Unexpected error while listening/transcribing: {e}")
            return ""
