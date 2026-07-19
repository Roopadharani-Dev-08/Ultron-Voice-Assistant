import tkinter as tk
from tkinter import ttk
import queue
from datetime import datetime
from utils import log

# Color Palette (Catppuccin Mocha / Obsidian inspired dark mode)
COLOR_BG = "#181825"             # Main window background (dark navy-charcoal)
COLOR_HEADER = "#11111b"         # Header background (crust)
COLOR_BUBBLE_USER = "#313244"     # User message bubble background (surface0)
COLOR_BUBBLE_AST = "#1e1e2e"      # Assistant message bubble background (base)
COLOR_BORDER_AST = "#89b4fa"      # Accent border color for assistant bubble (blue)
COLOR_TEXT_USER = "#cdd6f4"       # User message text color (text)
COLOR_TEXT_AST = "#cdd6f4"        # Assistant message text color (text)
COLOR_TEXT_MUTED = "#7f849c"      # Timestamp / muted status text color
COLOR_STATUS_BG = "#11111b"       # Status bar background
COLOR_INPUT_BG = "#313244"        # Input text area background
COLOR_ACCENT = "#89b4fa"          # Primary accent color (sky blue)
COLOR_ACCENT_HOVER = "#b4befe"    # Hover accent color
COLOR_EXIT = "#f38ba8"            # Exit button color (red)
COLOR_EXIT_HOVER = "#e05a7d"      # Exit hover

