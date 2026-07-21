"""
ui/phase2_splash.py - Loading screen while processing heavy background tasks.
"""
import threading
import traceback
import customtkinter as ctk
from core.theme import get_theme

from core.config import *
from core.sii_decoder import ensure_sii_decrypt
from core.mod_scanner import scan_mods, Mod
from core.logger import get_logger

_log = get_logger("phase2")


class Phase2SplashView(ctk.CTkFrame):
    """
    Shows a loading indicator and status messages while:
      1. Ensuring SII_Decrypt exists (downloading if needed)
      2. Scanning Mod files and extracting thumbnails
    """
    def __init__(self, master, on_scan_complete: callable, game: str = "ets2", **kwargs):
        self.palette = get_theme()
        super().__init__(master, fg_color=self.palette["bg"], **kwargs)
        self.on_scan_complete = on_scan_complete
        self.game = game

        # Logo
        from PIL import Image
        icon_path = get_logo_path()
        if icon_path:
            try:
                img = Image.open(icon_path)
                self.logo_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(80, 80))
                logo_lbl = ctk.CTkLabel(self, image=self.logo_ctk, text="")
                logo_lbl.pack(pady=(100, 20))
            except Exception:
                pass

        # UI Elements
        self.spinner = ctk.CTkProgressBar(self, mode="indeterminate", progress_color=self.palette["accent"], width=300)
        self.spinner.pack(pady=(20, 20))
        self.spinner.start()

        self.lbl_status = ctk.CTkLabel(
            self, text=txt("initializing"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_BODY),
            text_color=self.palette["muted"]
        )
        self.lbl_status.pack()

    def start_tasks(self):
        """Starts the heavy operations in a background thread."""
        self._done = False
        self._mods = []
        self._status_text = txt("checking_tools")
        self._error = None
        
        threading.Thread(target=self._background_work, daemon=True).start()
        self._poll_status()

    def _poll_status(self):
        """Runs on the main thread, safely updating the UI."""
        if self._done:
            if self._error:
                self.lbl_status.configure(text=f"{txt('error')}: {self._error}")
            else:
                self.lbl_status.configure(text=txt("processing_complete"))
            # Proceed to next phase
            self.after(500, lambda: self.on_scan_complete(self._mods))
        else:
            self.lbl_status.configure(text=self._status_text)
            self.after(100, self._poll_status)

    def _update_status(self, text: str):
        """Called by background thread to update the status text safely."""
        self._status_text = text

    def _background_work(self):
        try:
            _log.info("[Phase2] Checking SII tools...")
            self._update_status(txt("checking_tools"))
            ensure_sii_decrypt()

            _log.info("[Phase2] Starting mod scan [game=%s]...", self.game)
            self._mods = scan_mods(progress_callback=self._update_status, game=self.game)
            _log.info("[Phase2] Scan finished — %d mods", len(self._mods))

        except Exception as e:
            self._error = e
            _log.error("[Phase2] Background work failed: %s", e)
            _log.debug(traceback.format_exc())
        finally:
            self._done = True
