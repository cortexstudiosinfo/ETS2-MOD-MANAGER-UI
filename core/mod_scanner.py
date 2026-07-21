"""
core/mod_scanner.py - Discovers mods, reads manifests, and extracts thumbnails.
"""
import io
import re
import winreg
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, List, Tuple

from PIL import Image, ImageDraw

from core.config import (
    THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT,
    get_game_path, GAME_MODS_DIR, GAME_CONFIGS,
)
from core.logger import get_logger
from core.settings import get_saved_path_list

_log = get_logger("mod_scanner")

_PREVIEW_NAMES = frozenset({"preview.jpg", "description.jpg", "thumbnail.png", "preview.png", "mod_icon.jpg", "mod_icon.png", "icon.jpg", "icon.png"})

@dataclass
class Mod:
    name: str             # Human readable name
    filename: str         # The raw path/file reference for UI logs
    path: Path            # Path to the actual .scs/.zip or folder
    source: str           # "local" or "workshop"
    thumbnail: Optional[Image.Image] = field(default=None, repr=False)
    has_manifest_name: bool = field(default=False)  # True only if name came from manifest/Steam API
    preview_available: bool = field(default=False)

    @property
    def internal_id(self) -> str:
        """The base identifier (before the pipe) used inside ETS2 profile.sii."""
        if self.source == "workshop":
            steam_id_str = self.path.name
            try:
                numeric_id = int(steam_id_str)
                return f"mod_workshop_package.{numeric_id:016X}"
            except ValueError:
                return steam_id_str
        else:
            return self.path.stem

    @property
    def sii_entry(self) -> str:
        """The full string written into profile.sii: 'id|name' only when a real name exists."""
        if self.has_manifest_name:
            return f"{self.internal_id}|{self.name}"
        return self.internal_id

def find_steam_path() -> Optional[Path]:
    for hive, key_path in [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),
        (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Valve\Steam"),
    ]:
        try:
            with winreg.OpenKey(hive, key_path) as key:
                p = Path(winreg.QueryValueEx(key, "InstallPath")[0])
                if p.exists():
                    _log.info("Steam found via registry: %s", p)
                    return p
        except (FileNotFoundError, OSError):
            continue

    for candidate in [
        Path("C:/Program Files (x86)/Steam"),
        Path("C:/Program Files/Steam"),
        Path.home() / "Steam",
    ]:
        if candidate.exists() and (candidate / "steamapps").exists():
            _log.info("Steam found via fallback path: %s", candidate)
            return candidate

    _log.warning("Steam installation not found")
    return None

def find_workshop_paths(app_id: str) -> list[Path]:
    steam = find_steam_path()
    if not steam:
        return []

    roots: set[Path] = {steam.resolve()}
    vdf = steam / "config" / "libraryfolders.vdf"
    if vdf.exists():
        try:
            vdf_text = vdf.read_text(encoding="utf-8", errors="replace")
            for p_str in re.findall(r'"path"\s*"([^"]+)"', vdf_text):
                p = Path(p_str.replace("\\\\", "\\")).resolve()
                if p.exists():
                    roots.add(p)
        except OSError as exc:
            _log.warning("Could not read libraryfolders.vdf: %s", exc)

    final_paths = []
    for r in roots:
        ws_path = r / "steamapps" / "workshop" / "content" / app_id
        if ws_path.exists():
            _log.info("Workshop path found [app_id=%s]: %s", app_id, ws_path)
            final_paths.append(ws_path)

    if not final_paths:
        _log.warning("No workshop content found for app_id=%s", app_id)
    return final_paths


def _valid_dirs(paths: list[Path], label: str) -> list[Path]:
    valid: list[Path] = []
    for path in paths:
        if path.exists() and path.is_dir():
            valid.append(path)
        else:
            _log.warning("Ignoring invalid %s folder: %s", label, path)
    return valid


def _resolve_local_mod_dir(raw: Path, game: str) -> Path:
    raw = raw.expanduser()
    if raw.name.lower() == GAME_MODS_DIR.lower():
        return raw
    direct = raw / GAME_MODS_DIR
    if direct.exists() and direct.is_dir():
        return direct
    game_named = raw / GAME_CONFIGS[game]["documents_dir"] / GAME_MODS_DIR
    if game_named.exists() and game_named.is_dir():
        return game_named
    return raw


