from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from nf_services.nf_constants import NfConstants
from utils.logger import logger
from utils.env_loader import get_env_variable
from utils.helpers import get_after_word
from nf_services.other_services.data_service import create_data_service
from nf_services.main_services.expiry_service import create_service_expiry
from nf_services.main_services.access_code_service import create_access_code
from nf_services.main_services.ssg_service import define_bs_simple_service_group
from utils.exceptions import BulkServiceError

# Constants
from config.config import nf

POSTPAID_CONSTRUCT = {'postpaid recurring'}

class BulkServices:
    def __init__(self, worksheets, webdriver, gsheet):
        self.wd = webdriver
        self.gs = gsheet
        self.worksheets = worksheets
        self.list_bs_row_data = []

    def bulk_service_process(self):
        """Orchestrator of bulk service creation process"""
        logger.info("STARTING BULK SERVICE PROCESS")
        
        list_current_data = self._get_list_current_date_data()
        if not list_current_data:
            return []        
        for row_data in list_current_data:
            try:
                row = row_data[nf.KEY_ROW_NUMBER]
                if not self._process_single_data(row_data, row):
                    continue
                    
            except NoSuchElementException as e:
                self._handle_row_error(row, f"Unable to define bulk service - Element not found\nERROR: {e}")
            except Exception as e:
                self._handle_row_error(row, f"Unexpected error while defining bulk service: {e}")

        return self._get_all_successful_data()

    def _get_list_current_date_data(self):
        """Fetch rows pending for today's deployment"""
        return self.gs.fetch_current_date_data(self.worksheets["bulkService"])

    def _process_single_data(self, row_data, row) -> bool:
        """Process a single row of bulk service creation"""        
        # Skip if service ID already exists
        if row_data[nf.NF_INDEX_SERVICE_ID]:
            logger.warning(f"Row {row} has existing service id {row_data[nf.NF_INDEX_SERVICE_ID]}")
            self.list_bs_row_data.append(row_data)
            return False

        # Create bulk service
        service_id = self.create_bulk_service(row_data)
        if not service_id:
            logger.warning("No service id returned")
            self._update_rpa_remark(row, "Failed")
            return False

        return self._handle_successful_creation(row, service_id, row_data)

    def _handle_successful_creation(self, row: int, service_id: str, row_data: list) -> bool:
        """Handle steps after successful bulk service creation"""
        # Update service ID
        self.gs.update_row(row, 1, self.worksheets["bulkService"], service_id)
        row_data[nf.NF_INDEX_SERVICE_ID] = service_id
        self.list_bs_row_data.append(row_data)
        
        # Create access code
        self._update_rpa_remark(row, "Bulk Service: Success | Access Code: Pending | Expiry: Pending")
        create_access_code(service_id, self.wd)
        self._update_rpa_remark(row, "Bulk Service: Success | Access Code: Success | Expiry: Pending")
        
        # Handle expiry service
        expiry_success = create_service_expiry(
            row_data, 
            service_id, 
            self.worksheets["paramMatrix"], 
            self.wd, 
            self.gs
        )
        
        expiry_remark = ("Successful" if expiry_success 
                        else "Bulk Service: Success | Access Code: Success | Expiry: Failed")
        self._update_rpa_remark(row, expiry_remark)
        
        return True

    def _update_rpa_remark(self, row: int, remark: str):
        """Update RPA remark for a row"""
        self.gs.update_row(
            row,
            nf.COLUMN_BULK_SERVICE_RPA_REMARKS,
            self.worksheets["bulkService"],
            remark
        )

    def _handle_row_error(self, row: int, error_msg: str):
        """Handle errors during row processing"""
        logger.exception(error_msg)
        self._update_rpa_remark(row, "Failed")
        logger.warning("Continue to next process..")

    def _get_all_successful_data(self) -> list:
        """Get list of rows with successful creation"""
        if not self.list_bs_row_data:
            logger.warning("No successful bulk services created, terminating bot.")
            self.wd.stop_process()
            raise BulkServiceError

        successful_rows = [
           data[nf.NF_INDEX_SERVICE_ID] for data in self.list_bs_row_data
        ]
        logger.info(f"Successful Bulk Service Ids: {successful_rows}")
        return self.list_bs_row_data
    
    # Function to create bulk service
    def create_bulk_service(self, row_data):
        # Redirect to Add Page of Bulk Service
        url = get_env_variable("WEBTOOL_BULK_SERVICES_ADD_FULL_URL")
        self.wd.redirect_to_page(url, nf.NF_ADD_BTN_INPUT)

        logger.info(f"Creating bulk service for {row_data[nf.NF_INDEX_NAME]}")
        try:
            logger.info(f"Input Name: {row_data[nf.NF_INDEX_NAME]}")
            self.wd.perform_action(
                "xpath", nf.NF_INPUT_NAME, "sendkeys", row_data[nf.NF_INDEX_NAME]
            )

            self.handle_service_class(row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT])

            # logger.info(f"RadioBtn Service Class: Bulk Service")
            # self.wd.perform_action(
            #     "xpath", nf.BS_SERVICE_CLASS_BULK_SERVICE, "click"
            # )
            # This verify the input value for wallet if existing, if not, will create new data service
            logger.info(f"Check Group Status Inquiry?: {row_data[nf.NF_INDEX_GROUP_STATUS_INQUIRY]}")
            self.handle_group_status_inquiry(
                row_data[nf.NF_INDEX_GROUP_STATUS_INQUIRY],
                row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT],
                row_data[nf.NF_INDEX_WALLET_TYPE],
            )
            service_id_exist = self.handle_wallet_process(row_data[nf.NF_INDEX_WALLET], row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT], row_data[nf.NF_INDEX_GROUP_STATUS_INQUIRY], row_data)
            if service_id_exist:
                return service_id_exist
            logger.info(f"Dropdwn Status: ACTIVE")
            self.handle_nf_bs_status("active")

            logger.info(f"Input Thread Count: {row_data[nf.NF_INDEX_THREAD_COUNT]}")
            self.wd.perform_action(
                "name",
                nf.NF_BS_THREAD_COUNT_INPUT_NAME,
                "sendkeys",
                row_data[nf.NF_INDEX_THREAD_COUNT],
            )
            logger.info("Dropdwn Bulk Service Type: Wallet-Based")
            self.handle_nf_bs_type("Wallet-Based")

            logger.info(f"Checkbox Brands: {row_data[nf.NF_INDEX_BRAND]}")
            self.handle_nf_bs_brands(row_data[nf.NF_INDEX_BRAND])

            logger.info("Input Timeout(sec): 60")
            self.wd.perform_action("name", nf.NF_BS_TIMEOUT_SEC, "sendkeys", 60)

            logger.info("Input Status Charged Amount: 0")
            self.wd.perform_action(
                "name", nf.NF_BS_STATUS_CHARGED_AMOUNT, "sendkeys", 0
            )
            logger.info("Input Balance Charged Amount: 0")
            self.wd.perform_action(
                "name", nf.NF_BS_BALANCE_CHARGED_AMOUNT, "sendkeys", 0
            )

            logger.info(f"Input SMP Name: {row_data[nf.NF_INDEX_SMP_NAME]}")
            self.wd.perform_action(
                "name", nf.NF_BS_SMP_NAME, "sendkeys", row_data[nf.NF_INDEX_SMP_NAME]
            )

            logger.info("Input Access Code: 8080")
            self.wd.perform_action(
                "name", nf.NF_BS_DEFAULT_ACCESS_CODE, "sendkeys", 8080
            )

            logger.info("Input Queue Limit: 1000")
            self.wd.perform_action("name", nf.NF_BS_QUEUE_LIMIT, "sendkeys", 1000)

            logger.info(
                f"RadioBtn Deprov on empty: {row_data[nf.NF_INDEX_DEPROV_ON_EMPTY]}"
            )
            self.handle_bs_deprov_on_empty(row_data[nf.NF_INDEX_DEPROV_ON_EMPTY])

            logger.info("RadioBtn Pre-Expiry Notif: No")
            self.handle_bs_preexpiry_notifs("no")

            logger.info(
                f"RadioBtn Subscription Less: {row_data[nf.NF_INDEX_SUBSCRIPTION_LESS]}"
            )
            self.handle_bs_subscription_less(row_data[nf.NF_INDEX_SUBSCRIPTION_LESS])

            logger.info(f"RadioBtn Max Recurrence: No Recurrence")
            self.wd.perform_action("id", nf.NF_BS_MAX_RECURRENCE, "click")

            logger.info(
                f"Input Max Daily Extensions: {row_data[nf.NF_INDEX_MAX_DAILY_EXT]}"
            )
            self.wd.perform_action("name", nf.NF_BS_MAX_DAILY_EXTENSION, "clear")
            self.wd.perform_action(
                "name",
                nf.NF_BS_MAX_DAILY_EXTENSION,
                "sendkeys",
                row_data[nf.NF_INDEX_MAX_DAILY_EXT],
            )

            logger.info(
                f"Input Max Total Extensions: {row_data[nf.NF_INDEX_MAX_TOTAL_EXT]}"
            )
            self.wd.perform_action("name", nf.NF_BS_MAX_TOTAL_EXTENSION, "clear")
            self.wd.perform_action(
                "name",
                nf.NF_BS_MAX_TOTAL_EXTENSION,
                "sendkeys",
                row_data[nf.NF_INDEX_MAX_TOTAL_EXT],
            )

            logger.info(f"Input Promo Name: {row_data[nf.NF_INDEX_PROMO_NAME]}")
            self.wd.perform_action(
                "name",
                nf.NF_BS_PROMO_NAME,
                "sendkeys",
                row_data[nf.NF_INDEX_PROMO_NAME],
            )  

            # For postpaid recurring/rollback only
            self._fill_param_matrix_postpaid(row_data, row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT])

            logger.info("All input fields are done!")

            # Section to get success message after clicking submit button
            success_msg = self.wd.submit_form_and_wait_for_success(
                "xpath", nf.NF_ADD_BTN_INPUT, nf.SUCCESS_MESSAGE
            )

            # Section to get the service id in Success Message
            word_service_id = get_after_word(success_msg, "Service with id:")
            service_id = word_service_id.replace(".", "")
            logger.info(f"Bulk Service Id Retrieved: {service_id}")

            return service_id

        except Exception as e:
            logger.error(f"Failed to create bulk service for: {row_data[nf.NF_INDEX_NAME]}")
            raise
    
    def handle_service_class(self, construct_value):
        is_postpaid = construct_value.lower() in POSTPAID_CONSTRUCT

        service_class_name = "Simple Service, Data" if is_postpaid else "Bulk Service"
        element = nf.BS_SERVICE_CLASS_SIMPLE_SERVICE_DATA if is_postpaid else nf.BS_SERVICE_CLASS_BULK_SERVICE

        logger.info(f"Radiobtn Service Class: {service_class_name}")
        self.wd.perform_action("xpath", element, "click")

    def handle_group_status_inquiry(self, group_status_value, construct_value, wallet_type_value):
        if 'prepaid ctl with unli sms and unli voice' in construct_value.lower() or 'prepaid opm with unli sms and unli voice' in construct_value.lower() or group_status_value.lower() == "no":
            return
        else:
            self.wd.perform_action("id", nf.NF_BS_GROUP_STATUS_INQUIRY, "click")
            self.handle_wallet_type(wallet_type_value)

    def handle_wallet_process(self, wallet_value, construct_value, group_status_value, row_data):
        if 'prepaid ctl with unli sms and unli voice' in construct_value.lower() or 'prepaid opm with unli sms and unli voice' in construct_value.lower():
            return
        if group_status_value.lower() == "yes" or "data" in construct_value.lower() or "postpaid rollover" in construct_value.lower() or construct_value.lower() in POSTPAID_CONSTRUCT:
            logger.info("Verifying Wallet...")
            # Check if wallet exist or not, returns boolean True or False
            wallet_is_exist = self.check_wallet(wallet_value)

            # If wallet exist in dropdown select, click
            if wallet_is_exist:
                logger.info(f"Wallet exist, select: {wallet_value}")
                self.wd.perform_action(
                    "xpath", f"//select[@name='ss_wallet_data']//option[contains(text(), '{wallet_value}')]", "click"
                )
                return False
            # If wallet does not exist, define new wallet in Data Service
            else:
                logger.info(f"Wallet does not exist, creating wallet in data service...")
                create_data_service(self.wd, wallet_value)
                service_id = self.create_bulk_service(row_data)
                return service_id

    # Handle Radio Button Wallet Type.
    def handle_wallet_type(self, wallet_type_value):
        logger.info(f"RadioBtn Wallet Type: {wallet_type_value}")
        element_map = {
            "sms/voice": nf.BS_WALLET_TYPE_SMSVOICE,
            "data": nf.BS_WALLET_TYPE_DATA,
            "sps": nf.BS_WALLET_TYPE_SPS,
        }
        element = element_map.get(wallet_type_value.lower(), nf.BS_WALLET_TYPE_CPS)
        self.wd.perform_action("xpath", element, "click")

    # Function to check if wallet value exist return boolean True, if not, return False
    def check_wallet(self, wallet_value):
        try:
            logger.info(f"Dropdwn Name: {wallet_value}")
            self.wd.driver.find_element(
                By.XPATH, f"//option[contains(text(),'{wallet_value.strip()}')]"
            ).click()
            return True
        except NoSuchElementException:
            return False

    # def select_wallet(self, wallet_array):
    #     exists, value = wallet_array
    #     if exists:
    #         self.wd.perform_action(
    #             "xpath", f"//option[contains(text(),'{value}')]", "click"
    #         )

    # Handle Bulk Service Status Dropdown
    def handle_nf_bs_status(self, nf_status_value):
        element_map = {
            "inactive": nf.BS_STATUS_INACTIVE,
            "no prov": nf.BS_STATUS_NOPROV,
        }

        element = element_map.get(nf_status_value, nf.BS_STATUS_ACTIVE)
        self.wd.perform_action("xpath", element, "click")

    # Handle Bulk Service Type Dropdown
    def handle_nf_bs_type(self, nf_type_value):
        element = None

        if nf_type_value == "Time-Based":
            element = nf.NF_BS_TYPE_TIME_BASED
        else:
            element = nf.NF_BS_TYPE_WALLET_BASED

        self.wd.perform_action("xpath", element, "click")

    # Handle Bulk Service Brands Multiple Checkbox
    def handle_nf_bs_brands(self, brands_value):
        brands = brands_value.split(', ')

        element_map = {
            "ghp": nf.NF_BS_BRAND_GHP,
            "gp": nf.NF_BS_BRAND_GHP,
            "tm": nf.NF_BS_BRAND_TM,
            "postpaid": nf.NF_BS_BRAND_POSTPAID,
            "pw": nf.NF_BS_BRAND_PW,
        }  
        for brand in brands:
            self.wd.perform_action("id", element_map[brand.lower()], "click")

    # Handle Bulk Service Deprov on empty Radio Button
    def handle_bs_deprov_on_empty(self, deprov_value):
        element = None
        if deprov_value.lower() == "yes":
            element = nf.NF_BS_DEPROV_ON_EMPTY_YES
        else:
            element = nf.NF_BS_DEPROV_ON_EMPTY_NO

        self.wd.perform_action("xpath", element, "click")

    # Handle Bulk Service Pre expiry notif Radio Button
    def handle_bs_preexpiry_notifs(self, preexpiry_value):
        element = None
        if preexpiry_value.lower() == "yes":
            element = nf.NF_BS_CANCEL_PRE_EXPIRY_YES
        else:
            element = nf.NF_BS_CANCEL_PRE_EXPIRY_NO

        self.wd.perform_action("xpath", element, "click")

    # Handle Bulk Service Subscriptonless Radio Button
    def handle_bs_subscription_less(self, subscription_value):
        element = None
        if subscription_value.lower() == "yes":
            element = nf.NF_BS_SUBSCRIPTION_LESS
        else:
            element = nf.NF_BS_NOTSUBSCRIPTION_LESS

        self.wd.perform_action("id", element, "click")

    # Handle Bulk Service Community Pool Radio Button
    def handle_bs_community_pool(self, community_pool_value):
        element = None
        if community_pool_value.lower() == "yes":
            element = nf.NF_BS_COMM_POOL_YES
        else:
            element = nf.NF_BS_COMM_POOL_NO

        self.wd.perform_action("xpath", element, "click")

    def handle_sdm_postpaid_flow(self, construct_value):
        if construct_value in POSTPAID_CONSTRUCT:
            element_map = {
                "Default": nf.BS_SDM_TO_FLOW_DEFAULT,
                "API": nf.BS_SDM_TO_FLOW_API,
                "Web": nf.BS_SDM_TO_FLOW_WEB
            }
            for key, element_id in element_map.items():
                logger.info(f"Checkbox SDM Postpaid - {key}: Checked")
                self.wd.perform_action("id", element_id, "click")

    def _fill_param_matrix_postpaid(self, row_data, construct_value, config=None):
        if construct_value.lower() not in POSTPAID_CONSTRUCT:
            return
        logger.info(f"Filling up param fields..")
        # Input Default Wallet Keyword Field
        logger.info("Input Default Retry: 3")
        
        self.wd.perform_action("name", "ss_prov_retry", "sendkeys", 3)
        logger.info("Input Default Param: DEFAULT")
        logger.info(
            f"Input Default Wallet Keyword: {row_data[nf.NF_INDEX_WALLET]}"
        )
        self.wd.perform_action("name", "ss_params[data][0][wallet_keyword]", "sendkeys", row_data[nf.NF_INDEX_WALLET])

        # Input Default Data Alloc Field
        default_wallet_amount_string = row_data[nf.NF_INDEX_DEFAULT_WALLET_AMOUNT]

        if "kb" in default_wallet_amount_string.lower():
            default_wallet_amount = default_wallet_amount_string.replace("KB", "")
            data_alloc = default_wallet_amount_string
            data_alloc
        else:
            default_wallet_amount = int(default_wallet_amount_string)
            data_alloc = f"{default_wallet_amount // 1024}GB" if default_wallet_amount > 1000 else f"{default_wallet_amount}MB"
        logger.info(f"Input Default Data Alloc: {data_alloc}")
        self.wd.perform_action("name", "ss_params[data][0][data_allocation]", "sendkeys", data_alloc)

         # Input Default Wallet Amount Field
        logger.info(f"Input Default Wallet Amount: {default_wallet_amount}")
        self.wd.perform_action("name", "ss_params[data][0][wallet_amount]", "sendkeys", default_wallet_amount)

        # Input Default SDM Prov Keyword Field
        logger.info(f"Input Default SDM Prov Keyword: {row_data[nf.NF_INDEX_DEFAULT_WALLET_KEYWORD]}")
        self.wd.perform_action("name", "ss_params[data][0][sdm_prov_keyword]", "sendkeys", row_data[nf.NF_INDEX_DEFAULT_WALLET_KEYWORD])

        # Declare ParamMatrix Worksheet
        # param_worksheet = self.gs.create_worksheet(
        #     nf.WORKSHEET_TAB_BULK_SERVICES_TAB_PARAM_MATRIX
        # )

        # Section to Input Param Matrix Values
        param_worksheet = self.worksheets['paramMatrix']
        list_param_data = self.gs.fetch_by_service_name(
            param_worksheet, row_data[nf.NF_INDEX_NAME]
        )
        if len(list_param_data) != 0:
            logger.info(
                f"Found ParamMatrix inputs for {construct_value} data, filling up Param fields..."
            )
            try:
                for index, row_param_data in enumerate(list_param_data, 2):
                    # Get ParamMatrix data values via row
                    row = row_param_data[nf.KEY_ROW_NUMBER]
                
                    # Click 'Add More Param to Wallet Keyword &Data Allocation Map' to add new field entry
                    self.wd.perform_action(
                        "xpath",
                        "//button[@onclick='return add_simpleservice_param_prov_data()']",
                        "click",
                    )
                    
                    # Input Param Field
                    logger.info(f"Input Param: {row_param_data[nf.PARAMMATRIX_INDEX_PARAM]}")
                    self.wd.perform_action("name", f"ss_params[data][{index}][param]", "sendkeys", row_param_data[nf.PARAMMATRIX_INDEX_PARAM])

                    # Input Jnetx Wallet Keyword Field
                    logger.info(f"Input Jnetx Wallet Keyword: {row_data[nf.NF_INDEX_WALLET]}")
                    self.wd.perform_action("name", f"ss_params[data][{index}][wallet_keyword]", "sendkeys", row_data[nf.NF_INDEX_WALLET])

                    # Input Data Alloc Field
                    param_wallet_amount = int(row_param_data[nf.PARAMMATRIX_INDEX_WALLET_AMOUNT])
                    data_alloc = f"{param_wallet_amount // 1024}GB" if param_wallet_amount > 1000 else f"{param_wallet_amount}MB"
                    logger.info(f"Input Data Alloc: {data_alloc}")
                    self.wd.perform_action("name", f"ss_params[data][{index}][data_allocation]", "sendkeys", data_alloc)

                    # Input Wallet Amount Field
                    logger.info(f"Input Wallet Amount: {row_param_data[nf.PARAMMATRIX_INDEX_WALLET_AMOUNT]}")
                    self.wd.perform_action("name", f"ss_params[data][{index}][wallet_amount]", "sendkeys", row_param_data[nf.PARAMMATRIX_INDEX_WALLET_AMOUNT])

                    # Input Default SDM Prov Keyword Field
                    logger.info(f"Input SDM Prov Keyword: {row_param_data[nf.PARAMMATRIX_INDEX_WALLET_KEYWORD]}")
                    self.wd.perform_action("name", f"ss_params[data][{index}][sdm_prov_keyword]", "sendkeys", row_data[nf.NF_INDEX_DEFAULT_WALLET_KEYWORD])

                    # Save changes in worksheet parammatrix
                    self.gs.update_row(row, nf.COLUMN_PARAM_MATRIX_RPA_REMARKS, param_worksheet, "PARAM Successfully Define")

            except Exception as e:
                logger.info(
                    f"An error has occurred while using paramMatrix values, will continue to next step.."
                )
                self.gs.update_row(row, nf.COLUMN_PARAM_MATRIX_RPA_REMARKS, param_worksheet, "Failed")
                   
        # Checkbox Extend flow Field
        logger.info(f"Checkbox Extend Flow: Uncheck")
        self.wd.perform_action("id", "cbx_has_extendflow", "click")
        

    def nf_assign_bulk_service_flow(self, flow_key, bs_service_id, flow_id, construct_value_lower=None):
        try:
            # Assign flow and api flow depends if there's a double/extend/none flow
            logger.info(
                f"Assigning {flow_key.upper()} Flow and {flow_key.upper()} API Flow in Bulk Services For: {bs_service_id}"
            )
            flow_name = (
                "double_flow"
                if flow_key == "double"
                else (
                    "extend_flow" if flow_key == "extend" else "default_flow"
                )
            )
            api_flow_name = (
                "api_double_flow" if flow_key == "double" else "api_flow"
            )

            # Redirect to Bulk Service Edit page for current service id
            # self.wd.driver.get(
            #     f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=bulk_services&op=edit&id={bs_service_id}"
            # )
            url = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=bulk_services&op=edit&id={bs_service_id}"
            self.wd.redirect_to_page(url, nf.NF_ADD_BTN_INPUT)
            #self.wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")

            # Input Default Flow Dropwdown
            self.wd.perform_action(
                "xpath",
                f"//select[@name='{flow_name}']//option[@value='{flow_id}']",
                "click",
            )
            if flow_key != "extend":
                # Input API Flow Dropdown
                self.wd.perform_action(
                    "xpath",
                    f"//select[@name='{api_flow_name}']//option[@value='{flow_id}']",
                    "click",
                )

            # Handle after editing form. Stop loading the page if its taking time to load and doesn't need to get the element success message...
            # Click Update button
            # self.wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
            if construct_value_lower and "pre-reg" in construct_value_lower:
                logger.info("Selecting Webtool Flow for Pre-Reg construct..")
                self.wd.perform_action("xpath", f"//select[@name='webtool_flow']//option[@value='{flow_id}']", "click")

            self.wd.submit_form_and_wait_for_success(
                "xpath", nf.NF_ADD_BTN_INPUT, nf.SUCCESS_MESSAGE
            )

        except Exception as e:
            logger.info(
                f"An error has occurred while assigning flow in Edit page of bulk service id: {bs_service_id}\nERROR: {e}"
            )
            raise
