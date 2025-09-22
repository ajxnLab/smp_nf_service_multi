# from utils.logger import setup_logger
from utils.logger import logger
from nf_services.nf_constants import NfConstants
from utils.env_loader import get_env_variable
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
import time


# logger = setup_logger(service_name=f"NF {__name__}")

from config.config import nf


# Function to define the created bulk service to simple service group
def define_bs_simple_service_group(bs_service_id, construct_value, wd, retry=1, max_retries=2):
    try:
        if 'prepaid ctl with unli sms and unli voice' in construct_value.lower() or 'prepaid opm with unli sms and unli voice' in construct_value.lower():
            logger.warning("Skipping Simple Service Group based on construct flow")
            return
        rpa_remark_ssg = {}
        logger.info("STARTING SIMPLE SERVICE GROUP PROCESS")
        # Redirect to Simple Service Group Details Page
        logger.info("Redirecting to Simple Service Group Detail Page...")
        ssg_id = "4097" if "postpaid" in construct_value.lower() else "1"
        ssg_name = "POSTPAID" if ssg_id == "4097" else "DATA"
        url = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=simple_service_groups&op=details&id={ssg_id}"
        wd.redirect_to_page(url, nf.SSG_ADD_BTN_ACCESS_CODE)
        wd.wait_until_element(
            "xpath", nf.SSG_ADD_BTN_ACCESS_CODE, "clickable", timeout=180
        )
        try:
            wd.driver.find_element(By.XPATH, f"//td[@align='left' and starts-with(normalize-space(text()), '{bs_service_id}')]")
            #("xpath", f"//td[@align='left' and contains(text(), '{bs_service_id}')]", "visible", timeout=120)
            logger.warning(f"Service id {bs_service_id} already defined in Simple Service Group - {ssg_name}")
            return {}
        except NoSuchElementException:
            pass

        # Select Current Bulk Service ID
        wd.perform_action(
            "xpath",
            f"//select[@name='simple_service_id']//option[@value='{bs_service_id}']",
            "click",
        )

        # Input Priority Field = Default Value 1
        wd.perform_action("name", nf.SSG_PRIORITY_INPUT, "sendkeys", 1)

        try:
            # Click Add Button
            wd.perform_action("xpath", nf.SSG_ADD_BTN_SIMPLE_SERVICES, "click")
            logger.info(
                f"Defining service id to simple service group data..."
            )
            #wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable", timeout=60)
            # Validate if service id already added
            wd.wait_until_element("xpath", f"//td[@align='left' and contains(text(), '{bs_service_id}')]", "visible", timeout=120)
            logger.info(
                f"Bulk Service Id {bs_service_id} Successfully Defined in Simple Service Group '{ssg_name}' With Priority 1"
            )
            return {}
        except TimeoutException:
            logger.warning(
                "Timed out waiting for confirmation. Skipping further actions.."
            )
            wd.driver.execute_script("window.stop();")
            return {}
    except NoSuchElementException as e:
        # //td[@align='left' and contains(text(), '12151')] # For validation if already defined for future enhancement
        rpa_remark_ssg["SSG"] = "Failed - bulk service id may not listed in dropdown option"
        logger.error(f"Element not found, unable to define bulk service to Simple Service Group, please confirm input if step and flow construct includes data\nERROR: {e}")
        return rpa_remark_ssg
        
    except Exception as e:
        rpa_remark_ssg["SSG"] = "Failed"
        logger.error(
        f"An error has occurred while defining the bulk service in simple service group\nERROR: {e}"
        )
        return rpa_remark_ssg
        
