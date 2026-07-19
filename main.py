import tkinter as tk
import queue
import sys
from gui import UltronGUI
from assistant import Assistant
from utils import log

def main():
    log("Main", "Starting Ultron Personal Voice Assistant application...")

    # Thread-safe communication queues
    gui_queue = queue.Queue()
    command_queue = queue.Queue()

    # Initialize the background Assistant core
    assistant = Assistant(gui_queue, command_queue)
    assistant.start()

    # Create root Tkinter window
    root = tk.Tk()

    # Define cleanup behavior when GUI closes
    def shutdown_app():
        log("Main", "Shutting down application components...")
        assistant.stop()
        # Allow thread a tiny moment to exit loop and cleanup COM
        root.after(200, sys.exit)

    # Initialize the GUI
    # It takes the shutdown_app callback which runs when the user clicks Exit
    app_gui = UltronGUI(root, gui_queue, command_queue, on_close_callback=shutdown_app)

    # Intercept system 'X' close button to ensure clean shutdown
    root.protocol("WM_DELETE_WINDOW", app_gui.close_application)

    try:
        # Start GUI main loop
        root.mainloop()
    except KeyboardInterrupt:
        log("Main", "Keyboard interrupt caught. Cleaning up...")
        shutdown_app()

if __name__ == "__main__":
    main()
