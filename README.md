# Ultron – Personal Voice Assistant (Version 1.0)

Ultron is a desktop-based personal voice assistant developed entirely in Python using Tkinter. The assistant listens continuously for a wake word, interacts with users through speech synthesis and speech recognition, and displays the conversation history in a modern, dark-mode chat-style graphical interface inspired by modern AI platforms like ChatGPT and Gemini.

---

## 🚀 Key Features

* **Wake Word Detection**: Continuously listens for the wake word **"Ultron"** in the background and activates immediately.
* **Modern Chat UI**: A responsive, dark-theme Tkinter interface containing left/right aligned message bubbles and auto-scroll capability.
* **Status Indicators**: Dynamic status panel showcasing states: *STANDBY*, *CALIBRATING*, *LISTENING*, *THINKING*, and *SPEAKING*.
* **Play Songs & Videos**: Instantly searches and plays videos/tracks on YouTube using `pywhatkit`.
* **Wikipedia Queries**: Fetches concise 4–5 line summaries of queries (e.g. "Who is Nikola Tesla", "What is Artificial Intelligence") with disambiguation resolution.
* **Date & Time**: Responds to current system date and time queries.
* **Jokes**: Tells random programmer jokes using `pyjokes`.
* **Keyboard Fallback Entry**: Accessible text box at the bottom allowing you to type commands directly if a microphone is not connected.

---

## 🏗️ Project Architecture

To prevent the Tkinter GUI thread from freezing during speech synthesis and microphone listening, the application operates on a **dual-thread model**:

```
 ┌────────────────────────┐         Thread-Safe Queues         ┌────────────────────────┐
 │      Main Thread       │ ─────────────────────────────────> │   Assistant Thread     │
 │  (Tkinter GUI Loop)    │ <───────────────────────────────── │    (Speech & STT)      │
 └────────────────────────┘                                    └────────────────────────┘
```
1. **Main UI Thread**: Renders the GUI and polls a message queue every 100ms for status changes or text updates.
2. **Background Assistant Thread**: Initializes voice engines, calibrates ambient noise, listens to inputs, runs query logic, and schedules updates back to the UI.

---

## 📂 Project Structure

```
Ultron/
│
├── main.py          # App launcher & thread setup
├── assistant.py     # Background lifecycle thread loop
├── gui.py           # Tkinter modern interface elements
├── speech.py        # Speech-To-Text & Text-To-Speech engines
├── commands.py      # Core NLP processing & command resolution
└── utils.py         # Formatting and cleaning utility functions
```

---

## 📋 Requirements & Installation

### 1. Python Environment
* Python 3.10+ installed on your system.

### 2. External Libraries
Install the necessary requirements using pip:
```bash
pip install SpeechRecognition pyttsx3 wikipedia pywhatkit pyjokes PyAudio
```

> [!NOTE]
> On Windows, `PyAudio` is required for microphone access. If `pip install PyAudio` fails, you can install the binary wheel from unofficial sources or compile it with Visual C++ Build Tools.

---

## 🏃 How to Run the App

1. Clone or download this project directory.
2. Open your terminal/PowerShell in the project folder:
   ```powershell
   cd Ultron
   ```
3. Run the application:
   ```bash
   python main.py
   ```
4. On launch:
   - The assistant will calibrate the microphone for 1 second.
   - Say **"Ultron"** or click the **"🎙 Listen Now"** button to start asking questions!
