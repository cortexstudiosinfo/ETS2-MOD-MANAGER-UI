"""
ui/phase1_profile.py - Profile Selection UI
"""
import customtkinter as ctk
from core.theme import get_theme, get_theme_label, set_theme_label

from core.config import *
from core.profile_utils import list_profiles, Profile
from ui.settings_dialog import open_settings_dialog


class Phase1ProfileView(ctk.CTkFrame):
    """
    Shows a list of profiles for the selected game for the user to pick.
    """
    def __init__(self, master, on_profile_selected: callable, game: str = "ets2",
                 on_back: callable = None, **kwargs):
        self.palette = get_theme()
        super().__init__(master, fg_color=self.palette["bg"], **kwargs)
        self.on_profile_selected = on_profile_selected
        self.on_back = on_back
        self.game = game
        self.profiles: list[Profile] = []

        self._build_ui()
        self.refresh_profiles()

    def _build_ui(self):
        # Clear existing widgets for language/theme switching
        self.palette = get_theme()
        self.configure(fg_color=self.palette["bg"])
        for widget in self.winfo_children():
            widget.destroy()

        # Logo
        from PIL import Image
        icon_path = get_logo_path()
        if icon_path:
            try:
                img = Image.open(icon_path)
                self.logo_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(64, 64))
                logo_lbl = ctk.CTkLabel(self, image=self.logo_ctk, text="")
                logo_lbl.pack(pady=(40, 0))
            except Exception:
                pass

        # Language and theme switcher
        lang_frame = ctk.CTkFrame(self, fg_color="transparent")
        lang_frame.place(relx=1.0, rely=0.0, anchor="ne", x=-20, y=20)
        
        def switch_lang(l):
            set_lang(l)
            self._build_ui()
            self.refresh_profiles()

        def switch_theme(value):
            set_theme_label(value)
            self._build_ui()
            self.refresh_profiles()

        btn_es = ctk.CTkButton(
            lang_frame, text="ES", width=40,
            fg_color=self.palette["accent"] if CUR_LANG == "es" else self.palette["surface_2"],
            hover_color=self.palette["accent_hover"],
            text_color="#FFFFFF" if CUR_LANG == "es" else self.palette["text"],
            command=lambda: switch_lang("es"),
        )
        btn_es.pack(side="left", padx=2)
        btn_en = ctk.CTkButton(
            lang_frame, text="EN", width=40,
            fg_color=self.palette["accent"] if CUR_LANG == "en" else self.palette["surface_2"],
            hover_color=self.palette["accent_hover"],
            text_color="#FFFFFF" if CUR_LANG == "en" else self.palette["text"],
            command=lambda: switch_lang("en"),
        )
        btn_en.pack(side="left", padx=2)

        theme_control = ctk.CTkSegmentedButton(
            lang_frame,
            values=["Light", "Dark"],
            command=switch_theme,
            width=126,
            selected_color=self.palette["accent"],
            selected_hover_color=self.palette["accent_hover"],
            unselected_color=self.palette["surface_2"],
            unselected_hover_color=self.palette["border"],
        )
        theme_control.pack(side="left", padx=(10, 2))
        theme_control.set(get_theme_label())

        self.header = ctk.CTkLabel(
            self, text=txt("select_profile"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_TITLE, weight="bold"),
            text_color=self.palette["text"]
        )
        self.header.pack(pady=(10, 4))

        from core.config import GAME_CONFIGS
        game_name = GAME_CONFIGS.get(self.game, {}).get("name", self.game.upper())
        ctk.CTkLabel(
            self, text=game_name,
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_BODY),
            text_color=self.palette["accent"]
        ).pack(pady=(0, 20))

        # Profile List Container
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color=self.palette["surface"], corner_radius=12, width=400, height=300
        )
        self.scroll_frame.pack(pady=10, fill="y", expand=False)

        # Bottom buttons row
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=20)

        ctk.CTkButton(
            btn_row, text=txt("back"), fg_color=self.palette["surface_2"], text_color=self.palette["muted"],
            hover_color=self.palette["border"], width=90,
            command=self._go_back
        ).pack(side="left", padx=6)

        self.btn_refresh = ctk.CTkButton(
            btn_row, text=txt("refresh"), fg_color=self.palette["surface_2"], text_color=self.palette["text"],
            hover_color=self.palette["border"], command=self.refresh_profiles
        )
        self.btn_refresh.pack(side="left", padx=6)

        ctk.CTkButton(
            btn_row, text=txt("settings"), fg_color=self.palette["surface_2"], text_color=self.palette["text"],
            hover_color=self.palette["border"], command=self._open_settings
        ).pack(side="left", padx=6)

    def _go_back(self):
        if self.on_back:
            self.on_back()

    def _open_settings(self):
        open_settings_dialog(self, self.game, on_saved=self.refresh_profiles)

    def refresh_profiles(self):
        """Loads profiles in a background thread to avoid freezing the UI."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(
            self.scroll_frame,
            text=txt("loading"),
            text_color=self.palette["muted"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_BODY),
        ).pack(pady=40)

        import threading
        threading.Thread(target=self._load_profiles_bg, daemon=True).start()

    def _load_profiles_bg(self):
        profiles = list_profiles(self.game)
        self.after(0, lambda: self._render_profiles(profiles))

    def _render_profiles(self, profiles):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        self.profiles = profiles

        if not self.profiles:
            from core.config import GAME_CONFIGS
            game_name = GAME_CONFIGS.get(self.game, {}).get("name", self.game.upper())

            ctk.CTkLabel(
                self.scroll_frame,
                text=txt("no_profiles_found"),
                font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_BODY, weight="bold"),
                text_color=self.palette["text"],
            ).pack(pady=(30, 6))

            ctk.CTkLabel(
                self.scroll_frame,
                text=txt("profile_help").format(game=game_name),
                font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_SMALL),
                text_color=self.palette["muted"],
                justify="left",
            ).pack(padx=20, pady=(0, 20))
            return

        for profile in self.profiles:
            # Outer card frame
            card = ctk.CTkFrame(
                self.scroll_frame,
                fg_color=self.palette["surface_2"],
                corner_radius=8,
            )
            card.pack(fill="x", padx=10, pady=5)
            card.bind("<Button-1>", lambda e, p=profile: self.on_profile_selected(p))

            # Main profile label  — profile name + hex id
            main_text = f'("{profile.hex_id}")  {profile.display_name}'
            lbl_main = ctk.CTkLabel(
                card,
                text=main_text,
                font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_BODY, weight="bold"),
                text_color=self.palette["text"],
                anchor="w",
            )
            lbl_main.pack(fill="x", padx=14, pady=(8, 0))
            lbl_main.bind("<Button-1>", lambda e, p=profile: self.on_profile_selected(p))

            # Secondary info: driver name + level
            parts = []
            if profile.driver_name:
                parts.append(f"🚛  {profile.driver_name}")
            if profile.level is not None:
                parts.append(f"{txt("level")} {profile.level}")
            if parts:
                lbl_info = ctk.CTkLabel(
                    card,
                    text="   •   ".join(parts),
                    font=ctk.CTkFont(family=FONT_FAMILY, size=max(FONT_SIZE_BODY - 2, 11)),
                    text_color=self.palette["muted"],
                    anchor="w",
                )
                lbl_info.pack(fill="x", padx=14, pady=(0, 8))
                lbl_info.bind("<Button-1>", lambda e, p=profile: self.on_profile_selected(p))
            else:
                card.configure(height=40)

            # Hover highlight
            def _on_enter(e, c=card): c.configure(fg_color=self.palette["card_hover"])
            def _on_leave(e, c=card): c.configure(fg_color=self.palette["surface_2"])
            for w in (card, lbl_main):
                w.bind("<Enter>", _on_enter)
                w.bind("<Leave>", _on_leave)
            if parts:
                lbl_info.bind("<Enter>", _on_enter)
                lbl_info.bind("<Leave>", _on_leave)
