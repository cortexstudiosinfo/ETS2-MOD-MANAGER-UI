"""main.py - HTML/CSS launcher for Truck Manager."""
from core.logger import setup_logger, install_excepthook
_log = setup_logger()
install_excepthook(_log)

from webui.server import run

if __name__ == "__main__":
    _log.info("Starting Truck Manager HTML/CSS interface")
    run()
