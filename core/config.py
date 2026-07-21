from pathlib import Path
from typing import Optional
import sys
from core.settings import get_game_root, get_default_game_dir

# ---------------------------------------------------------------------------
# App Identity
# ---------------------------------------------------------------------------
APP_NAME = "Truck Manager"
APP_VERSION = "4.0.0"
APP_ICON = "Manager.ico"
APP_LOGO = "Manager.png"

# ---------------------------------------------------------------------------
# Game Configurations
# ---------------------------------------------------------------------------
GAME_CONFIGS = {
    "ets2": {
        "name": "Euro Truck Simulator 2",
        "short": "ETS2",
        "app_id": "227300",
        "documents_dir": "Euro Truck Simulator 2",
        "firestore_collection": "presets",
    },
    "ats": {
        "name": "American Truck Simulator",
        "short": "ATS",
        "app_id": "270880",
        "documents_dir": "American Truck Simulator",
        "firestore_collection": "ats_presets",
    },
}


def detect_installed_games() -> list[str]:
    """Returns game keys whose automatic or configured game folder exists."""
    found = []
    for key in GAME_CONFIGS:
        if get_default_game_dir(key).exists() or get_game_root(key).exists():
            found.append(key)
    return found

def get_icon_path() -> Optional[Path]:
    """Returns the path to the application icon, searching internal bundle and external folders."""
    # 1. Check in the bundled resources (PyInstaller internal)
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        internal_path = Path(sys._MEIPASS) / APP_ICON
        if internal_path.exists():
            return internal_path

    # 2. Check next to the executable
    if getattr(sys, "frozen", False):
        external_path = Path(sys.executable).parent / APP_ICON
        if external_path.exists():
            return external_path

    # 3. Development path
    dev_path = Path(__file__).parent.parent / APP_ICON
    if dev_path.exists():
        return dev_path

    return None

def get_logo_path() -> Optional[Path]:
    """Returns the PNG logo used inside the UI, avoiding ICO alpha artifacts."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        internal_path = Path(sys._MEIPASS) / APP_LOGO
        if internal_path.exists():
            return internal_path

    if getattr(sys, "frozen", False):
        external_path = Path(sys.executable).parent / APP_LOGO
        if external_path.exists():
            return external_path

    dev_path = Path(__file__).parent.parent / APP_LOGO
    if dev_path.exists():
        return dev_path

    return get_icon_path()


# ---------------------------------------------------------------------------
# Runtime Path Resolution
# Supports both running as a .py script and as a PyInstaller .exe bundle.
# ---------------------------------------------------------------------------

def get_app_dir() -> Path:
    """Returns the directory where the app executable or main.py lives."""
    if getattr(sys, "frozen", False):
        # Look for bundled resources first (PyInstaller standard)
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)
        return Path(sys.executable).parent
    return Path(__file__).parent.parent   # core/ -> project root


def get_documents_path() -> Path:
    """Returns the current user's Documents folder."""
    return Path.home() / "Documents"


def get_game_path(game: str = "ets2") -> Path:
    """Returns the configured game data directory, supporting custom -homedir roots."""
    return get_game_root(game)


def get_ets2_path() -> Path:
    """Returns the base ETS2 data directory inside Documents."""
    return get_game_path("ets2")


def get_tools_dir() -> Path:
    """Returns the tools/ directory next to the app (auto-created at runtime)."""
    return get_app_dir() / "tools"


def get_assets_dir() -> Path:
    """Returns the assets/ directory (bundled with the app)."""
    return get_app_dir() / "assets"


# ---------------------------------------------------------------------------
# Game Paths (shared constants)
# ---------------------------------------------------------------------------
ETS2_PROFILES_DIR_NAMES = ["profiles", "steam_profiles"]
ETS2_MODS_DIR = "mod"
ETS2_WORKSHOP_APP_ID = "227300"
ATS_WORKSHOP_APP_ID  = "270880"
GAME_PROFILES_DIR_NAMES = ["profiles", "steam_profiles"]
GAME_MODS_DIR = "mod"

