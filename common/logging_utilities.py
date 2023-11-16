import logging
import os

# Flag to check if logging is already configured
_is_logging_configured = False


def setup_logging(level=None):
    global _is_logging_configured
    if not _is_logging_configured:
        level = level or os.getenv("LOG_LEVEL", "INFO")
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format="%(asctime)s: %(levelname)s: %(message)s",
            # Uncomment the next line to log to a file
            # filename='/path/to/your/logfile.log',
        )
        _is_logging_configured = True
    return logging.getLogger()
