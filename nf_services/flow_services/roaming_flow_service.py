from selenium.webdriver.common.by import By
from utils.env_loader import get_env_variable
from utils.logger import logger
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from nf_services.nf_constants import NfConstants
from nf_services.main_services.bulk_service import BulkServices
import time

from config.config import nf

class RoamingFlowService:
    def __init__(self, worksheets, webdriver, gsheet):
        self.wd = webdriver
        self.gs = gsheet
        self.worksheets = worksheets
        self.bs = BulkServices(worksheets, webdriver, gsheet)

    def start_roaming_service_flow(self, bs_row_data):
        try:
            # Fetch updated row data
            bs_wallet = bs_row_data[nf.NF_INDEX_WALLET]            
            step_type_mapping = {
                "hlr_set_vssr_name": "HLR_SET_VSSR_TPLID", 
                "hlr_set_diamrrs_name": "HLR_SET_DIAMRRS_TPLID",
                "in_charge_name": "IN_CHARGE", 
                "extend_first_expiry_name": "EXTEND_FIRST_EXPIRY",
                "sdm_postpaid_name": "SDM_POSTPAID_CREATE_SUBSCRIBER",
                "data_prov_name": bs_wallet,
            }

            construct_value = bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT]
            bs_service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]
            logger.info(f"STARTING FLOW CREATION PROCESS FOR: {construct_value}")

            # Navigate to the add flow page
            url = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=flows&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
            self.wd.redirect_to_page(url, nf.NF_ADD_BTN_INPUT)
            #self.wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")

            construct_value_lower = construct_value.lower()

            if "prepaid" in construct_value_lower:
               self.define_prepaid_trigger_or_main_flow(step_type_mapping, bs_row_data)
            else:
                self.define_postpaid_trigger_or_main_flow(step_type_mapping, bs_row_data)

        except (TimeoutException, NoSuchElementException) as sel_err:
            logger.error(f"Selenium error during service flow processing: {sel_err}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in SERVICE FLOW PROCESS: {e}")
            raise

    def define_prepaid_trigger_or_main_flow(self, step_type_mapping, bs_row_data):
        construct_value = bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT]
        bs_service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]
        sf_construct_value = construct_value.lower()
        
        logger.info(f"Defining Flow for {construct_value}")
        first_step_name = "HLR_SET_VSSR_TPLID"
        self._create_flow("PROVISION", first_step_name)

        # Retrieve Flow ID
        flow_id = self._get_flow_id()

        # # Define flow steps based on construct type
        # define_step("in_charge", "extend_first_expiry", "HLR SET VSSR TPLID to HLR SET DIAMRRS TPLID")
        ROAM_PREPAID_TRIGGER = {
            "roaming prepaid trigger service": [
                ("hlr_set_vssr", "hlr_set_diamrrs"),
                ("hlr_set_diamrrs", "data_prov"),

            ],
            "roaming prepaid main service": [
                ("hlr_set_vssr", "hlr_set_diamrrs"),
                ("hlr_set_diamrrs", "extend_first_expiry"),
                ("extend_first_expiry", "data_prov"),
            ]
        }

        for step in ROAM_PREPAID_TRIGGER.get(sf_construct_value, []):
            if step:  # skip None
                #define_step(*step)
                self._define_step(step_type_mapping, *step)

        logger.info(f"FLOW SUCCESSFULLY DEFINED FOR = {construct_value}")
        
        # Assign flow to bulk service
        self.bs.nf_assign_bulk_service_flow("base", bs_service_id, flow_id)
        logger.info(f"Bulk Service Default and API Flow Updated")

    def define_postpaid_trigger_or_main_flow(self, step_type_mapping, bs_row_data):
        construct_value = bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT]
        bs_service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]
        sf_construct_value = construct_value.lower()
        
        logger.info(f"Defining Flow for {construct_value}")
        first_step_name = "SDM_POSTPAID_CREATE_SUBSCRIBER"
        self._create_flow("PROVISION", first_step_name)

        # Retrieve Flow ID
        flow_id = self._get_flow_id()

        # # Define flow steps based on construct type
        # define_step("in_charge", "extend_first_expiry", "HLR SET VSSR TPLID to HLR SET DIAMRRS TPLID")

        ROAM_POSTPAID_TRIGGER = {
            "roaming postpaid trigger service": [
                ("sdm_postpaid", "data_prov"),

            ],
            "roaming postpaid main service": [
                ("sdm_postpaid", "data_prov"),
                ("data_prov", "in_charge"),
            ]
        }

        for step in ROAM_POSTPAID_TRIGGER.get(sf_construct_value, []):
            if step:  # skip None
                self._define_step(step_type_mapping, *step)

        logger.info(f"FLOW SUCCESSFULLY DEFINED FOR = {construct_value}")
        
        # Assign flow to bulk service
        self.bs.nf_assign_bulk_service_flow("base", bs_service_id, flow_id, bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT].lower())
        logger.info(f"Bulk Service Default and API Flow Updated")

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

    # Function helper: safely define a step from to step to
    def _define_step(self, step_type_mapping, from_key, to_key, description=""):
        try:
            self._define_stepfrom_stepto(
                step_type_mapping[f"{from_key}_name"],
                step_type_mapping[f"{to_key}_name"]
            )
        except (KeyError, NoSuchElementException) as e:
            logger.error(f"Unexpected error - Skipping {description or f'{from_key} to {to_key}'}: {e}")

    # Function to retrieve flow id
    def _get_flow_id(self):
        
        flow_id_element = nf.FLOW_ID_PROD if "10.25" in self.wd.driver.current_url else nf.FLOW_ID_TESTBED
        self.wd.wait_until_element("xpath", flow_id_element, "visible")
        
        flow_id = self.wd.driver.find_element(By.XPATH, flow_id_element).text
        logger.info(f"Flow ID Retrieved: {flow_id}")
        self.wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")
        return flow_id

    def _define_stepfrom_stepto(self, step_name_from, step_name_to):
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
            success_element = f"//td[@align='left']//a[contains(text(), '{step_name_from}')] | //span[contains(text(), 'Flow already has flow path')]"            
            #self.wd.submit_form_and_wait_for_success("xpath", nf.NF_ADD_BTN_INPUT, success_element)
            logger.info("Saving flow path...")
            self.wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
            logger.info(f"Flow Path Successfully Added - From ({step_name_from}) => To: ({step_name_to})")
            time.sleep(3)
            self.wd.wait_until_element("xpath", success_element, "visible")

        except NoSuchElementException as e: 
            logger.error(f"Step name not found, please check '{step_name_from}' or '{step_name_to}' if its already define or not")

        except Exception as e:
            logger.error(
                f"Something went wrong in the function of 'define_stepfrom_stepto'\nERROR: {e}"
            )
