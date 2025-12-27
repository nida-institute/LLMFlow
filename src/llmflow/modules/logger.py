import logging
import sys


class Logger:
    """Singleton logger that writes to console (INFO+) and file (DEBUG+)."""

    _instance = None
    _initialized = False
    _log_file = 'llmflow.log'  # Default log file location

    def __new__(cls, log_file=None):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self, log_file=None):
        # Only initialize once per singleton instance
        if Logger._initialized:
            return

        # Use the log_file from reset() if available, otherwise use parameter or default
        if log_file is None:
            log_file = Logger._log_file

        Logger._initialized = True
        self.level = logging.INFO

        # Configure the llmflow logger specifically
        self.logger = logging.getLogger('llmflow')
        self.logger.setLevel(self.level)

        # Clear any existing handlers
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

        # Console handler (stderr) - set to INFO level to avoid debug spam on screen
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.INFO)  # Console shows only INFO and above
        console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        self.logger.addHandler(console_handler)

        # File handler - OVERWRITE mode ('w') not append, accepts DEBUG level
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # File gets all debug details
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(file_handler)

        # Don't set propagate=False - this breaks pytest's caplog fixture
        # self.logger.propagate = False

    @classmethod
    def reset(cls, log_file='llmflow.log'):
        """Reset the singleton for a new run (e.g., in tests or new pipeline execution)."""
        if cls._instance is not None:
            # Close all handlers
            for handler in cls._instance.logger.handlers[:]:
                handler.close()
                cls._instance.logger.removeHandler(handler)
        cls._instance = None
        cls._initialized = False
        cls._log_file = log_file

    def set_level(self, level: str):
        """Set logging level"""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
        }
        self.level = level_map.get(level.upper(), logging.INFO)
        self.logger.setLevel(self.level)

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def log_section(self, title, level="info"):
        """
        Log a section header with visual separation.

        Args:
            title: The section title
            level: Logging level ("info", "debug", "warning", "error")
        """
        separator = "=" * 60
        header = f"\n{separator}\n📋 {title}\n{separator}"

        if level == "debug":
            self.logger.debug(header)
        elif level == "warning":
            self.logger.warning(header)
        elif level == "error":
            self.logger.error(header)
        else:  # default to info
            self.logger.info(header)

    def log_subsection(self, title, level="info"):
        """
        Log a subsection header with lighter visual separation.

        Args:
            title: The subsection title
            level: Logging level ("info", "debug", "warning", "error")
        """
        separator = "-" * 40
        header = f"\n{separator}\n🔸 {title}\n{separator}"

        if level == "debug":
            self.logger.debug(header)
        elif level == "warning":
            self.logger.warning(header)
        elif level == "error":
            self.logger.error(header)
        else:  # default to info
            self.logger.info(header)

