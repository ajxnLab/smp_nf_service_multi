import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Any
from googleapiclient.discovery import build
from utils.logger import setup_in_memory_logger

logger,log_stream = setup_in_memory_logger(__name__)
class GSheetClient:
    def __init__(self, service_account_file: str, sheet_name: str):
        self.service_account_file = service_account_file
        self.sheet_name = sheet_name
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        self.sheet = self.authorize_service_account()
        

    def authorize_service_account(self):
        if not self.service_account_file:
            raise ValueError("Service account file path is required.")

        credentials = Credentials.from_service_account_file(
            self.service_account_file,
            scopes=self.scopes
        )
        self.credentials = credentials
        client = gspread.authorize(credentials)

        try:
            sheet = client.open(self.sheet_name)
            logger.info(f"Opened spreadsheet: {self.sheet_name}")
            return sheet
        except Exception as e:
            logger.error(f"Failed to open spreadsheet '{self.sheet_name}': {e}")
            raise

    def get_sheet_data(self, worksheet_name: str) -> List[Dict[str, Any]]:
        worksheet = self.sheet.worksheet(worksheet_name)
        return worksheet.get_all_records()

    def get_raw_values(self, worksheet_name: str) -> List[List[Any]]:
        worksheet = self.sheet.worksheet(worksheet_name)
        return worksheet.get_all_values()

    def find_row_index(self, records: List[Dict], identifier_column: str, identifier_value: str) -> Dict[str, Any] | None:
        for idx, record in enumerate(records, start=2):
            if record.get(identifier_column) == identifier_value:
                return {
                    "row_index": idx,
                    "record": record
                }
        return None

    def update_cell(self, worksheet_name: str, row_index: int, column_name: str, value: Any):
        worksheet = self.sheet.worksheet(worksheet_name)
        headers = worksheet.row_values(1)
        if column_name not in headers:
            raise ValueError(f"Column '{column_name}' not found in worksheet '{worksheet_name}'")
        col_index = headers.index(column_name) + 1
        worksheet.update_cell(row_index, col_index, value)

    def authenticate_google_drive(self):
        """Authenticate and return Google Drive service instance using service account."""
        return build('drive', 'v3', credentials=self.credentials)

