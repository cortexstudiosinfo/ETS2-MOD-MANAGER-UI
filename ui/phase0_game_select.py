"""
ui/phase0_game_select.py - Game selection screen shown before anything else.
Detects installed games via Documents folder + Steam Workshop.
Always shows the screen — never auto-skips.
"""
import customtkinter as ctk
from PIL import Image
from core.theme import get_theme, get_theme_label, set_theme_label

from core.config import (
    COLOR_BG, COLOR_CARD, COLOR_CARD_HOVER, COLOR_SURFACE_2, COLOR_BORDER,
    COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_TEXT_MUTED, FONT_FAMILY, FONT_SIZE_TITLE, FONT_SIZE_BODY, FONT_SIZE_SMALL,
    GAME_CONFIGS, get_logo_path, APP_VERSION, CUR_LANG, set_lang, txt,
)


def _detect_installed_games() -> list[str]:
    """
    Returns installed game keys detected via:
    1. Documents folder existence
    2. Steam Workshop content folder (fallback)
    """
    from pathlib import Path
    docs = Path.home() / "Documents"
    found = []

    for key, cfg in GAME_CONFIGS.items():
        if (docs / cfg["documents_dir"]).exists():
            found.append(key)
            continue

        # Fallback: check Steam Workshop
        try:
            from core.mod_scanner import find_workshop_paths
            ws = find_workshop_paths(cfg["app_id"])
            if ws:
                found.append(key)
        except Exception:
            pass

    return found


class Phase0GameSelectView(ctk.CTkFrame):
    """
    Always-visible game selector. Shows only the games detected on this machine.
    Calls on_game_selected(game_key) when the user clicks a card.
    """
    def __init__(self, master, on_game_selected: callable, **kwargs):
        self.palette = get_theme()
        super().__init__(master, fg_color=self.palette["bg"], **kwargs)
        self.on_game_selected = on_game_selected
        self._installed = list(GAME_CONFIGS.keys())
        self._build_ui()

    def _build_ui(self):
        # Clear for rebuild on language/theme switch
        self.palette = get_theme()
        self.configure(fg_color=self.palette["bg"])
        for w in self.winfo_children():
            w.destroy()

        # Language switcher — top right
        lang_frame = ctk.CTkFrame(self, fg_color="transparent")
        lang_frame.place(relx=1.0, rely=0.0, anchor="ne", x=-20, y=20)

        def switch_lang(l):
            set_lang(l)
            self._build_ui()

        from core.config import CUR_LANG as _CUR
        ctk.CTkButton(
            lang_frame, text="ES", width=40,
            fg_color=self.palette["accent"] if _CUR == "es" else self.palette["surface_2"],
            hover_color=self.palette["accent_hover"],
            text_color="#FFFFFF" if _CUR == "es" else self.palette["text"],
            command=lambda: switch_lang("es"),
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            lang_frame, text="EN", width=40,
            fg_color=self.palette["accent"] if _CUR == "en" else self.palette["surface_2"],
            hover_color=self.palette["accent_hover"],
            text_color="#FFFFFF" if _CUR == "en" else self.palette["text"],
            command=lambda: switch_lang("en"),
        ).pack(side="left", padx=2)

        def switch_theme(value):
            set_theme_label(value)
            self._build_ui()

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

        # Logo
        icon_path = get_logo_path()
        if icon_path:
            try:
                img = Image.open(icon_path)
                self._logo_ref = ctk.CTkImage(light_image=img, dark_image=img, size=(80, 80))
                ctk.CTkLabel(self, image=self._logo_ref, text="").pack(pady=(50, 0))
            except Exception:
                pass

        ctk.CTkLabel(
            self, text=txt("app_title"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_TITLE, weight="bold"),
            text_color=self.palette["text"],
        ).pack(pady=(16, 4))

        ctk.CTkLabel(
            self, text=txt("select_game_subtitle"),
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_BODY),
            text_color=self.palette["muted"],
        ).pack(pady=(0, 50))

        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack()

        if not self._installed:
            ctk.CTkLabel(
                cards_frame, text=txt("no_supported_games"),
                text_color=self.palette["muted"],
                font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_BODY),
                justify="center",
            ).pack(pady=40)
        else:
            select_label = txt("select")
            for game_key in self._installed:
                self._build_card(cards_frame, game_key, GAME_CONFIGS[game_key], select_label)

        ctk.CTkLabel(
            self, text=f"v{APP_VERSION}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_SMALL),
            text_color=self.palette["muted"],
        ).pack(side="bottom", pady=20)

    def _build_card(self, parent, game_key: str, cfg: dict, select_label: str = None):
        card = ctk.CTkFrame(
            parent, fg_color=self.palette["card"], corner_radius=8,
            width=260, height=160,
        )
        card.pack(side="left", padx=14)
        card.pack_propagate(False)

        ctk.CTkLabel(
            card,
            text=cfg["short"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=36, weight="bold"),
            text_color=self.palette["accent"],
        ).pack(pady=(26, 2))

        ctk.CTkLabel(
            card,
            text=cfg["name"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_SMALL),
            text_color=self.palette["muted"],
        ).pack()

        ctk.CTkButton(
            card,
            text=select_label,
            command=lambda k=game_key: self.on_game_selected(k),
            fg_color=self.palette["accent"],
            hover_color=self.palette["accent_hover"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_BODY, weight="bold"),
            corner_radius=8,
            width=130,
        ).pack(pady=(14, 0))

        card.bind("<Enter>", lambda e: card.configure(fg_color=self.palette["card_hover"]))
        card.bind("<Leave>", lambda e: card.configure(fg_color=self.palette["card"]))
        card.bind("<Button-1>", lambda e, k=game_key: self.on_game_selected(k))
