import datetime
from utils.env_loader import load_environment
load_environment()
from utils.google_sheet import GSheetClient
from config.config import nf

# gs = GSheetClient()
# worksheet = gs.spreadsheet.worksheet("BulkService")
# data_dictionary = worksheet.get_all_records()

# data_worksheet = worksheet.findall(datetime.datetime.now().strftime("%Y-%m-%d"))

# print(data_dictionary)

# OPTION 1: Use batch_get for specific columns only (Most Efficient)

# Initialize Google Sheets client
gs = GSheetClient()
worksheet = gs.spreadsheet.worksheet("BulkService")

# Get today's date in YYYY-MM-DD format
today = datetime.datetime.now().strftime("%Y-%m-%d")

# def fetch_with_batch_get(header_name, match_value):
#     """Fetch only necessary columns using batch_get"""
#     try:
#         # Get header row first to find column indices
#         headers = worksheet.row_values(1)
        
#         # Find the column index for 'Deployment Date' (assuming it's column AO based on your data)
#         deployment_date_col = None
#         for i, header in enumerate(headers):
#             if header == header_name:
#                 deployment_date_col = i + 1  # gspread uses 1-based indexing
#                 break
        
#         if deployment_date_col is None:
#             print("Deployment Date column not found")
#             return []
        
#         # Convert column number to letter (e.g., 1=A, 2=B, etc.)
#         def num_to_col_letter(n):
#             result = ""
#             while n > 0:
#                 n -= 1
#                 result = chr(n % 26 + ord('A')) + result
#                 n //= 26
#             return result
        
#         date_col_letter = num_to_col_letter(deployment_date_col)
        
#         # Get all values from the deployment date column
#         date_range = f"{date_col_letter}2:{date_col_letter}"  # Skip header row
#         date_values = worksheet.batch_get([date_range])[0]
        
#         # Find rows with today's date
#         matching_rows = []
#         for i, date_cell in enumerate(date_values):
#             if date_cell and len(date_cell) > 0 and date_cell[0] == match_value:
#                 matching_rows.append(i + 2)  # +2 because we skipped header and gspread is 1-based
        
#         if not matching_rows:
#             return []
        
#         # Fetch complete data only for matching rows
#         current_date_data = []
#         for row_num in matching_rows:
#             row_data = worksheet.row_values(row_num)
#             # Convert to dictionary
#             record = {}
#             for j, value in enumerate(row_data):
#                 if j < len(headers):
#                     record[headers[j]] = value
#             current_date_data.append(record)
        
#         return current_date_data
    
#     except Exception as e:
#         print(f"Error in batch_get method: {e}")
#         return []
    
# def fetch_with_batch_get_param():
#     """Fetch only necessary columns using batch_get"""
#     try:
#         # Get header row first to find column indices
#         headers = worksheet.row_values(1)
        
#         # Find the column index for 'Deployment Date' (assuming it's column AO based on your data)
#         service_name_col = None
#         for i, header in enumerate(headers):
#             if header == 'SERVICE NAME':
#                 service_name_col = i + 1  # gspread uses 1-based indexing
#                 break
        
#         if service_name_col is None:
#             print("Deployment Date column not found")
#             return []
        
#         # Convert column number to letter (e.g., 1=A, 2=B, etc.)
#         def num_to_col_letter(n):
#             result = ""
#             while n > 0:
#                 n -= 1
#                 result = chr(n % 26 + ord('A')) + result
#                 n //= 26
#             return result
        
#         service_name_col_letter = num_to_col_letter(service_name_col)
        
#         # Get all values from the deployment date column
#         service_name_range = f"{service_name_col_letter}2:{service_name_col_letter}"  # Skip header row
#         service_name_values = worksheet.batch_get([service_name_range])[0]
        
#         # Find rows with today's date
#         matching_rows = []
#         for i, name_cell in enumerate(service_name_values):
#             if name_cell and len(name_cell) > 0 and name_cell[0] == "P70000_100M01D08A01F":
#                 matching_rows.append(i + 2)  # +2 because we skipped header and gspread is 1-based
        
#         if not matching_rows:
#             return []
        
#         # Fetch complete data only for matching rows
#         current_date_data = []
#         for row_num in matching_rows:
#             row_data = worksheet.row_values(row_num)
#             # Convert to dictionary
#             record = {}
#             for j, value in enumerate(row_data):
#                 if j < len(headers):
#                     record[headers[j]] = value
#             current_date_data.append(record)
        
#         return current_date_data
    
#     except Exception as e:
#         print(f"Error in batch_get method: {e}")
#         return []

#OPTION 1: Use batch_get for specific columns only (Most Efficient)
def fetch_with_batch_get():
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
            if date_cell and len(date_cell) > 0 and date_cell[0] == today:
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
            #record['_headers'] = headers
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
                
                print(f"Added record with ServiceID: {record.get('ServiceID', 'N/A')} - blank columns: {blank_columns}")
            else:
                print(f"Skipped record with ServiceID: {record.get('ServiceID', 'N/A')} - all RPA remarks are filled")
        
        return current_date_data
    
    except Exception as e:
        print(f"Error in batch_get method: {e}")
        return []

# test_data = fetch_with_batch_get()

values = [[1234]] * 2
worksheet.update('A59:A60', values)

# print(test_data[0]['_row_number'])