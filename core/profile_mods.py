"""
core/profile_mods.py - Read and write the active mod list stored in profile.sii.
"""
import re
import shutil
from pathlib import Path

from core.sii_decoder import decode_sii, DecryptionError

# Updated regex to be more greedy and handle various whitespace/newlines
_ENTRY_RE = re.compile(r'active_mods\[\d+\]\s*:\s*"([^"]*)"', re.IGNORECASE)
_BLOCK_RE = re.compile(
    r'active_mods\s*:\s*\d+.*?(?:\r?\n\s*active_mods\[\d+\]\s*:\s*"[^"]*")*',
    re.IGNORECASE | re.DOTALL,
)

def read_active_mods(profile_path: Path) -> list[str]:
    sii_file = profile_path / "profile.sii"
    if not sii_file.exists():
        return []
    try:
        content = decode_sii(sii_file)
    except (DecryptionError, ValueError, FileNotFoundError, OSError):
        return []

    # Get all entries and remove duplicates while preserving order
    found = _ENTRY_RE.findall(content)
    seen = set()
    unique_entries = []
    for item in found:
        if item not in seen:
            unique_entries.append(item)
            seen.add(item)
    return unique_entries

_ACTIVE_MODS_LINE_RE = re.compile(r'^[ \t]*active_mods(?:\[\d+\])?\s*:', re.MULTILINE)

def write_active_mods(profile_path: Path, mod_list: list[str]) -> None:
    sii_file = profile_path / "profile.sii"
    backup   = profile_path / "profile.sii.bak"

    if not sii_file.exists():
        raise FileNotFoundError(f"profile.sii not found: {profile_path}")

    content = decode_sii(sii_file)

    if not content.lstrip().startswith("SiiNunit"):
        raise ValueError("Decoded profile.sii does not start with SiiNunit — cannot safely overwrite.")

    # Backup only after successful decode
    shutil.copy2(sii_file, backup)

    new_block = [f" active_mods: {len(mod_list)}"]
    for i, filename in enumerate(mod_list):
        new_block.append(f' active_mods[{i}]: "{filename}"')

    # Normalize line endings before splitting
    old_lines = content.replace("\r\n", "\n").replace("\r", "\n").splitlines()

    first_idx, last_idx = -1, -1
    for i, line in enumerate(old_lines):
        if _ACTIVE_MODS_LINE_RE.match(line):
            if first_idx == -1:
                first_idx = i
            last_idx = i

    if first_idx != -1:
        new_lines = old_lines[:first_idx] + new_block + old_lines[last_idx + 1:]
    else:
        idx = content.rfind("}")
        if idx != -1:
            insert = "\n".join(new_block)
            content = content[:idx] + "\n" + insert + "\n" + content[idx:]
            sii_file.write_text(content, encoding="utf-8")
            return
        new_lines = old_lines + new_block

    sii_file.write_text("\n".join(new_lines), encoding="utf-8")
