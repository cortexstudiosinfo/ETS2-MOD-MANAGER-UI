"""
core/profile_health.py - Profile validation and conservative repair helpers.
"""
from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from core.sii_decoder import decode_sii, DecryptionError

_ACTIVE_MODS_ENTRY_RE = re.compile(r'^\s*active_mods\[(?P<idx>\d+)\]\s*:\s*"(?P<value>[^"]*)"\s*$', re.IGNORECASE | re.MULTILINE)
_ACTIVE_MODS_COUNT_RE = re.compile(r'^\s*active_mods\s*:\s*(?P<count>\d+)\s*$', re.IGNORECASE | re.MULTILINE)
_ACTIVE_MODS_ANY_LINE_RE = re.compile(r'^\s*active_mods(?:\[\d+\])?\s*:.*$', re.IGNORECASE | re.MULTILINE)
_REQUIRED_FIELD_RE = {
    "profile_name": re.compile(r'^\s*profile_name\s*:\s*(?P<value>.+?)\s*$', re.IGNORECASE | re.MULTILINE),
    "online_user_name": re.compile(r'^\s*online_user_name\s*:\s*(?P<value>.+?)\s*$', re.IGNORECASE | re.MULTILINE),
}
_NUMERIC_FIELD_RE = {
    "cached_experience": re.compile(r'^\s*cached_experience\s*:\s*(?P<value>.+?)\s*$', re.IGNORECASE | re.MULTILINE),
    "money_account": re.compile(r'^\s*money_account\s*:\s*(?P<value>.+?)\s*$', re.IGNORECASE | re.MULTILINE),
}


@dataclass
class ProfileIssue:
    code: str
    message: str
    repairable: bool = True


@dataclass
class ProfileHealth:
    ok: bool
    needs_repair: bool
    can_repair: bool
    issues: list[ProfileIssue]
    backup_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["issues"] = [asdict(issue) for issue in self.issues]
        return data


def _read_profile(profile_path: Path) -> tuple[Path, str]:
    sii_file = profile_path / "profile.sii"
    if not sii_file.exists():
        raise FileNotFoundError(f"profile.sii not found: {sii_file}")
    content = decode_sii(sii_file)
    return sii_file, content


def _unique_valid_mods(content: str) -> list[str]:
    seen: set[str] = set()
    mods: list[str] = []
    for match in _ACTIVE_MODS_ENTRY_RE.finditer(content):
        value = match.group("value").strip()
        if not value:
            continue
        mod_id = value.split("|", 1)[0].strip()
        if not mod_id or mod_id in seen:
            continue
        seen.add(mod_id)
        mods.append(value)
    return mods


def validate_profile(profile_path: Path) -> ProfileHealth:
    issues: list[ProfileIssue] = []
    try:
        _sii_file, content = _read_profile(profile_path)
    except (FileNotFoundError, DecryptionError, ValueError, OSError) as exc:
        return ProfileHealth(False, True, False, [ProfileIssue("profile_unreadable", f"No se puede leer profile.sii: {exc}", False)])

    if not content.lstrip().startswith("SiiNunit"):
        return ProfileHealth(False, True, False, [ProfileIssue("bad_header", "El profile.sii decodificado no parece un archivo SII valido.", False)])

    for key, pattern in _REQUIRED_FIELD_RE.items():
        match = pattern.search(content)
        if not match or not match.group("value").strip():
            issues.append(ProfileIssue(f"missing_{key}", f"Falta el campo basico {key}; revisalo antes de editar el perfil.", False))

    for key, pattern in _NUMERIC_FIELD_RE.items():
        match = pattern.search(content)
        if match and not re.fullmatch(r'-?\d+(?:\.\d+)?', match.group("value").strip()):
            issues.append(ProfileIssue(f"bad_{key}", f"El campo {key} no tiene un numero valido.", False))

    count_match = _ACTIVE_MODS_COUNT_RE.search(content)
    entries = list(_ACTIVE_MODS_ENTRY_RE.finditer(content))
    any_active_lines = _ACTIVE_MODS_ANY_LINE_RE.findall(content)
    malformed_count = max(0, len(any_active_lines) - len(entries) - (1 if count_match else 0))
    valid_mods = _unique_valid_mods(content)

    if any_active_lines and not count_match:
        issues.append(ProfileIssue("missing_active_mods_count", "El contador active_mods falta o esta mal escrito."))
    if count_match and int(count_match.group("count")) != len(entries):
        issues.append(ProfileIssue("wrong_active_mods_count", "El contador active_mods no coincide con las lineas de mods activos."))
    if len(valid_mods) != len(entries):
        issues.append(ProfileIssue("duplicate_or_empty_active_mods", "Hay mods activos duplicados o entradas vacias en el orden de carga."))
    if malformed_count:
        issues.append(ProfileIssue("malformed_active_mods", "Hay lineas active_mods con formato incorrecto."))

    can_repair = any(issue.repairable for issue in issues)
    return ProfileHealth(ok=not issues, needs_repair=bool(issues), can_repair=can_repair, issues=issues)


def repair_profile(profile_path: Path) -> ProfileHealth:
    sii_file, content = _read_profile(profile_path)
    if not content.lstrip().startswith("SiiNunit"):
        raise ValueError("Decoded profile.sii does not start with SiiNunit; refusing to repair.")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = profile_path / f"profile.sii.repair_{stamp}.bak"
    shutil.copy2(sii_file, backup)

    mods = _unique_valid_mods(content)
    new_block = [f" active_mods: {len(mods)}"]
    for index, mod in enumerate(mods):
        escaped = mod.replace('\\', '\\\\').replace('"', '\\"')
        new_block.append(f' active_mods[{index}]: "{escaped}"')

    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    active_indexes = [idx for idx, line in enumerate(lines) if _ACTIVE_MODS_ANY_LINE_RE.match(line)]
    if active_indexes:
        first = active_indexes[0]
        active_set = set(active_indexes)
        repaired_lines = lines[:first] + new_block + [line for idx, line in enumerate(lines[first + 1:], start=first + 1) if idx not in active_set]
        new_content = "\n".join(repaired_lines)
    else:
        insert_at = content.rfind("}")
        insert = "\n".join(new_block)
        if insert_at != -1:
            new_content = content[:insert_at] + "\n" + insert + "\n" + content[insert_at:]
        else:
            new_content = content.rstrip() + "\n" + insert + "\n"

    sii_file.write_text(new_content, encoding="utf-8")
    health = validate_profile(profile_path)
    health.backup_path = str(backup)
    return health