# ---------------------------------------------------------------------------
# SII Decrypt Tool
# ---------------------------------------------------------------------------
SII_DECRYPT_EXE_NAME = "SII_Decrypt.exe"
SII_DECRYPT_GITHUB_API = "https://api.github.com/repos/Stearells/SII_Decrypt/releases"

# ---------------------------------------------------------------------------

# Firebase / Firestore

# ---------------------------------------------------------------------------

FIREBASE_CREDENTIALS_FILE = "firebase_credentials.json"

# Public build: Firebase credentials are intentionally not included.
FIREBASE_CONFIG = None

FIRESTORE_COLLECTION = "presets"

PRESET_CODE_LENGTH = 25

# ---------------------------------------------------------------------------
# UI Theme â€” Black, White, and Red palette
# ---------------------------------------------------------------------------
COLOR_BG            = "#F7F9FC"
COLOR_SURFACE       = "#FFFFFF"
COLOR_SURFACE_2     = "#F1F5F9"
COLOR_CARD          = "#FFFFFF"
COLOR_CARD_HOVER    = "#F8FAFC"
COLOR_ACCENT        = "#2563EB"
COLOR_ACCENT_HOVER  = "#1D4ED8"
COLOR_ACCENT_DIM    = "#DBEAFE"
COLOR_TEXT_PRIMARY  = "#0F172A"
COLOR_TEXT_SECONDARY = "#334155"
COLOR_TEXT_MUTED    = "#64748B"
COLOR_BORDER        = "#E2E8F0"
COLOR_SUCCESS       = "#28A745"
COLOR_ERROR         = "#DC3545"
COLOR_WARNING       = "#FFC107"

COLOR_BADGE_LOCAL    = "#475569"
COLOR_BADGE_WORKSHOP = "#7C3AED"

# ---------------------------------------------------------------------------
# UI Dimensions
# ---------------------------------------------------------------------------
SIDEBAR_WIDTH      = 220
THUMBNAIL_WIDTH    = 200
THUMBNAIL_HEIGHT   = 150
CARD_CORNER_RADIUS = 8

# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------
FONT_FAMILY      = "Segoe UI"
FONT_SIZE_TITLE  = 20
FONT_SIZE_SUBTITLE = 14
FONT_SIZE_BODY   = 13
FONT_SIZE_SMALL  = 11
FONT_SIZE_BADGE  = 10

# ---------------------------------------------------------------------------
# Multi-language Support
# ---------------------------------------------------------------------------
CUR_LANG = "en" # "es" or "en"

