"""
ui/phase3_dashboard.py - Modern dashboard UI.
"""
from pathlib import Path
import threading
from typing import Optional

import customtkinter as ctk
from customtkinter import CTkImage
from PIL import Image

from core.config import *
from core.profile_utils import Profile
from core.mod_scanner import Mod
from core.profile_mods import read_active_mods, write_active_mods
from core.profile_editor import read_editable_profile, write_editable_profile
from core.game_editor import GAME_FIELD_DEFS, read_game_editor_data, write_game_editor_data
from cloud.firebase_client import FirebaseClient
from core.config import launch_game
from ui.settings_dialog import open_settings_dialog
from core.theme import THEMES, get_theme_mode, get_theme_label, set_theme_label


DASHBOARD_ICONS = {
    "profiles": "dashboard_profiles.png",
    "mods": "dashboard_mods.png",
    "workshop": "dashboard_workshop.png",
    "order": "dashboard_order.png",
}


class DialogTitleBar(ctk.CTkFrame):
    def __init__(self, master, app, title_text):
        super().__init__(master, height=34, fg_color="#111827", corner_radius=0)
        self.app = app
        self.pack_propagate(False)
        ctk.CTkLabel(
            self, text=title_text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color="#FFFFFF",
        ).pack(side="left", padx=14)
        ctk.CTkButton(
            self, text="X", width=38, height=34,
            fg_color="transparent", hover_color="#DC2626",
            text_color="#FFFFFF", corner_radius=0,
            command=self._close_window,
        ).pack(side="right")
        self._drag_x = 0
        self._drag_y = 0
        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<B1-Motion>", self.do_move)

    def _close_window(self):
        try:
            self.app.grab_release()
        except Exception:
            pass
        self.app.destroy()

    def start_move(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def do_move(self, event):
        self.app.geometry(f"+{self.app.winfo_x() + event.x - self._drag_x}+{self.app.winfo_y() + event.y - self._drag_y}")


class Phase3DashboardView(ctk.CTkFrame):
    def __init__(self, master, profile: Profile, mods: list[Mod], game: str = "ets2", on_game_select=None, **kwargs):
        super().__init__(master, fg_color=THEMES["light"]["bg"], **kwargs)
        self.profile = profile
        self.game = game
        self.on_game_select = on_game_select
        self.all_mods = mods
        self.active_mod_filenames = read_active_mods(self.profile.path)
        self.mods_by_id = {m.internal_id: m for m in self.all_mods}
        self.cloud = FirebaseClient()
        self.current_view = "Dashboard"
        self.mode = get_theme_mode()
        self.palette = THEMES[self.mode]
        self._image_cache: list[CTkImage] = []
        self._thumb_cache: dict[str, CTkImage] = {}

        ctk.set_appearance_mode("Dark" if self.mode == "dark" else "Light")
        threading.Thread(target=self._preprocess_thumbs, daemon=True).start()
        self._build_shell()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_shell(self):
        self.palette = THEMES[self.mode]
        self.configure(fg_color=self.palette["bg"])
        for child in self.winfo_children():
            child.destroy()

        self.sidebar = ctk.CTkFrame(self, width=232, fg_color=self.palette["surface"], corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.content = ctk.CTkFrame(self, fg_color=self.palette["bg"], corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)

        self._build_sidebar()
        self._render_view()

    def _build_sidebar(self):
        p = self.palette
        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=20, pady=(24, 28))

        icon_path = get_logo_path()
        if icon_path:
            try:
                from PIL import Image
                img = Image.open(icon_path)
                self.logo_ctk = CTkImage(light_image=img, dark_image=img, size=(28, 28))
                ctk.CTkLabel(brand, image=self.logo_ctk, text="").pack(side="left", padx=(0, 10))
            except Exception:
                pass
        ctk.CTkLabel(
            brand, text="TRUCK MANAGER",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=p["text"],
        ).pack(side="left")

        nav_items = [
            ("Dashboard", txt("home")),
            ("Profiles", txt("profiles")),
            ("Orden", txt("order")),
            ("Settings", txt("settings")),
            ("About", txt("about")),
        ]
        for key, label in nav_items:
            self._nav_button(key, label).pack(fill="x", padx=16, pady=4)

        bottom = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=20, pady=22)
        ctk.CTkLabel(bottom, text=txt("theme"), text_color=p["muted"], anchor="w").pack(fill="x")
        self.theme_switch = ctk.CTkSegmentedButton(
            bottom,
            values=["Light", "Dark"],
            command=self._set_theme,
            selected_color=p["accent"],
            selected_hover_color=p["accent"],
            unselected_color=p["surface_2"],
            unselected_hover_color=p["border"],
        )
        self.theme_switch.pack(fill="x", pady=(8, 18))
        self.theme_switch.set(get_theme_label())
        ctk.CTkLabel(bottom, text=txt("connected"), text_color=p["success"], anchor="w").pack(fill="x")

    def _nav_button(self, key: str, label: str):
        p = self.palette
        selected = self.current_view == key
        return ctk.CTkButton(
            self.sidebar,
            text=label,
            height=42,
            corner_radius=8,
            anchor="w",
            fg_color=p["accent_soft"] if selected else "transparent",
            hover_color=p["surface_2"],
            text_color=p["accent"] if selected else p["text"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold" if selected else "normal"),
            command=lambda k=key: self._switch_view(k),
        )

    def _set_theme(self, value: str):
        set_theme_label(value)
        self.mode = get_theme_mode()
        self._build_shell()

    def _switch_view(self, key: str):
        if key == "Settings":
            self._open_settings()
            return
        self.current_view = key
        self._build_shell()

    def _render_view(self):
        p = self.palette
        for child in self.content.winfo_children():
            child.destroy()

        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.pack(fill="x", padx=36, pady=(34, 20))

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            left, text=self.current_view,
            font=ctk.CTkFont(family=FONT_FAMILY, size=24, weight="bold"),
            text_color=p["text"],
            anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            left,
            text=txt("dashboard_subtitle").format(game=GAME_CONFIGS[self.game]["name"], profile=self.profile.display_name),
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=p["muted"],
            anchor="w",
        ).pack(fill="x", pady=(6, 0))

        game_row = ctk.CTkFrame(header, fg_color="transparent")
        game_row.pack(side="right")
        self._action_button(game_row, GAME_CONFIGS[self.game]["short"], self._go_game_select, width=72).pack(side="left", padx=(0, 8))
        self._action_button(game_row, txt("games"), self._go_game_select, width=86).pack(side="left")

        if self.current_view == "Dashboard":
            self._view_dashboard()
        elif self.current_view == "Profiles":
            self._view_profiles()
        elif self.current_view == "Orden":
            self._view_order()
        elif self.current_view == "Presets":
            self._view_presets()
        elif self.current_view == "About":
            self._view_about()

    def _main_panel(self):
        panel = ctk.CTkFrame(
            self.content,
            fg_color=self.palette["surface"],
            border_color=self.palette["border"],
            border_width=1,
            corner_radius=12,
        )
        panel.pack(fill="both", expand=True, padx=36, pady=(0, 28))
        return panel

    # ------------------------------------------------------------------
    # Views
    # ------------------------------------------------------------------
    def _view_dashboard(self):
        p = self.palette
        panel = self._main_panel()
        top = ctk.CTkFrame(panel, fg_color="transparent")
        top.pack(fill="x", padx=18, pady=18)

        active_count = len(self.active_mod_filenames)
        workshop_count = len([m for m in self.all_mods if m.source == "workshop"])
        local_count = len([m for m in self.all_mods if m.source == "local"])
        cards = [
            ("profiles", txt("profiles"), txt("current_profile"), 1, p["accent"], self._go_profiles),
            ("mods", txt("mods"), txt("installed_locally"), local_count, p["success"], lambda: self._switch_view("Orden")),
            ("workshop", txt("workshop"), txt("subscribed_mods"), workshop_count, p["purple"], lambda: self._switch_view("Orden")),
            ("order", txt("order"), txt("active_mods"), active_count, p["warning"], lambda: self._switch_view("Orden")),
        ]
        for icon_key, title, desc, value, color, command in cards:
            self._summary_card(top, icon_key, title, desc, value, color, command).pack(side="left", fill="both", expand=True, padx=8)

        bottom = ctk.CTkFrame(panel, fg_color="transparent")
        bottom.pack(fill="both", expand=True, padx=26, pady=(8, 26))

        quick = self._sub_panel(bottom, txt("quick_actions"))
        quick.pack(side="left", fill="both", expand=True, padx=(0, 12))
        actions = [
            (txt("save_load_order"), self._save_to_game),
            (txt("launch_game"), self._launch_game),
            (txt("import_preset_code"), self._import_preset),
            (txt("open_settings"), self._open_settings),
        ]
        for label, cmd in actions:
            self._quick_action(quick, label, cmd).pack(fill="x", padx=18, pady=3)

        recent = self._sub_panel(bottom, txt("recent_profile"))
        recent.pack(side="left", fill="both", expand=True, padx=(12, 0))
        self._info_line(recent, self.profile.display_name, txt("active"), p["success"]).pack(fill="x", padx=18, pady=(16, 8))
        if self.profile.driver_name:
            self._info_line(recent, txt("driver"), self.profile.driver_name, p["muted"]).pack(fill="x", padx=18, pady=8)
        if self.profile.level is not None:
            self._info_line(recent, txt("level"), str(self.profile.level), p["muted"]).pack(fill="x", padx=18, pady=8)
        self._quick_action(recent, txt("view_order"), lambda: self._switch_view("Orden")).pack(fill="x", padx=18, pady=(16, 0))

    def _view_profiles(self):
        panel = self._main_panel()
        self._section_title(panel, txt("selected_profile"))
        self._profile_card(panel, self.profile).pack(fill="x", padx=22, pady=(0, 12))
        self._action_row(panel, [
            (txt("edit_profile"), self._open_profile_editor, self.palette["accent"]),
            (txt("change_game"), self._go_game_select, None),
            (txt("settings"), self._open_settings, None),
        ])

    def _view_order(self):
        panel = self._main_panel()
        self._section_title(panel, txt("order"))
        self._action_row(panel, [
            (txt("save_to_game"), self._save_to_game, self.palette["success"]),
            (txt("launch_game"), self._launch_game, self.palette["accent"]),
            (txt("clear_order"), self._clear_load_order, self.palette["danger"]),
        ])
        self._action_row(panel, [
            (txt("my_presets"), self._show_my_presets, None),
            (txt("import_code"), self._import_preset, None),
            (txt("share_preset"), self._share_preset, self.palette["accent"]),
        ])

        columns = ctk.CTkFrame(panel, fg_color="transparent")
        columns.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        left_col = ctk.CTkFrame(columns, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right_col = ctk.CTkFrame(columns, fg_color="transparent")
        right_col.pack(side="left", fill="both", expand=True, padx=(10, 0))

        active_ids = {item.split("|")[0].strip() for item in self.active_mod_filenames}
        inactive_mods = [m for m in sorted(self.all_mods, key=lambda item: item.name.lower()) if m.internal_id not in active_ids]
        active_items = list(reversed(self.active_mod_filenames))

        ctk.CTkLabel(
            left_col,
            text=f"{txt('available_mods')} ({len(inactive_mods)})",
            text_color=self.palette["text"],
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            right_col,
            text=f"{txt('load_order')} ({len(active_items)})",
            text_color=self.palette["text"],
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        scroll_inactive = ctk.CTkScrollableFrame(
            left_col,
            fg_color=self.palette["surface"],
            border_color=self.palette["border"],
            border_width=1,
            corner_radius=12,
        )
        scroll_inactive.pack(fill="both", expand=True)

        scroll_active = ctk.CTkScrollableFrame(
            right_col,
            fg_color=self.palette["surface"],
            border_color=self.palette["border"],
            border_width=1,
            corner_radius=12,
        )
        scroll_active.pack(fill="both", expand=True)

        if not inactive_mods:
            ctk.CTkLabel(scroll_inactive, text=txt("no_inactive_mods"), text_color=self.palette["muted"]).pack(pady=30)
        else:
            for mod in inactive_mods:
                self._mod_row(scroll_inactive, mod, False).pack(fill="x", padx=8, pady=5)

        if not active_items:
            ctk.CTkLabel(scroll_active, text=txt("no_active_mods_yet"), text_color=self.palette["muted"]).pack(pady=30)
        else:
            for raw in active_items:
                clean = raw.split("|")[0].strip()
                mod = self.mods_by_id.get(clean) or Mod(name=f"[MISSING] {raw}", filename=raw, path=Path(""), source="unknown")
                self._mod_row(scroll_active, mod, True).pack(fill="x", padx=8, pady=5)

    def _view_mods(self, source: Optional[str]):
        panel = self._main_panel()
        title = txt("workshop_mods_title") if source == "workshop" else txt("all_mods")
        self._section_title(panel, title)
        scroll = ctk.CTkScrollableFrame(panel, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        mods = [m for m in self.all_mods if source is None or m.source == source]
        active_ids = {item.split("|")[0].strip() for item in self.active_mod_filenames}
        if not mods:
            ctk.CTkLabel(scroll, text=txt("no_mods_found"), text_color=self.palette["muted"]).pack(pady=30)
            return
        for mod in sorted(mods, key=lambda m: m.name.lower()):
            self._mod_row(scroll, mod, mod.internal_id in active_ids).pack(fill="x", pady=5)

    def _view_load_order(self):
        panel = self._main_panel()
        self._section_title(panel, txt("load_order"))
        self._action_row(panel, [
            (txt("save_to_game"), self._save_to_game, self.palette["success"]),
            (txt("clear_order"), self._clear_load_order, self.palette["danger"]),
        ])
        scroll = ctk.CTkScrollableFrame(panel, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        items = list(reversed(self.active_mod_filenames))
        if not items:
            ctk.CTkLabel(scroll, text=txt("no_active_mods_yet"), text_color=self.palette["muted"]).pack(pady=30)
            return
        for raw in items:
            clean = raw.split("|")[0].strip()
            mod = self.mods_by_id.get(clean) or Mod(name=f"[MISSING] {raw}", filename=raw, path=Path(""), source="unknown")
            self._mod_row(scroll, mod, True).pack(fill="x", pady=5)

    def _view_presets(self):
        panel = self._main_panel()
        self._section_title(panel, txt("presets"))
        self._action_row(panel, [
            (txt("my_presets"), self._show_my_presets, None),
            (txt("import_code"), self._import_preset, None),
            (txt("share_preset"), self._share_preset, self.palette["accent"]),
        ])
        ctk.CTkLabel(
            panel,
            text=txt("presets_description"),
            text_color=self.palette["muted"],
            anchor="w",
        ).pack(fill="x", padx=22, pady=(0, 16))

    def _view_about(self):
        panel = self._main_panel()
        self._section_title(panel, txt("about"))
        ctk.CTkLabel(
            panel,
            text=txt("about_text").format(app=APP_NAME, version=APP_VERSION),
            text_color=self.palette["muted"],
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=22, pady=(0, 22))

    # ------------------------------------------------------------------
    # Components
    # ------------------------------------------------------------------
    def _summary_card(self, parent, icon_key, title, desc, value, color, command):
        p = self.palette
        card = ctk.CTkFrame(parent, fg_color=p["card"], border_color=p["border"], border_width=1, corner_radius=12)

        icon_wrap = ctk.CTkFrame(card, width=54, height=54, fg_color=p["surface_2"], corner_radius=27)
        icon_wrap.pack(anchor="w", padx=20, pady=(22, 14))
        icon_wrap.pack_propagate(False)

        icon = self._dashboard_icon(icon_key)
        if icon:
            ctk.CTkLabel(icon_wrap, image=icon, text="").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(card, text=title, text_color=p["text"], font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20)
        ctk.CTkLabel(card, text=desc, text_color=p["muted"], justify="left").pack(anchor="w", padx=20, pady=(10, 22))
        ctk.CTkLabel(card, text=str(value), text_color=color, font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=20)
        ctk.CTkButton(card, text=txt("open"), command=command, width=78, height=30, fg_color="transparent", hover_color=p["surface_2"], text_color=p["accent"]).pack(anchor="w", padx=14, pady=(4, 18))
        return card

    def _dashboard_icon(self, key: str):
        icon_name = DASHBOARD_ICONS.get(key)
        if not icon_name:
            return None
        cache_key = f"dashboard:{key}"
        if cache_key in self._thumb_cache:
            return self._thumb_cache[cache_key]
        candidates = [
            get_app_dir() / "ui" / "assets" / icon_name,
            get_app_dir() / "assets" / icon_name,
            Path(__file__).resolve().parent / "assets" / icon_name,
        ]
        path = next((candidate for candidate in candidates if candidate.exists()), None)
        if path is None:
            return None
        image = Image.open(path)
        icon = CTkImage(light_image=image, dark_image=image, size=(30, 30))
        self._thumb_cache[cache_key] = icon
        return icon

    def _sub_panel(self, parent, title: str):
        p = self.palette
        frame = ctk.CTkFrame(parent, fg_color=p["card"], border_color=p["border"], border_width=1, corner_radius=12)
        ctk.CTkLabel(frame, text=title, text_color=p["text"], font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=18, pady=(18, 8))
        return frame

    def _quick_action(self, parent, label: str, command):
        p = self.palette
        return ctk.CTkButton(parent, text=label, command=command, height=38, anchor="w", fg_color="transparent", hover_color=p["surface_2"], text_color=p["text"])

    def _info_line(self, parent, left: str, right: str, right_color: str):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(row, text=left, text_color=self.palette["text"], anchor="w").pack(side="left")
        ctk.CTkLabel(row, text=right, text_color=right_color, anchor="e").pack(side="right")
        return row

    def _section_title(self, parent, title: str):
        ctk.CTkLabel(parent, text=title, text_color=self.palette["text"], font=ctk.CTkFont(size=17, weight="bold"), anchor="w").pack(fill="x", padx=22, pady=(20, 14))

    def _profile_card(self, parent, profile: Profile):
        p = self.palette
        card = ctk.CTkFrame(parent, fg_color=p["card"], border_color=p["border"], border_width=1, corner_radius=12)
        ctk.CTkLabel(card, text=profile.display_name, text_color=p["text"], font=ctk.CTkFont(size=16, weight="bold"), anchor="w").pack(fill="x", padx=18, pady=(16, 4))
        detail = f"{profile.hex_id}"
        if profile.driver_name:
            detail += f"  -  {profile.driver_name}"
        if profile.level is not None:
            detail += f"  -  {txt("level")} {profile.level}"
        ctk.CTkLabel(card, text=detail, text_color=p["muted"], anchor="w").pack(fill="x", padx=18, pady=(0, 16))
        return card

    def _mod_row(self, parent, mod: Mod, active: bool):
        p = self.palette
        row = ctk.CTkFrame(parent, fg_color=p["card"], border_color=p["border"], border_width=1, corner_radius=10)
        img = self._thumb_cache.get(mod.internal_id)
        if img:
            self._image_cache.append(img)
            ctk.CTkLabel(row, image=img, text="").pack(side="left", padx=10, pady=8)
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, padx=8, pady=8)
        ctk.CTkLabel(info, text=mod.name, text_color=p["text"], font=ctk.CTkFont(size=13, weight="bold"), anchor="w").pack(fill="x")
        ctk.CTkLabel(info, text=mod.source.upper(), text_color=p["muted"], font=ctk.CTkFont(size=11), anchor="w").pack(fill="x", pady=(4, 0))
        sw = ctk.CTkSwitch(row, text="", progress_color=p["accent"], command=lambda m=mod: self._toggle_mod(m, bool(sw.get())))
        if active:
            sw.select()
        sw.pack(side="right", padx=16)
        return row

    def _action_row(self, parent, items):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=22, pady=(0, 18))
        for label, command, color in items:
            self._action_button(row, label, command, fg=color).pack(side="left", padx=(0, 8))

    def _action_button(self, parent, text, command, width=120, fg=None):
        p = self.palette
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            width=width,
            height=34,
            corner_radius=8,
            fg_color=fg or p["surface_2"],
            hover_color=fg or p["border"],
            text_color="#FFFFFF" if fg else p["text"],
        )

    # ------------------------------------------------------------------
    # Behavior
    # ------------------------------------------------------------------
    def _preprocess_thumbs(self):
        from PIL import Image as PILImage
        for mod in self.all_mods:
            if mod.thumbnail:
                try:
                    resized = mod.thumbnail.resize((72, 54), PILImage.Resampling.BILINEAR)
                    self._thumb_cache[mod.internal_id] = CTkImage(light_image=resized, dark_image=resized, size=(72, 54))
                except Exception:
                    pass
        self.after(0, self._render_view)

    def _toggle_mod(self, mod: Mod, state: bool):
        if state:
            if not any(f.split("|")[0].strip() == mod.internal_id for f in self.active_mod_filenames):
                self.active_mod_filenames.append(mod.sii_entry)
        else:
            self.active_mod_filenames = [f for f in self.active_mod_filenames if f.split("|")[0].strip() != mod.internal_id]
        self._render_view()

    def _go_profiles(self):
        self._switch_view("Profiles")

    def _go_game_select(self):
        if self.on_game_select:
            self.on_game_select()

    def _open_profile_editor(self):
        try:
            profile_data = read_editable_profile(self.profile.path)
            game_data = read_game_editor_data(self.profile.path)
        except Exception as e:
            self._show_dialog(txt("error"), str(e))
            return

        p = self.palette
        dlg = ctk.CTkToplevel(self)
        dlg.title(txt("profile_editor"))
        dlg.geometry("720x650")
        dlg.minsize(640, 560)
        dlg.overrideredirect(True)
        DialogTitleBar(dlg, dlg, txt("profile_editor")).pack(fill="x", side="top")
        dlg.configure(fg_color=p["bg"])
        dlg.grab_set()
        dlg.focus_force()

        shell = ctk.CTkFrame(dlg, fg_color=p["bg"])
        shell.pack(fill="both", expand=True, padx=22, pady=18)
        ctk.CTkLabel(shell, text=txt("profile_save_warning"), text_color=p["warning"], anchor="w", wraplength=620).pack(fill="x", pady=(0, 12))

        tabs = ctk.CTkTabview(
            shell,
            fg_color=p["surface"],
            segmented_button_selected_color=p["accent"],
            segmented_button_selected_hover_color=p["accent_hover"],
            segmented_button_unselected_color=p["surface_2"],
            segmented_button_unselected_hover_color=p["border"],
            text_color=p["text"],
        )
        tabs.pack(fill="both", expand=True)
        tab_profile = tabs.add(txt("editor_profile_section"))
        tab_economy = tabs.add(txt("editor_economy_section"))
        tab_skills = tabs.add(txt("editor_skills_section"))
        tab_company = tabs.add(txt("editor_company_section"))

        entries = {}
        game_entries = {}
        skill_sliders = {}

        def add_entry(parent, key: str, label: str, value: str, enabled: bool = True, target: dict = entries, limit: str = ""):
            title = f"{label} ({limit})" if limit else label
            ctk.CTkLabel(parent, text=title, text_color=p["text"], anchor="w", font=ctk.CTkFont(size=13, weight="bold")).pack(fill="x", pady=(8, 4), padx=12)
            entry = ctk.CTkEntry(parent, height=34, fg_color=p["bg"], border_color=p["border"], text_color=p["text"])
            entry.insert(0, value)
            if not enabled:
                entry.configure(state="disabled")
            entry.pack(fill="x", padx=12)
            target[key] = entry
            if not enabled:
                ctk.CTkLabel(parent, text=txt("field_not_found"), text_color=p["muted"], anchor="w").pack(fill="x", padx=12, pady=(2, 0))

        def add_slider(parent, store: dict, key: str, label: str, value, min_value: int, max_value: int, enabled: bool = True, value_formatter=None):
            formatter = value_formatter or (lambda item: str(int(round(float(item)))))
            current = min_value
            try:
                current = max(min_value, min(max_value, int(float(value))))
            except (TypeError, ValueError):
                enabled = False
            header = ctk.CTkFrame(parent, fg_color="transparent")
            header.pack(fill="x", padx=12, pady=(10, 2))
            ctk.CTkLabel(header, text=f"{label} ({formatter(min_value)} - {formatter(max_value)})", text_color=p["text"], anchor="w", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
            value_label = ctk.CTkLabel(header, text=formatter(current), text_color=p["accent"], width=120)
            value_label.pack(side="right")
            slider = ctk.CTkSlider(parent, from_=min_value, to=max_value, number_of_steps=max_value - min_value, progress_color=p["accent"], button_color=p["accent"], button_hover_color=p["accent_hover"])
            slider.set(current)
            slider.pack(fill="x", padx=12, pady=(0, 4))
            if not enabled:
                slider.configure(state="disabled")
                ctk.CTkLabel(parent, text=txt("field_not_found"), text_color=p["muted"], anchor="w").pack(fill="x", padx=12, pady=(2, 0))
            def on_slide(raw):
                value_label.configure(text=formatter(raw))
            slider.configure(command=on_slide)
            store[key] = (slider, value_label, enabled)

        add_entry(tab_profile, "profile_name", txt("profile_name"), profile_data.profile_name)
        add_entry(tab_profile, "online_user_name", txt("driver_name"), profile_data.online_user_name)
        add_entry(tab_profile, "company_name", txt("company_name"), profile_data.company_name)
        add_slider(tab_profile, skill_sliders, "cached_experience", txt("experience"), profile_data.level or 1, 1, 150, profile_data.cached_experience is not None)

        if game_data.save_path:
            ctk.CTkLabel(tab_economy, text=f"{txt('save_file')}: {game_data.save_path}", text_color=p["muted"], anchor="w", wraplength=620).pack(fill="x", padx=12, pady=(10, 4))
            economy_labels = {
                "money_account": txt("money"),
                "bank_loan": txt("bank_loan"),
                "total_distance": txt("total_distance"),
            }
            money_value = game_data.fields.get("money_account")
            add_slider(tab_economy, skill_sliders, "money_account", txt("money"), money_value or 1, 1, 1_000_000_000, money_value is not None, lambda item: f"{int(round(float(item))):,}".replace(",", "."))
            for key in [item for item in GAME_FIELD_DEFS["economy"] if item != "money_account"]:
                value = game_data.fields.get(key)
                add_entry(tab_economy, key, economy_labels[key], "" if value is None else str(value), value is not None, game_entries, "0+")

            skill_labels = {
                "adr": txt("skill_adr"),
                "long_dist": txt("skill_long_dist"),
                "heavy": txt("skill_heavy"),
                "fragile": txt("skill_fragile"),
                "urgent": txt("skill_urgent"),
                "mechanical": txt("skill_mechanical"),
            }
            skill_limits = {"adr": 63, "long_dist": 6, "heavy": 6, "fragile": 6, "urgent": 6, "mechanical": 6}
            for key in GAME_FIELD_DEFS["skills"]:
                value = game_data.fields.get(key)
                add_slider(tab_skills, skill_sliders, key, skill_labels[key], "" if value is None else str(value), 0, skill_limits[key], value is not None)
        else:
            for parent in (tab_economy, tab_skills):
                ctk.CTkLabel(parent, text=txt("game_save_not_found"), text_color=p["muted"], wraplength=580, justify="left").pack(fill="x", padx=12, pady=18)

        ctk.CTkLabel(tab_company, text=txt("read_only_summary"), text_color=p["muted"], anchor="w").pack(fill="x", padx=12, pady=(14, 10))
        for label, value in [
            (txt("garages"), game_data.garage_count),
            (txt("trucks"), game_data.truck_count),
            (txt("drivers"), game_data.driver_count),
        ]:
            row = ctk.CTkFrame(tab_company, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=6)
            ctk.CTkLabel(row, text=label, text_color=p["text"], anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")
            ctk.CTkLabel(row, text=str(value), text_color=p["accent"], anchor="e").pack(side="right")

        def _parse_number(key: str, label: str, raw: str):
            raw = raw.strip()
            if raw == "":
                return None
            try:
                if "." in raw:
                    float(raw)
                    return raw
                int(raw)
                return raw
            except ValueError:
                raise ValueError(txt("invalid_number").format(field=label))

        def save():
            try:
                level_slider, _level_label, level_enabled = skill_sliders.get("cached_experience", (None, None, False))
                selected_level = int(round(float(level_slider.get()))) if level_slider and level_enabled else None
                profile_values = {
                    "profile_name": entries["profile_name"].get(),
                    "online_user_name": entries["online_user_name"].get(),
                    "company_name": entries["company_name"].get(),
                    "cached_experience": ((selected_level - 1) * 5000) if selected_level else None,
                }
                game_values = {}
                for key, entry in game_entries.items():
                    if str(entry.cget("state")) == "disabled":
                        continue
                    labels = {
                        "bank_loan": txt("bank_loan"),
                        "total_distance": txt("total_distance"),
                    }
                    parsed = _parse_number(key, labels.get(key, key), entry.get())
                    if parsed is not None:
                        game_values[key] = parsed
                for key, slider_data in skill_sliders.items():
                    if key == "cached_experience":
                        continue
                    slider, _value_label, enabled = slider_data
                    if enabled:
                        game_values[key] = str(int(round(float(slider.get()))))
            except ValueError as e:
                self._show_dialog(txt("error"), str(e))
                return

            try:
                write_editable_profile(self.profile.path, profile_values)
                if game_data.save_path and game_values:
                    write_game_editor_data(game_data.save_path, game_values)
                fresh = read_editable_profile(self.profile.path)
                self.profile.display_name = fresh.profile_name or self.profile.display_name
                self.profile.driver_name = fresh.online_user_name or fresh.company_name or self.profile.driver_name
                self.profile.level = fresh.level
                dlg.destroy()
                self._render_view()
                self._show_dialog(txt("success"), txt("profile_saved"))
            except Exception as e:
                self._show_dialog(txt("error"), str(e))

        actions = ctk.CTkFrame(shell, fg_color="transparent")
        actions.pack(fill="x", pady=(18, 0))
        ctk.CTkButton(actions, text=txt("cancel"), fg_color=p["surface_2"], hover_color=p["border"], text_color=p["text"], command=dlg.destroy).pack(side="right", padx=(8, 0))
        ctk.CTkButton(actions, text=txt("save_profile"), fg_color=p["accent"], hover_color=p["accent_hover"], command=save).pack(side="right")
        self._center_window(dlg)

    def _open_settings(self):
        open_settings_dialog(self, self.game, on_saved=lambda: self._show_dialog(txt("settings"), txt("settings_saved")))

    def _save_to_game(self):
        try:
            write_active_mods(self.profile.path, self.active_mod_filenames)
            self._show_dialog(txt("success"), txt("save_success"))
        except Exception as e:
            self._show_dialog(txt("error"), f"{txt('save_error')} {e}")

    def _launch_game(self):
        try:
            write_active_mods(self.profile.path, self.active_mod_filenames)
            launch_game(self.game)
        except Exception as e:
            self._show_dialog(txt("error"), str(e))

    def _clear_load_order(self):
        self.active_mod_filenames = []
        self._render_view()

    def _share_preset(self):
        if not self.cloud.is_configured():
            self._show_dialog("Cloud Error", "Firebase is not configured.")
            return
        preset_name = self._show_input_dialog(txt("share_preset"), txt("enter_preset_name"))
        if not preset_name:
            return
        def task():
            try:
                code = self.cloud.upload_preset(preset_name, self.active_mod_filenames)
                self.after(0, lambda: self._show_dialog(txt("preset_shared"), f"{txt('your_code_is')}\n\n{code}\n\n{txt('share_with_friends')}"))
            except Exception as e:
                self.after(0, lambda err=str(e): self._show_dialog("Error", err))
        threading.Thread(target=task, daemon=True).start()

    def _import_preset(self):
        if not self.cloud.is_configured():
            self._show_dialog("Cloud Error", "Firebase is not configured.")
            return
        code = self._show_input_dialog(txt("import_preset"), txt("enter_code"))
        if not code:
            return
        def task():
            try:
                mods = self.cloud.download_preset(code)
                if mods is None:
                    self.after(0, lambda: self._show_dialog(txt("error"), txt("invalid_code")))
                else:
                    self.active_mod_filenames = mods
                    self.after(0, self._render_view)
                    self.after(0, lambda: self._show_dialog(txt("success"), txt("preset_imported")))
            except Exception as e:
                self.after(0, lambda err=str(e): self._show_dialog("Error", err))
        threading.Thread(target=task, daemon=True).start()

    def _show_my_presets(self):
        if not self.cloud.is_configured():
            self._show_dialog("Cloud Error", "Firebase is not configured.")
            return

        def task():
            try:
                presets = self.cloud.get_my_presets()
                self.after(0, lambda: self._open_my_presets_window(presets))
            except Exception as e:
                self.after(0, lambda err=str(e): self._show_dialog("Error", err))

        threading.Thread(target=task, daemon=True).start()

    def _open_my_presets_window(self, presets: list[dict]):
        p = self.palette
        top = ctk.CTkToplevel(self)
        top.title(txt("my_shared_presets"))
        top.geometry("620x680")
        top.minsize(560, 520)
        top.overrideredirect(True)
        DialogTitleBar(top, top, txt("my_shared_presets")).pack(fill="x", side="top")
        top.configure(fg_color=p["bg"])
        top.grab_set()
        top.focus_force()

        shell = ctk.CTkFrame(top, fg_color=p["bg"])
        shell.pack(fill="both", expand=True, padx=22, pady=18)

        icon_path = get_logo_path()
        if icon_path:
            try:
                img = Image.open(icon_path)
                logo_ctk = CTkImage(light_image=img, dark_image=img, size=(48, 48))
                top._logo_ref = logo_ctk
                ctk.CTkLabel(shell, image=logo_ctk, text="").pack(pady=(4, 10))
            except Exception:
                pass

        ctk.CTkLabel(
            shell,
            text=txt("click_to_copy"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=p["text"],
        ).pack(anchor="w", pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(
            shell,
            fg_color=p["surface"],
            border_color=p["border"],
            border_width=1,
            corner_radius=12,
        )
        scroll.pack(fill="both", expand=True)

        if not presets:
            ctk.CTkLabel(scroll, text=txt("no_presets_yet"), text_color=p["muted"]).pack(pady=32)

        def copy_code(code: str):
            top.clipboard_clear()
            top.clipboard_append(code or "")
            self._show_dialog(txt("copied"), txt("code_copied"))

        ordered_presets = sorted(
            presets,
            key=lambda item: (-int(item.get("timestamp") or 0), (item.get("preset_name") or item.get("profile_name") or "").lower()),
        )
        for index, preset in enumerate(ordered_presets, start=1):
            code = preset.get("code", "?")
            name = preset.get("preset_name") or preset.get("profile_name") or "Unnamed"
            card = ctk.CTkFrame(scroll, fg_color=p["card"], border_color=p["border"], border_width=1, corner_radius=10)
            card.pack(fill="x", padx=12, pady=8)

            ctk.CTkLabel(
                card,
                text=f"{index}. {name}",
                text_color=p["accent"],
                font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
                anchor="w",
            ).pack(fill="x", padx=14, pady=(12, 2))
            ctk.CTkLabel(
                card,
                text=f"Code: {code}",
                text_color=p["muted"],
                anchor="w",
            ).pack(fill="x", padx=14)

            actions = ctk.CTkFrame(card, fg_color="transparent")
            actions.pack(fill="x", padx=10, pady=12)
            ctk.CTkButton(
                actions,
                text=txt("copy_code"),
                width=120,
                fg_color=p["accent"],
                hover_color=p["accent_hover"],
                command=lambda c=code: copy_code(c),
            ).pack(side="left", padx=(0, 8))
            ctk.CTkButton(
                actions,
                text=txt("delete"),
                width=96,
                fg_color=p["surface_2"],
                hover_color=p["danger"],
                text_color=p["text"],
                command=lambda c=code: self._delete_preset_flow(c, top),
            ).pack(side="right")

        ctk.CTkButton(
            shell,
            text=txt("ok"),
            width=120,
            fg_color=p["surface_2"],
            hover_color=p["border"],
            text_color=p["text"],
            command=top.destroy,
        ).pack(pady=(14, 0))

        self._center_window(top)

    def _delete_preset_flow(self, code: str, parent_win: ctk.CTkToplevel):
        def on_confirm():
            try:
                self.cloud.delete_preset(code)
                self._show_dialog(txt("success"), txt("preset_deleted"))
                parent_win.destroy()
                self._show_my_presets()
            except Exception as e:
                self._show_dialog(txt("error"), str(e))

        self._show_confirm_dialog(txt("delete"), txt("confirm_delete"), on_confirm)

    # ------------------------------------------------------------------
    # Dialogs
    # ------------------------------------------------------------------
    def _show_dialog(self, title: str, text: str):
        dlg = ctk.CTkToplevel(self)
        dlg.title(title)
        dlg.geometry("480x300")
        dlg.overrideredirect(True)
        DialogTitleBar(dlg, dlg, title).pack(fill="x", side="top")
        dlg.configure(fg_color=self.palette["surface"])
        ctk.CTkLabel(dlg, text=text, text_color=self.palette["text"], wraplength=390, justify="center").pack(expand=True, padx=24, pady=24)
        ctk.CTkButton(dlg, text=txt("ok"), command=dlg.destroy, fg_color=self.palette["accent"]).pack(pady=(0, 22))
        dlg.grab_set()
        dlg.focus_force()

    def _show_input_dialog(self, title: str, text: str) -> Optional[str]:
        result = [None]
        dlg = ctk.CTkToplevel(self)
        dlg.title(title)
        dlg.geometry("480x300")
        dlg.overrideredirect(True)
        DialogTitleBar(dlg, dlg, title).pack(fill="x", side="top")
        dlg.configure(fg_color=self.palette["surface"])
        ctk.CTkLabel(dlg, text=text, text_color=self.palette["text"]).pack(pady=(48, 10))
        entry = ctk.CTkEntry(dlg, width=310)
        entry.pack(pady=10)
        entry.focus_set()
        def ok(*args):
            result[0] = entry.get()
            dlg.destroy()
        ctk.CTkButton(dlg, text=txt("ok"), command=ok, fg_color=self.palette["accent"]).pack(pady=(14, 0))
        dlg.bind("<Return>", ok)
        dlg.bind("<Escape>", lambda e: dlg.destroy())
        dlg.grab_set()
        self.wait_window(dlg)
        return result[0]

    def _show_confirm_dialog(self, title: str, text: str, on_confirm: callable):
        p = self.palette
        dlg = ctk.CTkToplevel(self)
        dlg.title(title)
        dlg.geometry("480x320")
        dlg.overrideredirect(True)
        DialogTitleBar(dlg, dlg, title).pack(fill="x", side="top")
        dlg.configure(fg_color=p["surface"])

        ctk.CTkLabel(
            dlg,
            text=text,
            text_color=p["text"],
            wraplength=380,
            justify="center",
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_BODY),
        ).pack(expand=True, padx=24, pady=28)

        def cancel(*args):
            dlg.destroy()

        def confirm(*args):
            dlg.destroy()
            on_confirm()

        row = ctk.CTkFrame(dlg, fg_color="transparent")
        row.pack(pady=(0, 24))
        ctk.CTkButton(row, text=txt("delete"), fg_color=p["danger"], hover_color=p["danger"], command=confirm).pack(side="left", padx=8)
        ctk.CTkButton(row, text=txt("cancel"), fg_color=p["surface_2"], hover_color=p["border"], text_color=p["text"], command=cancel).pack(side="left", padx=8)
        dlg.bind("<Return>", confirm)
        dlg.bind("<Escape>", cancel)
        dlg.grab_set()
        dlg.focus_force()
        self._center_window(dlg)

    def _center_window(self, win: ctk.CTkToplevel):
        win.update_idletasks()
        root = self.winfo_toplevel()
        x = root.winfo_x() + max((root.winfo_width() - win.winfo_width()) // 2, 0)
        y = root.winfo_y() + max((root.winfo_height() - win.winfo_height()) // 2, 0)
        win.geometry(f"+{x}+{y}")
