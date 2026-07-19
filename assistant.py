import time
import queue
import threading
from speech import SpeechEngine, SpeechListener
from commands import process_command
from utils import log

class Assistant:
    """
    Main background assistant controller. Coordinates TTS (speaking),
    STT (listening), and command execution. Runs in a dedicated background thread
    so the Tkinter GUI remains fully responsive.
    
    Communicates with the GUI thread using thread-safe queues.
    """
    def __init__(self, gui_queue: queue.Queue, command_queue: queue.Queue):
        self.gui_queue = gui_queue
        self.command_queue = command_queue
        self.running = False
        self.thread = None
        
        # We will initialize these inside the run thread to avoid COM apartment model errors on Windows
        self.tts = None
        self.listener = None

    def start(self) -> None:
        """Starts the assistant thread."""
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, name="UltronAssistantThread", daemon=True)
        self.thread.start()
        log("Assistant", "Assistant background thread started.")

    def stop(self) -> None:
        """Stops the assistant thread."""
        self.running = False
        log("Assistant", "Stopping assistant thread...")
        # The thread will exit on the next loop iteration

    def _post_status(self, status: str) -> None:
        """Helper to post status updates to the GUI."""
        self.gui_queue.put({"type": "status", "text": status})

    def _post_message(self, sender: str, text: str) -> None:
        """Helper to post conversation messages (user or assistant) to the GUI."""
        self.gui_queue.put({"type": "message", "sender": sender, "text": text})

    def _run_loop(self) -> None:
        """
        Main execution loop of the assistant thread.
        """
        # Initialize engines in this thread
        self.tts = SpeechEngine()
        self.listener = SpeechListener()
        
        # Warm-up / Ambient noise adjustment
        if self.listener.mic_available:
            self._post_status("Calibrating Microphone...")
            self.listener.adjust_for_ambient_noise()
        else:
            self._post_status("Microphone Unavailable")
            self.gui_queue.put({"type": "error", "text": "Microphone not found. You can still chat by typing below."})

        # Main assistant lifecycle loop
        while self.running:
            # 1. First, check if there are any GUI-injected commands in the command queue (non-blocking)
            try:
                cmd = self.command_queue.get_nowait()
                self._handle_gui_command(cmd)
                continue  # Skip normal listening for this iteration
            except queue.Empty:
                pass

            # 2. If no GUI command, handle voice listening (if microphone is available)
            if self.listener.mic_available:
                self._post_status("Waiting for Wake Word...")
                # Listen for the wake word with a short timeout so we can exit or check GUI queue
                heard_text = self.listener.listen(timeout=1.5, phrase_time_limit=2.5)
                
                # Check for wake word
                if heard_text:
                    cleaned_heard = heard_text.lower().strip()
                    log("Assistant", f"Heard raw speech in standby: '{heard_text}'")
                    if "ultron" in cleaned_heard:
                        log("Assistant", "Wake word 'Ultron' detected!")
                        self._trigger_voice_interaction()
            else:
                # If mic is not available, we sleep briefly to prevent 100% CPU usage
                time.sleep(0.2)

        log("Assistant", "Assistant background thread terminated.")

    def _handle_gui_command(self, cmd: dict) -> None:
        """
        Processes directives sent from the Tkinter GUI (e.g. typing a message
        or clicking the microphone button to bypass wake word detection).
        """
        cmd_type = cmd.get("type")
        
        if cmd_type == "text_command":
            text = cmd.get("text", "").strip()
            if not text:
                return
                
            log("Assistant", f"Handling GUI text command: '{text}'")
            # Post user message to UI
            self._post_message("user", text)
            
            # Process command
            self._post_status("Thinking...")
            response = process_command(text)
            
            # Post response to UI
            self._post_message("assistant", response)
            self._post_status("Speaking...")
            self.tts.speak(response)
            self._post_status("Waiting for Wake Word...")

        elif cmd_type == "force_listen":
            log("Assistant", "GUI forced microphone listen command.")
            self._trigger_voice_interaction()

    def _trigger_voice_interaction(self) -> None:
        """
        Executes the voice interaction sequence:
        1. Say "Yes, I'm listening."
        2. Listen for the actual command.
        3. Process and speak response.
        """
        # Prompt user
        self._post_status("Speaking...")
        reply = "Yes, I'm listening."
        self._post_message("assistant", reply)
        self.tts.speak(reply)
        
        # Listen for command
        self._post_status("Listening...")
        command_text = self.listener.listen(timeout=5.0, phrase_time_limit=8.0)
        
        if command_text:
            log("Assistant", f"Command received: '{command_text}'")
            self._post_message("user", command_text)
            
            # Process command
            self._post_status("Thinking...")
            response = process_command(command_text)
            
            # Speak and show response
            self._post_message("assistant", response)
            self._post_status("Speaking...")
            self.tts.speak(response)
        else:
            log("Assistant", "No command heard (silent or timeout).")
            # Inform user we're going back to standby
            self._post_status("Speaking...")
            standby_msg = "Going back to standby."
            self._post_message("assistant", standby_msg)
            self.tts.speak(standby_msg)
            
        self._post_status("Waiting for Wake Word...")
