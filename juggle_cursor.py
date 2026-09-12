#!/usr/bin/env python3
"""
StayOn - Subtle cursor movement with automatic takeover detection and GUI control.
"""

import math
import random
import sys
import threading
import time
import argparse
import pyautogui

# Disable PyAutoGUI failsafe corner crash to prevent abrupt terminations
pyautogui.FAILSAFE = False


class CursorJiggler:
    """Handles subtle cursor movement and detects physical user takeover."""

    def __init__(self, radius=4, interval=3.0, stop_on_takeover=True,
                 auto_resume=True, resume_delay=5.0, on_status_change=None):
        self.radius = radius
        self.interval = interval
        self.stop_on_takeover = stop_on_takeover
        self.auto_resume = auto_resume
        self.resume_delay = resume_delay
        self.on_status_change = on_status_change

        self._running = False
        self._paused = False
        self._thread = None
        self._lock = threading.Lock()

        # Coordinates tracking
        self.expected_pos = None
        self.sensitivity_threshold = 4  # pixels deviation indicating user input

    @property
    def is_running(self):
        return self._running

    @property
    def is_paused(self):
        return self._paused

    def start(self):
        with self._lock:
            if self._running:
                return
            self._running = True
            self._paused = False
            self.expected_pos = pyautogui.position()
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

        if self.on_status_change:
            self.on_status_change("running", "Jiggler active")

    def stop(self, reason="Stopped"):
        with self._lock:
            if not self._running:
                return
            self._running = False
            self._paused = False

        if self.on_status_change:
            self.on_status_change("stopped", reason)

    def _sleep_with_takeover_check(self, duration):
        """Sleep in tiny increments while monitoring mouse position for physical user movement."""
        start_time = time.time()
        step = 0.04  # 40ms polling interval

        while time.time() - start_time < duration:
            if not self._running:
                return False

            curr_x, curr_y = pyautogui.position()
            if self.expected_pos is not None:
                exp_x, exp_y = self.expected_pos
                dist = math.hypot(curr_x - exp_x, curr_y - exp_y)
                if dist > self.sensitivity_threshold:
                    # User moved the mouse!
                    self._handle_takeover(curr_x, curr_y)
                    return False

            time.sleep(step)
        return True

    def _handle_takeover(self, curr_x, curr_y):
        """Triggered when human mouse input is detected."""
        if self.stop_on_takeover and not self.auto_resume:
            self._running = False
            if self.on_status_change:
                self.on_status_change("takeover_stopped", "Stopped: User took control")
        elif self.auto_resume:
            self._paused = True
            if self.on_status_change:
                self.on_status_change("takeover_paused", "Paused: User active, will resume when idle")
            # Wait for user idle
            threading.Thread(target=self._wait_for_idle, args=(curr_x, curr_y), daemon=True).start()

    def _wait_for_idle(self, last_x, last_y):
        """Wait until user stops moving the mouse for resume_delay seconds."""
        idle_start = time.time()
        check_interval = 0.1

        while self._running and self._paused:
            time.sleep(check_interval)
            curr_x, curr_y = pyautogui.position()
            if math.hypot(curr_x - last_x, curr_y - last_y) > 2:
                # Still moving
                last_x, last_y = curr_x, curr_y
                idle_start = time.time()
            else:
                # Resting
                if time.time() - idle_start >= self.resume_delay:
                    with self._lock:
                        if not self._running:
                            return
                        self._paused = False
                        self.expected_pos = (curr_x, curr_y)
                    if self.on_status_change:
                        self.on_status_change("running", "Jiggler resumed (idle detected)")
                    return

    def _run_loop(self):
        """Main jiggler execution loop using subtle nudges."""
        angle = 0.0
        screen_w, screen_h = pyautogui.size()

        while self._running:
            if self._paused:
                time.sleep(0.1)
                continue

            # Capture current anchor position
            anchor_x, anchor_y = pyautogui.position()
            self.expected_pos = (anchor_x, anchor_y)

            # Wait for configured interval while detecting takeover
            if not self._sleep_with_takeover_check(self.interval):
                continue

            if not self._running or self._paused:
                continue

            # Minor movement calculation
            # Perform a subtle displacement and return to anchor
            r = max(1, self.radius)
            angle += random.uniform(0.8, 1.6)
            dx = int(r * math.cos(angle))
            dy = int(r * math.sin(angle))

            target_x = max(0, min(screen_w - 1, anchor_x + dx))
            target_y = max(0, min(screen_h - 1, anchor_y + dy))

            # Perform subtle move
            self.expected_pos = (target_x, target_y)
            pyautogui.moveTo(target_x, target_y, duration=0.08)

            # Brief pause at displaced point
            if not self._sleep_with_takeover_check(0.12):
                continue

            # Return smoothly back to anchor so cursor doesn't wander away
            self.expected_pos = (anchor_x, anchor_y)
            pyautogui.moveTo(anchor_x, anchor_y, duration=0.08)


