"""
core/theme.py - Shared light/dark theme state for the redesigned UI.
"""
import customtkinter as ctk

THEMES = {
    "light": {
        "bg": "#F7F9FC",
        "surface": "#FFFFFF",
        "surface_2": "#F1F5F9",
        "card": "#FFFFFF",
        "card_hover": "#F8FAFC",
        "border": "#E2E8F0",
        "text": "#0F172A",
        "muted": "#64748B",
        "accent": "#2563EB",
        "accent_hover": "#1D4ED8",
        "accent_soft": "#EAF1FF",
        "success": "#16A34A",
        "danger": "#DC2626",
        "warning": "#D97706",
        "purple": "#7C3AED",
    },
    "dark": {
        "bg": "#0B1120",
        "surface": "#111827",
        "surface_2": "#182233",
        "card": "#111827",
        "card_hover": "#1F2937",
        "border": "#263244",
        "text": "#F8FAFC",
        "muted": "#94A3B8",
        "accent": "#60A5FA",
        "accent_hover": "#3B82F6",
        "accent_soft": "#172554",
        "success": "#22C55E",
        "danger": "#F87171",
        "warning": "#F59E0B",
        "purple": "#A78BFA",
    },
}

_current_mode = "light"


def get_theme_mode() -> str:
    return _current_mode


def get_theme() -> dict:
    return THEMES[_current_mode]


def set_theme_mode(mode: str) -> dict:
    global _current_mode
    _current_mode = "dark" if str(mode).lower() == "dark" else "light"
    ctk.set_appearance_mode("Dark" if _current_mode == "dark" else "Light")
    return get_theme()


def set_theme_label(label: str) -> dict:
    return set_theme_mode("dark" if label == "Dark" else "light")


def get_theme_label() -> str:
    return "Dark" if _current_mode == "dark" else "Light"
