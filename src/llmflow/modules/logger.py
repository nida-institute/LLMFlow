import logging
import sys


class Logger:
    def __init__(self, log_file='llmflow.log'):
        self.level = logging.INFO
        # Configure the llmflow logger specifically
        self.logger = logging.getLogger('llmflow')
        self.logger.setLevel(self.level)

        # Add handlers if not already present
        if not self.logger.handlers:
            # Console handler (stderr)
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
            self.logger.addHandler(console_handler)

            # File handler
            file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(file_handler)

        self.logger.propagate = False

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

