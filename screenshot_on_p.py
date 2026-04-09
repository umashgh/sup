#!/usr/bin/env python3
"""
Press P → screenshot the active window, saved to ./screenshots/
Press Q or Esc → quit
"""

import os, sys, subprocess
from datetime import datetime
from pathlib import Path

# ── auto-install deps ──────────────────────────────────────────────────────
def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", pkg])

try:
    from pynput import keyboard
except ImportError:
    print("Installing pynput…"); install("pynput")
    from pynput import keyboard

try:
    from PIL import ImageGrab
except ImportError:
    print("Installing pillow…"); install("pillow")
    from PIL import ImageGrab

try:
    import Quartz   # bundled with macOS Python / pyobjc
    HAS_QUARTZ = True
except ImportError:
    HAS_QUARTZ = False

# ── save folder ────────────────────────────────────────────────────────────
SAVE_DIR = Path(__file__).parent / "screenshots"
SAVE_DIR.mkdir(exist_ok=True)

# ── window capture ─────────────────────────────────────────────────────────
def active_window_bounds():
    """Return (x, y, w, h) of the topmost on-screen window, or None."""
    if not HAS_QUARTZ:
        return None
    wins = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly |
        Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID
    )
    for w in wins:
        if w.get(Quartz.kCGWindowLayer, 99) == 0:   # layer 0 = normal app window
            b = w.get("kCGWindowBounds", {})
            if b.get("Width", 0) > 50:              # skip tiny utility windows
                return (
                    int(b["X"]), int(b["Y"]),
                    int(b["Width"]), int(b["Height"])
                )
    return None


def take_screenshot():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = SAVE_DIR / f"shot_{ts}.png"

    bounds = active_window_bounds()
    if bounds:
        x, y, w, h = bounds
        img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    else:
        img = ImageGrab.grab()          # fallback: full screen

    img.save(path)
    kb = path.stat().st_size // 1024
    print(f"  📸  {path.name}  ({w if bounds else '?'}×{h if bounds else '?'}  {kb}KB)")


# ── keyboard listener ──────────────────────────────────────────────────────
count = 0

def on_press(key):
    global count
    try:
        ch = key.char.lower() if hasattr(key, "char") and key.char else None
    except Exception:
        ch = None

    if ch == "p":
        count += 1
        print(f"[{count}] ", end="", flush=True)
        take_screenshot()
    elif ch == "q" or key == keyboard.Key.esc:
        print(f"\nDone — {count} screenshot(s) saved to {SAVE_DIR}")
        return False          # stop listener


print("🎯  Screenshot on keypress")
print(f"    P  →  capture active window  →  {SAVE_DIR}")
print("    Q / Esc  →  quit\n")

with keyboard.Listener(on_press=on_press, suppress=False) as lst:
    lst.join()
