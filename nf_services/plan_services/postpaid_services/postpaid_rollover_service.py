from utils.env_loader import get_env_variable
from utils.logger import logger
from nf_services.nf_constants import NfConstants
from selenium.webdriver.common.by import By

from config.config import nf

# Function to Define Gyro Command
def create_dummy_step_type(bs_service_id, wd):
    try:
        logger.info("DEFINING STEP TYPE")

        # Declare variable
        url = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
        wd.redirect_to_page(url, nf.NF_ADD_BTN_INPUT)

        logger.info("Filling up step fields..")
        logger.info(f"Input Name: DUMMY")
        wd.perform_action("xpath", nf.NF_INPUT_NAME, "sendkeys", "DUMMY")
        logger.info(f"Select Step Type: DUMMY")
        wd.perform_action("xpath", "//option[contains(text(), 'DUMMY') and @value='71']", "click")
        wd.perform_action("name", nf.NF_STEPS_RETRY_INPUT, "sendkeys", 3)

        # Click Add button
        wd.submit_form_and_wait_for_success("xpath", nf.NF_ADD_BTN_INPUT, nf.STEP_SUCCESS_MESSAGE)
        logger.info(f"Step type DUMMY created successfully")
        return True
    except Exception as e:
        logger.info(
            f"An error has occurred while defining access code\nERROR: {e}"
        )
        return False

def nf_assign_bulk_service_flow(bs_service_id, flow_id, wd, dummy_service=False):
    try:
        # Assign flow and api flow depends if there's a double/extend/none flow
        logger.info(
            f"Assigning Default/Double Flow and API/API Double Flow in Bulk Services For: {bs_service_id}"
        )

        # Redirect to Bulk Service Edit page for current service id
        wd.driver.get(
            f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=bulk_services&op=edit&id={bs_service_id}"
        )
        wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")

        # Input Default Flow Dropwdown
        logger.info(
            f"Assigning Default Flow: {flow_id} (PROVISION)"
        )
        wd.perform_action(
            "xpath",
            f"//select[@name='default_flow']//option[@value='{flow_id}']",
            "click",
        )
    
        # Input API Flow Dropdown
        logger.info(
            f"Assigning API Flow: {flow_id} (PROVISION)"
        )
        wd.perform_action(
            "xpath",
            f"//select[@name='api_flow']//option[@value='{flow_id}']",
            "click",
        )

        # If step and flow construct is DUMMY SERVICE, just save the form after assigning default and api flow then return
        if dummy_service:
            wd.submit_form_and_wait_for_success("xpath", nf.NF_ADD_BTN_INPUT, nf.SUCCESS_MESSAGE)
            return
    
        # Input Double Flow Dropwdown
        logger.info(
            f"Assigning Double Flow: {flow_id} (PROVISION)"
        )
        wd.perform_action(
            "xpath",
            f"//select[@name='double_flow']//option[@value='{flow_id}']",
            "click",
        )

        # Input API Double Flow Dropdown
        logger.info(
            f"Assigning API Double Flow: {flow_id} (PROVISION)"
        )
        wd.perform_action(
            "xpath",
            f"//select[@name='api_double_flow']//option[@value='{flow_id}']",
            "click",
        )

        # Handle after editing form. Stop loading the page if its taking time to load and doesn't need to get the element success message...
        # Click Update button
        # wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")

        wd.submit_form_and_wait_for_success(
            "xpath", nf.NF_ADD_BTN_INPUT, nf.SUCCESS_MESSAGE
        )

    except Exception as e:
        logger.info(
            f"An error has occurred while assigning flow for Postpaid Rollover\nERROR: {e}"
        )
            

def define_flow_dummy(bs_row_data, wd):
    try:
        construct_value = bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT]
        bs_service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]

        logger.info(f"Defining Flow for {construct_value}")
        # Navigate to the add flow page
        url = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=flows&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
        wd.redirect_to_page(url, nf.NF_ADD_BTN_INPUT)

        # Fill Flow form
        wd.perform_action("name", nf.NF_FLOWS_NAME_INPUT, "sendkeys", "PROVISION")
        wd.perform_action(
            "xpath",
            f"//select[@name='first_step_id']//option[contains(text(), 'DUMMY')]",
            "click"
        )
        wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
        logger.info("SERVICE FLOW SUCCESSFULLY CREATED!")

        # Retrieve Flow ID
        #flow_id_element = nf.FLOW_ID_PROD if "10.25" in wd.driver.current_url else nf.FLOW_ID_TESTBED
        logger.info("Fetching flow ID...")
        wd.wait_until_element("xpath", nf.FLOW_ID_ELEMENT, "visible")
        flow_id = wd.driver.find_element(By.XPATH, nf.FLOW_ID_ELEMENT).text
        logger.info(f"Flow ID Retrieved: {flow_id}")
        wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")

        # Helper: safely define a step
        logger.info(f"FLOW SUCCESSFULLY DEFINED FOR = {construct_value}")
        
        # Assign flow to bulk service
        is_dummy_service = True if "dummy" in construct_value.lower() else False
        nf_assign_bulk_service_flow(bs_service_id, flow_id, wd, is_dummy_service)
        return {}
    except Exception:
        logger.error("Unexpected error while creating step dummy")
        return {"FLOW": "Failed"}