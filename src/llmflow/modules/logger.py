import logging
import sys
from pathlib import Path

class Logger:
    def __init__(self):
        self.logger = logging.getLogger('llmflow')
        if not self.logger.handlers:
            self._setup_logger()

    def _setup_logger(self):
        self.logger.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_format)

        # File handler
        file_handler = logging.FileHandler('llmflow.log', mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def log_section(self, title, level="info"):
        """
        Log a section header with visual separation for better readability.

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

# Usage in any module:
# from llmflow.modules.logger import Logger
# logger = Logger()
# logger.info("Step started")
# logger.debug("Debug details")
# logger.error("Error message")
# logger.warning("Warning message")
