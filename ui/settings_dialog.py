"""
ui/settings_dialog.py - Simple path settings dialog for ETS2/ATS.
"""
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from core.theme import get_theme

from core.config import *
from core.settings import (
    get_game_settings,
    get_default_game_dir,
    get_game_root,
    resolve_game_data_dir,
    update_game_settings,
    reset_game_settings,
    validate_existing_dirs,
)
from core.mod_scanner import find_workshop_paths


class PathListEditor(ctk.CTkFrame):
    def __init__(self, master, title: str, paths: list[str], palette: dict, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.title = title
        self.palette = palette
        self.rows: list[ctk.CTkEntry] = []

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(
            header, text=title,
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_BODY, weight="bold"),
            text_color=self.palette["text"],
        ).pack(side="left")
        ctk.CTkButton(
            header, text=txt("add_path"), width=92, height=28,
            fg_color=self.palette["surface_2"], hover_color=self.palette["border"],
            command=lambda: self.add_row("")
        ).pack(side="right")

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="x")
        for path in paths:
            self.add_row(path)

    def add_row(self, value: str):
        row = ctk.CTkFrame(self.body, fg_color="transparent")
        row.pack(fill="x", pady=3)

        entry = ctk.CTkEntry(
            row, height=32, fg_color=self.palette["bg"], border_color=self.palette["border"],
            text_color=self.palette["text"],
        )
        entry.insert(0, value)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.rows.append(entry)

        def browse():
            start = entry.get().strip() or str(Path.home())
            folder = filedialog.askdirectory(initialdir=start if Path(start).exists() else str(Path.home()))
            if folder:
                entry.delete(0, "end")
                entry.insert(0, folder)

        def remove():
            if entry in self.rows:
                self.rows.remove(entry)
            row.destroy()

        ctk.CTkButton(row, text=txt("browse"), width=72, height=32, fg_color=self.palette["surface_2"], hover_color=self.palette["border"], command=browse).pack(side="left", padx=(0, 6))
        ctk.CTkButton(row, text=txt("remove"), width=70, height=32, fg_color=self.palette["surface_2"], hover_color=self.palette["danger"], command=remove).pack(side="left")

    def set_paths(self, paths: list[str]):
        for child in self.body.winfo_children():
            child.destroy()
        self.rows.clear()
        for path in paths:
            self.add_row(path)

    def get_paths(self) -> list[str]:
        values: list[str] = []
        seen: set[str] = set()
        for entry in self.rows:
            value = entry.get().strip()
            if not value:
                continue
            key = str(Path(value).expanduser()).lower()
            if key not in seen:
                values.append(value)
                seen.add(key)
        return values


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, master, game: str, on_saved=None):
        super().__init__(master)
        self.game = game
        self.on_saved = on_saved
        self.palette = get_theme()
        self.title(txt("settings"))
        self.geometry("780x640")
        self.minsize(720, 560)
        self.configure(fg_color=self.palette["bg"])
        self.grab_set()
        self.focus_force()

        cfg = GAME_CONFIGS[game]
        saved = get_game_settings(game)
        mode = saved.get("game_dir_mode", "auto")
        manual_dir = saved.get("manual_game_dir", "") or ""
        resolved_manual_dir = str(resolve_game_data_dir(game, manual_dir)) if manual_dir else ""

        shell = ctk.CTkFrame(self, fg_color=self.palette["bg"])
        shell.pack(fill="both", expand=True, padx=22, pady=20)

        ctk.CTkLabel(
            shell, text=f"{txt('settings')} - {cfg['short']}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_TITLE, weight="bold"),
            text_color=self.palette["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            shell, text=cfg["name"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_SMALL),
            text_color=self.palette["muted"],
        ).pack(anchor="w", pady=(2, 18))

        scroll = ctk.CTkScrollableFrame(shell, fg_color=self.palette["surface"], corner_radius=8)
        scroll.pack(fill="both", expand=True)

        section = ctk.CTkFrame(scroll, fg_color="transparent")
        section.pack(fill="x", padx=16, pady=16)

        ctk.CTkLabel(
            section, text=txt("game_directory"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_SUBTITLE, weight="bold"),
            text_color=self.palette["text"],
        ).pack(anchor="w", pady=(0, 8))

        self.mode_var = ctk.StringVar(value=mode if mode in ("auto", "manual") else "auto")
        self.mode_control = ctk.CTkSegmentedButton(
            section,
            values=[txt("automatic"), txt("manual")],
            command=self._on_mode_changed,
            selected_color=self.palette["accent"],
            selected_hover_color=self.palette["accent_hover"],
            unselected_color=self.palette["surface_2"],
            unselected_hover_color=self.palette["border"],
        )
        self.mode_control.pack(anchor="w", pady=(0, 10))
        self.mode_control.set(txt("manual") if self.mode_var.get() == "manual" else txt("automatic"))

        self.auto_info_frame = ctk.CTkFrame(section, fg_color="transparent")
        self.auto_info_label = ctk.CTkLabel(
            self.auto_info_frame,
            text=f"{txt('auto_game_dir_hint')} {get_default_game_dir(game)}",
            text_color=self.palette["muted"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_SMALL),
            anchor="w",
        )
        self.auto_info_label.pack(fill="x")

        self.manual_frame = ctk.CTkFrame(section, fg_color="transparent")
        ctk.CTkLabel(
            self.manual_frame,
            text=txt("manual_game_dir_hint"),
            text_color=self.palette["muted"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_SMALL),
            anchor="w",
        ).pack(fill="x", pady=(0, 6))
        manual_row = ctk.CTkFrame(self.manual_frame, fg_color="transparent")
        manual_row.pack(fill="x")
        self.manual_entry = ctk.CTkEntry(manual_row, height=34, fg_color=self.palette["bg"], border_color=self.palette["border"], text_color=self.palette["text"])
        self.manual_entry.insert(0, resolved_manual_dir)
        self.manual_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(manual_row, text=txt("browse"), width=84, height=34, fg_color=self.palette["surface_2"], hover_color=self.palette["border"], command=self._browse_game_dir).pack(side="left")

        local_saved = saved.get("local_mod_dirs")
        local_paths = local_saved if local_saved is not None else [str(get_game_root(game) / GAME_MODS_DIR)]
        workshop_saved = saved.get("workshop_mod_dirs")
        workshop_paths = workshop_saved if workshop_saved is not None else [str(p) for p in find_workshop_paths(cfg["app_id"])]

        self.sources_frame = ctk.CTkFrame(section, fg_color="transparent")
        self.local_editor = PathListEditor(self.sources_frame, txt("downloaded_mods"), local_paths, self.palette)
        self.local_editor.pack(fill="x", pady=(6, 16))

        self.ws_header = ctk.CTkFrame(self.sources_frame, fg_color="transparent")
        self.ws_header.pack(fill="x")
        ctk.CTkButton(
            self.ws_header, text=txt("workshop_hint"), width=170, height=28,
            fg_color=self.palette["surface_2"], hover_color=self.palette["border"],
            command=self._suggest_workshop,
        ).pack(side="right", pady=(0, 2))
        self.workshop_editor = PathListEditor(self.sources_frame, txt("workshop_mods"), workshop_paths, self.palette)
        self.workshop_editor.pack(fill="x", pady=(0, 10))

        self.error_label = ctk.CTkLabel(shell, text="", text_color=self.palette["danger"], justify="left")
        self.error_label.pack(fill="x", pady=(8, 0))

        actions = ctk.CTkFrame(shell, fg_color="transparent")
        actions.pack(fill="x", pady=(12, 0))
        ctk.CTkButton(actions, text=txt("reset"), width=110, fg_color=self.palette["surface_2"], hover_color=self.palette["border"], command=self._reset).pack(side="left")
        ctk.CTkButton(actions, text=txt("cancel"), width=100, fg_color=self.palette["surface_2"], hover_color=self.palette["border"], command=self.destroy).pack(side="right", padx=(8, 0))
        ctk.CTkButton(actions, text=txt("save_settings"), width=140, fg_color=self.palette["accent"], hover_color=self.palette["accent_hover"], command=self._save).pack(side="right")

        self._on_mode_changed(self.mode_control.get())

    def _on_mode_changed(self, value):
        manual = value == txt("manual")
        self.mode_var.set("manual" if manual else "auto")
        if manual:
            self.auto_info_frame.pack_forget()
            self.manual_frame.pack(fill="x", pady=(0, 18))
            self.sources_frame.pack(fill="x")
            self.manual_entry.configure(state="normal")
        else:
            self.manual_frame.pack_forget()
            self.sources_frame.pack_forget()
            self.auto_info_frame.pack(fill="x", pady=(0, 18))

    def _browse_game_dir(self):
        start = self.manual_entry.get().strip() or str(Path.home())
        folder = filedialog.askdirectory(initialdir=start if Path(start).exists() else str(Path.home()))
        if folder:
            self.manual_entry.configure(state="normal")
            self.manual_entry.delete(0, "end")
            self.manual_entry.insert(0, folder)
            if self.mode_var.get() != "manual":
                self.mode_control.set(txt("manual"))
                self._on_mode_changed(txt("manual"))

    def _suggest_workshop(self):
        paths = [str(p) for p in find_workshop_paths(GAME_CONFIGS[self.game]["app_id"])]
        self.workshop_editor.set_paths(paths)

    def _reset(self):
        reset_game_settings(self.game)
        callback = self.on_saved
        self.destroy()
        if callback:
            self.master.after(100, callback)

    def _save(self):
        mode = self.mode_var.get()
        manual_dir = self.manual_entry.get().strip() if mode == "manual" else ""
        resolved_manual_dir = resolve_game_data_dir(self.game, manual_dir) if manual_dir else Path("")
        errors: list[str] = []
        if mode == "manual":
            if not manual_dir:
                errors.append(txt("game_dir_empty"))
            elif not resolved_manual_dir.is_dir():
                errors.append(txt("game_dir_invalid").format(path=manual_dir))

        if mode == "manual":
            local_paths = self.local_editor.get_paths()
            workshop_paths = self.workshop_editor.get_paths()
            errors.extend(validate_existing_dirs(local_paths))
            errors.extend(validate_existing_dirs(workshop_paths))
        else:
            local_paths = None
            workshop_paths = None

        if errors:
            self.error_label.configure(text=txt("invalid_paths") + "\n" + "\n".join(errors[:6]))
            return

        update_game_settings(self.game, {
            "game_dir_mode": mode,
            "manual_game_dir": str(resolved_manual_dir) if mode == "manual" else "",
            "local_mod_dirs": local_paths,
            "workshop_mod_dirs": workshop_paths,
        })
        callback = self.on_saved
        self.destroy()
        if callback:
            self.master.after(100, callback)


def open_settings_dialog(master, game: str, on_saved=None):
    return SettingsDialog(master, game, on_saved=on_saved)
