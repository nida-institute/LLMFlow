import logging
import os
import typer
from datetime import datetime


def setup_logging(output_dir, book, debug=False):
    """Setup file-based logging that captures all debug output."""
    log_file = os.path.join(output_dir, f"{book}_backtranslation.log")
    # Suppress external library loggers entirely
    for logger_name in ['httpx', 'openai', 'urllib3', 'httpcore']:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.CRITICAL)
        logger.propagate = False
        # Remove all handlers from these loggers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    # Remove existing handlers to avoid duplicate logs
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # File handler - always captures everything
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(message)s'))
    logging.root.addHandler(file_handler)

    # Console handler - respects debug flag
    if debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter('%(message)s'))
        logging.root.addHandler(console_handler)

    # Setup root logger
    logging.root.setLevel(logging.DEBUG)

    # Log session start
    logging.info(f"=== Back-translation session started for {book} ===")
    logging.info(f"Log file: {log_file}")

    return log_file


def log_section(label, data, debug=False):
    msg = f"\n=== {label} ===\n{data}\n"
    logging.debug(msg)
    if debug:
        typer.secho(msg, fg=typer.colors.CYAN)

def log_info(message, debug=False):
    logging.info(message)
    if debug:
        typer.secho(message, fg=typer.colors.GREEN)

class PipelineLogger:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Only initialize once
        if not PipelineLogger._initialized:
            self.logger = logging.getLogger('llmflow')
            self.logger.setLevel(logging.DEBUG)

            # CRITICAL: Prevent propagation to avoid duplicates
            self.logger.propagate = False

            # Clear any existing handlers
            self.logger.handlers.clear()

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter('%(message)s')
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

            # File handler
            file_handler = logging.FileHandler('llmflow.log')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

            PipelineLogger._initialized = True