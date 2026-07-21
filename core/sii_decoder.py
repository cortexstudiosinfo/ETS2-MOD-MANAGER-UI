"""
core/sii_decoder.py - SII file format detection and decryption.
"""
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import requests

from core.config import SII_DECRYPT_GITHUB_API, SII_DECRYPT_EXE_NAME, get_tools_dir
from core.logger import get_logger

_log = get_logger("sii_decoder")

_MAGIC_PLAINTEXT  = b"SiiNunit"
_MAGIC_BINARY     = b"SiiNbin\x00"
_MAGIC_COMPRESSED = b"BSII"
_MAGIC_SCSC       = b"ScsC"

"""
core/sii_decoder.py - SII file format detection and decryption.
"""
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import requests

from core.config import SII_DECRYPT_GITHUB_API, SII_DECRYPT_EXE_NAME, get_tools_dir
from core.logger import get_logger

_log = get_logger("sii_decoder")

_MAGIC_PLAINTEXT  = b"SiiNunit"
_MAGIC_BINARY     = b"SiiNbin\x00"
_MAGIC_COMPRESSED = b"BSII"
_MAGIC_SCSC       = b"ScsC"

class DecryptionError(Exception):
    pass


def _find_bundled(filename: str) -> Optional[Path]:
    """
    Looks for a file in the PyInstaller bundle (_MEIPASS) first,
    then in the tools/ folder next to the exe/script.
    Returns the Path if found, None otherwise.
    """
    # 1. PyInstaller bundle (frozen exe)
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        p = Path(sys._MEIPASS) / "tools" / filename
        if p.exists():
            _log.debug("Found bundled %s: %s", filename, p)
            return p

    # 2. tools/ folder next to exe or main.py
    p = get_tools_dir() / filename
    if p.exists():
        _log.debug("Found local %s: %s", filename, p)
        return p

    return None


def ensure_sii_decrypt() -> Path:
    """Returns the path to SII_Decrypt.exe, bundled or downloaded."""

    # --- Priority 1: already bundled inside the exe or in tools/ ---
    bundled = _find_bundled(SII_DECRYPT_EXE_NAME)
    if bundled:
        _log.info("SII_Decrypt.exe ready (bundled): %s", bundled)
        return bundled

    # --- Priority 2: download from GitHub ---
    _log.info("SII_Decrypt.exe not bundled — downloading from GitHub...")
    tools_dir = get_tools_dir()
    exe_path = tools_dir / SII_DECRYPT_EXE_NAME

    try:
        resp = requests.get(SII_DECRYPT_GITHUB_API, timeout=15, headers={"User-Agent": "TruckModManager/2.0"})
        resp.raise_for_status()
        releases = resp.json()
        _log.debug("GitHub API returned %d release(s)", len(releases))
    except Exception as exc:
        _log.error("GitHub API query failed: %s", exc)
        raise RuntimeError(f"GitHub API query failed: {exc}") from exc

    download_url_7z: Optional[str] = None
    for release in releases:
        for asset in release.get("assets", []):
            if asset["name"].endswith(".7z"):
                download_url_7z = asset["browser_download_url"]
                break
        if download_url_7z:
            break

    if not download_url_7z:
        _log.error("No .7z asset found in SII_Decrypt releases")
        raise RuntimeError("No .7z asset found in SII_Decrypt releases.")

    _log.info("Downloading Release.7z from: %s", download_url_7z)
    tools_dir.mkdir(parents=True, exist_ok=True)
    archive = tools_dir / "Release.7z"

    try:
        with requests.get(download_url_7z, stream=True, timeout=60, headers={"User-Agent": "TruckModManager/2.0"}) as r:
            r.raise_for_status()
            with open(archive, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
        _log.info("Release.7z downloaded")
    except Exception as exc:
        _log.error("Download of Release.7z failed: %s", exc)
        raise RuntimeError(f"Download of Release.7z failed: {exc}") from exc

    # Find 7zr.exe — bundled first, then download as last resort
    zip_exe = _find_bundled("7zr.exe")
    if not zip_exe:
        _log.info("7zr.exe not bundled — downloading from 7-zip.org...")
        zip_exe = tools_dir / "7zr.exe"
        try:
            with requests.get("https://www.7-zip.org/a/7zr.exe", stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(zip_exe, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
            _log.info("7zr.exe downloaded")
        except Exception as exc:
            _log.error("Failed to download 7zr.exe: %s", exc)
            raise RuntimeError(f"Failed to download 7zr.exe: {exc}") from exc

    try:
        _log.info("Extracting Release.7z...")
        result = subprocess.run(
            [str(zip_exe), "x", "-y", f"-o{tools_dir}", str(archive)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            err = result.stderr or result.stdout
            _log.error("7zr extraction failed: %s", err)
            raise RuntimeError(f"7zr extractor failed: {err}")
        _log.info("Extraction successful")
    except Exception as exc:
        _log.error("Extraction error: %s", exc)
        raise RuntimeError(f"Extraction failed: {exc}") from exc
    finally:
        try:
            if archive.exists():
                archive.unlink()
        except OSError:
            pass

    if not exe_path.exists():
        found = list(tools_dir.rglob(SII_DECRYPT_EXE_NAME))
        if found:
            shutil.move(str(found[0]), str(exe_path))
            _log.info("Moved SII_Decrypt.exe to tools dir")
            for item in tools_dir.iterdir():
                if item.is_dir():
                    try:
                        shutil.rmtree(item, ignore_errors=True)
                    except Exception:
                        pass
        else:
            _log.error("SII_Decrypt.exe not found after extraction")
            raise RuntimeError(f"{SII_DECRYPT_EXE_NAME} not found after extraction.")

    _log.info("SII_Decrypt.exe ready: %s", exe_path)
    return exe_path

def decode_sii(path: Path) -> str:
    if not path.exists():
        _log.error("SII file not found: %s", path)
        raise FileNotFoundError(f"SII file not found: {path}")

    with open(path, "rb") as f:
        header = f.read(8)

    if header.startswith(_MAGIC_PLAINTEXT):
        _log.debug("decode_sii: plaintext format — %s", path.name)
        return path.read_text(encoding="utf-8", errors="replace")

    if header.startswith(_MAGIC_BINARY) or header[:4] in (_MAGIC_COMPRESSED, _MAGIC_SCSC):
        _log.debug("decode_sii: encrypted/binary format — %s", path.name)
        return _decrypt_with_exe(path)

    _log.debug("decode_sii: unknown header, trying UTF-8 — %s", path.name)
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        _log.error("Unrecognized SII format: %s — %s", path, exc)
        raise ValueError(f"Unrecognized SII format: {path}") from exc

def _decrypt_with_exe(path: Path) -> str:
    exe = ensure_sii_decrypt()
    tmp = path.with_suffix(".sii_tmp")
    try:
        shutil.copy2(path, tmp)
        result = subprocess.run([str(exe), str(tmp)], capture_output=True, timeout=15)
        if result.returncode != 0:
            err = result.stderr.decode("utf-8", errors="replace")
            _log.error("SII_Decrypt.exe failed (code %d): %s", result.returncode, err)
            raise DecryptionError(f"SII_Decrypt.exe failed (code {result.returncode}): {err}")
        _log.debug("Decrypted: %s", path.name)
        return tmp.read_text(encoding="utf-8", errors="replace")
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