TRANSLATIONS = {
    "es": {
        "select_profile": "Selecciona un perfil para escanear y editar.",
        "refresh": "Actualizar",
        "no_profiles": "No se encontraron perfiles.\nPor favor, inicia el juego y crea uno primero.",
        "initializing": "Inicializando...",
        "checking_tools": "Comprobando herramientas (descargando si faltan)...",
        "processing_complete": "Â¡Procesado completado! Preparando panel...",
        "available_mods": "Mods Disponibles",
        "load_order": "Orden de Carga (Prioridad alta arriba)",
        "share_preset": "Compartir Preset",
        "import_code": "Importar CÃ³digo",
        "save_to_game": "Guardar al Juego",
        "my_presets": "Mis Presets",
        "active": "Activos",
        "inactive": "Inactivos",
        "total": "Total Procesados",
        "enter_preset_name": "Introduce un nombre para este preset:",
        "preset_shared": "Preset Compartido",
        "your_code_is": "Tu cÃ³digo es:",
        "share_with_friends": "Â¡Comparte este cÃ³digo con tus amigos!",
        "import_preset": "Importar Preset",
        "enter_code": "Introduce el cÃ³digo del preset:",
        "invalid_code": "CÃ³digo invÃ¡lido o caducado.",
        "preset_imported": "Â¡Preset importado! No olvides darle a Guardar al Juego.",
        "save_success": "Â¡Orden de carga guardada correctamente en el perfil!",
        "save_error": "Error al guardar en profile.sii:",
        "my_shared_presets": "Mis Presets Compartidos",
        "click_to_copy": "Haz clic en un preset para copiar su cÃ³digo:",
        "no_presets_yet": "AÃºn no has compartido ningÃºn preset.",
        "copied": "Copiado",
        "code_copied": "Â¡CÃ³digo copiado al portapapeles!",
        "copy_code": "Copiar CÃ³digo",
        "delete": "Eliminar",
        "confirm_delete": "Â¿EstÃ¡s seguro de que quieres eliminar este preset?",
        "preset_deleted": "Preset eliminado correctamente.",
        "clear_order": "Limpiar Orden",
        "launch_game": "Lanzar Juego",
        "launching": "Lanzando...",
        "loading": "Cargando...",
        "settings": "Ajustes",
        "change_game": "Juegos",
        "cloud_group": "Nube",
        "actions_group": "Acciones",
        "paths_settings": "Ajustes de carpetas",
        "game_directory": "Directorio del juego",
        "auto_game_dir_hint": "Ruta detectada automÃ¡ticamente:",
        "manual_game_dir_hint": "Selecciona la carpeta de datos del juego o tu carpeta -homedir:",
        "automatic": "AutomÃ¡tico",
        "manual": "Manual",
        "browse": "Buscar",
        "reset": "Restablecer",
        "downloaded_mods": "Mods descargados",
        "workshop_mods": "Mods de Steam Workshop",
        "add_path": "AÃ±adir ruta",
        "remove": "Quitar",
        "save_settings": "Guardar ajustes",
        "settings_saved": "Ajustes guardados. Vuelve a escanear para aplicar cambios.",
        "invalid_paths": "Hay rutas no vÃ¡lidas:",
        "workshop_hint": "Sugerir rutas de Workshop",
        "error": "Error",
        "success": "Ã‰xito",
        "cancel": "Cancelar",
        "ok": "OK"
    },
    "en": {
        "select_profile": "Select Profile",
        "refresh": "Refresh List",
        "no_profiles": "No profiles found.\nPlease launch the game and create one first.",
        "initializing": "Initializing...",
        "checking_tools": "Checking tools (downloading if missing)...",
        "processing_complete": "Processing complete! Preparing dashboard...",
        "available_mods": "Available Mods",
        "load_order": "Load Order (Highest priority top)",
        "share_preset": "Share Preset",
        "import_code": "Import Code",
        "save_to_game": "Save to Game",
        "my_presets": "My Presets",
        "active": "Active",
        "inactive": "Inactive",
        "total": "Total Processed",
        "enter_preset_name": "Enter a name for this preset:",
        "preset_shared": "Preset Shared",
        "your_code_is": "Your code is:",
        "share_with_friends": "Share this code with friends!",
        "import_preset": "Import Preset",
        "enter_code": "Enter preset code:",
        "invalid_code": "Invalid or expired code.",
        "preset_imported": "Preset imported! Don't forget to click Save to Game.",
        "save_success": "Load order saved successfully to game profile!",
        "save_error": "Failed to save to profile.sii:",
        "my_shared_presets": "My Shared Presets",
        "click_to_copy": "Click a preset to copy its code:",
        "no_presets_yet": "You haven't shared any presets yet.",
        "copied": "Copied",
        "code_copied": "Code copied to clipboard!",
        "copy_code": "Copy Code",
        "delete": "Delete",
        "confirm_delete": "Are you sure you want to delete this preset?",
        "preset_deleted": "Preset deleted successfully.",
        "clear_order": "Clear Order",
        "launch_game": "Launch Game",
        "launching": "Launching...",
        "loading": "Loading...",
        "settings": "Settings",
        "change_game": "Games",
        "cloud_group": "Cloud",
        "actions_group": "Actions",
        "paths_settings": "Folder settings",
        "game_directory": "Game directory",
        "automatic": "Automatic",
        "manual": "Manual",
        "browse": "Browse",
        "reset": "Reset",
        "downloaded_mods": "Downloaded mods",
        "workshop_mods": "Steam Workshop mods",
        "add_path": "Add path",
        "remove": "Remove",
        "save_settings": "Save settings",
        "settings_saved": "Settings saved. Scan again to apply changes.",
        "invalid_paths": "Some folders are not valid:",
        "workshop_hint": "Suggest Workshop folders",
        "error": "Error",
        "success": "Success",
        "cancel": "Cancel",
        "ok": "OK"
    }
}