def _resolve_workshop_dir(raw: Path, app_id: str) -> Path:
    raw = raw.expanduser()
    if raw.name == app_id:
        return raw
    candidates = [
        raw / app_id,
        raw / "content" / app_id,
        raw / "workshop" / "content" / app_id,
        raw / "steamapps" / "workshop" / "content" / app_id,
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    return raw


def get_local_mod_paths(game: str) -> list[Path]:
    saved = get_saved_path_list(game, "local_mod_dirs")
    if saved is None:
        paths = [get_game_path(game) / GAME_MODS_DIR]
    else:
        paths = [_resolve_local_mod_dir(Path(item), game) for item in saved]
    return _valid_dirs(paths, "local mods")


def get_workshop_source_paths(game: str) -> list[Path]:
    app_id = GAME_CONFIGS[game]["app_id"]
    saved = get_saved_path_list(game, "workshop_mod_dirs")
    if saved is None:
        paths = find_workshop_paths(app_id)
    else:
        paths = [_resolve_workshop_dir(Path(item), app_id) for item in saved]
    return _valid_dirs(paths, "Workshop")

def _parse_manifest(content: str) -> dict:
    """Extracts basic info from a manifest.sii text."""
    info = {}
    display_match = re.search(r'display_name\s*:\s*"([^"]+)"', content, re.IGNORECASE)
    if display_match:
        info['name'] = display_match.group(1)
    
    author_match = re.search(r'author\s*:\s*"([^"]+)"', content, re.IGNORECASE)
    if author_match:
        info['author'] = author_match.group(1)
        
    icon_match = re.search(r'icon\s*:\s*"([^"]+)"', content, re.IGNORECASE)
    if icon_match:
        info['icon'] = icon_match.group(1)
        
    return info

def _format_image(img: Image.Image) -> Image.Image:
    """Resizes and letterboxes an image to thumbnail size."""
    try:
        img = img.convert("RGB")
        img.thumbnail((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.LANCZOS)
        canvas = Image.new("RGB", (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), (20, 25, 38))
        canvas.paste(img, ((THUMBNAIL_WIDTH  - img.width)  // 2, (THUMBNAIL_HEIGHT - img.height) // 2))
        return canvas
    except Exception:
        return _make_placeholder()

def _extract_from_zip(zip_path: Path) -> Tuple[Optional[str], Optional[Image.Image]]:
    """Attempts to read manifest.sii and thumbnails from a ZIP/SCS file."""
    name, thumb = None, None
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            # 1. Search for manifest
            manifest_candidates = [n for n in zf.namelist() if Path(n).name.lower() == "manifest.sii"]
            icon_name = None
            if manifest_candidates:
                try:
                    text = zf.read(manifest_candidates[0]).decode("utf-8", errors="ignore")
                    info = _parse_manifest(text)
                    name = info.get("name")
                    icon_name = info.get("icon")
                except Exception:
                    pass
            
            # 2. Search for thumbnail
            target = None
            if icon_name and icon_name in zf.namelist():
                target = icon_name
            else:
                target = next((e for e in zf.namelist() if Path(e).name.lower() in _PREVIEW_NAMES), None)
                
            if target:
                img = Image.open(io.BytesIO(zf.read(target)))
                thumb = _format_image(img)
                
    except Exception:
        pass
    return name, thumb

def _extract_from_folder(folder_path: Path) -> Tuple[Optional[str], Optional[Image.Image]]:
    """Attempts to read manifest.sii and thumbnails from a physical folder structure."""
    name, thumb = None, None
    try:
        manifest = next(folder_path.rglob("manifest.sii"), None)
        icon_name = None
        if manifest:
            text = manifest.read_text(encoding="utf-8", errors="ignore")
            info = _parse_manifest(text)
            name = info.get("name")
            icon_name = info.get("icon")
            
        target = None
        if icon_name:
            target = next(folder_path.rglob(icon_name), None)
            
        if not target:
            for ext in ["*.jpg", "*.png"]:
                target = next((img_candidate for img_candidate in folder_path.rglob(ext) if img_candidate.name.lower() in _PREVIEW_NAMES), None)
                if target: break
                
        # Last resort fallback: any image
        if not target:
            target = next(folder_path.rglob("*.jpg"), None) or next(folder_path.rglob("*.png"), None)
            
        if target:
            img = Image.open(target)
            thumb = _format_image(img)
            
    except Exception:
        pass
    return name, thumb

def _make_placeholder() -> Image.Image:
    # Use the new COLOR_BG and COLOR_ACCENT equivalents
    bg_color = (10, 10, 10)  # Near black
    accent_color = (204, 0, 0)  # Red
    muted_color = (100, 100, 100) # Grey
    
    img  = Image.new("RGB", (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), bg_color)
    draw = ImageDraw.Draw(img)
    cx, cy = THUMBNAIL_WIDTH // 2, THUMBNAIL_HEIGHT // 2
    draw.rounded_rectangle([20, 30, THUMBNAIL_WIDTH - 20, THUMBNAIL_HEIGHT - 30], radius=8, outline=muted_color, width=2)
    draw.rectangle([cx - 28, cy - 12, cx + 28, cy + 14], outline=accent_color, width=2)
    draw.rectangle([cx - 28, cy - 20, cx - 4,  cy - 12], outline=accent_color, width=2)
    for wx in [cx - 20, cx + 12]:
        draw.ellipse([wx - 6, cy + 14, wx + 6, cy + 26], outline=accent_color, width=2)
    return img

def _display_name(filename: str) -> str:
    return Path(filename.split("/")[-1]).stem.replace("_", " ").replace("-", " ").title()

def scan_mods(progress_callback: Optional[Callable[[str], None]] = None, game: str = "ets2") -> list[Mod]:
    import requests
    from concurrent.futures import ThreadPoolExecutor

    _log.info("Starting mod scan for [%s]", game)
    placeholder = _make_placeholder()
    mods: list[Mod] = []

    # ---- 1. WORKSHOP MODS ----
    if progress_callback: progress_callback("Scanning Workshop content...")
    ws_paths = get_workshop_source_paths(game)
    ws_folders_set: set[Path] = set()
    for ws_dir in ws_paths:
        for mod_folder in ws_dir.iterdir():
            if mod_folder.is_dir():
                ws_folders_set.add(mod_folder.resolve())

    ws_folders = list(ws_folders_set)
    _log.info("Workshop folders found: %d", len(ws_folders))

    steam_data = {}
    if ws_folders:
        if progress_callback: progress_callback("Fetching perfect metadata from Steam API...")
        try:
            data = {"itemcount": len(ws_folders)}
            for i, folder in enumerate(ws_folders):
                data[f"publishedfileids[{i}]"] = folder.name
            resp = requests.post(
                "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/",
                data=data, timeout=10
            )
            if resp.status_code == 200:
                for item in resp.json().get("response", {}).get("publishedfiledetails", []):
                    steam_data[item["publishedfileid"]] = {
                        "title": item.get("title"),
                        "preview_url": item.get("preview_url")
                    }
                _log.info("Steam API returned metadata for %d item(s)", len(steam_data))
            else:
                _log.warning("Steam API responded with HTTP %d", resp.status_code)
        except Exception as exc:
            _log.warning("Steam API call failed: %s", exc)

    def process_workshop(mod_folder: Path) -> Mod:
        name, thumb = None, None
        steam_info = steam_data.get(mod_folder.name)
        if steam_info and steam_info.get("title"):
            name = steam_info["title"]
        if steam_info and steam_info.get("preview_url"):
            try:
                r = requests.get(steam_info["preview_url"], timeout=5)
                if r.status_code == 200:
                    img = Image.open(io.BytesIO(r.content))
                    thumb = _format_image(img)
            except Exception as exc:
                _log.debug("Thumbnail fetch failed for %s: %s", mod_folder.name, exc)

        if not name or not thumb:
            local_name, local_thumb = _extract_from_folder(mod_folder)
            if not local_name or not local_thumb:
                for zf in [*mod_folder.glob("*.zip"), *mod_folder.glob("*.scs")]:
                    z_name, z_thumb = _extract_from_zip(zf)
                    local_name = local_name or z_name
                    local_thumb = local_thumb or z_thumb
            name = name or local_name or f"Workshop Mod {mod_folder.name}"
            thumb = thumb or local_thumb

        return Mod(
            name=name,
            filename=f"workshop/{mod_folder.name}",
            path=mod_folder,
            source="workshop",
            thumbnail=thumb or placeholder,
            has_manifest_name=bool(name),
            preview_available=thumb is not None
        )

    if ws_folders:
        with ThreadPoolExecutor(max_workers=5) as executor:
            total = len(ws_folders)
            for i, res in enumerate(executor.map(process_workshop, ws_folders)):
                mods.append(res)
                if progress_callback and i % max(1, total // 5) == 0:
                    progress_callback(f"Downloading Workshop Images... ({i}/{total})")

    # ---- 2. LOCAL MODS ----
    if progress_callback: progress_callback("Scanning local mods (Deep Scan)...")
    local_dirs = get_local_mod_paths(game)
    _log.info("Local mod source folders: %d", len(local_dirs))
    local_count = 0
    for local_dir in local_dirs:
        _log.info("Local mods dir: %s", local_dir)
        for f in local_dir.iterdir():
            if f.is_file() and f.suffix.lower() in [".scs", ".zip"]:
                name, thumb = _extract_from_zip(f)
                if not thumb:
                    for ext in [".jpg", ".png", ".jpeg"]:
                        custom_cover = f.with_suffix(ext)
                        if custom_cover.exists():
                            try:
                                thumb = _format_image(Image.open(custom_cover))
                                break
                            except Exception as exc:
                                _log.debug("Custom cover load failed for %s: %s", f.name, exc)
                mods.append(Mod(
                    name=name or _display_name(f.name),
                    filename=f.name,
                    path=f,
                    source="local",
                    thumbnail=thumb or placeholder,
                    has_manifest_name=bool(name),
                    preview_available=thumb is not None
                ))
                local_count += 1
            elif f.is_dir() and (f / "manifest.sii").exists():
                name, thumb = _extract_from_folder(f)
                mods.append(Mod(
                    name=name or _display_name(f.name),
                    filename=f.name,
                    path=f,
                    source="local",
                    thumbnail=thumb or placeholder,
                    has_manifest_name=bool(name),
                    preview_available=thumb is not None
                ))
                local_count += 1

    _log.info("Local mods found: %d", local_count)

    # ---- 3. DEDUPLICATION ----
    unique_mods: dict[str, Mod] = {}
    for mod in mods:
        if mod.internal_id not in unique_mods:
            unique_mods[mod.internal_id] = mod

    final_list = list(unique_mods.values())
    _log.info("Scan complete — total unique mods: %d", len(final_list))
    return sorted(final_list, key=lambda m: m.name.lower())
