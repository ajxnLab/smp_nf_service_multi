import re
import utils.helpers
from selenium.common.exceptions import TimeoutException
from utils.logger import log_traceback,finalize_log_upload,attach_drive_client,setup_in_memory_logger

from config.env_config import get_env_variable
from utils.google_sheet import GSheetClient
from utils.web_driver import WebDriver
from smp.smp_constant import SMPConstants


# Instantiate constants
smp = SMPConstants()

#Setup logger for the SMP process
logger,log_stream = setup_in_memory_logger("SMP")

class SMPService:
    def __init__(self):

        # Google Sheets client
        gsheet_credential = get_env_variable("GOOGLE_SERVICE_ACCOUNT")
        gsheet_id = get_env_variable("GSHEET")

        # Fix path for PyInstaller
        resolved_credential_path = utils.helpers.get_resource_path(gsheet_credential)

        self.gs = GSheetClient(resolved_credential_path, gsheet_id)

        # Start datetime
        self.start_time = utils.helpers.get_datetime("full")

        # WebDriver
        self.wd = WebDriver()

    def run(self):
        logger.info(">>> Starting SMP process sequence")
        try:
            logger.info(f"Start Time: {self.start_time}")

            url_param = get_env_variable("SMP_WEBTOOL_URL")
            logger.info("Account Authorized!, Logging into SMP Webtool..")
            logger.info(">>> Redirecting to SMP login page")

            self.wd.redirect_nf_login_page(url_param)
            self.wd.wait_until_element("name", get_env_variable("SMP_LOGIN_USERNAME_NAME"), "visible")

            # Call login and service creation
            self.login_sequence()
            self.add_smp_service()

            # End datetime and log duration
            end_time = utils.helpers.get_datetime("full")
            duration = utils.helpers.duration_time(self.start_time, end_time)
            logger.info(f"End Time: {end_time}")
            logger.info(f"Duration: {duration}")

        except Exception as e:
            logger.error(f"Error in SMP process: {repr(e)}")
            log_traceback(logger)
        finally:
            attach_drive_client(logger, self.gs ,smp, log_stream)
            finalize_log_upload(logger)
            self.wd.stop_process()

    # Login Sequence Function.
    def login_sequence(self):
        try:
            sheet_tab = smp.WORKSHEET_TAB_CREDENTIAL

            # Retrieve credentials from Google Sheet
            creds_data = self.gs.get_raw_values(sheet_tab)
        
            # Skip the header (row 0), loop through each row of credentials
            for index, row in enumerate(creds_data[1:], start=2):  # Starting from row 2 (index 1)
                if len(row) < 2:
                    logger.warning(f"Skipping row {index}: not enough columns for username/password.")
                    continue
                username, password = row[0], row[1]

            # Fill in the login form and submit
            self.wd.perform_action("name", get_env_variable("SMP_LOGIN_USERNAME_NAME"), "sendkeys", username)
            self.wd.perform_action("name", get_env_variable("SMP_LOGIN_PASSWORD_NAME"), "sendkeys", password)
            self.wd.perform_action("name", get_env_variable("SMP_LOGIN_BUTTON"), "click")

            try:
                try:
                    self.wd.wait_until_element("xpath", smp.SUBSCRIBER_SERVICES, "visible")
                    logger.info(">>> Login Success!")
                except TimeoutException:
                    logger.warning(">>> Could not find SUBSCRIBER_SERVICES, checking for unauthorized message...")
                    try:
                        self.wd.wait_until_element("xpath", smp.LOGIN_FAILED, "visible")
                        logger.error(">>> Unauthorized User!")
                        raise RuntimeError("Unauthorized User: Login failed.")
                    except TimeoutException:
                        logger.error(">>> Login failed: Unknown reason (neither SUBSCRIBER_SERVICES nor LOGIN_FAILED found).")
                        raise RuntimeError("Login failed: Neither success nor unauthorized message found.")
            except Exception as e:
                logger.exception(f"Exception during login process: {e}")
                raise


            logger.info(">>> Login sequence completed")

        except Exception as e:
            logger.error(f"Something went wrong in the Login Sequence: {repr(e)}")
            log_traceback(logger)
            raise

    #Create New SMP Service
    def add_smp_service(self):
        """
            Automates adding a new SMP service from data in GSheet, and updates GSheet with results.
        """
        try:
            #Get Gsheet data 
            sheet_tab = smp.WORKSHEET_TAB_ADD_SERVICE   
            data = self.gs.get_sheet_data(sheet_tab)
            today_date  = utils.helpers.get_datetime("date")

            # Log the retrieval
            logger.info(f"Retrieved {len(data)} rows from sheet '{sheet_tab}'")

            # Filter rows with today's Deployment Date and empty or 'failed' RPA Remarks
            filtered_data = []
            for row in data:
                deployment_date = row.get("Deployment Date", "").strip()
                remarks = row.get("SMP RPA Remarks", "").strip().lower()

                if deployment_date == today_date:
                    if not remarks or "failed" in remarks:
                        filtered_row = {
                            "SMP Name": row.get("SMP Name", "").strip(),
                            "Allow Multiple": row.get("Allow Multiple", "").strip(),
                            "Subscriber Group Name": row.get("Subscriber Group Name", "").strip(),
                            **smp.SMP_CONSTANT_VALUES
                        }
                        filtered_data.append(filtered_row)

            #logger.info(f"FILTERED DATA : {filtered_data}")
            # Extract only the 'Name' values
            names = [row.get("SMP Name", "Unnamed") for row in filtered_data]
            logger.info(f"Retrieved Names: {names}")     


            # Process filtered rows
            for row in filtered_data:
                try:
                    name_value = row.get("SMP Name", None)
                    # Get service name and ID from form
                    identifier_column = smp.SUBSCRIBER_ADD_SERVICES_NAME

                    # Find row index in GSheet for updating
                    result = self.gs.find_row_index(data, identifier_column, name_value)
                    #logger.info(f"Row Index {result}")
                    row_index = result["row_index"]  
                    
                    # Navigate to 'Add Services' section in the UI
                    self.wd.wait_until_element("xpath", smp.SUBSCRIBER_SERVICES, "visible")
                    self.wd.perform_action("xpath", smp.SUBSCRIBER_SERVICES, "hover")

                    self.wd.wait_until_element("xpath", smp.SUBSCRIBER_ADD_SERVICES, "clickable")
                    self.wd.perform_action("xpath", smp.SUBSCRIBER_ADD_SERVICES, "click")
                    logger.info(f"Proccessing {name_value}") 
                    
                    # Build row_data matching field_mapping keys
                    row_data = {
                        "Name": row.get("SMP Name", ""),
                        "URL": row.get("URL", ""),
                        "Thread Count": row.get("Thread Count", ""),
                        "Allow Multiple": row.get("Allow Multiple", ""),
                        "Frontier URL": row.get("Frontier URL", ""),
                        "Frontier API URL": row.get("Frontier API URL", "")
                        # Add others as needed
                    }
                    #logger.info(f"ROW DATA : {row_data}")

                    # Fill in the service form fields based on mapping
                    def fill_fields(row_data):
                        for col, val in row_data.items():
                            if col in smp.field_mapping:
                                loc, elem, typ = smp.field_mapping[col]
                                self.wd.field_types(loc, elem, typ, val)

                    fill_fields(row_data)  # Initial form fill
                    # Submit the service creation form
                    utils.helpers.safe_click_with_refresh(
                                self.wd,
                                locator_type="name",
                                element_value=smp.SUBSCRIBER_ADD_SERVICES_BTN,
                                logger=logger,
                                wait_target_locator_type="xpath",
                                wait_target_value=smp.SUBSCRIBER_ADD_SERVICES_ID,
                                gs=self.gs,
                                sheet_tab_retry=sheet_tab,
                                row_index_retry=row_index,
                                post_refresh_action=lambda: fill_fields(row) )
                    
                    error_text = self.wd.get_element_text("classname", "ErrMsg")

                    if error_text and "Service name already exists" in error_text:
                        logger.warning(f"Service creation failed: {error_text}")
                        self.gs.update_cell(sheet_tab, row_index, "SMP RPA Remarks", "Service name already exists.")
                        continue
                           
                    logger.info(f"Successfully created SMP Service for {name_value}")

                    #Get ID after creation of SMP sevice
                    logger.info(f"Waiting for service ID to appear")
                    self.wd.wait_until_element("xpath", smp.SUBSCRIBER_ADD_SERVICES_ID, "visible")
                    
                    
                    identifier_value = self.wd.get_input_value("name", smp.SUBSCRIBER_ADD_SERVICES_NAME.lower())
                    
                    target_column = smp.SUBSCRIBER_ADD_SERVICES_ID_IN_GSHEET
                    target_column_value = self.wd.get_input_value("xpath", smp.SUBSCRIBER_ADD_SERVICES_ID)

                    #Update sheet
                    if result:
                          
                        logger.info(f"Proccessing Access Code")
                        # Add Access Code if present
                        try:
                            access_code =smp.ACCESS_CODE
                            locator, element, input_type = smp.field_mapping_access_code["ACCESS CODE"]
                            self.wd.field_types(locator, element, input_type, access_code)
                            utils.helpers.safe_click_with_refresh(
                                self.wd,
                                locator_type="xpath",
                                element_value=smp.SUBSCRIBER_ADD_SERVICES_ACCESS_CODE_BTN,
                                logger=logger,
                                wait_target_locator_type="xpath",
                                wait_target_value=smp.SUBSCRIBER_GROUP,
                                gs=self.gs,
                                sheet_tab_retry=sheet_tab,
                                row_index_retry=row_index,
                                post_refresh_action=lambda: self.wd.field_types(locator, element, input_type, access_code) )
                           
                            logger.info(f"Successfully added Access Code to {identifier_value} service")
                            
                        except Exception as e:
                            logger.error(f"Failed to add Access Code to {identifier_value} service: {e}")
                            raise

                        logger.info("Click succeeded. Proceeding to add_subscriber_group_service...")
                        
                        #Add New Subscriber Group Service
                        self.wd.wait_until_element("xpath", smp.SUBSCRIBER_GROUP, "visible")
                        self.wd.perform_action("xpath", smp.SUBSCRIBER_GROUP, "hover")
                        logger.info("Success waiting Subscriber Group Tab")

                        self.wd.wait_until_element("xpath",smp.SUBSCRIBER_GROUP_ADD_SERVICE, "clickable")
                        self.wd.perform_action("xpath", smp.SUBSCRIBER_GROUP_ADD_SERVICE, "click")
                        logger.info("Success clicking Subscriber Group Tab")

                        self.add_subscriber_group_service(result, identifier_column,sheet_tab)

                        # Update GSheet with ID
                        self.gs.update_cell(sheet_tab,row_index, target_column, target_column_value)
                        logger.info(f"Updated row {row_index} with column {target_column} and id {target_column_value}")
                        
                        #Log success to Deployment Date and RPA Remarks
                        self.gs.update_cell(sheet_tab, row_index, "SMP RPA Remarks", "Successful")
                        
                    else:
                        logger.info(f"Identifier '{identifier_value}' not found in '{identifier_column}' column.")
                        self.gs.update_cell(sheet_tab, row_index, "SMP RPA Remarks", "Failed")

                except Exception as inner_e:
                    #Log failure
                    identifier_value = row.get(smp.SUBSCRIBER_ADD_SERVICES_NAME, "Unknown")
                    result = self.gs.find_row_index(data, smp.SUBSCRIBER_ADD_SERVICES_NAME, identifier_value)
                    row_index = result["row_index"] 

                    if isinstance(row_index, int):
                        self.gs.update_cell(sheet_tab, row_index, "SMP RPA Remarks", "Failed")  # Truncate if too long

                    logger.error(f"Error processing {identifier_value}: {inner_e}")
                    raise

        except Exception as e:
            logger.error(f"Something went wrong creating SMP Service: {repr(e)}")
            log_traceback(logger)
            raise

    def add_subscriber_group_service(self, result, identifier_column, sheet_tab):
        """
            Adds a service to one or more subscriber groups from GSheet data.
        """
        try:

            row_index = result["row_index"]  
            record = result["record"]

            raw_group_value = record.get(smp.SUBSCRIBER_GROUP_NAME, "")
            service_name = record.get(identifier_column, "")

            # Clean and split the raw subscriber group string into individual group names
            groups = [
                item.strip()                                                                # Remove leading/trailing whitespace
                for item in re.split(r'[\n,;;]+', raw_group_value)                          # Split on comma
                if item.strip()                                                             # Exclude empty or whitespace-only entries
            ]
            logger.info(f"SUBSCRIBER GROUP NAME {groups}")

            #Fill the service name
            locator_service_name, element_service_name, input_type_service_name = smp.field_mapping_add_subs_group["Service Name"]
            self.wd.field_types(locator_service_name, element_service_name, input_type_service_name, service_name)
            select_value = self.wd.select_value

            if select_value == 1:

                # Loop through each group and fill in the website
                for group in groups:
                    logger.info(f"group {group}")
                    self.wd.wait_until_element(locator_service_name, element_service_name, "visible")
                    # Fill the Subscriber Group Name
                    locator, element, input_type = smp.field_mapping_add_subs_group["Subscriber Group Name"]
                    self.wd.field_types(locator, element, input_type, group)
                    select_value_group = self.wd.select_value

                    if select_value_group == 1:
                        utils.helpers.safe_click_with_refresh(
                            self.wd,
                            locator_type="name",
                            element_value=smp.SUBSCRIBER_GROUP_ADD_SERVICE_BTN,
                            logger=logger,
                            wait_target_locator_type=locator_service_name,
                            wait_target_value=element_service_name, 
                            gs=self.gs,
                            sheet_tab_retry=sheet_tab,
                            row_index_retry=row_index,
                            post_refresh_action=lambda: self.wd.field_types(locator, element, input_type, group)
                        )
                    else:
                        #Log Failure Deployment Date and RPA Remarks
                        self.gs.update_cell(sheet_tab, row_index, "SMP RPA Remarks", "Subscriber Group Name is not found in dropdown")

                    
            else:
                #Log Failure Deployment Date and RPA Remarks
                self.gs.update_cell(sheet_tab, row_index, "SMP RPA Remarks", "Service Name is not found in dropdown. Skipping subscriber group processing.")

        except Exception as e:
                logger.error(f"Something went wrong adding Subscriber Group Service: {repr(e)}")
                log_traceback(logger)
                raise
