"""
cloud/firebase_client.py - Cloud Presets using Firestore (google-cloud-firestore).

Uses a simple 'presets' collection where docs are named by a unique code.
Format:
{
  "code": "XXXX-YYYY-ZZZZ...",
  "profile_name": "My Profile",
  "mods": [
    "mod_a.scs",
    "workshop/227300/abc.zip"
  ],
  "timestamp": 1690000000
}
"""
import secrets
import string
import time
from typing import Optional

from google.cloud import firestore

from core.config import get_app_dir, FIREBASE_CREDENTIALS_FILE, FIRESTORE_COLLECTION, PRESET_CODE_LENGTH, FIREBASE_CONFIG, APP_VERSION
from core.logger import get_logger

_log = get_logger("firebase")

PRESENCE_COLLECTION = "manager_presence"
PRESENCE_TIMEOUT_SECONDS = 12

import hashlib
import uuid

def _get_device_id() -> str:
    """Generates a consistent anonymized hardware fingerprint for this PC."""
    mac_node = uuid.getnode()
    return hashlib.sha256(str(mac_node).encode("utf-8")).hexdigest()[:16]

class FirebaseClient:
    """Wrapper for Firestore operations."""
    def __init__(self):
        self.db: Optional[firestore.Client] = None
        self._init_client()
        self.device_id = _get_device_id()

    def _init_client(self):
        """Initializes the Firestore client from embedded config or local JSON."""
        import firebase_admin
        from firebase_admin import credentials, firestore as admin_firestore
        from core.config import FIREBASE_CONFIG

        self.last_error = None
        try:
            try:
                app = firebase_admin.get_app()
                _log.debug("Firebase app already initialized")
            except ValueError:
                if FIREBASE_CONFIG and isinstance(FIREBASE_CONFIG, dict):
                    cred = credentials.Certificate(FIREBASE_CONFIG)
                    app = firebase_admin.initialize_app(cred)
                    _log.info("Firebase initialized from embedded config")
                else:
                    cred_path = get_app_dir() / "firebase_credentials.json"
                    if cred_path.exists():
                        cred = credentials.Certificate(str(cred_path))
                        app = firebase_admin.initialize_app(cred)
                        _log.info("Firebase initialized from credentials file")
                    else:
                        self.last_error = "Firebase config missing."
                        _log.warning("Firebase config missing — cloud features disabled")
                        return

            self.db = admin_firestore.client()
            _log.info("Firestore client ready")
        except Exception as e:
            self.last_error = str(e)
            _log.error("Firebase init failed: %s", e)

    def is_configured(self) -> bool:
        """Returns True if the database client is successfully initialized."""
        return self.db is not None

    def update_presence(self) -> None:
        """Marks this device as currently online."""
        if not self.db:
            raise RuntimeError("Database not configured.")

        now = int(time.time())
        self.db.collection(PRESENCE_COLLECTION).document(self.device_id).set({
            "device_id": self.device_id,
            "last_seen": now,
            "app_version": APP_VERSION,
        }, merge=True)

    def get_active_user_count(self, timeout_seconds: int = PRESENCE_TIMEOUT_SECONDS) -> int:
        """Counts devices that have sent a heartbeat recently."""
        if not self.db:
            raise RuntimeError("Database not configured.")

        cutoff = int(time.time()) - timeout_seconds
        from google.cloud.firestore_v1.base_query import FieldFilter
        docs = self.db.collection(PRESENCE_COLLECTION)\
            .where(filter=FieldFilter("last_seen", ">=", cutoff))\
            .stream()
        return sum(1 for _ in docs)

    def clear_presence(self) -> None:
        """Removes this device from the online list when the app closes."""
        if not self.db:
            return
        try:
            self.db.collection(PRESENCE_COLLECTION).document(self.device_id).delete()
        except Exception as e:
            _log.debug("Presence cleanup failed: %s", e)

    def _generate_code(self) -> str:
        """Generates a secure random alphabetical code formatted as AAAA-BBBB-CCCC."""
        alphabet = string.ascii_uppercase
        raw = ''.join(secrets.choice(alphabet) for _ in range(PRESET_CODE_LENGTH))
        return "-".join(raw[i:i+5] for i in range(0, len(raw), 5))

    def upload_preset(self, preset_name: str, active_mods: list[str]) -> str:
        """Uploads an active mod list to Firestore and returns the access code."""
        if not self.db:
            raise RuntimeError("Database not configured. Missing credentials file.")

        code = self._generate_code()
        _log.info("Uploading preset '%s' with %d mods, code=%s", preset_name, len(active_mods), code)
        doc_ref = self.db.collection(FIRESTORE_COLLECTION).document(code)
        doc_ref.set({
            "code": code,
            "preset_name": preset_name,
            "mods": active_mods,
            "timestamp": int(time.time()),
            "device_id": self.device_id
        })
        _log.info("Preset uploaded successfully")
        return code

    def download_preset(self, code: str) -> Optional[list[str]]:
        """Retrieves a preset by code."""
        if not self.db:
            raise RuntimeError("Database not configured.")

        clean_code = code.replace(" ", "").upper()
        _log.info("Downloading preset code=%s", clean_code)
        doc = self.db.collection(FIRESTORE_COLLECTION).document(clean_code).get()

        if doc.exists:
            mods = doc.to_dict().get("mods", [])
            _log.info("Preset found — %d mods", len(mods))
            return mods
        _log.warning("Preset not found: %s", clean_code)
        return None

    def get_my_presets(self) -> list[dict]:
        """Queries Firestore for all presets created by this specific hardware."""
        if not self.db:
            raise RuntimeError("Database not configured.")

        _log.info("Fetching presets for device_id=%s", self.device_id)
        from google.cloud.firestore_v1.base_query import FieldFilter
        docs = self.db.collection(FIRESTORE_COLLECTION)\
            .where(filter=FieldFilter("device_id", "==", self.device_id))\
            .limit(50)\
            .stream()
        results = sorted([doc.to_dict() for doc in docs], key=lambda x: x.get("timestamp", 0), reverse=True)
        _log.info("Found %d preset(s)", len(results))
        return results

    def delete_preset(self, code: str):
        """Deletes a preset by code, but only if it belongs to this device."""
        if not self.db:
            raise RuntimeError("Database not configured.")

        _log.info("Deleting preset code=%s", code)
        doc_ref = self.db.collection(FIRESTORE_COLLECTION).document(code)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            if data.get("device_id") == self.device_id:
                doc_ref.delete()
                _log.info("Preset deleted")
            else:
                _log.warning("Delete denied — preset belongs to another device")
                raise PermissionError("You can only delete your own presets.")
        else:
            _log.warning("Preset not found for deletion: %s", code)
            raise FileNotFoundError("Preset not found.")

    def rename_preset(self, code: str, preset_name: str):
        """Renames a preset, but only if it belongs to this device."""
        if not self.db:
            raise RuntimeError("Database not configured.")

        clean_code = code.replace(" ", "").upper()
        new_name = preset_name.strip()
        _log.info("Renaming preset code=%s", clean_code)
        doc_ref = self.db.collection(FIRESTORE_COLLECTION).document(clean_code)
        doc = doc_ref.get()
        if not doc.exists:
            _log.warning("Preset not found for rename: %s", clean_code)
            raise FileNotFoundError("Preset not found.")

        data = doc.to_dict()
        if data.get("device_id") != self.device_id:
            _log.warning("Rename denied - preset belongs to another device")
            raise PermissionError("You can only rename your own presets.")

        doc_ref.update({
            "preset_name": new_name,
            "updated_at": int(time.time()),
        })
        _log.info("Preset renamed")
