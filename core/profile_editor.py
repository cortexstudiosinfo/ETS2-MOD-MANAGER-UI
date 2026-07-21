"""
core/profile_editor.py - Safe profile.sii field editor.

This edits only simple scalar fields in plaintext-decoded profile.sii and creates a
backup before writing. It intentionally avoids deep save-game edits that belong to
save/*.sii until those structures are mapped safely.
"""
from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from core.profile_utils import _xp_to_level
from core.sii_decoder import decode_sii


_FIELD_PATTERNS = {
    "profile_name": re.compile(r'^(?P<indent>\s*)profile_name\s*:\s*(?P<value>.+?)\s*$', re.MULTILINE),
    "online_user_name": re.compile(r'^(?P<indent>\s*)online_user_name\s*:\s*(?P<value>.+?)\s*$', re.MULTILINE),
    "company_name": re.compile(r'^(?P<indent>\s*)company_name\s*:\s*(?P<value>.+?)\s*$', re.MULTILINE),
    "cached_experience": re.compile(r'^(?P<indent>\s*)cached_experience\s*:\s*(?P<value>\d+)\s*$', re.MULTILINE),
    "money_account": re.compile(r'^(?P<indent>\s*)money_account\s*:\s*(?P<value>-?\d+)\s*$', re.MULTILINE),
}


@dataclass
class EditableProfileData:
    profile_name: str = ""
    online_user_name: str = ""
    company_name: str = ""
    cached_experience: Optional[int] = None
    level: Optional[int] = None
    money_account: Optional[int] = None
    has_money_account: bool = False


def _clean_string(raw: str) -> str:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
        raw = raw[1:-1]
    return raw.replace('\\"', '"').replace('\\\\', '\\')


def _quote_string(value: str) -> str:
    value = value.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{value}"'


def _read_field(content: str, key: str) -> Optional[str]:
    match = _FIELD_PATTERNS[key].search(content)
    if not match:
        return None
    return match.group('value').strip()


def read_editable_profile(profile_path: Path) -> EditableProfileData:
    content = decode_sii(profile_path / 'profile.sii')
    xp_raw = _read_field(content, 'cached_experience')
    money_raw = _read_field(content, 'money_account')
    xp = int(xp_raw) if xp_raw and xp_raw.isdigit() else None
    money = int(money_raw) if money_raw and re.fullmatch(r'-?\d+', money_raw) else None
    return EditableProfileData(
        profile_name=_clean_string(_read_field(content, 'profile_name') or ''),
        online_user_name=_clean_string(_read_field(content, 'online_user_name') or ''),
        company_name=_clean_string(_read_field(content, 'company_name') or ''),
        cached_experience=xp,
        level=_xp_to_level(xp) if xp is not None else None,
        money_account=money,
        has_money_account=money_raw is not None,
    )


def _replace_existing(content: str, key: str, formatted_value: str) -> tuple[str, bool]:
    pattern = _FIELD_PATTERNS[key]
    def repl(match: re.Match) -> str:
        return f"{match.group('indent')}{key}: {formatted_value}"
    new_content, count = pattern.subn(repl, content, count=1)
    return new_content, count > 0


def write_editable_profile(profile_path: Path, values: dict[str, object]) -> None:
    sii_file = profile_path / 'profile.sii'
    if not sii_file.exists():
        raise FileNotFoundError(f'profile.sii not found: {sii_file}')

    content = decode_sii(sii_file)
    if not content.lstrip().startswith('SiiNunit'):
        raise ValueError('Decoded profile.sii does not start with SiiNunit; refusing to overwrite.')

    replacements = {
        'profile_name': _quote_string(str(values.get('profile_name', '')).strip()),
        'online_user_name': _quote_string(str(values.get('online_user_name', '')).strip()),
        'company_name': _quote_string(str(values.get('company_name', '')).strip()),
    }
    if values.get('cached_experience') is not None:
        replacements['cached_experience'] = str(int(values['cached_experience']))
    if values.get('money_account') is not None and _FIELD_PATTERNS['money_account'].search(content):
        replacements['money_account'] = str(int(values['money_account']))

    new_content = content
    for key, formatted in replacements.items():
        if key in ('profile_name', 'online_user_name', 'company_name') and not str(values.get(key, '')).strip():
            continue
        new_content, _ = _replace_existing(new_content, key, formatted)

    if new_content == content:
        return

    backup = profile_path / 'profile.sii.profile_editor.bak'
    shutil.copy2(sii_file, backup)
    sii_file.write_text(new_content, encoding='utf-8')
