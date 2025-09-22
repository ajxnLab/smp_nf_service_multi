from utils.env_loader import get_env_variable
from utils.logger import logger
from utils import helpers as helper
from nf_services.plan_services.prepaid_services.prepaid_roam_service import PrepaidRoamService
from nf_services.plan_services.postpaid_services.postpaid_roam_service import PostpaidRoamService
from nf_services.plan_services.prepaid_services.prepaid_ctl_opm_service import PrepaidCTLOPMService
from nf_services.flow_services.ctl_opm_flow_service import CTLOPMFlowService
from nf_services.flow_services.roaming_flow_service import RoamingFlowService
from nf_services.main_services import keyword_service as key
from nf_services.main_services import extension_expiry_service as ees
from nf_services.main_services import ssg_service as ssg
from nf_services.nf_constants import FlowType
from nf_services.main_services import message_service as ms
from nf_services.plan_services.postpaid_services.postpaid_rollover_service import create_dummy_step_type, define_flow_dummy
from nf_services.other_services.soc_to_nf_service import define_soc_to_nf
from nf_services.settings_service.wallet_empty_criteria_service import define_wallet_empty_criteria
from nf_services.main_services.gyro_service import create_gyro_command
from nf_services.main_services.modification_services.check_has_subscription_service import add_service_id_to_check_has
from nf_services.config.process_config import PROCESS_MAP
from config.config import nf
from utils.login import login_credential
from multiprocessing import Process, Event
import traceback



