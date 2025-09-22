from selenium.webdriver.common.by import By
from utils.env_loader import get_env_variable
from utils.logger import logger
from nf_services.nf_constants import NfConstants
import time

from config.config import nf

class ModifyStepService:
    def __init__(self, webdriver, gsheet):
        self.wd = webdriver
        self.gs = gsheet

    # Modification to add Extend Param for EXTEND FIRST EXPIRY (EXTEND FLOW ONLY)
    def modify_extend_first_expiry(self, bs_row_data):
        try:
            service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]
            extend_amount = bs_row_data[nf.NF_INDEX_EXTEND_AMOUNT]
            extend_duration = bs_row_data[nf.NF_INDEX_EXTEND_DURATION_IN_DAYS]
            # Redirection to Edit page for Extend First Expiry using its old step id
            logger.info(f"STARTING MODIFICATION FOR EXTEND FIRST EXPIRY")

            # Redirect first to Edit Bulk service page
            base_url = get_env_variable("WEBTOOL_BASE_URL")
            self.wd.redirect_to_page(f"{base_url}/nf/index.php?mod=bulk_services&op=details&id={service_id}", nf.BS_EDIT_PAGE_REMINDER_MSG_BTN)

            # Redirect to existing EXTEND FIRST EXPIRY step details
            self.wd.driver.find_element(By.XPATH, f"//td[@align='left' and contains(text(), ' EXTEND_FIRST_EXPIRY ')]/preceding::a[1]").click()
            self.wd.wait_until_element(
                "xpath", nf.EDIT_STEP_INPUT_FIELD_PARAM, "visible"
            )
            logger.info(f"Current Page: Edit Step Details")

            # Input Amount Field for Extend Flow
            logger.info("Adding Param Values for existing Extend First Expiry...")
            logger.info(f"Input Extend Param: {extend_amount}")
            self.wd.perform_action(
                "xpath",
                nf.EDIT_STEP_INPUT_FIELD_PARAM,
                "sendkeys",
                extend_amount,
            )
            logger.info(f"Input Extend Duration: {extend_duration}")
            self.wd.perform_action(
                "xpath",
                nf.EDIT_STEP_INPUT_FIELD_DURATION,
                "sendkeys",
                extend_duration,
            )

            # Click 'Add' Button
            logger.info("Saving changes...")
            self.wd.perform_action("xpath", nf.NF_STEP_ADD_BTN_INPUT, "click")

            # Trigger Time sleep, helps to finish loading edit webpage..
            time.sleep(2)
            self.wd.wait_until_element("xpath", f"//td[@align='left' and contains(text(), ' {extend_amount} ')]", "visible")
            logger.info("Param Successfully Added in EXTEND FIRST EXPIRY")

        except Exception as e:
            logger.info(
                f"An error has occurred while modifying EXTEND FIRST EXPIRY\nERROR: {e}"
            )