TRANSLATIONS["es"].update({
    "app_title": "Truck Mod Manager",
    "back": "Volver",
    "select": "Seleccionar",
    "select_game_subtitle": "Selecciona el juego que quieres gestionar",
    "choose_game": "Elige el juego",
    "choose_profile": "Elige el perfil",
    "no_supported_games": "No se encontraron juegos compatibles.\nInstala ETS2 o ATS y \u00e1brelos una vez.",
    "level": "Nivel",
    "no_profiles_found": "No se encontraron perfiles",
    "profile_help": "No se encontraron perfiles para {game}.\n\n1. Abre el juego y crea un perfil o empresa, guarda y sal.\n\n2. Si usas Steam Cloud, desact\u00edvalo:\n   Steam > Biblioteca > clic derecho en el juego\n   > Propiedades > General > desmarca\n   'Guardar partidas en Steam Cloud'\n   Luego abre el juego una vez para sincronizarlo localmente.\n\n3. Pulsa Actualizar cuando termines.",
    "home": "Inicio",
    "profiles": "Perfiles",
    "mods": "Mods",
    "workshop": "Workshop",
    "order": "Orden",
    "presets": "Presets",
    "about": "Acerca de",
    "theme": "Tema",
    "connected": "Conectado",
    "online_users": "Usuarios: {count}",
    "online_users_unknown": "Usuarios: --",
    "games": "Juegos",
    "dashboard_subtitle": "Gestiona los mods de {game} para el perfil {profile}.",
    "current_profile": "Perfil actual",
    "installed_locally": "Instalados localmente",
    "subscribed_mods": "Mods suscritos",
    "active_mods": "Mods activos",
    "quick_actions": "Acciones r\u00e1pidas",
    "save_load_order": "Guardar orden",
    "launch_game": "Abrir juego",
    "import_preset_code": "Importar c\u00f3digo",
    "open_settings": "Abrir ajustes",
    "recent_profile": "Perfil reciente",
    "active": "Activo",
    "driver": "Conductor",
    "view_order": "Ver Orden",
    "selected_profile": "Perfil seleccionado",
    "edit_profile": "Editar perfil",
    "profile_editor": "Editor de perfil",
    "editor_profile_section": "Perfil",
    "editor_economy_section": "EconomÃ­a",
    "editor_skills_section": "Habilidades",
    "editor_company_section": "CompaÃ±Ã­a",
    "game_save_not_found": "No se encontrÃ³ ningÃºn game.sii en las partidas guardadas de este perfil.",
    "save_file": "Partida",
    "field_not_found": "No disponible en esta partida",
    "bank_loan": "PrÃ©stamo bancario",
    "total_distance": "Distancia total",
    "experience_points": "Experiencia de partida",
    "skill_adr": "ADR",
    "skill_long_dist": "Larga distancia",
    "skill_heavy": "Carga pesada",
    "skill_fragile": "Carga frÃ¡gil",
    "skill_urgent": "Entrega urgente",
    "skill_mechanical": "ConducciÃ³n eficiente",
    "garages": "Garajes",
    "trucks": "Camiones",
    "drivers": "Conductores",
    "read_only_summary": "Resumen detectado en la partida actual",
    "profile_name": "Nombre del perfil",
    "driver_name": "Nombre del conductor",
    "company_name": "Nombre de la empresa",
    "experience": "Experiencia",
    "money": "Dinero",
    "money_not_available": "El campo de dinero no estÃ¡ disponible en este profile.sii.",
    "save_profile": "Guardar perfil",
    "profile_saved": "Perfil guardado correctamente. Se creÃ³ una copia de seguridad.",
    "profile_save_warning": "Cierra el juego antes de guardar cambios en el perfil.",
    "invalid_number": "NÃºmero invÃ¡lido: {field}",
    "auto_game_dir_hint": "Ruta detectada autom\u00e1ticamente:",
    "manual_game_dir_hint": "Selecciona la carpeta de datos del juego o tu carpeta -homedir:",
    "change_game": "Cambiar juego",
    "save_to_game": "Guardar en el juego",
    "clear_order": "Limpiar orden",
    "no_inactive_mods": "No hay mods inactivos.",
    "no_active_mods_yet": "Todav\u00eda no hay mods activos.",
    "workshop_mods_title": "Mods de Workshop",
    "all_mods": "Todos los mods",
    "no_mods_found": "No se encontraron mods.",
    "presets_description": "Comparte tu orden actual o importa un c\u00f3digo de otro jugador.",
    "about_text": "{app} v{version}\nVersi\u00f3n de prueba del redise\u00f1o moderno\nCompatible con Euro Truck Simulator 2 y American Truck Simulator.",
    "open": "Abrir",
    "game_dir_empty": "El directorio del juego est\u00e1 vac\u00edo.",
    "game_dir_invalid": "El directorio del juego no es v\u00e1lido: {path}",
    "language": "Idioma",
    "dark": "Oscuro",
    "light": "Claro",
    "dashboard": "Dashboard",
    "dashboard_html_subtitle": "Gestiona perfiles, mods y ajustes desde una interfaz HTML/CSS.",
    "game": "Juego",
    "profile": "Perfil",
    "unselected": "Sin seleccionar",
    "status": "Estado",
    "ready": "Listo",
    "installed_workshop": "Instalados y Workshop",
    "available_mods": "Mods disponibles",
    "save_order_game": "Guardar en el juego",
    "load_order_plain": "Orden de carga",
    "settings_subtitle": "Configura detecciÃ³n automÃ¡tica o manual.",
    "mode": "Modo",
    "auto_path": "Ruta automÃ¡tica:",
    "game_directory_homedir": "Directorio del juego / -homedir",
    "company": "Empresa",
    "economy": "EconomÃ­a",
    "skills": "Habilidades",
    "company_section": "CompaÃ±Ã­a",
    "game_sii_not_found": "No se encontrÃ³ game.sii.",
    "saved": "Guardado.",
    "settings_saved_short": "Ajustes guardados.",
    "profile_saved_short": "Perfil guardado.",
    "about_html": "Interfaz HTML/CSS conectada al backend Python del manager.",
    "save_preset_title": "Guardar preset",
    "preset_name": "Nombre del preset",
    "unnamed_preset": "Preset sin nombre",
    "preset_code_empty": "El cÃ³digo del preset estÃ¡ vacÃ­o.",
    "preset_name_empty": "El nombre del preset estÃ¡ vacÃ­o.",
    "rename_preset": "Cambiar nombre",
    "rename_preset_hint": "Escribe el nuevo nombre del preset.",
    "preset_renamed": "Nombre del preset actualizado.",
    "mod_preview": "Vista previa",
    "mod_preview_unavailable": "La vista previa no estÃ¡ disponible. Puede que este mod sea privado, estÃ© encriptado o no incluya imagen.",
    "profile_not_found": "No se encontrÃ³ el perfil.",
    "select_profile_first": "Selecciona un perfil primero.",
    "mod_not_found": "No se encontrÃ³ el mod.",
    "not_found": "No encontrado.",
    "save": "Guardar",
    "firebase_not_configured": "Firebase no estÃ¡ configurado.",
})

