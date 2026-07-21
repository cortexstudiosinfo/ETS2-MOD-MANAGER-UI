"""
core/profile_utils.py - ETS2/ATS profile discovery and display-name resolution.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from core.config import get_game_path, GAME_PROFILES_DIR_NAMES
from core.sii_decoder import decode_sii, DecryptionError
from core.logger import get_logger

_log = get_logger("profile_utils")

# ETS2 values can be quoted ("value") or unquoted (value)
_VAL = r'"?([^"\r\n]+?)"?\s*$'
_PROFILE_NAME_RE   = re.compile(r'^\s*profile_name\s*:\s*' + _VAL, re.IGNORECASE | re.MULTILINE)
_ONLINE_NAME_RE    = re.compile(r'^\s*online_user_name\s*:\s*' + _VAL, re.IGNORECASE | re.MULTILINE)
_COMPANY_NAME_RE   = re.compile(r'^\s*company_name\s*:\s*' + _VAL, re.IGNORECASE | re.MULTILINE)
_EXPERIENCE_RE     = re.compile(r'^\s*cached_experience\s*:\s*(\d+)', re.IGNORECASE | re.MULTILINE)
_SII_ESCAPE_RE     = re.compile(r'\\([0-9a-fA-F]{2})')

# ETS2 XP per level (each level costs 5000 XP, level 1 starts at 0)
_XP_PER_LEVEL = 5_000

def _xp_to_level(xp: int) -> int:
    """Convert raw cached_experience to in-game driver level (1-based)."""
    return max(1, xp // _XP_PER_LEVEL + 1)

@dataclass
class Profile:
    hex_id: str
    display_name: str
    path: Path
    driver_name: Optional[str] = field(default=None)
    level: Optional[int] = field(default=None)

    def __str__(self) -> str:
        return f"{self.display_name} ({self.hex_id})"

def _unescape_sii_string(s: str) -> str:
    return _SII_ESCAPE_RE.sub(lambda m: chr(int(m.group(1), 16)), s)

def _read_profile_info(profile_path: Path) -> tuple[Optional[str], Optional[str], Optional[int]]:
    """Returns (profile_name, driver_name, level) from profile.sii."""
    sii_file = profile_path / "profile.sii"
    if not sii_file.exists():
        _log.warning("profile.sii not found: %s", profile_path)
        return None, None, None
    try:
        content = decode_sii(sii_file)

        m_name = _PROFILE_NAME_RE.search(content)
        profile_name = _unescape_sii_string(m_name.group(1).strip()) if m_name else None

        m_driver = _ONLINE_NAME_RE.search(content)
        if not m_driver:
            m_driver = _COMPANY_NAME_RE.search(content)
        driver_name = _unescape_sii_string(m_driver.group(1).strip()) if m_driver else None

        m_xp = _EXPERIENCE_RE.search(content)
        level = _xp_to_level(int(m_xp.group(1))) if m_xp else None

        _log.debug("Profile read: name=%s driver=%s level=%s", profile_name, driver_name, level)
        return profile_name, driver_name, level
    except (DecryptionError, ValueError, FileNotFoundError, OSError) as exc:
        _log.error("Failed to read profile.sii at %s: %s", profile_path, exc)
        return None, None, None

def list_profiles(game: str = "ets2") -> list[Profile]:
    base = get_game_path(game)
    _log.info("Scanning profiles for [%s] in: %s", game, base)
    profiles: list[Profile] = []
    seen: set[str] = set()

    for dir_name in GAME_PROFILES_DIR_NAMES:
        profiles_dir = base / dir_name
        if not profiles_dir.exists():
            _log.debug("Profiles dir not found: %s", profiles_dir)
            continue
        for entry in profiles_dir.iterdir():
            if not entry.is_dir() or entry.name in seen:
                continue
            if not (entry / "profile.sii").exists():
                _log.debug("Skipping %s — no profile.sii (game not fully set up yet)", entry.name)
                continue
            seen.add(entry.name)
            profile_name, driver_name, level = _read_profile_info(entry)
            display = profile_name or entry.name
            profiles.append(Profile(
                hex_id=entry.name,
                display_name=display,
                path=entry,
                driver_name=driver_name,
                level=level,
            ))

    _log.info("Found %d profile(s) for [%s]", len(profiles), game)
    return sorted(profiles, key=lambda p: p.display_name.lower())