class ServiceController:
    def __init__(self, worksheets, webdriver, gsheet):
        self.wd = webdriver
        self.gs = gsheet
        self.worksheets = worksheets
        self.rpa_remark_aux_fail = {}
        self.ctlopm_flow = CTLOPMFlowService(worksheets, webdriver, gsheet)
        self.roaming_flow = RoamingFlowService(worksheets, webdriver, gsheet)
        self.prepaid_ctlopm = PrepaidCTLOPMService(webdriver, gsheet, worksheets)
        self.prepaid_roam = PrepaidRoamService(webdriver, gsheet, worksheets)
        self.postpaid_roam = PostpaidRoamService(webdriver, gsheet, worksheets)

    # Function to start service process PER successful created bulk service rows
    def start_service_controller(self, bs_success_data):
        if not bs_success_data:
            logger.warning("No deployment today to work on, terminating bot...")
            return
        
        for row_data in bs_success_data:
            try:
                row = row_data[nf.KEY_ROW_NUMBER]
                self._process_single_bs_data(row_data, row)
            except Exception as e:
                logger.exception(f"Error processing row {row}: {e}")
                logger.info(traceback.format_exc())
                continue
    
    # Function to handle whole step and flow process for given bulk service row
    def _process_single_bs_data(self, bs_row_data, row):
        construct_value = bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT]
        soc_id = bs_row_data[nf.BS_INDEX_SOCID]
        bs_service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]
        
        logger.info(f"START PROCESSING: {construct_value} - FOR SERVICE ID: {bs_service_id}")
        
        # Set of dictionary to determine what process to execute based on Step and Flow Construct 
        PROCESS_EXECUTE = {
            "process_ctl_opm": lambda: self._process_ctl_opm(bs_row_data, row),
            "process_recurring_rollover": lambda: self._process_postpaid_recurring_rollover(bs_row_data, bs_service_id, soc_id, construct_value, row),
            "process_roaming": lambda: self._process_roaming(bs_row_data, construct_value, row),
            "dummy_service": lambda: self._process_dummy(bs_row_data, row),

        }
        process_map_value = tuple(value for key, value in PROCESS_MAP.items() if any(tuple_value in construct_value.lower() for tuple_value in key))[0]

        # Execute the selected process
        if process_map_value and process_map_value in PROCESS_EXECUTE:
            PROCESS_EXECUTE[process_map_value]()
        else:
            raise(f"No matching process found: {construct_value}")
        
    # Function to process contstruct for "Prepaid CTL/OPM"
    def _process_ctl_opm(self, bs_row_data, row):
        bs_service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]
        username, password = login_credential("NF_2", self.gs)
        if username and password:
            credential = {"username": username, "password": password}
            logger.info(f"NF_2 Credential Exist. Will trigger secondary process")
            self._handle_ctl_opm_multi_process(bs_row_data, credential, row)
            return
        self._handle_step_and_flows(row, bs_row_data)
        self._handle_wallet_empty(bs_service_id, bs_row_data)
        self._handle_gyro_command(bs_row_data, bs_service_id)
        self._handle_ssg(row, bs_row_data, bs_service_id)
        self._update_messages_tab(row, bs_row_data, bs_service_id)
        self._handle_aux_flow(row, bs_row_data)

    # Function to process contstruct for "Postpaid Recurring/Rollover"
    def _process_postpaid_recurring_rollover(self, bs_row_data, service_id, soc_id, construct_value, row):
        bs_service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]
        # For Postpaid Recurring Flow
        if "recurring" in construct_value.lower():
            self._handle_soc_to_nf(service_id, soc_id)
            for column in range(nf.COLUMN_BULK_SERVICE_RPA_REMARKS_BASE_FLOW, nf.COLUMN_BULK_SERVICE_RPA_REMARKS_KEYWORD+1):
                self.gs.update_row(row, column, self.worksheets['bulkService'], "Not Applicable")
            self._handle_ssg(row, bs_row_data, service_id)    
            self._handle_wallet_empty(bs_service_id, bs_row_data)
            self._update_messages_tab(row, bs_row_data, service_id)
            self._handle_aux_flow(row, bs_row_data)

        # For Postpaid Rollover Flow
        else:
            self._handle_step_and_flow_rollover(bs_row_data, service_id, row)
            self._handle_soc_to_nf(service_id, soc_id)
            self._handle_ssg(row, bs_row_data, service_id)
            for column in range(nf.COLUMN_BULK_SERVICE_RPA_REMARKS_DOUBLE_FLOW, nf.COLUMN_BULK_SERVICE_RPA_REMARKS_KEYWORD+1):
                self.gs.update_row(row, column, self.worksheets['bulkService'], "Not Applicable")
            self._handle_wallet_empty(bs_service_id, bs_row_data)
            self._update_messages_tab(row, bs_row_data, service_id)
            self._handle_aux_flow(row, bs_row_data)

    # Function to process contstruct for "Prepaid/Postpaid Trigger or Main service"
    def _process_roaming(self, bs_row_data, construct_value, row):
        bs_service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]
        self._handle_roaming_step_and_flows(bs_row_data, bs_service_id, construct_value, row)
        if "trigger" in construct_value.lower():
            return
        self._handle_keywords(row, bs_service_id, bs_row_data)
        self._handle_wallet_empty(bs_service_id, bs_row_data)
        self._update_messages_tab(row, bs_row_data, bs_service_id)
        self._handle_aux_flow(row, bs_row_data)

    # Function to process contstruct for "Dummy Service"
    def _process_dummy(self, bs_row_data, row):
        service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]
        self._handle_step_and_flow_dummy(bs_row_data, service_id, row)
        for column in range(nf.COLUMN_BULK_SERVICE_RPA_REMARKS_DOUBLE_FLOW, nf.COLUMN_BULK_SERVICE_RPA_REMARKS_KEYWORD+1):
            self.gs.update_row(row, column, self.worksheets['bulkService'], "Not Applicable")
        self._update_messages_tab(row, bs_row_data, service_id)
        self._handle_aux_flow(row, bs_row_data)
        

    # Function to handle prepaid and postpaid roaming HLR process 
    def _handle_roaming_step_and_flows(self, bs_row_data, bs_service_id, construct_value, row):
        if "prepaid" in construct_value.lower():
            self.prepaid_roam.process_step_prepaid_roam(bs_row_data, bs_service_id, row)
        else:
            self.postpaid_roam.process_step_postpaid_roam(bs_row_data, bs_service_id, row)

        # Call flow service function for Roaming service
        self.roaming_flow.start_roaming_service_flow(bs_row_data)

        # Update non-process RPA remarks
        add_loop = 2 if "trigger" in construct_value.lower() else 1
        for column in range(nf.COLUMN_BULK_SERVICE_RPA_REMARKS_DOUBLE_FLOW, nf.COLUMN_BULK_SERVICE_RPA_REMARKS_KEYWORD+add_loop):
            self.gs.update_row(row, column, self.worksheets['bulkService'], "Not Applicable")

    # Function to handle creation of step types and mapping flow path specifically for construct "Prepaid CTL/OPM"
    def _handle_step_and_flows(self, row, bs_row_data):
        bs_service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]
        with_double = bs_row_data[nf.NF_INDEX_WITH_DOUBLE_FLOW].lower()
        with_extend = bs_row_data[nf.NF_INDEX_WITH_EXTEND_STEPS_AND_FLOW].lower()

        flow_conditions = {
            "base": True,
            "double": with_double == "yes",
            "extend": with_extend == "yes",
        }

        for flow_key, enabled in flow_conditions.items():            
            # Section if the flow key is False, update RPA Remark to 'Not Applicable' for Double or Extend flow
            if not enabled:
                logger.warning(f"{flow_key.upper()} flow not applicable to process, Skipping...")
                column = nf.COLUMN_BULK_SERVICE_RPA_REMARKS_DOUBLE_FLOW if flow_key == "double" else nf.COLUMN_BULK_SERVICE_RPA_REMARKS_EXTEND_FLOW
                self.gs.update_row(row, column, self.worksheets["bulkService"], "Not Applicable")
                continue

            logger.info(f"CURRENT FLOW: {flow_key.upper()}")
            # Check RPA Flow Remarks - BASE, DOUBLE and EXTEND
            # Under 'try' block code, if the current flow key (BASE, DOUBLE, or EXTEND) of RPA remark found 'Successful', will skip the step and flow process and proceed to next process or next entry
            try:
                index_map = {
                    "double": nf.BS_INDEX_RPA_REMARKS_DOUBLE_FLOW,
                    "extend": nf.BS_INDEX_RPA_REMARKS_EXTEND_FLOW,
                    "base": nf.BS_INDEX_RPA_REMARKS_BASE_FLOW
                }
                rpa_remark_value = bs_row_data[index_map.get(flow_key, nf.BS_INDEX_RPA_REMARKS_BASE_FLOW)]
                print(f"Check RPA REMARK: {rpa_remark_value}")
                if "success" in rpa_remark_value.lower():
                    logger.warning(f"Current Flow {flow_key.upper()} is already successful, continue to next process..")
                    continue
            except KeyError:
                pass
                
            # Determine on what to create step type based on step and flow construct
            self.determine_step_type(bs_row_data, row, flow_key)
            self.ctlopm_flow.start_ctl_opm_flow(flow_key, bs_row_data)

            if flow_key == FlowType.EXTEND.value:
                ees.create_extension_expiry(bs_service_id, bs_row_data, self.wd)

        self._handle_keywords(row, bs_service_id, bs_row_data, flow_key)

    # Function to define Wallet Empty Criteria
    def _handle_wallet_empty(self, bs_service_id, bs_row_data):
        if bs_row_data[nf.NF_INDEX_DEPROV_ON_EMPTY].lower() == "no":
            return
        bs_wallet = bs_row_data[nf.NF_INDEX_WALLET]
        is_success = define_wallet_empty_criteria(self.wd, bs_service_id, bs_wallet)
        if not is_success:
            self.rpa_remark_aux_fail['WALLET EMPTY CRITERIA'] = "Failed"

    # Function to handle creation of keyword service
    def _handle_keywords(self, row, bs_service_id, bs_row_data, flow_key="base"):
        try:
            if "success" in bs_row_data[nf.BS_INDEX_RPA_REMARKS_KEYWORD].lower():
                logger.warning(f"Keyword service already define, continue to next process..")
                return
        except KeyError:
            pass

        keyword_fail_remark = key.create_keyword(
            bs_service_id,
            bs_row_data,
            self.wd,
            flow_key=flow_key,
        )

        rpa_remark = helper.convert_string_hashmap(keyword_fail_remark, "string") if keyword_fail_remark else "Successful"

        self.gs.update_row(
            row,
            nf.COLUMN_BULK_SERVICE_RPA_REMARKS_KEYWORD,
            self.worksheets["bulkService"],
            rpa_remark,
        )

    # Function to define gyro command
    def _handle_gyro_command(self, bs_row_data, bs_service_id):
        command_string = bs_row_data[nf.BS_INDEX_GYRO_COMMAND]
        if not command_string:
            logger.info("Skipping Gyro Command as no command string provided.")
            return

        # Check RPA Flow Remarks - BASE, DOUBLE and EXTEND
        # Under 'try' block code, if the current AUX flow of RPA remark found 'Successful', will skip the step and flow process and proceed to next process or next entry
        try:
            rpa_remark_value = bs_row_data[nf.BS_INDEX_RPA_REMARKS_AUX_FLOW]
            print(f"Check RPA REMARK: {rpa_remark_value}")
            if "success" in rpa_remark_value.lower():
                logger.warning(f"Current Flow AUX - GYRO is already successful, continue to next process..")
                return
        except KeyError:
            pass

        logger.info("Processing Gyro Command...")
        gyro_rpa_remark = create_gyro_command(command_string, bs_service_id, self.wd)
        if gyro_rpa_remark:
            self.rpa_remark_aux_fail.update(gyro_rpa_remark)

    # Function to define Simple Service Group
    def _handle_ssg(self, row, bs_row_data, bs_service_id):
        # Check RPA Flow Remarks - BASE, DOUBLE and EXTEND
        # Under 'try' block code, if the current AUX flow of RPA remark found 'Successful', will skip the step and flow process and proceed to next process or next entry
        try:
            rpa_remark_value = bs_row_data[nf.BS_INDEX_RPA_REMARKS_AUX_FLOW]
            if "ssg: success" in rpa_remark_value.lower():
                logger.warning(f"Current Flow AUX - SIMPLE SERVICE GROUP is already successful, continue to next process..")
                return
        except KeyError:
            pass
        ssg_required = bs_row_data[nf.NF_INDEX_GROUP_STATUS_INQUIRY].lower() == "yes"
        construct_lower = bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT].lower()
        
        if ssg_required and "data" in construct_lower or construct_lower in ("postpaid recurring", "postpaid rollover"):
            rpa_remark_ssg = ssg.define_bs_simple_service_group(bs_service_id, bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT], self.wd)
            if rpa_remark_ssg:
                self.rpa_remark_aux_fail.update(rpa_remark_ssg)
        else:
            logger.info("Skipping Simple Service Group as criteria not met.")
    
    # Function to insert service id to message worksheet tab
    def _update_messages_tab(self, row, bs_row_data, bs_service_id):
        # Check RPA Flow Remarks - BASE, DOUBLE and EXTEND
        # Under 'try' block code, if the current AUX flow of RPA remark found 'Successful', will skip the step and flow process and proceed to next process or next entry
        try:
            rpa_remark_value = bs_row_data[nf.BS_INDEX_RPA_REMARKS_AUX_FLOW]
            if "success" in rpa_remark_value.lower():
                logger.warning(f"Messages with service id is already updated, skipping..")
                return
        except KeyError:
            pass
        try:
            logger.info("Updating 'Messages' worksheet with service ID...")
            #messages_worksheet = self.gs.create_worksheet(nf.WORKSHEET_TAB_BULK_SERVICES_TAB_MESSAGES)
            messages_worksheet = self.worksheets["messages"]
            bs_name = bs_row_data[nf.NF_INDEX_NAME].strip()
            messages_rows = self.gs.get_rows_by_name(messages_worksheet, bs_name)
            # first_row, last_row = messages_rows[0], messages_rows[-1]
            # list_service_id = [[bs_service_id]] * len(messages_rows)
            #messages_worksheet.update(f"M{first_row}:M{last_row}", list_service_id)
            if not messages_rows:
                logger.warning(f"Service Name '{bs_name}' not found in Messages tab")
                return
            self.gs.update_row_range(self.worksheets["messages"], bs_service_id, messages_rows)
            #logger.info(f"Row range from M{first_row} to M{last_row} has been updated with service id {bs_service_id}")

            # for msg_row in messages_rows:
            #     self.gs.update_row(
            #         msg_row,
            #         nf.COLUMN_MESSAGES_SERVICE_ID,
            #         messages_worksheet,
            #         bs_service_id,
            #     )
            #     logger.info(f"Updated row {msg_row} with service ID {bs_service_id}")

        except Exception as e:
            logger.exception(f"Failed to update Messages worksheet: {e}")

    # Function to handle creation of AUX Serivces
    def _handle_aux_flow(self, row, bs_row_data):
        # Under 'try' block code, if the current AUX flow of RPA remark found 'Successful', will skip the step and flow process and proceed to next process or next entry
        try:
            rpa_remark_value = bs_row_data[nf.BS_INDEX_RPA_REMARKS_AUX_FLOW]
            print(f"Check RPA REMARK: {rpa_remark_value}")
            if "success" in rpa_remark_value.lower():
                logger.warning(f"Current Flow AUX - MESSAGE is already successful, continue to next process..")
                return
        except KeyError:
            pass

        try:
            logger.info("Processing AUX FLOW..")

            # Process Message Service
            message_failed_true = ms.create_message(
                self.wd,
                self.gs,
                bs_row_data[nf.NF_INDEX_NAME].strip()
            )
            if message_failed_true:
                self.rpa_remark_aux_fail["MESSAGE"] = "Failed"

            # Process Check Has Subscription Service
            check_has_failed_true_with_ids = add_service_id_to_check_has(
                self.wd,
                self.gs,
                bs_row_data,
                bs_row_data[nf.BS_INDEX_CHECK_HAS_IDS]
            )
            if check_has_failed_true_with_ids:
                self.rpa_remark_aux_fail["CHECK_HAS_OTHER"] = f"Failed {check_has_failed_true_with_ids}"
            
            # Update RPA Remark for AUX Flow
            self._rpa_remark_final_update(self.rpa_remark_aux_fail, nf.COLUMN_BULK_SERVICE_RPA_REMARKS_AUX_FLOW, row)
 
        except Exception as e:
            logger.exception(f"Failed in AUX flow process: {e}")


    # Funcion to handle/to determine what step and flow construct to execute
    def determine_step_type(self, bs_row_data, row, flow_key=None):
        try:
            # Declare bs_service_id value from bulk service service id and construct_value
            bs_service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]
            construct_value_lower = bs_row_data[
                nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT
            ].lower()
            # Determine what specific process to defining steps and flows for bulk services.
            # Execute Process For Step Type = Prepaid CTL With Data
            logger.info(f"Executing Step and Flow Construct => '{bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT]}'")

            # Calling function to execute step type services for Prepaid CTL
            if "prepaid ctl" in construct_value_lower or "prepaid opm" in construct_value_lower:
                self.prepaid_ctlopm.start_prepaid_ctl_opm_process(
                    flow_key,
                    bs_service_id,
                    bs_row_data,
                    self.worksheets["paramMatrix"],
                    row,
                )

            else:
                logger.info(
                    f"Value doesn't recognize '{bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT]}' to process for steps and flows construct."
                )

        except Exception as e:
            error_msg = f"Something went wrong in 'determine_step_type'\nERROR: {e}"
            logger.info(error_msg)
            raise
           
    # Function to Create Gyro Command
    def create_gyro_command(self, command_string, bs_service_id, wd):
        try:
            logger.info("STARTING GYRO COMMAND PROCESS")

            # Declare variable
            url = get_env_variable("WEBTOOL_GYRO_COMMAND_ADD_FULL_URL")
            array_command = command_string.split(", ")

            # Loop array command values
            for command_value in array_command:

                # Redirect to Gyro Command Add page
                logger.info("Redirecting to Gyro Command Add Page...")
                wd.redirect_to_page(url, nf.NF_ADD_BTN_INPUT)
                #wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")

                logger.info(f"Adding Gyro Command: {command_value}")

                # Input Command Field
                wd.perform_action(
                    "name", nf.GYRO_COMMAND_FIELD, "sendkeys", command_value
                )

                # Choose Current Bulk Service - Service ID
                wd.perform_action(
                    "xpath",
                    f"//select[@name='svc_id']//option[@value='{bs_service_id}']",
                    "click",
                )

                # Click Add button
                logger.info("Saving gyro command...")
                wd.submit_form_and_wait_for_success(
                    "xpath", nf.NF_ADD_BTN_INPUT, nf.SUCCESS_OR_EXIST
                )
                logger.info(
                    f"Gyro Command '{command_value}' Successfully Created - For Service ID: {bs_service_id}"
                )

        except Exception as e:
            logger.info(
                f"An error has occurred while defining gyro command\nERROR: {e}"
            )
            self.rpa_remark_aux_fail["GYRO"] = "Failed"

    def _handle_step_and_flow_rollover(self, bs_row_data, service_id, row):
        rpa_remark_base_fail = {}
        is_success = create_dummy_step_type(service_id, self.wd)
        if not is_success:
            rpa_remark_base_fail['DUMMY'] = "Failed"
        flow_remark = define_flow_dummy(bs_row_data, self.wd)
        rpa_remark_base_fail.update(flow_remark)
        self._rpa_remark_final_update(rpa_remark_base_fail, nf.COLUMN_BULK_SERVICE_RPA_REMARKS_BASE_FLOW, row)

    def _handle_step_and_flow_dummy(self, bs_row_data, service_id, row):
        rpa_remark_base_fail = {}
        is_success = create_dummy_step_type(service_id, self.wd)
        if not is_success:
            rpa_remark_base_fail['STEP_DUMMY'] = "Failed"
        flow_remark = define_flow_dummy(bs_row_data, self.wd)
        rpa_remark_base_fail.update(flow_remark)
        self._rpa_remark_final_update(rpa_remark_base_fail, nf.COLUMN_BULK_SERVICE_RPA_REMARKS_BASE_FLOW, row)

    def _handle_soc_to_nf(self, service_id, soc_id):
        is_success = define_soc_to_nf(service_id, soc_id, self.wd)
        if not is_success:
            self.rpa_remark_aux_fail['SOC to NF'] = "Failed"

    def _rpa_remark_final_update(self, rpa_remark, column, row):
        rpa_aux_string = helper.convert_string_hashmap(rpa_remark, "string")
        rpa_aux_final = rpa_aux_string if rpa_remark else "Successful"

        self.gs.update_row(
            row,
            column,
            self.worksheets["bulkService"],
            rpa_aux_final,
        )

    def _handle_ctl_opm_multi_process(self, bs_row_data, credential, row):
        from nf_services.nf_service_process import execute_new_aux_instance_process
        """Handle parallel processing of main and auxiliary flows"""
        logger.info("STARTING MULTI-PROCESS FOR AUX FLOW..")

         # Create synchronization events
        main_done = Event()
        aux_done = Event()

        # Start auxiliary process with sync events
        aux_process = Process(
            target=execute_new_aux_instance_process,  # Note: Using standalone function
            args=(bs_row_data, row, aux_done, credential)
        )
        aux_process.start()

        try:            
            # Execute main process
            self._handle_step_and_flows(row, bs_row_data)
            # Signal main process is done
            main_done.set()
             # Wait for auxiliary process
            logger.info("Main process waiting for auxiliary process...")
            aux_done.wait()

        except Exception as e:
            logger.exception(f"Main process error for row {row}: {e}")
            main_done.set()  # Signal even on error
            aux_done.wait()
        finally:
            if aux_process.is_alive():
                aux_process.terminate()
            aux_process.join()
            
