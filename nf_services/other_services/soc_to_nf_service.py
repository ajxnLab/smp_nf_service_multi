from utils.logger import logger
from nf_services.nf_constants import NfConstants
from utils.env_loader import get_env_variable
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config.config import nf

def mapping_exists_current_page(service_id, soc_id, wd):
    xpath = f"//tr[td[normalize-space(.)='{soc_id}']]"
    try:
        #wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")
        #xpath = f"//tr[td[normalize-space(.)='{soc_id}'] and td[contains(.,'{service_id}')]]"
        wd.driver.find_element(By.XPATH, xpath)
        return True
    except NoSuchElementException:
        return False

def define_soc_to_nf(service_id, soc_id, wd):
    try:
        logger.info("Processing SOC to NF service mapping..")
        url = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=soc_to_nf_service_mapping"
        wd.redirect_to_page(url, nf.NF_ADD_BTN_INPUT)

        # VALIDATION IF ALREADY EXIST
        # if mapping_exists_current_page(service_id, soc_id, wd):
        #     print("MAP TRUE")
        #     logger.warning(f"SOCID {soc_id} is already mapped to bulk service {service_id}")
        #     return True
        # Proceed with form submission
        logger.info(f"Input SOC ID: {soc_id}")
        wd.perform_action("xpath", "//input[@name='soc_id']", "sendkeys", soc_id)
        
        logger.info(f"Dropdown Bulk Service Id: {service_id}")
        wd.perform_action("xpath", f"//select[@name='bulk_service_id']//option[@value='{service_id}']", "click")

        logger.info("Input Param: DEFAULT")
        wd.perform_action("xpath", "//input[@name='param']", "sendkeys", "DEFAULT")
        #wd.submit_form_and_wait_for_success("xpath", nf.NF_ADD_BTN_INPUT, nf.SUCCESS_MESSAGE)
        wd.driver.find_element(By.XPATH, nf.NF_ADD_BTN_INPUT).click()
        # 2nd VALIDATION
        try:
            WebDriverWait(wd.driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//body[contains(text(), 'violated')]"))
            )
            #wd.wait_until_element("xpath", "//body[contains(text(), 'violated')]", "visible", timeout=5)
            logger.warning(f"SOCID {soc_id} is already mapped.")
            return True
        except (NoSuchElementException, TimeoutException):
            pass
        wd.wait_until_element("xpath", nf.SUCCESS_MESSAGE, "visible", timeout=10)
        logger.info("SOC to NF Service Successfully Defined!")
        return True
    
    except Exception as e:
        logger.warning(f"Something went wrong mapping SOC to NF: {e}")
        return False
