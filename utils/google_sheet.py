from google.oauth2.service_account import Credentials
from typing import List, Dict, Any
from utils.env_loader import get_env_variable
from nf_services.nf_constants import NfConstants
from gspread.exceptions import APIError, SpreadsheetNotFound, WorksheetNotFound
import gspread
import datetime
import logging
import gspread

logger = logging.getLogger(__name__)

from config.config import nf

class GSheetClient:
    def __init__(self, service_account_file: str = None, scopes: List[str] = None, service_name: str = None ):
        self.logger = logger
        # To Authorize Service Account Access to spreadsheet via gsheet id
        if scopes is None:
            scopes = ["https://www.googleapis.com/auth/drive"]
        
        

        if not service_account_file:
            service_account_file = get_env_variable("GOOGLE_SERVICE_ACCOUNT")
        
        print("Authorized for gsheet:", service_account_file)

        self.credentials = Credentials.from_service_account_file(
            service_account_file, scopes=scopes
        )
    
        client = gspread.authorize(self.credentials)
        self.spreadsheet = client.open_by_key(get_env_variable("GSHEET_ID"))
        print("Authorized scope for gsheet:", self.credentials.scopes)

    # Get Google Worksheet Data using spreadsheet ID
    def get_sheet_data(self, worksheet_name: str) -> List[Dict[str, Any]]:
        worksheet = self.spreadsheet.worksheet(worksheet_name)
        return worksheet.get_all_records()

    def get_raw_values(self, worksheet_name: str) -> List[List[Any]]:
        worksheet = self.spreadsheet.worksheet(worksheet_name)
        return worksheet.get_all_values()

    def create_worksheet(self, worksheet_name: str) -> List[List[Any]]:
        worksheet = self.spreadsheet.worksheet(worksheet_name)
        return worksheet

    # NEW ADDED METHODS ====================================================
    # Get row data based on current date.
    def create_worksheets(self, dict_worksheet_name: Dict) -> Dict:
        dict_worksheet_result = {}
        for key, value in dict_worksheet_name.items():
            worksheet = self.spreadsheet.worksheet(value)
            dict_worksheet_result[key] = worksheet
        return dict_worksheet_result

    def update_row_range(self, worksheet, service_id, list_row, char="M"):
        first_row, last_row = list_row[0], list_row[-1]
        list_service_id = [[service_id]] * len(list_row)
        worksheet.update(f"{char}{first_row}:{char}{last_row}", list_service_id)
        logger.info(f"Row range from M{first_row} to M{last_row} has been updated with service id {service_id}")

    # Function to Update a specific row via row and column coordinates
    def update_row(self, row: int, column: int, worksheet, value: str, retry=1, max_retries=2):
        try:
            self.logger.info(f"{worksheet}: Updating Cell.. R{row}C{column} - Value: {value}")
            # Update cell using 'value'
            worksheet.update_cell(int(row), int(column), value)
        except APIError as e:
            if retry == max_retries:
                self.logger.exception(f"APIError: {e}")
            self.logger.warning(f"gspread API Error - retrying..")
            self.update_row(row, column, worksheet, value, retry=retry+1)

    # Get row data for ParamMatrix worksheet
    def get_rows_by_name(self, worksheet, name_to_find):
        self.logger.info(f"Fetching rows using service name: '{name_to_find}'")

        # find all cells that matches the name_to_find value
        current_cells = worksheet.findall(name_to_find)

        result = []
        if len(current_cells) != 0:
            for cell in current_cells:
                # logger.info(f"Row Fetched: {cell.row}")
                result.append(cell.row)
        else:
            self.logger.info(
                f"The bot was unable to find service name that matches with: '{name_to_find}' under worksheet {worksheet}"
            )
            return []

        self.logger.info(f"Fetch complete: {result}")
        return result
    
    # NEW METHOD TO FETCH DATA CONVERTED TO DICTIONARY

    #OPTION 1: Use batch_get for specific columns only (Most Efficient)
    def fetch_current_date_data(self, worksheet):
        """Fetch only necessary columns using batch_get with additional RPA remarks filtering"""
        try:
            # Get header row first to find column indices
            headers = worksheet.row_values(1)
            
            # Find the column index for 'Deployment Date' (assuming it's column AO based on your data)
            deployment_date_col = None
            for i, header in enumerate(headers):
                if header == 'Deployment Date':
                    deployment_date_col = i + 1  # gspread uses 1-based indexing
                    break
            
            if deployment_date_col is None:
                print("Deployment Date column not found")
                return []
            
            # Convert column number to letter (e.g., 1=A, 2=B, etc.)
            def num_to_col_letter(n):
                result = ""
                while n > 0:
                    n -= 1
                    result = chr(n % 26 + ord('A')) + result
                    n //= 26
                return result
            
            date_col_letter = num_to_col_letter(deployment_date_col)
            
            # Get all values from the deployment date column
            date_range = f"{date_col_letter}2:{date_col_letter}"  # Skip header row
            date_values = worksheet.batch_get([date_range])[0]
            
            # Find rows with today's date
            matching_rows = []
            for i, date_cell in enumerate(date_values):
                if date_cell and len(date_cell) > 0 and date_cell[0] == datetime.datetime.now().strftime("%Y-%m-%d"):
                    matching_rows.append(i + 2)  # +2 because we skipped header and gspread is 1-based
            
            if not matching_rows:
                return []
            
            # Define ALL RPA columns to check (including Base Flow)
            all_rpa_columns = [
                "Base Flow RPA Remarks",
                "Double Flow RPA Remarks", 
                "Extend Flow RPA Remarks", 
                "Keyword RPA Remarks", 
                "AUXILIARY RPA Remarks"
            ]
            
            def should_append_record(record):
                """
                Check if record should be appended based on RPA remarks status
                Returns True if:
                1. At least one RPA column is blank/null/missing, AND
                2. NOT all RPA columns have existing values
                """
                has_blank = False
                all_filled = True
                
                for column in all_rpa_columns:
                    try:
                        value = record.get(column, "").strip()  # Get value, default to empty string, strip whitespace
                        if not value:  # If empty, None, or whitespace only
                            has_blank = True
                            all_filled = False
                        # If value exists and is not empty, continue checking
                    except KeyError:
                        # If KeyError is raised (column doesn't exist), consider it blank
                        has_blank = True
                        all_filled = False
                    except AttributeError:
                        # If value is None and .strip() fails, consider it blank
                        if record.get(column) is None or record.get(column) == "":
                            has_blank = True
                            all_filled = False
                
                # Only append if there's at least one blank AND not all are filled
                return has_blank and not all_filled
            
            # Fetch complete data only for matching rows and apply additional filtering
            current_date_data = []
            for row_num in matching_rows:
                row_data = worksheet.row_values(row_num)
                # Convert to dictionary
                record = {}
                for j, value in enumerate(row_data):
                    if j < len(headers):
                        record[headers[j]] = value

                record['_row_number'] = row_num
                
                # Apply the RPA remarks checking
                if should_append_record(record):
                    current_date_data.append(record)
                    
                    # Show which columns are blank for debugging
                    blank_columns = []
                    for col in all_rpa_columns:
                        try:
                            value = record.get(col, "").strip()
                            if not value:
                                blank_columns.append(col)
                        except (KeyError, AttributeError):
                            blank_columns.append(col)
                else:
                    print(f"Skipped record with ServiceID: {record.get('ServiceID', 'N/A')} - all RPA remarks are filled")
            
            return current_date_data
        
        except Exception as e:
            print(f"Error in batch_get method: {e}")
            return []

    # OPTION 1B: Fetch data with 'Failed' keyword in RPA remarks
    def fetch_failed_rpa_records(self, worksheet):
        """Fetch records with 'Failed' or 'failed' keyword in any RPA remarks column"""
        try:
            # Get header row first to find column indices
            headers = worksheet.row_values(1)
            
            # Find the column index for 'Deployment Date'
            deployment_date_col = None
            for i, header in enumerate(headers):
                if header == 'Deployment Date':
                    deployment_date_col = i + 1  # gspread uses 1-based indexing
                    break
            
            if deployment_date_col is None:
                print("Deployment Date column not found")
                return []
            
            # Convert column number to letter (e.g., 1=A, 2=B, etc.)
            def num_to_col_letter(n):
                result = ""
                while n > 0:
                    n -= 1
                    result = chr(n % 26 + ord('A')) + result
                    n //= 26
                return result
            
            date_col_letter = num_to_col_letter(deployment_date_col)
            
            # Get all values from the deployment date column
            date_range = f"{date_col_letter}2:{date_col_letter}"  # Skip header row
            date_values = worksheet.batch_get([date_range])[0]
            
            # Find rows with today's date
            matching_rows = []
            for i, date_cell in enumerate(date_values):
                if date_cell and len(date_cell) > 0 and date_cell[0] == datetime.datetime.now().strftime("%Y-%m-%d"):
                    matching_rows.append(i + 2)  # +2 because we skipped header and gspread is 1-based
            
            if not matching_rows:
                return []
            
            # Define RPA columns to check for 'Failed' keyword
            rpa_columns_to_check = [
                "Base Flow RPA Remarks",
                "Double Flow RPA Remarks", 
                "Extend Flow RPA Remarks", 
                "Keyword RPA Remarks", 
                "AUXILIARY RPA Remarks"
            ]
            
            def has_failed_rpa_remarks(record):
                """Check if any RPA remarks column contains 'Failed' or 'failed' keyword"""
                failed_columns = []
                
                for column in rpa_columns_to_check:
                    try:
                        value = str(record.get(column, "")).strip()
                        # Check for 'Failed' or 'failed' (case-insensitive)
                        if 'failed' in value.lower() or 'pending' in value.lower():
                            failed_columns.append(column)
                    except (KeyError, AttributeError):
                        # If column doesn't exist or value is None, skip
                        continue
                
                return failed_columns  # Return list of columns with 'failed'
            
            # Fetch complete data only for matching rows and apply failed checking
            failed_records = []
            for row_num in matching_rows:
                row_data = worksheet.row_values(row_num)
                # Convert to dictionary
                record = {}
                for j, value in enumerate(row_data):
                    if j < len(headers):
                        record[headers[j]] = value
                record['_row_number'] = row_num

                # Check for failed RPA remarks
                failed_columns = has_failed_rpa_remarks(record)
                if failed_columns:
                    failed_records.append(record)
                    print(f"Added FAILED record with ServiceID: {record.get('ServiceID', 'N/A')} - failed columns: {failed_columns}")
                    
                    # Show the actual failed values for debugging
                    for col in failed_columns:
                        failed_value = record.get(col, "")
                        print(f"  {col}: '{failed_value}'")
                else:
                    print(f"Skipped record with ServiceID: {record.get('ServiceID', 'N/A')} - no failed RPA remarks found")
            
            return failed_records
        
        except Exception as e:
            print(f"Error in fetch_failed_rpa_records method: {e}")
            return []

    # OPTION 1C: Fetch data by SERVICE NAME parameter (no date filtering)
    def fetch_by_service_name(self, worksheet, service_name_value):
        """Fetch all records that match the given SERVICE NAME value (no date filtering)"""
        try:
            # Get header row first to find column indices
            headers = worksheet.row_values(1)
            
            # Find the column index for 'SERVICE NAME'
            service_name_col = None
            for i, header in enumerate(headers):
                if header == 'SERVICE NAME':
                    service_name_col = i + 1  # gspread uses 1-based indexing
                    break
            
            if service_name_col is None:
                print("SERVICE NAME column not found")
                return []
            
            # Convert column number to letter (e.g., 1=A, 2=B, etc.)
            def num_to_col_letter(n):
                result = ""
                while n > 0:
                    n -= 1
                    result = chr(n % 26 + ord('A')) + result
                    n //= 26
                return result
            
            service_name_col_letter = num_to_col_letter(service_name_col)
            
            # Get all values from the SERVICE NAME column
            service_name_range = f"{service_name_col_letter}2:{service_name_col_letter}"  # Skip header row
            service_name_values = worksheet.batch_get([service_name_range])[0]
            
            # Find rows with matching service name
            matching_rows = []
            for i, service_cell in enumerate(service_name_values):
                if service_cell and len(service_cell) > 0 and service_cell[0] == service_name_value:
                    matching_rows.append(i + 2)  # +2 because we skipped header and gspread is 1-based
            
            if not matching_rows:
                print(f"\nNo records found with SERVICE NAME: '{service_name_value}' in ParamMatrix")
                return []
            
            # Fetch complete data for matching rows
            service_name_data = []
            for row_num in matching_rows:
                row_data = worksheet.row_values(row_num)
                # Convert to dictionary
                record = {}
                for j, value in enumerate(row_data):
                    if j < len(headers):
                        record[headers[j]] = value
                record['_row_number'] = row_num

                service_name_data.append(record)
            return service_name_data
        
        except Exception as e:
            print(f"Error in fetch_by_service_name method: {e}")
            return []
        
