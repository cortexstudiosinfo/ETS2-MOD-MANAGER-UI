"""
core/settings.py - Persistent user settings for paths and scan sources.
"""
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

GAME_DEFAULTS = {
    "ets2": "Euro Truck Simulator 2",
    "ats": "American Truck Simulator",
}

DEFAULT_SETTINGS = {
    "games": {
        "ets2": {
            "game_dir_mode": "auto",
            "manual_game_dir": "",
            "local_mod_dirs": None,
            "workshop_mod_dirs": None,
        },
        "ats": {
            "game_dir_mode": "auto",
            "manual_game_dir": "",
            "local_mod_dirs": None,
            "workshop_mod_dirs": None,
        },
    }
}


def get_settings_path() -> Path:
    base = Path(os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming"))
    return base / "Truck Mod Manager" / "settings.json"


def _merge_defaults(data: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(DEFAULT_SETTINGS)
    for game, values in data.get("games", {}).items():
        if game in merged["games"] and isinstance(values, dict):
            merged["games"][game].update(values)
    return merged


def load_settings() -> dict[str, Any]:
    path = get_settings_path()
    if not path.exists():
        return deepcopy(DEFAULT_SETTINGS)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            return _merge_defaults(raw)
    except Exception:
        pass
    return deepcopy(DEFAULT_SETTINGS)


def save_settings(settings: dict[str, Any]) -> None:
    path = get_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_merge_defaults(settings), indent=2), encoding="utf-8")


def get_game_settings(game: str) -> dict[str, Any]:
    settings = load_settings()
    return settings["games"].setdefault(game, deepcopy(DEFAULT_SETTINGS["games"][game]))


def update_game_settings(game: str, values: dict[str, Any]) -> None:
    settings = load_settings()
    settings["games"].setdefault(game, deepcopy(DEFAULT_SETTINGS["games"][game]))
    settings["games"][game].update(values)
    save_settings(settings)


def reset_game_settings(game: str) -> None:
    settings = load_settings()
    settings["games"][game] = deepcopy(DEFAULT_SETTINGS["games"][game])
    save_settings(settings)


def get_default_game_dir(game: str) -> Path:
    return Path.home() / "Documents" / GAME_DEFAULTS[game]


def _looks_like_game_data_dir(path: Path) -> bool:
    return any((path / name).exists() for name in ("profiles", "steam_profiles", "mod"))


def resolve_game_data_dir(game: str, raw_path: str | Path) -> Path:
    """Resolves a manual selection to the ETS2/ATS data folder.

    Accepts the exact data folder, a -homedir parent containing the game folder,
    or a folder that directly contains profiles/steam_profiles/mod.
    """
    base = Path(raw_path).expanduser()
    candidates = [
        base,
        base / GAME_DEFAULTS[game],
        base / "Documents" / GAME_DEFAULTS[game],
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir() and _looks_like_game_data_dir(candidate):
            return candidate
    return base


def get_game_root(game: str) -> Path:
    cfg = get_game_settings(game)
    manual_dir = str(cfg.get("manual_game_dir") or "").strip()
    if cfg.get("game_dir_mode") == "manual" and manual_dir:
        return resolve_game_data_dir(game, manual_dir)
    return get_default_game_dir(game)


def normalize_path_list(value: Any) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = str(item).strip()
        if not text:
            continue
        key = str(Path(text).expanduser()).lower()
        if key not in seen:
            cleaned.append(text)
            seen.add(key)
    return cleaned


def get_saved_path_list(game: str, key: str) -> list[str] | None:
    return normalize_path_list(get_game_settings(game).get(key))


def validate_existing_dirs(paths: list[str]) -> list[str]:
    errors: list[str] = []
    for raw in paths:
        p = Path(raw).expanduser()
        if not p.exists():
            errors.append(f"Folder does not exist: {p}")
        elif not p.is_dir():
            errors.append(f"Path is not a folder: {p}")
    return errors
