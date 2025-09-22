import logging
import sys
from io import StringIO
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from utils.env_loader import get_env_variable
from io import BytesIO  # Add this import


# ──────────────────────────────────────────────────────────────
# COLORS
grey = "\x1b[37m"
yellow = "\x1b[33;20m"
red = "\x1b[31;20m"
bold_red = "\x1b[31;1m"
reset = "\x1b[0m"

class ColoredFormatter(logging.Formatter):
    def __init__(self, fmt, datefmt):
        super().__init__()
        self.datefmt = datefmt
        self.base_fmt = fmt
        self.FORMATS = {
            logging.DEBUG: grey + fmt + reset,
            logging.INFO: grey + fmt + reset,
            logging.WARNING: yellow + fmt + reset,
            logging.ERROR: red + fmt + reset,
            logging.CRITICAL: bold_red + fmt + reset,
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, self.datefmt)
        return formatter.format(record)

# ──────────────────────────────────────────────────────────────
# GLOBALS

_log_stream = StringIO()
logger = logging.getLogger("NF")
_initialized = False  # tracks if logger was already initialized

# ──────────────────────────────────────────────────────────────
# INITIALIZER

def _initialize():
    global _initialized
    if _initialized:
        return

    # Force UTF-8 encoding for stdout
    sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')

    try:
        from utils.google_sheet import GDriveClient
        gd_client = GDriveClient()
    except Exception as e:
        gd_client = None
        print(f"[LOGGER INIT WARNING]: GDrive not initialized: {e}")

    logger.setLevel(logging.INFO)
    fmt = "[%(asctime)s,%(msecs)03d]: [%(name)s] : [%(levelname)s]:[%(filename)s:%(lineno)d - %(funcName)s()]: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    formatter = ColoredFormatter(fmt=fmt, datefmt=datefmt)

    # Console handler with proper Unicode handling
    console_handler = logging.StreamHandler()  # Use default sys.stdout
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    # In-memory handler for file output
    memory_formatter = logging.Formatter(fmt, datefmt)
    stream_handler = logging.StreamHandler(_log_stream)
    stream_handler.setFormatter(memory_formatter)
    stream_handler.setLevel(logging.INFO)
    logger.addHandler(stream_handler)

    # Attach GDrive client
    if gd_client:
        logger.gd_client = gd_client
        logger.log_stream = _log_stream
        logger.info("Drive logger initialized successfully.")
    else:
        logger.warning("Drive logging is disabled — GDriveClient not available.")

    _initialized = True


# ──────────────────────────────────────────────────────────────
# EXPORT LOGGER ON IMPORT

_initialize()

# Now this is importable everywhere as: from utils.logger import logger

# ──────────────────────────────────────────────────────────────
# DRIVE UPLOAD LOGIC

def create_drive_folder(service, name: str, parent_id: str = None) -> str:
    query = f"mimeType='application/vnd.google-apps.folder' and trashed=false and name='{name}'"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    results = service.files().list(
        q=query,
        fields="files(id, name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    items = results.get('files', [])
    if items:
        return items[0]['id']
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id] if parent_id else []
    }
    folder = service.files().create(body=file_metadata, supportsAllDrives=True, fields='id').execute()
    return folder['id']


def create_nested_drive_path(service, base_folder_id: str, path_parts: list[str]) -> str:
    current_folder_id = base_folder_id
    for part in path_parts:
        current_folder_id = create_drive_folder(service, part, current_folder_id)
    return current_folder_id

def upload_log_to_drive(service, content: str, filename: str, folder_id: str):
    """Upload log content to Google Drive"""
    try:
        # Normalize and encode content to bytes
        import unicodedata
        content = unicodedata.normalize('NFKC', content)
        encoded_content = content.encode('utf-8', errors='backslashreplace')
        
        # Use BytesIO instead of StringIO
        binary_stream = BytesIO(encoded_content)
        
        media = MediaIoBaseUpload(
            binary_stream,
            mimetype='text/plain; charset=utf-8',
            resumable=True
        )
        
        file_metadata = {
            'name': filename,
            'parents': [folder_id],
            'mimeType': 'text/plain; charset=utf-8'
        }
        
        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            supportsAllDrives=True,
            fields='id, name'
        ).execute()
        
        logger.info(f"Uploaded log: {uploaded_file['name']} to Google Drive")
        return True
        
    except Exception as e:
        logger.error(f"Failed to upload log file: {e}")
        return False


def finalize_log_upload():
    if hasattr(logger, "gd_client") and hasattr(logger, "log_stream"):
        drive = build('drive', 'v3', credentials=logger.gd_client.credentials)
        now = datetime.now()
        filename = f"{logger.name}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.log"
        subfolders = [now.strftime("%Y"), now.strftime("%B"), now.strftime("%d"), now.strftime("%H")]

        folder_id = create_nested_drive_path(drive, get_env_variable("ROOT_LOG_FOLDER_ID"), subfolders)
        upload_log_to_drive(drive, logger.log_stream.getvalue(), filename, folder_id)
        logger.info("Logs uploaded to Google Drive.")
