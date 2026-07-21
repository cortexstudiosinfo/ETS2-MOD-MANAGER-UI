from __future__ import annotations

import json
import io
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from cloud.firebase_client import FirebaseClient
import core.config as config
from core.config import APP_NAME, APP_VERSION, GAME_CONFIGS, get_icon_path, get_logo_path, txt, TRANSLATIONS, set_lang
from core.mod_scanner import scan_mods
from core.profile_utils import list_profiles
from core.profile_mods import read_active_mods, write_active_mods
from core.profile_editor import read_editable_profile, write_editable_profile
from core.profile_health import validate_profile, repair_profile
from core.game_editor import read_game_editor_data, write_game_editor_data, GAME_FIELD_DEFS
from core.settings import get_game_settings, update_game_settings, reset_game_settings, get_default_game_dir, get_game_root

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / 'static'

class AppState:
    def __init__(self):
        self.game = 'ets2'
        self.profile_id = None
        self.profile_path = None
        self.profile_display_name = None
        self.profile_driver_name = None
        self.mods = []
        self.active_mods = []
        self.scanning = False
        self.scan_message = ''
        self.online_count = None
        self.cloud = FirebaseClient()
        self.presence_running = True

    def start_presence(self):
        def loop():
            while self.presence_running:
                try:
                    if self.cloud.is_configured():
                        self.cloud.update_presence()
                        self.online_count = self.cloud.get_active_user_count()
                except Exception:
                    self.online_count = None
                time.sleep(3)
        threading.Thread(target=loop, daemon=True).start()

STATE = AppState()
STATE.start_presence()


def _set_windows_app_id():
    if config.sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            f"CortexStudios.{APP_NAME.replace(' ', '')}.{APP_VERSION}"
        )
    except Exception:
        pass


def _json(handler, data, status=200):
    raw = json.dumps(data, ensure_ascii=False).encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Content-Length', str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def _read_body(handler):
    size = int(handler.headers.get('Content-Length') or 0)
    if size <= 0:
        return {}
    return json.loads(handler.rfile.read(size).decode('utf-8'))


def _profile_payload(profile):
    return {
        'hex_id': profile.hex_id,
        'display_name': profile.display_name,
        'driver_name': profile.driver_name,
        'level': profile.level,
        'path': str(profile.path),
    }