TRANSLATIONS["en"].update({
    "app_title": "Truck Mod Manager",
    "back": "Back",
    "select": "Select",
    "select_game_subtitle": "Select the game you want to manage",
    "choose_game": "Choose game",
    "choose_profile": "Choose profile",
    "no_supported_games": "No supported games found.\nInstall ETS2 or ATS and launch them once.",
    "level": "Level",
    "no_profiles_found": "No profiles found",
    "profile_help": "No profiles were found for {game}.\n\n1. Launch the game and create a profile/company, then save and exit.\n\n2. If you use Steam Cloud, disable it:\n   Steam > Library > Right-click the game\n   > Properties > General > uncheck\n   'Keep game saves in Steam Cloud'\n   Then launch the game once to sync locally.\n\n3. Click Refresh when done.",
    "home": "Home",
    "profiles": "Profiles",
    "mods": "Mods",
    "workshop": "Workshop",
    "order": "Order",
    "presets": "Presets",
    "about": "About",
    "theme": "Theme",
    "connected": "Connected",
    "online_users": "Users: {count}",
    "online_users_unknown": "Users: --",
    "games": "Games",
    "dashboard_subtitle": "Manage {game} mods for profile {profile}.",
    "current_profile": "Current profile",
    "installed_locally": "Installed locally",
    "subscribed_mods": "Subscribed mods",
    "active_mods": "Active mods",
    "quick_actions": "Quick Actions",
    "save_load_order": "Save load order",
    "launch_game": "Launch game",
    "import_preset_code": "Import preset code",
    "open_settings": "Open settings",
    "recent_profile": "Recent Profile",
    "active": "Active",
    "driver": "Driver",
    "view_order": "View Order",
    "selected_profile": "Selected profile",
    "edit_profile": "Edit profile",
    "profile_editor": "Profile editor",
    "editor_profile_section": "Profile",
    "editor_economy_section": "Economy",
    "editor_skills_section": "Skills",
    "editor_company_section": "Company",
    "game_save_not_found": "No game.sii was found in this profile's saves.",
    "save_file": "Save file",
    "field_not_found": "Not available in this save",
    "bank_loan": "Bank loan",
    "total_distance": "Total distance",
    "experience_points": "Save experience",
    "skill_adr": "ADR",
    "skill_long_dist": "Long distance",
    "skill_heavy": "Heavy cargo",
    "skill_fragile": "Fragile cargo",
    "skill_urgent": "Urgent delivery",
    "skill_mechanical": "Eco driving",
    "garages": "Garages",
    "trucks": "Trucks",
    "drivers": "Drivers",
    "read_only_summary": "Detected summary in the current save",
    "profile_name": "Profile name",
    "driver_name": "Driver name",
    "company_name": "Company name",
    "experience": "Experience",
    "money": "Money",
    "money_not_available": "The money field is not available in this profile.sii.",
    "save_profile": "Save profile",
    "profile_saved": "Profile saved successfully. A backup was created.",
    "profile_save_warning": "Close the game before saving profile changes.",
    "invalid_number": "Invalid number: {field}",
    "auto_game_dir_hint": "Automatically detected path:",
    "manual_game_dir_hint": "Select the game data folder or your -homedir folder:",
    "change_game": "Change game",
    "save_to_game": "Save to Game",
    "clear_order": "Clear Order",
    "no_inactive_mods": "No inactive mods.",
    "no_active_mods_yet": "No active mods yet.",
    "workshop_mods_title": "Workshop Mods",
    "all_mods": "All Mods",
    "no_mods_found": "No mods found.",
    "presets_description": "Share your current load order or import a code from another player.",
    "about_text": "{app} v{version}\nModern redesign test build\nSupports Euro Truck Simulator 2 and American Truck Simulator.",
    "open": "Open",
    "game_dir_empty": "Game directory is empty.",
    "game_dir_invalid": "Game directory is not valid: {path}",
    "language": "Language",
    "dark": "Dark",
    "light": "Light",
    "dashboard": "Dashboard",
    "dashboard_html_subtitle": "Manage profiles, mods, and settings from an HTML/CSS interface.",
    "game": "Game",
    "profile": "Profile",
    "unselected": "Not selected",
    "status": "Status",
    "ready": "Ready",
    "installed_workshop": "Installed and Workshop",
    "available_mods": "Available mods",
    "save_order_game": "Save to game",
    "load_order_plain": "Load order",
    "settings_subtitle": "Configure automatic or manual detection.",
    "mode": "Mode",
    "auto_path": "Automatic path:",
    "game_directory_homedir": "Game directory / -homedir",
    "company": "Company",
    "economy": "Economy",
    "skills": "Skills",
    "company_section": "Company",
    "game_sii_not_found": "game.sii was not found.",
    "saved": "Saved.",
    "settings_saved_short": "Settings saved.",
    "profile_saved_short": "Profile saved.",
    "about_html": "HTML/CSS interface connected to the manager Python backend.",
    "save_preset_title": "Save preset",
    "preset_name": "Preset name",
    "unnamed_preset": "Unnamed preset",
    "preset_code_empty": "Preset code is empty.",
    "preset_name_empty": "Preset name is empty.",
    "rename_preset": "Rename",
    "rename_preset_hint": "Enter the new preset name.",
    "preset_renamed": "Preset name updated.",
    "mod_preview": "Preview",
    "mod_preview_unavailable": "Preview is not available. The mod may be private, encrypted, or may not include an image.",
    "profile_not_found": "Profile not found.",
    "select_profile_first": "Select a profile first.",
    "mod_not_found": "Mod not found.",
    "not_found": "Not found.",
    "save": "Save",
    "firebase_not_configured": "Firebase is not configured.",
})