class ScrollableChatFrame(tk.Frame):
    """
    A custom Tkinter widget that embeds a scrollable area for chat bubbles.
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.configure(bg=COLOR_BG)

        # Create a canvas and scrollbar
        self.canvas = tk.Canvas(self, bg=COLOR_BG, bd=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        # Inner frame to hold all chat bubbles
        self.scrollable_frame = tk.Frame(self.canvas, bg=COLOR_BG)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Create window inside canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configure canvas scroll
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack layouts
        self.canvas.pack(side="left", fill="both", expand=True, padx=(10, 0))
        self.scrollbar.pack(side="right", fill="y", padx=(0, 5))
        
        # Mousewheel scrolling compatibility
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind("<Configure>", self._on_frame_configure)

    def _on_mousewheel(self, event):
        # Support scrolling with mouse wheel
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_frame_configure(self, event):
        # Update width of inner frame to match canvas
        self.canvas.itemconfig(self.canvas_window, width=event.width - 20)


class UltronGUI:
    """
    Manages the Tkinter Graphical User Interface for Ultron.
    It runs on the main thread and polls a queue for updates from the assistant thread.
    """
    def __init__(self, root: tk.Tk, gui_queue: queue.Queue, command_queue: queue.Queue, on_close_callback=None):
        self.root = root
        self.gui_queue = gui_queue
        self.command_queue = command_queue
        self.on_close_callback = on_close_callback

        # Set up Window properties
        self.root.title("Ultron Assistant")
        self.root.geometry("460://680")
        self.root.geometry("460x680")
        self.root.minsize(400, 550)
        self.root.configure(bg=COLOR_BG)

        # Apply dark theme styling to ttk scrollbars
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TScrollbar",
                             gripcount=0,
                             background=COLOR_BUBBLE_USER,
                             troughcolor=COLOR_BG,
                             bordercolor=COLOR_BG,
                             arrowcolor=COLOR_ACCENT,
                             lightcolor=COLOR_BG,
                             darkcolor=COLOR_BG)

        self._build_ui()
        
        # Welcome message
        self.add_message("assistant", "Greetings, I am Ultron. Say my name to wake me up, or type your command below.")

        # Start checking the message queue
        self.root.after(100, self.poll_queue)

    def _build_ui(self):
        # 1. Header Frame
        header = tk.Frame(self.root, bg=COLOR_HEADER, height=60, bd=0)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="ULTRON 1.0",
            bg=COLOR_HEADER,
            fg=COLOR_ACCENT,
            font=("Segoe UI", 16, "bold")
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=10)

        # Pulse indicator in header
        self.indicator = tk.Canvas(header, width=12, height=12, bg=COLOR_HEADER, bd=0, highlightthickness=0)
        self.indicator.pack(side=tk.RIGHT, padx=25, pady=20)
        self.indicator_circle = self.indicator.create_oval(2, 2, 10, 10, fill=COLOR_TEXT_MUTED, outline="")

        # 2. Scrollable Chat History Panel
        self.chat_frame = ScrollableChatFrame(self.root)
        self.chat_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 5))

        # 3. Bottom Control Frame (Input area + Buttons)
        control_panel = tk.Frame(self.root, bg=COLOR_BG)
        control_panel.pack(fill=tk.X, side=tk.BOTTOM, padx=15, pady=(5, 10))

        # Text Input Box (Accessibility/Fallback Input)
        input_container = tk.Frame(control_panel, bg=COLOR_INPUT_BG, bd=1, highlightthickness=0)
        input_container.pack(fill=tk.X, pady=(0, 10))

        self.input_field = tk.Entry(
            input_container,
            bg=COLOR_INPUT_BG,
            fg=COLOR_TEXT_USER,
            insertbackground=COLOR_ACCENT,
            font=("Segoe UI", 11),
            bd=0,
            relief=tk.FLAT
        )
        self.input_field.pack(fill=tk.X, side=tk.LEFT, padx=10, pady=10, expand=True)
        self.input_field.bind("<Return>", self._send_text_command)
        
        # Placeholder text handling
        self.input_field.insert(0, "Type a command and press Enter...")
        self.input_field.bind("<FocusIn>", self._clear_placeholder)
        self.input_field.bind("<FocusOut>", self._restore_placeholder)

        # Button row container
        button_row = tk.Frame(control_panel, bg=COLOR_BG)
        button_row.pack(fill=tk.X)

        # Microphone Button
        self.mic_btn = tk.Button(
            button_row,
            text="🎙 Listen Now",
            bg=COLOR_ACCENT,
            fg="#11111b",
            activebackground=COLOR_ACCENT_HOVER,
            activeforeground="#11111b",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2",
            relief=tk.FLAT,
            command=self._force_microphone_listen
        )
        self.mic_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # Exit Button
        self.exit_btn = tk.Button(
            button_row,
            text="Exit App",
            bg=COLOR_BUBBLE_USER,
            fg=COLOR_EXIT,
            activebackground=COLOR_EXIT_HOVER,
            activeforeground="#ffffff",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2",
            relief=tk.FLAT,
            command=self.close_application
        )
        self.exit_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # 4. Status Bar
        self.status_bar = tk.Frame(self.root, bg=COLOR_STATUS_BG, height=25)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(
            self.status_bar,
            text="STATUS: Standby",
            bg=COLOR_STATUS_BG,
            fg=COLOR_TEXT_MUTED,
            font=("Segoe UI", 8, "bold")
        )
        self.status_label.pack(side=tk.LEFT, padx=15, pady=3)

    # Placeholders helpers
    def _clear_placeholder(self, event):
        if self.input_field.get() == "Type a command and press Enter...":
            self.input_field.delete(0, tk.END)

    def _restore_placeholder(self, event):
        if not self.input_field.get().strip():
            self.input_field.delete(0, tk.END)
            self.input_field.insert(0, "Type a command and press Enter...")

    def _send_text_command(self, event=None):
        text = self.input_field.get().strip()
        if not text or text == "Type a command and press Enter...":
            return
            
        self.input_field.delete(0, tk.END)
        # Put the command on the queue for the assistant thread to pick up
        self.command_queue.put({"type": "text_command", "text": text})

    def _force_microphone_listen(self):
        # Force the assistant thread to bypass the wake word and listen immediately
        self.command_queue.put({"type": "force_listen"})

    def add_message(self, sender: str, text: str):
        """
        Dynamically appends a modern styled message bubble into the scrollable area.
        """
        bubble_frame = tk.Frame(self.chat_frame.scrollable_frame, bg=COLOR_BG)
        bubble_frame.pack(fill=tk.X, padx=10, pady=8)

        # Set alignments and text properties based on sender
        if sender == "user":
            bubble_bg = COLOR_BUBBLE_USER
            text_color = COLOR_TEXT_USER
            side = tk.RIGHT
            anchor = "e"
            sender_display = "You"
            border_style = {}
        else:
            bubble_bg = COLOR_BUBBLE_AST
            text_color = COLOR_TEXT_AST
            side = tk.LEFT
            anchor = "w"
            sender_display = "Ultron"
            # Assistant bubbles get a subtle accent border to look more premium
            border_style = {"highlightbackground": COLOR_BORDER_AST, "highlightcolor": COLOR_BORDER_AST, "highlightthickness": 1}

        # Timestamp and sender name
        timestamp = datetime.now().strftime("%I:%M %p")
        info_label = tk.Label(
            bubble_frame,
            text=f"{sender_display}  •  {timestamp}",
            bg=COLOR_BG,
            fg=COLOR_TEXT_MUTED,
            font=("Segoe UI", 8)
        )
        info_label.pack(side=tk.TOP, anchor=anchor, padx=5, pady=(0, 2))

        # Main message card (bubble)
        card = tk.Frame(bubble_frame, bg=bubble_bg, padx=14, pady=10, **border_style)
        card.pack(side=side, anchor=anchor)

        # Label wrapping text
        msg_label = tk.Label(
            card,
            text=text,
            bg=bubble_bg,
            fg=text_color,
            font=("Segoe UI", 10),
            justify=tk.LEFT,
            wraplength=320,
            anchor=anchor
        )
        msg_label.pack()

        # Small delay to allow layout recalculation before scrolling down
        self.root.after(50, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        """Scrolls the chat canvas to the bottom to display latest message."""
        self.chat_frame.canvas.yview_moveto(1.0)

    def update_status(self, status: str):
        """
        Updates the status bar text and color coding, and pulses the header indicator.
        """
        self.status_label.config(text=f"STATUS: {status.upper()}")
        
        # Color code based on state
        status_lower = status.lower()
        if "listening" in status_lower:
            indicator_color = "#23a55a"  # Neon green
            status_fg = "#23a55a"
        elif "thinking" in status_lower:
            indicator_color = "#faa61a"  # Orange
            status_fg = "#faa61a"
        elif "speaking" in status_lower:
            indicator_color = "#5865f2"  # Discord indigo-blue
            status_fg = "#5865f2"
        elif "wake word" in status_lower or "standby" in status_lower:
            indicator_color = COLOR_TEXT_MUTED
            status_fg = COLOR_TEXT_MUTED
        elif "calibrating" in status_lower:
            indicator_color = "#f5c2e7"  # Pinkish
            status_fg = "#f5c2e7"
        else:
            indicator_color = COLOR_EXIT
            status_fg = COLOR_EXIT

        self.status_label.config(fg=status_fg)
        self.indicator.itemconfig(self.indicator_circle, fill=indicator_color)

    def poll_queue(self):
        """
        Periodically checks the queue for UI events coming from the assistant thread.
        """
        try:
            while True:
                event = self.gui_queue.get_nowait()
                event_type = event.get("type")
                
                if event_type == "status":
                    self.update_status(event.get("text"))
                elif event_type == "message":
                    self.add_message(event.get("sender"), event.get("text"))
                elif event_type == "error":
                    self.add_message("assistant", f"⚠️ Error: {event.get('text')}")
                    
                self.gui_queue.task_done()
        except queue.Empty:
            pass
        finally:
            # Re-schedule polling (every 100 milliseconds)
            self.root.after(100, self.poll_queue)

    def close_application(self):
        """Triggered upon closing the GUI."""
        if self.on_close_callback:
            self.on_close_callback()
        self.root.destroy()
