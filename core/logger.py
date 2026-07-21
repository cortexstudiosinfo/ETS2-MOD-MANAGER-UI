"""
core/logger.py - Centralized logging for the Truck Mod Manager.

- Writes to console (stdout) AND log.txt simultaneously.
- Adds system info header at startup (OS, Python, app version).
- On unhandled crash: shows a GUI error window with a 'Copy log' button
  so users can send you the full log instantly.
"""
import logging
import os
import platform
import sys
import traceback
from pathlib import Path


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def get_log_path() -> Path:
    """Returns the path to log.txt — always next to the .exe or main.py."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "log.txt"
    return Path(__file__).parent.parent / "log.txt"


# ---------------------------------------------------------------------------
# System info header
# ---------------------------------------------------------------------------

def _system_info() -> str:
    """Collects system info useful for bug reports."""
    try:
        import customtkinter as ctk
        ctk_ver = ctk.__version__
    except Exception:
        ctk_ver = "unknown"

    try:
        from PIL import __version__ as pil_ver
    except Exception:
        pil_ver = "unknown"

    lines = [
        "=" * 60,
        "  TRUCK MOD MANAGER — SESSION LOG",
        "=" * 60,
        f"  OS          : {platform.system()} {platform.release()} {platform.version()}",
        f"  Machine     : {platform.machine()}",
        f"  Python      : {platform.python_version()}",
        f"  CustomTkinter: {ctk_ver}",
        f"  Pillow      : {pil_ver}",
        f"  Executable  : {sys.executable}",
        f"  Frozen      : {getattr(sys, 'frozen', False)}",
        f"  Log file    : {get_log_path()}",
        "=" * 60,
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def setup_logger() -> logging.Logger:
    """
    Configures the root 'tmm' logger.
    Adds StreamHandler (console) + FileHandler (log.txt).
    Writes system info header at the top of the log file.
    """
    logger = logging.getLogger("tmm")
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  [%(module)s]  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File handler — overwrite each session
    try:
        log_path = get_log_path()
        fh = logging.FileHandler(log_path, mode="w", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

        # Write system info as plain text header (no formatter)
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(_system_info() + "\n\n")

        # Re-open in append mode now that header is written
        logger.removeHandler(fh)
        fh.close()
        fh = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    except Exception as exc:
        logger.warning("Could not open log file: %s", exc)

    return logger


def get_logger(name: str = "tmm") -> logging.Logger:
    """Returns a child logger under the 'tmm' namespace."""
    return logging.getLogger(f"tmm.{name}")


# ---------------------------------------------------------------------------
# Crash handler
# ---------------------------------------------------------------------------

def _show_crash_dialog(error_text: str) -> None:
    """
    Shows a Tkinter crash window with the full log content and a
    'Copy to clipboard' button so users can send it easily.
    Only shown when running as a compiled .exe (frozen).
    """
    try:
        import tkinter as tk
        from tkinter import scrolledtext

        TEXTS = {
            "en": {
                "title":   "Truck Mod Manager — Crash Report",
                "heading": "The application crashed unexpectedly.",
                "body":    "Please copy the log below and send it to the developer:\n"
                           "  •  Email:  cortex.studios.info@gmail.com\n"
                           "  •  Or post it in the comments/forum of the release page.",
                "copy":    "Copy log to clipboard",
                "copied":  "Copied!",
                "open":    "Open log.txt",
                "close":   "Close",
            },
            "es": {
                "title":   "Truck Mod Manager — Informe de Error",
                "heading": "La aplicación ha fallado inesperadamente.",
                "body":    "Por favor copia el log de abajo y envíaselo al desarrollador:\n"
                           "  •  Email:  cortex.studios.info@gmail.com\n"
                           "  •  O publícalo en los comentarios/foro de la página de descarga.",
                "copy":    "Copiar log al portapapeles",
                "copied":  "¡Copiado!",
                "open":    "Abrir log.txt",
                "close":   "Cerrar",
            },
        }

        lang = ["en"]

        root = tk.Tk()
        root.title(TEXTS["en"]["title"])
        root.configure(bg="#0A0A0A")
        root.resizable(True, True)

        w, h = 820, 620
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        root.minsize(700, 520)

        # Read full log file content once
        log_content = error_text
        try:
            log_path = get_log_path()
            if log_path.exists():
                log_content = log_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass

        # --- Header frame ---
        header = tk.Frame(root, bg="#0A0A0A")
        header.pack(fill="x", padx=20, pady=(20, 0))

        lbl_heading = tk.Label(
            header,
            font=("Segoe UI", 14, "bold"),
            fg="#FF4444", bg="#0A0A0A", anchor="w",
        )
        lbl_heading.pack(side="left", fill="x", expand=True)

        # Language toggle — top right
        lang_frame = tk.Frame(header, bg="#0A0A0A")
        lang_frame.pack(side="right")

        btn_en = tk.Button(lang_frame, text="EN", width=4,
                           bg="#CC0000", fg="white",
                           font=("Segoe UI", 9, "bold"),
                           relief="flat", cursor="hand2")
        btn_en.pack(side="left", padx=(0, 2))

        btn_es = tk.Button(lang_frame, text="ES", width=4,
                           bg="#333333", fg="#B0B0B0",
                           font=("Segoe UI", 9),
                           relief="flat", cursor="hand2")
        btn_es.pack(side="left")

        lbl_body = tk.Label(
            root,
            font=("Segoe UI", 10),
            fg="#B0B0B0", bg="#0A0A0A",
            justify="left", anchor="w",
        )
        lbl_body.pack(fill="x", padx=20, pady=(8, 10))

        # --- Log text area ---
        txt = scrolledtext.ScrolledText(
            root, font=("Consolas", 9),
            bg="#1A1A1A", fg="#FFFFFF",
            insertbackground="white",
            relief="flat", bd=0,
        )
        txt.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        txt.insert("1.0", log_content)
        txt.configure(state="disabled")

        # --- Button row ---
        btn_frame = tk.Frame(root, bg="#0A0A0A")
        btn_frame.pack(fill="x", padx=16, pady=(0, 16))

        btn_copy = tk.Button(
            btn_frame,
            bg="#CC0000", fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat", padx=16, pady=6, cursor="hand2",
        )
        btn_copy.pack(side="left", padx=(0, 8))

        btn_open = tk.Button(
            btn_frame,
            bg="#1E1E1E", fg="#B0B0B0",
            font=("Segoe UI", 10),
            relief="flat", padx=16, pady=6, cursor="hand2",
        )
        btn_open.pack(side="left", padx=(0, 8))

        btn_close = tk.Button(
            btn_frame,
            bg="#1E1E1E", fg="#B0B0B0",
            font=("Segoe UI", 10),
            relief="flat", padx=16, pady=6, cursor="hand2",
        )
        btn_close.pack(side="right")

        # --- Language switcher logic ---
        def _apply_lang(l):
            lang[0] = l
            t = TEXTS[l]
            root.title(t["title"])
            lbl_heading.configure(text=t["heading"])
            lbl_body.configure(text=t["body"])
            btn_copy.configure(text=t["copy"])
            btn_open.configure(text=t["open"])
            btn_close.configure(text=t["close"])
            btn_en.configure(bg="#CC0000" if l == "en" else "#333333",
                             fg="white"  if l == "en" else "#B0B0B0")
            btn_es.configure(bg="#CC0000" if l == "es" else "#333333",
                             fg="white"  if l == "es" else "#B0B0B0")

        btn_en.configure(command=lambda: _apply_lang("en"))
        btn_es.configure(command=lambda: _apply_lang("es"))

        def _copy():
            root.clipboard_clear()
            root.clipboard_append(log_content)
            btn_copy.configure(text=TEXTS[lang[0]]["copied"], bg="#28A745")
            root.after(2000, lambda: btn_copy.configure(
                text=TEXTS[lang[0]]["copy"], bg="#CC0000"))

        def _open_log():
            try:
                os.startfile(str(get_log_path()))
            except Exception:
                pass

        btn_copy.configure(command=_copy)
        btn_open.configure(command=_open_log)
        btn_close.configure(command=root.destroy)

        _apply_lang("en")

        root.mainloop()

    except Exception:
        pass


def install_excepthook(logger: logging.Logger) -> None:
    """
    Replaces sys.excepthook so any unhandled exception is:
    1. Logged to console + log.txt
    2. Shown in a crash dialog (only in .exe builds)
    """
    def _hook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return

        error_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        logger.critical("UNHANDLED EXCEPTION\n%s", error_text)

        # Show crash dialog only in compiled .exe — in dev the console is enough
        if getattr(sys, "frozen", False):
            _show_crash_dialog(error_text)

    sys.excepthook = _hook
