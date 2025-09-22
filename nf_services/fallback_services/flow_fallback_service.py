from nf_services.flow_services.ctl_opm_flow_service import CTLOPMFlowService
from utils.env_loader import get_env_variable
from nf_services.nf_constants import NfConstants
from nf_services.config.flow_mappings import get_flow_map
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from utils.logger import logger

# Constants
from config.config import nf


class FlowFlashbackService:
    def __init__(self, webdriver, gsheet, worksheets):
        self.wd = webdriver
        self.gs = gsheet
        self.flow = CTLOPMFlowService(worksheets, webdriver, gsheet)
        self.get_flow_map = get_flow_map

    def redirect_to_edit_flow(self, service_id, flow_name, logic_flow, construct_value):
        base_url = get_env_variable("WEBTOOL_BASE_URL")
        self.wd.redirect_to_page(
            f"{base_url}/nf/index.php?mod=bulk_services&op=details&id={service_id}"
        )
        self.wd.wait_until_element(
            "xpath", "//input[contains(@onclick, 'mod=reminder_messages')]", "clickable"
        )
        try:
            # self.wd.perform_action(
            #     "xpath",
            #     f"//td[@align='left' and contains(text(), ' {flow_name} ')]/preceding::a[1]",
            #     "click",
            # )
            self.wd.driver.find_element(By.XPATH, f"//td[@align='left' and contains(text(), ' {flow_name} ')]/preceding::a[1]").click()
        except NoSuchElementException:
            logger.warning(f"Flow {flow_name.upper()} does not exist, creating flow {flow_name}")
            flow_id = self.create_flow(service_id, logic_flow, construct_value)
            
        self.wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")
         # Retrieve Flow ID
        flow_id_element = nf.FLOW_ID_PROD if "10.25" in self.wd.driver.current_url else nf.FLOW_ID_TESTBED
        self.wd.wait_until_element("xpath", flow_id_element, "visible")

        flow_id = self.wd.driver.find_element(By.XPATH, flow_id_element).text
        logger.info(f"Flow ID Retrieved: {flow_id}")
        logger.info(f"Flow {flow_name.upper()} Successfully Define")
        return flow_id

    def handle_flow(self, row_data, logic_flow, step_type):
        step_and_flow_construct_val = row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT].lower()
        wallet = row_data[nf.NF_INDEX_WALLET]
        tackon_lower = row_data[nf.BS_INDEX_TACKON].lower()
        logger.info(f"Currently in {logic_flow.capitalize()} Flow")
        #flow_type = "charge" if "charge" in step_type else "extend" if "extend" in step_type else step_type
        
        # assign flow_type based on step_type one word only which requires for flow mappings
        flow_type = {"in_charge": "charge", "extend_charge": "charge", "extend_first_expiry": "extend", "check_has_subscription": "check"}.get(step_type, step_type)
        print(f"Flow type = {flow_type}")
        flow_map = self.get_flow_map(flow_type, logic_flow, step_and_flow_construct_val, wallet, tackon_lower)
        logger.info(f"Final Flow map: {flow_map}")

        for from_step, to_step in flow_map:
            self.flow.define_stepfrom_stepto(from_step, to_step)

    # Function handles flow serivce.
    def process_fallback_flow(
        self, logic_flow, service_id, row_data, step_type
    ):
        # Declare initial variables
        flow_name = {"double": "DOUBLE_PROVISION", "extend": "EXTEND_PROVISION"}.get(logic_flow, "PROVISION")
        step_type_lower = step_type.lower()
        logic_flow = logic_flow.lower()

        # Redirect to Edit flow page using service id
        flow_id = self.redirect_to_edit_flow(service_id, flow_name, logic_flow, row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT])
        logger.info(f"Flow defining path: {step_type}")

        # Handle defining Flow path step from = step to 
        self.handle_flow(row_data, logic_flow, step_type_lower)

        # Call function to assign flow id to default and API flow
        self.nf_assign_bulk_service_flow(logic_flow, service_id, flow_id)

    def create_flow(self, service_id, logic_flow, construct_value):
        
        # Navigate to the add flow page
        url = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=flows&op=add&svc_id={service_id}&details_id={service_id}"
        self.wd.redirect_to_page(url, nf.NF_ADD_BTN_INPUT)
        construct_value_lower = construct_value.lower()
        flow_name = {
            "double": "DOUBLE_PROVISION",
            "extend": "EXTEND_PROVISION",
        }.get(logic_flow, "PROVISION")

        first_step_type = "EXTEND_FIRST_EXPIRY" if "opm" in construct_value_lower else "HLR_SET_VSSR_TPLID" if "prepaid trigger" in construct_value_lower or "prepaid main" in construct_value_lower else "SDM_POSTPAID_CREATE_SUBSCRIBER" if "postpaid trigger" in construct_value_lower or "postpaid main" in construct_value_lower else "EXTEND_CHARGE" if "extend" in logic_flow.lower() else "IN_CHARGE"
        
        logger.info(f"Assigning First Step: {first_step_type}")
        # Fill Flow form
        self.wd.perform_action("name", nf.NF_FLOWS_NAME_INPUT, "sendkeys", flow_name)
        self.wd.perform_action(
            "xpath",
            f"//select[@name='first_step_id']//option[contains(text(), '{first_step_type}')]",
            "click"
        )
        self.wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")

        # Retrieve Flow ID
        flow_id_element = nf.FLOW_ID_PROD if "10.25" in self.wd.driver.current_url else nf.FLOW_ID_TESTBED
        self.wd.wait_until_element("xpath", flow_id_element, "visible")

        flow_id = self.wd.driver.find_element(By.XPATH, flow_id_element).text
        logger.info(f"Flow ID Retrieved: {flow_id}")
        logger.info(f"Flow {flow_name.upper()} Successfully Define")
        return flow_id

    def nf_assign_bulk_service_flow(self, flow_key, bs_service_id, flow_id):
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
        self.wd.driver.get(
            f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=bulk_services&op=edit&id={bs_service_id}"
        )
        self.wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")

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

        self.wd.submit_form_and_wait_for_success(
            "xpath", nf.NF_ADD_BTN_INPUT, nf.SUCCESS_MESSAGE
        )