# def _execute_new_instance_process(row_data: dict, row: int, aux_done, main_done):
#     """Process 2: Handles auxiliary flows and services"""
#     from utils.google_sheet import GSheetClient
#     from utils.login import login_credential
#     gs = GSheetClient()
#     username, password = login_credential("NF_2", gs)
#     if username is None or password is None:
#         logger.warning("Multi-process not applicable")
#         return
#     try:
#         # Initialize fresh clients for Process 2
#         from utils.env_loader import get_env_variable
#         from utils.web_driver import WebDriver
#         from utils.logger import finalize_log_upload
#         from config.config import WORKSHEET_CONFIG, nf
#         import sys
#         #from nf_services.nf_constants import NfConstants

#         #load_environment()
#         wd = WebDriver()
        
#         # Execute Login Sequence for secondary process
#         worksheets = gs.create_worksheets(WORKSHEET_CONFIG)
#         url_param = get_env_variable("WEBTOOL_LOGIN_FULL_URL")
#         logger.info(f"2ND PROCESS: Redirecting to NF login page: {url_param}")
        
#         wd.redirect_to_page(url_param)
#         wd.wait_until_element("id", nf.NF_LOGIN_BUTTON, "clickable")        
#         wd.perform_action("name", "uname", "sendkeys", username)
#         wd.perform_action("name", "passwd", "sendkeys", password)
#         wd.perform_action("id", nf.NF_LOGIN_BUTTON, "click")
#         wd.wait_until_element("id", "content", "visible")
#         logger.info("2ND PROCESS: Login Successful!")

#         # Initialize service controller for this process
#         controller = ServiceController(worksheets, wd, gs)
        
#         # Execute auxiliary processes
#         bs_service_id = row_data[nf.NF_INDEX_SERVICE_ID]            
#         controller._handle_wallet_empty(bs_service_id, row_data)
#         controller._handle_gyro_command(row_data, bs_service_id)
#         controller._handle_ssg(row, row_data, bs_service_id)
#         controller._update_messages_tab(row, row_data, bs_service_id)
#         controller._handle_aux_flow(row, row_data)
        
#         # Signal auxiliary process is done
#         # Wait for main process
#         # logger.info("Auxiliary process waiting for main process...")
#         # main_done.wait()

#     except Exception as e:
#         logger.error(f"2ND PROCESS: Something went wrong - Failed to process: {e}")
#         aux_done.set()  # Signal even on error
#     finally:
#         logger.info("Terminating bot secondary process..")
#         finalize_log_upload()
#         wd.driver.quit()
#         aux_done.set()
#         sys.exit()