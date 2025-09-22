from selenium.webdriver.common.by import By
from utils.env_loader import get_env_variable
from utils.logger import logger
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from nf_services.nf_constants import TackOn
from nf_services.main_services.bulk_service import BulkServices
import time


# logger = setup_logger(service_name=f"NF {__name__}")

from config.config import nf


class CTLOPMFlowService:
    def __init__(self, worksheets, webdriver, gsheet):
        self.wd = webdriver
        self.gs = gsheet
        self.worksheets = worksheets
        self.bs = BulkServices(worksheets, webdriver, gsheet)

    def start_ctl_opm_flow(self, flow_key, bs_row_data):
        try:
        
            # Validate row has sufficient data
            # if len(bs_row_data) <= max(nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT, nf.NF_INDEX_SERVICE_ID):
            #     logger.error(f"Invalid or incomplete row data at index {bs_row}: {bs_row_data}")
            #     return
            # Fetch updated row data
            wallet_value = bs_row_data[nf.NF_INDEX_WALLET].strip()
            bs_row = bs_row_data[nf.KEY_ROW_NUMBER]
            construct_value = bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT].strip()
            bs_service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]
            construct_value_lower = construct_value.lower()
            network_type_lower = bs_row_data[nf.BS_KEY_SMS_VOICE_NETWORK_TYPE].lower()
            logger.info(f"STARTING FLOW CREATION PROCESS FOR: {construct_value}")

            #self.wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")
            prefix = "EXTEND_" if "extend" in flow_key else "DOUBLE_" if "double" in flow_key else ""
            sms_voice_suffx = "INTRA_BULK" if "intra" in network_type_lower else "ALLNET_BULK" if "all network" in network_type_lower else "ALLNET_UNLI"

            step_mapping = {
                "check_has_subscription_name": "CHECK_HAS_SUBSCRIPTION",
                "in_charge_name": "EXTEND_CHARGE" if "extend" in flow_key else "IN_CHARGE",
                "extend_first_expiry_name": "EXTEND_FIRST_EXPIRY",
                "data_prov_name": f"{prefix}{wallet_value}",
                "unli_sms_name": f"{prefix}SMS_{sms_voice_suffx}",
                "unli_voice_name": f"{prefix}VOICE_{sms_voice_suffx}",
                "hlr_ply_name": "HLR_PLY",
            }

            if "prepaid ctl" in construct_value_lower:
                self.create_flow_prepaid_ctl(flow_key, step_mapping, bs_row_data, bs_row)

            elif "prepaid opm" in construct_value_lower:
                self.create_flow_prepaid_opm(flow_key, step_mapping, bs_row_data, bs_row)

        except (TimeoutException, NoSuchElementException) as sel_err:
            logger.error(f"Selenium error during service flow processing: {sel_err}")
            
        except Exception as e:
            logger.error(f"Unexpected error in SERVICE FLOW PROCESS: {e}")
            

    def create_flow_prepaid_ctl(self, flow_key, step_mapping, bs_row_data, bs_row):
        construct_value = bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT].strip()
        bs_service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID].strip()
        tackon_value_lower = bs_row_data[nf.BS_INDEX_TACKON].lower().strip()
        construct_value_lower = construct_value.lower()
        flow_name = {
            "double": "DOUBLE_PROVISION",
            "extend": "EXTEND_PROVISION",
        }.get(flow_key, "PROVISION")

        flow_name_exist = self._flow_validation(bs_service_id, flow_name)

        if not flow_name_exist:
            # Navigate to the add flow page
            url = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=flows&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
            self.wd.redirect_to_page(url, nf.NF_ADD_BTN_INPUT)

            logger.info(f"Defining Flow for {construct_value}")
            first_step_name = "CHECK_HAS_SUBSCRIPTION" if tackon_value_lower == TackOn.CHECK_HAS_ADD.value and flow_key != 'extend' else step_mapping['in_charge_name']
            self._create_flow(flow_name, first_step_name)
        else:
            self.wd.perform_action("xpath", f"//td[@align='left' and contains(text(), ' {flow_name} ')]/preceding::a[1]", "click")
            logger.warning(f"Flow name '{flow_name}' already exist")
        # Retrieve Flow ID
        flow_id = self._get_flow_id()

        #============================== START FLOW PATH DEFINITION CTL ============================#

        # Safely create function to define a step
        def handle_define_step(from_key, to_key, description=""):
            try:
                self.define_stepfrom_stepto(
                    step_mapping[from_key],
                    step_mapping[to_key]
                )
            except KeyError as e:
                logger.error(f"KeyError - step name does not exist in flow_definitions - Skipping {description or f'{from_key} to {to_key}'}: {e}")

        flow_definitions = {
            "prepaid ctl with data, unli sms and unli voice": [
                ("check_has_subscription_name", "in_charge_name") if tackon_value_lower == TackOn.CHECK_HAS_ADD.value and "extend" not in flow_key else None,
                ("in_charge_name", "extend_first_expiry_name"),
                ("extend_first_expiry_name", "data_prov_name"),
                ("data_prov_name", "unli_sms_name"),
                ("unli_sms_name", "unli_voice_name"),
                ("unli_voice_name", "hlr_ply_name") if flow_key not in ("double", "extend") else None
            ],
            "prepaid ctl with data and unli sms": [
                ("check_has_subscription_name", "in_charge_name") if tackon_value_lower == TackOn.CHECK_HAS_ADD.value and "extend" not in flow_key else None,
                ("in_charge_name", "extend_first_expiry_name"),
                ("extend_first_expiry_name", "data_prov_name"),
                ("data_prov_name", "unli_sms_name"),
            ],
            "prepaid ctl with unli sms and unli voice": [
                ("check_has_subscription_name", "in_charge_name") if tackon_value_lower == TackOn.CHECK_HAS_ADD.value and "extend" not in flow_key else None,
                ("in_charge_name", "extend_first_expiry_name"),
                ("extend_first_expiry_name", "unli_sms_name"),
                ("unli_sms_name", "unli_voice_name"),
                ("unli_voice_name", "hlr_ply_name") if flow_key not in ("double", "extend") else None
            ],
            "prepaid ctl with data": [
                ("check_has_subscription_name", "in_charge_name") if tackon_value_lower == TackOn.CHECK_HAS_ADD.value and "extend" not in flow_key else None,
                ("in_charge_name", "extend_first_expiry_name"),
                ("extend_first_expiry_name", "data_prov_name"),
            ], #==============#
            "prepaid ctl with data, bulk sms and bulk voice": [
                ("check_has_subscription_name", "in_charge_name") if tackon_value_lower == TackOn.CHECK_HAS_ADD.value and "extend" not in flow_key else None,
                ("in_charge_name", "extend_first_expiry_name"),
                ("extend_first_expiry_name", "data_prov_name"),
                ("data_prov_name", "unli_sms_name"),
                ("unli_sms_name", "unli_voice_name"),
                ("unli_voice_name", "hlr_ply_name") if flow_key not in ("double", "extend") else None
            ],
            "prepaid ctl with data and bulk sms": [
                ("check_has_subscription_name", "in_charge_name") if tackon_value_lower == TackOn.CHECK_HAS_ADD.value and "extend" not in flow_key else None,
                ("in_charge_name", "extend_first_expiry_name"),
                ("extend_first_expiry_name", "data_prov_name"),
                ("data_prov_name", "unli_sms_name"),
            ],
            "prepaid ctl with bulk sms and bulk voice": [
                ("check_has_subscription_name", "in_charge_name") if tackon_value_lower == TackOn.CHECK_HAS_ADD.value and "extend" not in flow_key else None,
                ("in_charge_name", "extend_first_expiry_name"),
                ("extend_first_expiry_name", "unli_sms_name"),
                ("unli_sms_name", "unli_voice_name"),
                ("unli_voice_name", "hlr_ply_name") if flow_key not in ("double", "extend") else None
            ],
        }
        logger.info(flow_definitions)
        for step in flow_definitions.get(construct_value_lower, []):
            if step:  # skip None
                handle_define_step(*step)

        logger.info(f"FLOW SUCCESSFULLY DEFINED FOR = {construct_value}")
        
        # Assign flow to bulk service
        self.bs.nf_assign_bulk_service_flow(flow_key, bs_service_id, flow_id)
        flow_string = f"{'Base' if not flow_key else flow_key.upper()}"
        logger.info(f"Bulk Service {flow_string} Flow and API Flow Updated")

    # Function to Execute Flow process Specifically for Prepaid CTL With Data
    def create_flow_prepaid_opm(self, flow_key, step_mapping, bs_row_data, bs_row):
        construct_value = bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT]
        bs_service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]
        tackon_value_lower = bs_row_data[nf.BS_INDEX_TACKON].lower()
        construct_value_lower = construct_value.lower()
        flow_name = {
            "double": "DOUBLE_PROVISION",
            "extend": "EXTEND_PROVISION"
        }.get(flow_key, "PROVISION")

        flow_name_exist = self._flow_validation(bs_service_id, flow_name)

        if not flow_name_exist:
            # Navigate to the add flow page
            url = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=flows&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
            self.wd.redirect_to_page(url, nf.NF_ADD_BTN_INPUT)

            logger.info(f"Defining Flow for {construct_value}")
            first_step_name = "CHECK_HAS_SUBSCRIPTION" if tackon_value_lower == TackOn.CHECK_HAS_ADD.value and flow_key != "extend" else step_mapping['in_charge_name'] if "extend" in flow_key else step_mapping['extend_first_expiry_name']
            self._create_flow(flow_name, first_step_name)
        else:
            self.wd.perform_action("xpath", f"//td[@align='left' and contains(text(), ' {flow_name} ')]/preceding::a[1]", "click")
            logger.warning(f"Flow name '{flow_name}' already exist")

        # Retrieve Flow ID
        flow_id = self._get_flow_id()

        #============================== START FLOW PATH DEFINITION OPM ============================#

         # Safely create function to define a step
        def handle_define_step(from_key, to_key, description=""):
            try:
                self.define_stepfrom_stepto(
                    step_mapping[from_key],
                    step_mapping[to_key]
                )
            except KeyError as e:
                logger.info(f"KeyError - step name does not exist in flow_definitions - Skipping {description or f'{from_key} to {to_key}'}: {e}")

        flow_definitions = {
            "prepaid opm with data, unli sms and unli voice": [
                ("check_has_subscription_name", "extend_first_expiry_name") if tackon_value_lower == TackOn.CHECK_HAS_ADD.value and "extend" not in flow_key else None,
                ("in_charge_name", "extend_first_expiry_name") if "extend" in flow_key else None,
                ("extend_first_expiry_name", "data_prov_name"),
                ("data_prov_name", "unli_sms_name"),
                ("unli_sms_name", "unli_voice_name"),
                ("unli_voice_name", "hlr_ply_name") if flow_key not in ("double", "extend") else None
            ],
            "prepaid opm with data and unli sms": [
                ("check_has_subscription_name", "extend_first_expiry_name") if tackon_value_lower == TackOn.CHECK_HAS_ADD.value and "extend" not in flow_key else None,
                ("in_charge_name", "extend_first_expiry_name") if "extend" in flow_key else None,
                ("extend_first_expiry_name", "data_prov_name"),
                ("data_prov_name", "unli_sms_name"),
            ],
            "prepaid opm with data and unli voice": [
                ("check_has_subscription_name", "extend_first_expiry_name") if tackon_value_lower == TackOn.CHECK_HAS_ADD.value and "extend" not in flow_key else None,
                ("in_charge_name", "extend_first_expiry_name") if "extend" in flow_key else None,
                ("extend_first_expiry_name", "data_prov_name"),
                ("data_prov_name", "unli_voice_name"),
                ("unli_voice_name", "hlr_ply_name") if flow_key not in ("double", "extend") else None
            ],
            "prepaid opm with unli sms and unli voice": [
                ("check_has_subscription_name", "extend_first_expiry_name") if tackon_value_lower == TackOn.CHECK_HAS_ADD.value and "extend" not in flow_key else None,
                ("in_charge_name", "extend_first_expiry_name") if "extend" in flow_key else None,
                ("extend_first_expiry_name", "unli_sms_name"),
                ("unli_sms_name", "unli_voice_name"),
                ("unli_voice_name", "hlr_ply_name") if flow_key not in ("double", "extend") else None
            ],
            "prepaid opm with data": [
                ("check_has_subscription_name", "extend_first_expiry_name") if tackon_value_lower == TackOn.CHECK_HAS_ADD.value and "extend" not in flow_key else None,
                ("in_charge_name", "extend_first_expiry_name") if "extend" in flow_key else None,
                ("extend_first_expiry_name", "data_prov_name"),
            ], #==============#
            "prepaid opm with data, bulk sms and bulk voice": [
                ("check_has_subscription_name", "extend_first_expiry_name") if tackon_value_lower == TackOn.CHECK_HAS_ADD.value and "extend" not in flow_key else None,
                ("in_charge_name", "extend_first_expiry_name") if "extend" in flow_key else None,
                ("extend_first_expiry_name", "data_prov_name"),
                ("data_prov_name", "unli_sms_name"),
                ("unli_sms_name", "unli_voice_name"),
                ("unli_voice_name", "hlr_ply_name") if flow_key not in ("double", "extend") else None
            ],
            "prepaid opm with data and bulk sms": [
                ("check_has_subscription_name", "extend_first_expiry_name") if tackon_value_lower == TackOn.CHECK_HAS_ADD.value and "extend" not in flow_key else None,
                ("in_charge_name", "extend_first_expiry_name") if "extend" in flow_key else None,
                ("extend_first_expiry_name", "data_prov_name"),
                ("data_prov_name", "unli_sms_name"),
            ],
            "prepaid opm with bulk sms and bulk voice": [
                ("check_has_subscription_name", "extend_first_expiry_name") if tackon_value_lower == TackOn.CHECK_HAS_ADD.value and "extend" not in flow_key else None,
                ("in_charge_name", "extend_first_expiry_name") if "extend" in flow_key else None,
                ("extend_first_expiry_name", "unli_sms_name"),
                ("unli_sms_name", "unli_voice_name"),
                ("unli_voice_name", "hlr_ply_name") if flow_key not in ("double", "extend") else None
            ],
        }
        # logger.info(flow_definitions)
        for step in flow_definitions.get(construct_value_lower, []):
            if step:  # skip None
                handle_define_step(*step)

        logger.info(f"FLOW SUCCESSFULLY DEFINED FOR = {construct_value}")

        # Final Bulk Assignment
        self.bs.nf_assign_bulk_service_flow(flow_key, bs_service_id, flow_id)
        flow_string = f"{'Base' if not flow_key else flow_key.upper()}"
        logger.info(f"Bulk Service {flow_string} Flow and API Flow Updated")

    # Function to create Flow for service id
    def _create_flow(self, flow_name, first_step_name):
        # Fill Flow form
        self.wd.perform_action("name", nf.NF_FLOWS_NAME_INPUT, "sendkeys", flow_name)
        self.wd.perform_action(
            "xpath",
            f"//select[@name='first_step_id']//option[contains(text(), '{first_step_name}')]",
            "click"
        )
        self.wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
        logger.info("SERVICE FLOW SUCCESSFULLY CREATED!")

    # Function to retrieve flow id
    def _get_flow_id(self):
        logger.info("Fetching flow ID...")
        self.wd.wait_until_element("xpath", nf.FLOW_ID_ELEMENT, "visible")
        flow_id = self.wd.driver.find_element(By.XPATH, nf.FLOW_ID_ELEMENT).text.strip()
        logger.info(f"Flow ID Retrieved: {flow_id}")
        self.wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")
        return flow_id

    def define_stepfrom_stepto(self, step_name_from, step_name_to):
        try:
            logger.info(
                f"Assigning Flow - STEP FROM: {step_name_from} - STEP TO: {step_name_to}"
            )
            # Dropdown Step from Dropdown
            self.wd.perform_action(
                "xpath",
                f"//select[@name='step_id_from']//option[contains(text(), '({step_name_from})')]",
                "click",
            )

            # Dropdown Step to Dropdown
            self.wd.perform_action(
                "xpath",
                f"//select[@name='step_id_to']//option[contains(text(), '({step_name_to})')]",
                "click",
            )

            # Click 'Add' Button //select[@name='condition']
            #success_element = f"//tr[td/a[contains(text(), '(VOICE_ALLNET_UNLI)')] and td/a[contains(text(), '(HLR_PLY)')] and td[contains(text(), 'Success')]] | //span[contains(text(), 'Flow already has flow path')]"            
            #self.wd.submit_form_and_wait_for_success("xpath", nf.NF_ADD_BTN_INPUT, success_element)
            logger.info("Saving flow path...")
            self.wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
            self.wd.wait_until_element("xpath", nf.SUCCESS_FLOW_PATH.format(step_from=step_name_from, step_to=step_name_to), "visible")
            logger.info(f"Flow Path Successfully Added - From ({step_name_from}) => To: ({step_name_to})")
            
            # Refresh page to avoid stale element
            time.sleep(1)
            self.wd.wait_staleness_of(nf.NF_ADD_BTN_INPUT)

        except NoSuchElementException as e: 
            logger.error(f"Step name not found, please check '{step_name_from}' or '{step_name_to}' if its already define or not")

        except Exception as e:
            logger.error(
                f"Something went wrong in the function of 'define_stepfrom_stepto'\nERROR: {e}"
            )

    def _flow_validation(self, service_id, flow_name):
        logger.info(f"Check if existing flow {flow_name}")
        # Redirect to Edit Bulk service page
        base_url = get_env_variable("WEBTOOL_BASE_URL")
        self.wd.redirect_to_page(f"{base_url}/nf/index.php?mod=bulk_services&op=details&id={service_id}", nf.BS_EDIT_PAGE_REMINDER_MSG_BTN)

        # Validate if step name exist in edit page of Bulk Service
        try:
            flow_xpath = f"//td[@align='left' and contains(text(), ' {flow_name} ')]"
            self.wd.driver.find_element(By.XPATH, flow_xpath)
            is_exist = True
        except NoSuchElementException:
            is_exist = False
        logger.info(f"Flow '{flow_name}' Exist?: {is_exist}")
        return is_exist