"""
core/game_editor.py - Safe game.sii editor helpers.

Reads the latest save/game.sii for the selected profile and edits only existing
simple scalar fields. Backups are created before writing.
"""
from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from core.sii_decoder import decode_sii

GAME_FIELD_DEFS = {
    "economy": ["money_account", "bank_loan", "total_distance"],
    "skills": ["adr", "long_dist", "heavy", "fragile", "urgent", "mechanical"],
}

_SCALAR_RE_CACHE: dict[str, re.Pattern] = {}


def _scalar_pattern(key: str) -> re.Pattern:
    if key not in _SCALAR_RE_CACHE:
        _SCALAR_RE_CACHE[key] = re.compile(rf'^(?P<indent>\s*){re.escape(key)}\s*:\s*(?P<value>-?\d+(?:\.\d+)?)\s*$', re.MULTILINE)
    return _SCALAR_RE_CACHE[key]


@dataclass
class GameEditorData:
    save_path: Optional[Path]
    fields: dict[str, Optional[str]] = field(default_factory=dict)
    garage_count: int = 0
    truck_count: int = 0
    driver_count: int = 0


def find_latest_game_sii(profile_path: Path) -> Optional[Path]:
    save_root = profile_path / "save"
    preferred = [
        save_root / "autosave" / "game.sii",
        save_root / "quicksave" / "game.sii",
    ]
    for path in preferred:
        if path.exists():
            return path
    if not save_root.exists():
        return None
    saves = [path for path in save_root.rglob("game.sii") if path.is_file()]
    if not saves:
        return None
    return max(saves, key=lambda path: path.stat().st_mtime)


def _read_scalar(content: str, key: str) -> Optional[str]:
    match = _scalar_pattern(key).search(content)
    if not match:
        return None
    return match.group("value")


def _count_defs(content: str, name: str) -> int:
    return len(re.findall(rf'^\s*{re.escape(name)}\s*:', content, re.MULTILINE))


def read_game_editor_data(profile_path: Path) -> GameEditorData:
    save_path = find_latest_game_sii(profile_path)
    keys = [key for section in GAME_FIELD_DEFS.values() for key in section]
    if not save_path:
        return GameEditorData(save_path=None, fields={key: None for key in keys})

    content = decode_sii(save_path)
    fields = {key: _read_scalar(content, key) for key in keys}
    return GameEditorData(
        save_path=save_path,
        fields=fields,
        garage_count=_count_defs(content, "garage"),
        truck_count=_count_defs(content, "vehicle"),
        driver_count=_count_defs(content, "driver"),
    )


def write_game_editor_data(save_path: Path, values: dict[str, str]) -> None:
    if not save_path.exists():
        raise FileNotFoundError(f"game.sii not found: {save_path}")
    content = decode_sii(save_path)
    if not content.lstrip().startswith("SiiNunit"):
        raise ValueError("Decoded game.sii does not start with SiiNunit; refusing to overwrite.")

    new_content = content
    changed = False
    for key, value in values.items():
        value = str(value).strip()
        if value == "":
            continue
        pattern = _scalar_pattern(key)
        if not pattern.search(new_content):
            continue
        def repl(match: re.Match) -> str:
            return f"{match.group('indent')}{key}: {value}"
        new_content, count = pattern.subn(repl, new_content, count=1)
        changed = changed or count > 0

    if not changed or new_content == content:
        return

    backup = save_path.with_suffix(".sii.game_editor.bak")
    shutil.copy2(save_path, backup)
    save_path.write_text(new_content, encoding="utf-8")
