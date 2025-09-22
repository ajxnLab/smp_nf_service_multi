import logging
import os
import pathlib
from datetime import datetime


class CustomFormatter(logging.Formatter):

    def __init__(self, log_format):
        super().__init__()
        grey = "\x1b[37m"
        yellow = "\x1b[33;20m"
        red = "\x1b[31;20m"
        bold_red = "\x1b[31;1m"
        reset = "\x1b[0m"

        self.FORMATS = {
            logging.DEBUG: grey + log_format + reset,
            logging.INFO: grey + log_format + reset,
            logging.WARNING: yellow + log_format + reset,
            logging.ERROR: red + log_format + reset,
            logging.CRITICAL: bold_red + log_format + reset,
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def configure_logger(name, logger_level="INFO") -> logging.Logger:
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    logger_level = (
        logger_level
        if logger_level is not None
        else os.environ.get("LOGGER_LEVEL", "INFO")
    )
    log_level = log_level_map.get(logger_level, logging.INFO)
    log_format = "[%(asctime)s]: [pid-%(process)d]: [%(levelname)s]:[%(filename)s:%(lineno)d - %(funcName)2s()]: %(message)s"

    # Create a logger object
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    handler.setFormatter(CustomFormatter(log_format))

    # Prevent propagation to the parent logger
    logger.propagate = False
    logger.addHandler(handler)
    logger.setLevel(log_level)

    return logger


# Console Logger. Use when you do not need to create a log file
# logger = configure_logger(__name__, "DEBUG")


class Logger:
    """
    Logger class that sets up python logger
    :params str log_dir: exact path to where the logs will be created
    :params str log_id: name of the app, would be part of the file name of the log file.
    :params str set_logger_name: set the name of the app to logger name, so that you can choose which file to log if
     you have multiple log files.

    Sample use 1:
    logger = Logger(log_id).logger

    Sample use 2:
    import logging

    Logger(log_dir, log_id_a, True)
    Logger(log_dir, log_id_b, True)

    logger_a = logging.getLogger("log_id_a")
    logger_b = logging.getLogger("log_id_b")

    logger_a.info("Hello")
    logger_b.info("Hi")

    return
    logger : logger object
    log_dir str: params
    """

    def __init__(
        self,
        log_id,
        create_file=True,
        log_dir=None,
        set_logger_name: bool = False,
        show_logger_id: bool = False,
        enable_stdout: bool = False,
    ) -> None:

        self.log_id = log_id
        self.create_file = create_file
        self.log_format = None
        self.base_dir = (
            log_dir
            or os.environ.get("LOG_BASE_DIR", None)
            or os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "\\logs\\"
        )
        self.set_logger_name = set_logger_name
        self.show_logger_id = show_logger_id
        self.logger_name = ""
        self.LOG_DIR = os.path.join(
            self.base_dir,
            datetime.today().strftime("%Y"),
            datetime.today().strftime("%B"),
        )
        self.with_milliseconds = True
        self.enable_stdout = enable_stdout

        self.logger_level = "INFO"
        self.log_level = None
        self.logger = self.configure_logger()

    def configure_logger(self):

        if self.create_file:
            # checks if directory exists, if not create it
            try:
                pathlib.Path(self.LOG_DIR).mkdir(parents=True, exist_ok=True)
                os.makedirs(self.LOG_DIR)

            except OSError:
                if not os.path.isdir(self.LOG_DIR):
                    raise

        self.LOG_DIR = os.path.join(
            self.LOG_DIR,
            f"{self.log_id}_{datetime.today().strftime('%Y-%m-%d_%H%M%S')}.log",
        )

        if self.set_logger_name is not False:
            logger = logging.getLogger(self.log_id)
        else:
            logger = logging.getLogger(__name__)

        if self.show_logger_id:
            self.logger_name = f" [%(name)-{len(self.log_id)}s]:"

        logger.setLevel(logging.DEBUG)
        # log format: for more formats, check here: https://docs.python.org/3/library/logging.html#logrecord-attributes
        if not self.show_logger_id:
            self.log_format = (
                f"[%(asctime)s]: [pid-%(process)d]: [%(levelname)s]:[%(filename)s:%(lineno)d - "
                f"%(funcName)2s()]: %(message)s"
            )
            formatter = logging.Formatter(self.log_format)
        else:
            self.log_format = (
                f"[%(asctime)s]: [pid-%(process)d]:{self.logger_name} "
                f"[%(levelname)s]:[%(filename)s:%(lineno)d - %(funcName)2s()]: %(message)s"
            )
            formatter = logging.Formatter(self.log_format)

        log_level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        self.logger_level = (
            self.logger_level
            if self.logger_level is not None
            else os.environ.get("LOGGER_LEVEL", "INFO")
        )
        self.log_level = log_level_map.get(self.logger_level, logging.INFO)

        # Create a logger object
        logger = logging.getLogger(self.log_id)
        handler = logging.StreamHandler()
        handler.setFormatter(CustomFormatter(self.log_format))

        self.create_file = (
            True  # Disable storing logs temporary for development and testing purpose
        )
        if self.create_file:
            # create file handler, for file log
            formatter = logging.Formatter(self.log_format)

            file_handler = logging.FileHandler(self.LOG_DIR)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # Prevent propagation to the parent logger
        logger.propagate = False
        logger.addHandler(handler)
        logger.setLevel(self.log_level)

        return logger


# dev logs
local_logger = Logger("NF-")
logger = local_logger.logger


def log_attempt_number(retry_state):
    """return the result of the last call attempt"""
    logger.error(
        f"Attempt #{retry_state.attempt_number}: Retrying after {retry_state.next_action.sleep} seconds."
    )