# ==============================================================================
# Modern Desktop GUI (Tkinter)
# ==============================================================================

def launch_gui():
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("StayOn")
    root.geometry("380x480")
    root.minsize(360, 460)
    root.resizable(True, True)

    # Color Palette & Styling
    BG_COLOR = "#18181b"          # zinc-900
    CARD_BG = "#27272a"           # zinc-800
    TEXT_PRIMARY = "#f4f4f5"      # zinc-100
    TEXT_MUTED = "#a1a1aa"        # zinc-400
    ACCENT_GREEN = "#10b981"      # emerald-500
    ACCENT_RED = "#ef4444"        # red-500
    ACCENT_AMBER = "#f59e0b"      # amber-500
    ACCENT_BLUE = "#3b82f6"       # blue-500

    root.configure(bg=BG_COLOR)

    # Styling for TTK widgets
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("TFrame", background=BG_COLOR)
    style.configure("Card.TFrame", background=CARD_BG, relief="flat")
    style.configure("TLabel", background=BG_COLOR, foreground=TEXT_PRIMARY, font=("SF Pro Display", 11))
    style.configure("Card.TLabel", background=CARD_BG, foreground=TEXT_PRIMARY, font=("SF Pro Display", 11))
    style.configure("Muted.TLabel", background=CARD_BG, foreground=TEXT_MUTED, font=("SF Pro Display", 9))
    style.configure("TCheckbutton", background=CARD_BG, foreground=TEXT_PRIMARY, font=("SF Pro Display", 10))
    style.map("TCheckbutton", background=[("active", CARD_BG)], foreground=[("active", TEXT_PRIMARY)])

    # Jiggler Engine Instance
    jiggler = CursorJiggler()

    # GUI Variables
    radius_var = tk.IntVar(value=4)
    interval_var = tk.DoubleVar(value=3.0)
    stop_on_takeover_var = tk.BooleanVar(value=True)
    auto_resume_var = tk.BooleanVar(value=True)
    resume_delay_var = tk.IntVar(value=5)
    always_on_top_var = tk.BooleanVar(value=False)

    def apply_settings():
        jiggler.radius = radius_var.get()
        jiggler.interval = interval_var.get()
        jiggler.stop_on_takeover = stop_on_takeover_var.get()
        jiggler.auto_resume = auto_resume_var.get()
        jiggler.resume_delay = resume_delay_var.get()

    # Thread-safe status updater
    def update_status_ui(status_type, message):
        def _update():
            if status_type == "running":
                status_dot.config(foreground=ACCENT_GREEN, text="●")
                status_label.config(text="Active (Jiggling)", foreground=TEXT_PRIMARY)
                status_subtext.config(text=message)
                btn_toggle.config(
                    text="■ Stop Jiggler",
                    bg=ACCENT_RED,
                    fg="#ffffff"
                )
            elif status_type == "takeover_stopped":
                status_dot.config(foreground=ACCENT_AMBER, text="●")
                status_label.config(text="Stopped by Takeover", foreground=ACCENT_AMBER)
                status_subtext.config(text="Mouse movement detected. Jiggler halted.")
                btn_toggle.config(
                    text="▶ Start Jiggler",
                    bg=ACCENT_GREEN,
                    fg="#ffffff"
                )
            elif status_type == "takeover_paused":
                status_dot.config(foreground=ACCENT_AMBER, text="●")
                status_label.config(text="Paused (User Active)", foreground=ACCENT_AMBER)
                status_subtext.config(text=f"Will auto-resume after {resume_delay_var.get()}s idle")
                btn_toggle.config(
                    text="■ Stop Jiggler",
                    bg=ACCENT_RED,
                    fg="#ffffff"
                )
            else:  # stopped
                status_dot.config(foreground=TEXT_MUTED, text="●")
                status_label.config(text="Idle / Stopped", foreground=TEXT_MUTED)
                status_subtext.config(text=message)
                btn_toggle.config(
                    text="▶ Start Jiggler",
                    bg=ACCENT_GREEN,
                    fg="#ffffff"
                )
        root.after(0, _update)

    jiggler.on_status_change = update_status_ui

    def toggle_jiggler():
        if jiggler.is_running:
            jiggler.stop("Stopped by user")
        else:
            apply_settings()
            jiggler.start()

    def on_top_toggle():
        root.attributes("-topmost", always_on_top_var.get())

    # Window Content Container
    main_frame = ttk.Frame(root, padding=16)
    main_frame.pack(fill="both", expand=True)

    # Header
    header_frame = ttk.Frame(main_frame)
    header_frame.pack(fill="x", pady=(0, 12))

    title_label = tk.Label(
        header_frame,
        text="StayOn",
        font=("SF Pro Display", 18, "bold"),
        bg=BG_COLOR,
        fg=TEXT_PRIMARY
    )
    title_label.pack(anchor="w")

    subtitle_label = tk.Label(
        header_frame,
        text="Subtle movement with auto-stop on mouse takeover",
        font=("SF Pro Display", 10),
        bg=BG_COLOR,
        fg=TEXT_MUTED
    )
    subtitle_label.pack(anchor="w")

    # Status Card
    status_card = tk.Frame(main_frame, bg=CARD_BG, padx=14, pady=12, highlightthickness=1, highlightbackground="#3f3f46")
    status_card.pack(fill="x", pady=(0, 14))

    status_top_row = tk.Frame(status_card, bg=CARD_BG)
    status_top_row.pack(fill="x")

    status_dot = tk.Label(status_top_row, text="●", font=("SF Pro Display", 14), fg=TEXT_MUTED, bg=CARD_BG)
    status_dot.pack(side="left", padx=(0, 6))

    status_label = tk.Label(
        status_top_row,
        text="Idle / Stopped",
        font=("SF Pro Display", 12, "bold"),
        fg=TEXT_MUTED,
        bg=CARD_BG
    )
    status_label.pack(side="left")

    status_subtext = tk.Label(
        status_card,
        text="Press Start to begin subtle jiggling",
        font=("SF Pro Display", 9),
        fg=TEXT_MUTED,
        bg=CARD_BG,
        anchor="w",
        justify="left"
    )
    status_subtext.pack(fill="x", pady=(4, 0))

    # Big Toggle Action Button (using Label to ensure background color works on macOS)
    btn_toggle = tk.Label(
        main_frame,
        text="▶ Start Jiggler",
        font=("SF Pro Display", 13, "bold"),
        bg=ACCENT_GREEN,
        fg="#ffffff",
        cursor="pointinghand",
        pady=10
    )
    btn_toggle.pack(fill="x", pady=(0, 16))
    btn_toggle.bind("<Button-1>", lambda e: toggle_jiggler())

    def on_btn_enter(e):
        if jiggler.is_running:
            btn_toggle.config(bg="#dc2626")  # hover red
        else:
            btn_toggle.config(bg="#059669")  # hover green

    def on_btn_leave(e):
        if jiggler.is_running:
            btn_toggle.config(bg=ACCENT_RED)
        else:
            btn_toggle.config(bg=ACCENT_GREEN)

    btn_toggle.bind("<Enter>", on_btn_enter)
    btn_toggle.bind("<Leave>", on_btn_leave)

    # Controls Card
    controls_card = tk.Frame(main_frame, bg=CARD_BG, padx=14, pady=14, highlightthickness=1, highlightbackground="#3f3f46")
    controls_card.pack(fill="both", expand=True, pady=(0, 12))

    # Control 1: Movement Radius (Minor Movement)
    lbl_radius_title = tk.Frame(controls_card, bg=CARD_BG)
    lbl_radius_title.pack(fill="x", pady=(0, 2))

    tk.Label(
        lbl_radius_title,
        text="Movement Range:",
        font=("SF Pro Display", 10, "bold"),
        bg=CARD_BG,
        fg=TEXT_PRIMARY
    ).pack(side="left")

    lbl_radius_val = tk.Label(
        lbl_radius_title,
        text="4 px (Minor)",
        font=("SF Pro Display", 10),
        bg=CARD_BG,
        fg=ACCENT_BLUE
    )
    lbl_radius_val.pack(side="right")

    def on_radius_change(val):
        px = int(float(val))
        radius_var.set(px)
        lbl_radius_val.config(text=f"{px} px {'(Minor)' if px <= 8 else '(Moderate)' if px <= 20 else '(Wide)'}")
        apply_settings()

    scale_radius = ttk.Scale(
        controls_card,
        from_=1,
        to=30,
        orient="horizontal",
        value=radius_var.get(),
        command=on_radius_change
    )
    scale_radius.pack(fill="x", pady=(0, 12))

    # Control 2: Interval (seconds)
    lbl_interval_title = tk.Frame(controls_card, bg=CARD_BG)
    lbl_interval_title.pack(fill="x", pady=(0, 2))

    tk.Label(
        lbl_interval_title,
        text="Frequency Interval:",
        font=("SF Pro Display", 10, "bold"),
        bg=CARD_BG,
        fg=TEXT_PRIMARY
    ).pack(side="left")

    lbl_interval_val = tk.Label(
        lbl_interval_title,
        text="3.0 s",
        font=("SF Pro Display", 10),
        bg=CARD_BG,
        fg=ACCENT_BLUE
    )
    lbl_interval_val.pack(side="right")

    def on_interval_change(val):
        sec = round(float(val), 1)
        interval_var.set(sec)
        lbl_interval_val.config(text=f"{sec} s")
        apply_settings()

    scale_interval = ttk.Scale(
        controls_card,
        from_=1,
        to=20,
        orient="horizontal",
        value=interval_var.get(),
        command=on_interval_change
    )
    scale_interval.pack(fill="x", pady=(0, 14))

    # Takeover Behavior Options
    sep = tk.Frame(controls_card, bg="#3f3f46", height=1)
    sep.pack(fill="x", pady=(0, 12))

    chk_takeover = ttk.Checkbutton(
        controls_card,
        text="Auto-stop immediately when I take control",
        variable=stop_on_takeover_var,
        command=apply_settings
    )
    chk_takeover.pack(anchor="w", pady=(0, 8))

    def on_autoresume_toggle():
        apply_settings()
        if auto_resume_var.get():
            resume_frame.pack(fill="x", pady=(4, 8))
        else:
            resume_frame.pack_forget()

    chk_autoresume = ttk.Checkbutton(
        controls_card,
        text="Auto-resume after user becomes idle",
        variable=auto_resume_var,
        command=on_autoresume_toggle
    )
    chk_autoresume.pack(anchor="w", pady=(0, 4))

    resume_frame = tk.Frame(controls_card, bg=CARD_BG)
    if auto_resume_var.get():
        resume_frame.pack(fill="x", pady=(4, 8))
    lbl_resume_delay = tk.Label(
        resume_frame,
        text=f"Resume delay: {resume_delay_var.get()}s",
        font=("SF Pro Display", 9),
        bg=CARD_BG,
        fg=TEXT_MUTED
    )
    lbl_resume_delay.pack(anchor="w")

    def on_resume_delay_change(val):
        s = int(float(val))
        resume_delay_var.set(s)
        lbl_resume_delay.config(text=f"Resume delay: {s}s")
        apply_settings()

    scale_resume_delay = ttk.Scale(
        resume_frame,
        from_=2,
        to=30,
        orient="horizontal",
        value=resume_delay_var.get(),
        command=on_resume_delay_change
    )
    scale_resume_delay.pack(fill="x", pady=(2, 0))

    # Footer Options
    footer_frame = ttk.Frame(main_frame)
    footer_frame.pack(fill="x", pady=(4, 0))

    chk_ontop = ttk.Checkbutton(
        footer_frame,
        text="Keep window always on top",
        variable=always_on_top_var,
        command=on_top_toggle
    )
    chk_ontop.pack(side="left")

    # Safe Clean-up on Exit
    def on_closing():
        jiggler.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


