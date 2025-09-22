
from utils.env_loader import get_env_variable
from utils.logger import logger

def login_credential(platform , gs):
    try:
        sheet_tab = get_env_variable("WORKSHEET_TAB_CREDENTIAL")

        # Retrieve credentials from Google Sheet
        creds_data = gs.get_sheet_data(sheet_tab)

        # Find row where App Type == app_name
        creds_row = next(
            (row for row in creds_data if row["Platform"] == platform),
            None
        )

        if creds_row:
            username = creds_row["Username"]
            password = creds_row["Password"]
            return username, password
        else:
            logger.error(f"No credentials found '{platform}'") 
            return None, None

    except Exception as e:
        logger.error(f"Something went wrong in the Login Sequence: {repr(e)}")
        raise