def _mod_payload(mod):
    return {
        'id': mod.internal_id,
        'name': mod.name,
        'source': mod.source,
        'filename': mod.filename,
        'preview_available': bool(getattr(mod, 'preview_available', False)),
        'active': any(item.split('|')[0].strip() == mod.internal_id for item in STATE.active_mods),
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        return

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == '/':
            self._send_file(STATIC / 'index.html', 'text/html; charset=utf-8')
            return
        if path == '/favicon.ico':
            icon = get_icon_path()
            if icon:
                self._send_file(icon, 'image/x-icon')
                return
            self.send_error(404)
            return
        if path.startswith('/static/'):
            target = STATIC / path.removeprefix('/static/')
            ctype = 'text/plain'
            if target.suffix == '.css': ctype = 'text/css; charset=utf-8'
            elif target.suffix == '.js': ctype = 'application/javascript; charset=utf-8'
            elif target.suffix == '.png': ctype = 'image/png'
            self._send_file(target, ctype)
            return
        if path == '/api/state':
            _json(self, self._state())
            return
        if path == '/api/profiles':
            profiles = [_profile_payload(p) for p in list_profiles(STATE.game)]
            _json(self, {'profiles': profiles})
            return
        if path == '/api/mods':
            _json(self, {'mods': [_mod_payload(m) for m in STATE.mods], 'active': STATE.active_mods})
            return
        if path == '/api/mod-thumb':
            query = dict([part.split('=', 1) if '=' in part else (part, '') for part in parsed.query.split('&') if part])
            mod_id = query.get('id')
            mod = next((m for m in STATE.mods if m.internal_id == mod_id), None)
            if not mod or not getattr(mod, 'thumbnail', None) or not getattr(mod, 'preview_available', False):
                _json(self, {'error': txt('mod_preview_unavailable')}, 404)
                return
            buffer = io.BytesIO()
            mod.thumbnail.save(buffer, format='PNG')
            raw = buffer.getvalue()
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if path == '/api/settings':
            query = parse_qs(parsed.query)
            game = (query.get('game') or [STATE.game])[0]
            if game not in GAME_CONFIGS:
                game = STATE.game
            settings = get_game_settings(game)
            _json(self, {'game': game, 'settings': settings, 'auto_dir': str(get_default_game_dir(game)), 'current_root': str(get_game_root(game))})
            return
        if path == '/api/profile-health':
            if not STATE.profile_path:
                _json(self, {'error': txt('select_profile_first')}, 400); return
            _json(self, {'health': validate_profile(STATE.profile_path).to_dict()})
            return
        if path == '/api/presets':
            if not STATE.cloud.is_configured():
                _json(self, {'error': txt('firebase_not_configured')}, 503); return
            presets = STATE.cloud.get_my_presets()
            _json(self, {'presets': presets})
            return
        if path == '/api/profile-editor':
            if not STATE.profile_path:
                _json(self, {'error': txt('select_profile_first')}, 400); return
            profile_data = read_editable_profile(STATE.profile_path)
            game_data = read_game_editor_data(STATE.profile_path)
            _json(self, {
                'profile': profile_data.__dict__,
                'game': {
                    'save_path': str(game_data.save_path) if game_data.save_path else None,
                    'fields': game_data.fields,
                    'garage_count': game_data.garage_count,
                    'truck_count': game_data.truck_count,
                    'driver_count': game_data.driver_count,
                },
                'defs': GAME_FIELD_DEFS,
            })
            return
        _json(self, {'error': txt('not_found')}, 404)

    def _send_file(self, target: Path, ctype: str):
        if not target.exists() or not target.is_file():
            self.send_error(404); return
        raw = target.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        path = urlparse(self.path).path
        body = _read_body(self)
        try:
            if path == '/api/lang':
                set_lang(body.get('lang', 'es'))
                _json(self, self._state()); return
            if path == '/api/game':
                STATE.game = body.get('game', 'ets2')
                STATE.profile_id = None; STATE.profile_path = None; STATE.profile_display_name = None; STATE.profile_driver_name = None; STATE.mods = []; STATE.active_mods = []
                _json(self, self._state()); return
            if path == '/api/profile':
                selected = body.get('hex_id')
                profiles = list_profiles(STATE.game)
                profile = next((p for p in profiles if p.hex_id == selected), None)
                if not profile:
                    _json(self, {'error': txt('profile_not_found')}, 404); return
                STATE.profile_id = profile.hex_id
                STATE.profile_path = profile.path
                STATE.profile_display_name = profile.display_name
                STATE.profile_driver_name = profile.driver_name
                STATE.active_mods = read_active_mods(profile.path)
                health = validate_profile(profile.path).to_dict()
                _json(self, {'profile': _profile_payload(profile), 'health': health}); return
            if path == '/api/scan':
                if not STATE.profile_path:
                    _json(self, {'error': txt('select_profile_first')}, 400); return
                def scan():
                    STATE.scanning = True
                    STATE.scan_message = txt('checking_tools')
                    try:
                        STATE.mods = scan_mods(progress_callback=lambda msg: setattr(STATE, 'scan_message', msg), game=STATE.game)
                        STATE.active_mods = read_active_mods(STATE.profile_path)
                    finally:
                        STATE.scanning = False
                threading.Thread(target=scan, daemon=True).start()
                _json(self, {'ok': True}); return
            if path == '/api/toggle-mod':
                mod_id = body.get('id')
                active = bool(body.get('active'))
                mod = next((m for m in STATE.mods if m.internal_id == mod_id), None)
                if not mod:
                    _json(self, {'error': txt('mod_not_found')}, 404); return
                if active and not any(item.split('|')[0].strip() == mod_id for item in STATE.active_mods):
                    STATE.active_mods.append(mod.sii_entry)
                if not active:
                    STATE.active_mods = [item for item in STATE.active_mods if item.split('|')[0].strip() != mod_id]
                _json(self, {'active': STATE.active_mods}); return
            if path == '/api/order':
                ids = body.get('ids') or []
                by_id = {m.internal_id: m for m in STATE.mods}
                ordered = []
                for mod_id in reversed(ids):
                    mod = by_id.get(str(mod_id))
                    if mod:
                        ordered.append(mod.sii_entry)
                STATE.active_mods = ordered
                _json(self, {'ok': True, 'active': STATE.active_mods}); return
            if path == '/api/save-order':
                if not STATE.profile_path:
                    _json(self, {'error': txt('select_profile_first')}, 400); return
                write_active_mods(STATE.profile_path, STATE.active_mods)
                _json(self, {'ok': True}); return
            if path == '/api/repair-profile':
                if not STATE.profile_path:
                    _json(self, {'error': txt('select_profile_first')}, 400); return
                health = repair_profile(STATE.profile_path)
                STATE.active_mods = read_active_mods(STATE.profile_path)
                _json(self, {'ok': True, 'health': health.to_dict()}); return
            if path == '/api/presets/share':
                if not STATE.cloud.is_configured():
                    _json(self, {'error': txt('firebase_not_configured')}, 503); return
                name = (body.get('name') or '').strip() or 'Preset'
                code = STATE.cloud.upload_preset(name, STATE.active_mods)
                _json(self, {'ok': True, 'code': code}); return
            if path == '/api/presets/import':
                if not STATE.cloud.is_configured():
                    _json(self, {'error': txt('firebase_not_configured')}, 503); return
                code = (body.get('code') or '').strip()
                if not code:
                    _json(self, {'error': txt('preset_code_empty')}, 400); return
                mods = STATE.cloud.download_preset(code)
                if mods is None:
                    _json(self, {'error': txt('invalid_code')}, 404); return
                STATE.active_mods = list(mods)
                _json(self, {'ok': True, 'active': STATE.active_mods}); return
            if path == '/api/presets/delete':
                if not STATE.cloud.is_configured():
                    _json(self, {'error': txt('firebase_not_configured')}, 503); return
                code = (body.get('code') or '').strip()
                if not code:
                    _json(self, {'error': txt('preset_code_empty')}, 400); return
                STATE.cloud.delete_preset(code)
                _json(self, {'ok': True}); return
            if path == '/api/presets/rename':
                if not STATE.cloud.is_configured():
                    _json(self, {'error': txt('firebase_not_configured')}, 503); return
                code = (body.get('code') or '').strip()
                name = (body.get('name') or '').strip()
                if not code:
                    _json(self, {'error': txt('preset_code_empty')}, 400); return
                if not name:
                    _json(self, {'error': txt('preset_name_empty')}, 400); return
                STATE.cloud.rename_preset(code, name)
                _json(self, {'ok': True}); return
            if path == '/api/settings':
                game = body.get('game') or STATE.game
                if game not in GAME_CONFIGS:
                    _json(self, {'error': txt('not_found')}, 404); return
                values = dict(body)
                values.pop('game', None)
                if values.get('game_dir_mode') == 'manual' and not str(values.get('manual_game_dir') or '').strip():
                    values['manual_game_dir'] = str(get_default_game_dir(game))
                update_game_settings(game, values)
                _json(self, {'ok': True}); return
            if path == '/api/reset-settings':
                game = body.get('game') or STATE.game
                if game not in GAME_CONFIGS:
                    _json(self, {'error': txt('not_found')}, 404); return
                reset_game_settings(game)
                _json(self, {'ok': True}); return
            if path == '/api/profile-editor':
                if not STATE.profile_path:
                    _json(self, {'error': txt('select_profile_first')}, 400); return
                profile_values = body.get('profile', {})
                game_values = body.get('game', {})
                write_editable_profile(STATE.profile_path, profile_values)
                game_data = read_game_editor_data(STATE.profile_path)
                if game_data.save_path and game_values:
                    write_game_editor_data(game_data.save_path, game_values)
                _json(self, {'ok': True}); return
            _json(self, {'error': txt('not_found')}, 404)
        except Exception as e:
            _json(self, {'error': str(e)}, 500)

    def _state(self):
        return {
            'app': APP_NAME,
            'version': APP_VERSION,
            'game': STATE.game,
            'games': GAME_CONFIGS,
            'profile_id': STATE.profile_id,
            'profile_display_name': STATE.profile_display_name,
            'profile_driver_name': STATE.profile_driver_name,
            'scanning': STATE.scanning,
            'scan_message': STATE.scan_message,
            'online_count': STATE.online_count,
            'lang': config.CUR_LANG,
            'translations': TRANSLATIONS.get(config.CUR_LANG, TRANSLATIONS.get('en', {})),
        }


def run(host='127.0.0.1', port=8765):
    _set_windows_app_id()
    server = ThreadingHTTPServer((host, port), Handler)
    url = f'http://{host}:{port}'
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f'{APP_NAME} web UI running at {url}')

    def cleanup():
        STATE.presence_running = False
        try:
            STATE.cloud.clear_presence()
        except Exception:
            pass
        server.shutdown()

    try:
        import webview
        icon = get_icon_path()
        webview.create_window(APP_NAME, url, width=1360, height=820, min_size=(1100, 720))
        try:
            webview.start(icon=str(icon) if icon else None)
        finally:
            cleanup()
    except Exception:
        webbrowser.open(url)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            cleanup()