TRANSLATIONS["es"].update({
    "close": "Cerrar",
    "profile_review_required": "El perfil necesita revisión",
    "profile_review_manual": "He encontrado detalles que conviene revisar manualmente:\n\n{issues}",
    "repair_profile_recommended": "Reparar perfil (muy recomendado)",
    "repair_profile_message": "He encontrado detalles en el perfil que pueden afectar al orden de carga o a la lectura del profile.sii. Antes de reparar se creará una copia de seguridad.\n\n{issues}",
    "repair_profile": "Reparar perfil",
    "continue_without_repair": "Continuar sin reparar",
    "profile_repaired": "Perfil reparado correctamente.",
    "pending_review": "Revisión pendiente",
    "profile_repair_remaining": "Se reparó lo automático, pero queda algo para revisar:\n\n{issues}",
    "local_mods_auto_hint": "Automático usa la carpeta mod dentro del directorio del juego / -homedir.",
    "workshop_auto_hint": "Automático busca Workshop en las bibliotecas de Steam.",
})

TRANSLATIONS["en"].update({
    "close": "Close",
    "profile_review_required": "Profile needs review",
    "profile_review_manual": "I found details that should be reviewed manually:\n\n{issues}",
    "repair_profile_recommended": "Repair profile (strongly recommended)",
    "repair_profile_message": "I found details in this profile that can affect the load order or profile.sii reading. A backup will be created before repairing.\n\n{issues}",
    "repair_profile": "Repair profile",
    "continue_without_repair": "Continue without repairing",
    "profile_repaired": "Profile repaired successfully.",
    "pending_review": "Review still needed",
    "profile_repair_remaining": "The automatic repair was applied, but something still needs review:\n\n{issues}",
    "local_mods_auto_hint": "Automatic uses the mod folder inside the game directory / -homedir.",
    "workshop_auto_hint": "Automatic searches for Workshop mods in Steam libraries.",
})
def txt(key: str) -> str:
    """Helper to get translated text."""
    return TRANSLATIONS.get(CUR_LANG, TRANSLATIONS["en"]).get(key, key)

def set_lang(lang: str):
    """Sets the current language."""
    global CUR_LANG
    if lang in TRANSLATIONS:
        CUR_LANG = lang

def launch_game(game: str = "ets2") -> None:
    """Launches the given game via Steam protocol."""
    import subprocess
    app_id = GAME_CONFIGS[game]["app_id"]
    subprocess.Popen(["cmd", "/c", f"start steam://rungameid/{app_id}"])


def launch_ets2() -> None:
    """Launches ETS2 via Steam protocol."""
    launch_game("ets2")



