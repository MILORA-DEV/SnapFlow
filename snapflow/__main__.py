"""SnapFlow desktop application entry point."""

from __future__ import annotations

import logging
import sys
import traceback
from pathlib import Path

from snapflow.ui.app import SnapFlowApp


def get_log_dir() -> Path:
    """Get UAC-safe log directory in %LOCALAPPDATA%."""
    if sys.platform == "win32":
        log_dir = Path.home() / "AppData" / "Local" / "SnapFlow"
    else:
        log_dir = Path.home() / ".snapflow"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logging() -> None:
    """Configure logging to file with global exception handling."""
    log_dir = get_log_dir()
    log_file = log_dir / "snapflow_debug.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Global exception hook to catch all unhandled exceptions
    def global_exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logging.critical(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )
        # Also write to log file explicitly
        with open(log_file, "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write("FATAL UNHANDLED EXCEPTION\n")
            f.write("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            f.write("\n" + "=" * 80 + "\n")

    sys.excepthook = global_exception_handler


def main() -> int:
    """Run the SnapFlow desktop application."""
    setup_logging()
    logging.info("SnapFlow starting...")
    logging.info("Log file: %s", get_log_dir() / "snapflow_debug.log")

    try:
        app = SnapFlowApp()
        app.run()
        return 0
    except KeyboardInterrupt:
        logging.info("SnapFlow interrupted by user")
        return 0
    except Exception as exc:
        logging.exception("Fatal error starting SnapFlow")
        return 1


if __name__ == "__main__":
    sys.exit(main())
