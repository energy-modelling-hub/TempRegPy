import logging
import os

try:
    import colorlog
    _HAS_COLORLOG = True
except ImportError:
    _HAS_COLORLOG = False


def setup_logging():
    """Configure and return the package-wide logger.

    Uses colorlog for colored terminal output if installed,
    otherwise falls back to standard library logging.
    """
    # Get or create the logger first — we need it to clean up old handlers
    if _HAS_COLORLOG:
        logger = colorlog.getLogger('tempregpy')
    else:
        logger = logging.getLogger('tempregpy')

    # ── Close and remove any existing handlers (safe for reload / re-entry) ──
    for h in logger.handlers[:]:          # iterate over a copy of the list
        try:
            h.close()
        except Exception:
            pass
        logger.removeHandler(h)

    # ── Console handler ──────────────────────────────────────────────────────
    if _HAS_COLORLOG:
        handler = colorlog.StreamHandler()
        formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)-8s%(reset)s %(yellow)s%(message)s",
            datefmt=None,
            reset=True,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
        )
        handler.setFormatter(formatter)
    else:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)-8s %(message)s')
        handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # ── File handler ─────────────────────────────────────────────────────────
    log_file = 'app.log'
    if os.path.exists(log_file):
        try:
            os.remove(log_file)
        except OSError:
            pass                          # file locked by another process; reuse it

    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


logger = setup_logging()