# ==============================================================================
# CLI Fallback Mode
# ==============================================================================

def run_cli(radius=4, interval=3.0, auto_resume=True):
    print("=" * 50)
    print("StayOn (CLI Mode)")
    print(f"- Movement radius: {radius} px (Minor)")
    print(f"- Interval: {interval}s")
    print("- Takeover detection: AUTO-STOP ON MOUSE MOVEMENT")
    print("Press Ctrl+C to quit.")
    print("=" * 50)

    stop_event = threading.Event()

    def status_callback(status, msg):
        print(f"[{time.strftime('%H:%M:%S')}] {status.upper()}: {msg}")
        if status == "takeover_stopped":
            stop_event.set()

    jiggler = CursorJiggler(
        radius=radius,
        interval=interval,
        stop_on_takeover=True,
        auto_resume=auto_resume,
        on_status_change=status_callback
    )

    jiggler.start()

    try:
        while not stop_event.is_set():
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\nStopping jiggler...")
    finally:
        jiggler.stop()
        print("Jiggler exited.")


def main():
    parser = argparse.ArgumentParser(description="Subtle StayOn with Takeover Detection")
    parser.add_argument("--cli", action="store_true", help="Run in terminal CLI mode instead of GUI")
    parser.add_argument("--radius", type=int, default=4, help="Movement radius in pixels (default: 4)")
    parser.add_argument("--interval", type=float, default=3.0, help="Interval between moves in seconds (default: 3.0)")
    parser.add_argument("--no-auto-resume", dest="auto_resume", action="store_false", help="Disable auto-resume in CLI mode")
    parser.set_defaults(auto_resume=True)
    args = parser.parse_args()

    if args.cli:
        run_cli(radius=args.radius, interval=args.interval, auto_resume=args.auto_resume)
    else:
        launch_gui()


if __name__ == "__main__":
    main()