#SMP

    def find_row_index_multi(self, data, conditions):
        """
            data: list of dicts (rows)
            conditions: dict of key-value pairs to match, e.g.
                {'service_id': 'abc123', 'message_type': 'sms', 'brand': 'xyz'}
            Returns: index of the first matching row, or -1 if not found.
        """
        for idx, row in enumerate(data, start=1):
            if all(str(row.get(k)).strip() == str(v).strip() for k, v in conditions.items()):
                return idx + 1
        return -1
    
    def update_cell(
        self,
        worksheet_name: str,
        row_index: int,
        column_name: str,
        value: Any,
        append: bool = False,
        append_line: int | None = None,
        replace_match: str | None = None
    ):
        """
        Update or modify a cell in the worksheet.

        Args:
            worksheet_name: Name of the sheet/tab
            row_index: Row index (1-based)
            column_name: Column name (must match header row)
            value: The text to write
            append: If True, append at the end of the cell.
            append_line: If set, insert at this line number (1-based).
            replace_match: If set, replace the first line containing this text.
                        If not found, inserts at append_line if provided, else appends at the end.
        """
        worksheet = self.spreadsheet.worksheet(worksheet_name)
        headers = worksheet.row_values(1)
        if column_name not in headers:
            raise ValueError(f"Column '{column_name}' not found in worksheet '{worksheet_name}'")

        col_index = headers.index(column_name) + 1

        current_value = worksheet.cell(row_index, col_index).value or ""
        lines = current_value.split("\n") if current_value else []

        if replace_match is not None:
            # Replace first line that contains the match
            replaced = False
            for i, line in enumerate(lines):
                if replace_match in line:
                    lines[i] = str(value)
                    replaced = True
                    break

            if not replaced:
                # If no match found → insert at append_line (if given) else append at end
                if append_line is not None and 1 <= append_line <= len(lines) + 1:
                    lines.insert(append_line - 1, str(value))
                else:
                    lines.append(str(value))

            new_value = "\n".join(lines)

        elif append_line is not None:
            # Insert at specific line position
            if 1 <= append_line <= len(lines) + 1:
                lines.insert(append_line - 1, str(value))
            else:
                lines.append(str(value))
            new_value = "\n".join(lines)

        elif append:
            # Append at the end
            lines.append(str(value))
            new_value = "\n".join(lines)

        else:
            # Overwrite entire cell
            new_value = str(value)

        worksheet.update_cell(row_index, col_index, new_value)



class GDriveClient:
    def __init__(self, service_account_file: str = None, scopes: List[str] = None):
            # To Authorize Service Account Access to spreadsheet via gsheet id
            if scopes is None:
                scopes = ["https://www.googleapis.com/auth/drive"]

            if not service_account_file:
                service_account_file = get_env_variable("GOOGLE_SERVICE_ACCOUNT")

            self.credentials = Credentials.from_service_account_file(
                service_account_file, scopes=scopes
            )
            client = gspread.authorize(self.credentials)
            self.spreadsheet = client.open_by_key(get_env_variable("GSHEET_ID"))
            print("Authorized scope for gsheet:", self.credentials.scopes)