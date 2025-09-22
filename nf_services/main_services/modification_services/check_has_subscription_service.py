from typing import Dict, Optional
from utils.env_loader import get_env_variable
from utils.logger import logger
from nf_services.nf_constants import TackOn
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from config.config import nf

class ServiceIdExistsException(Exception):
    """Custom exception for when service ID already exists"""
    pass

def add_service_id_to_check_has(wd, gs, bs_row_data, tackon_active_ids) -> Optional[Dict]:
        """Execute process for CHECK HAS SUBSCRIPTIONS modification"""
        global check_has_failed_ids
        bs_service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]
        tackon_value_lower = bs_row_data[nf.BS_INDEX_TACKON].lower()
        #tackon_active_ids = bs_row_data[nf.BS_INDEX_CHECK_HAS_IDS]
        check_has_failed_ids = []
        try:
            if tackon_value_lower != TackOn.CHECK_HAS_OTHER.value or not tackon_active_ids:
                if tackon_value_lower == "none": return
                msg = "Validation input error, no active service ids to add for CHECK HAS SUBSCRIPTIONS, please check input, skipping process.." if not tackon_active_ids else "Tack-On option 'Add This Service to Other Check-Has Logic' is not selected, skipping process.."
                logger.warning(msg)
                return
            
            logger.info("STARTING CHECK HAS SUBSCRIPTIONS PROCESS => 'Add This Service to Other Check-Has Logic'")

            # Convert Check has ids from string to tuple
            list_active_service_id = [x.strip() for x in tackon_active_ids.split(",") if x.strip()]
            if list_active_service_id:
                _process_select_active_subscriptions(wd, bs_service_id, list_active_service_id)
                if check_has_failed_ids:
                    logger.warning(f"List of failed CHECK HAS SUBSCRIPTION Service IDs: {check_has_failed_ids}")
                    raise

            logger.info(f"CHECK HAS SUBSCRIPTIONS Process Completed for Bulk Service ID: {bs_service_id}")
            return None
            
        except Exception as e:
            logger.error(f"Catch unexpected error of list of failed ids 'CHECK HAS SUBSCRIPTION': {e}")
            converted_ids = ', '.join(check_has_failed_ids)
            final_ids = f"({converted_ids})"
            return final_ids
        
# def _process_select_active_subscriptions(wd, bs_service_id, list_active_service_id):
#     """Select step params for CHECK HAS SUBSCRIPTIONS"""
#     logger.info(f"List of active service id/ids to be process: {list_active_service_id}")
#     try:
#         for active_id in list_active_service_id: 
#             try:
#                 logger.info(f"Adding bulk service id: {bs_service_id} to Check Has id: {active_id}")
#                 url = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=bulk_services&op=details&id={active_id}"
#                 step_id = _redirect_and_validate_to_check_has(wd, url)
#                 if not step_id:
#                     logger.error(f"Failed to redirect to Check Has Subscription page for Check Has id: {active_id} CHECK_HAS_SUBSCRIPTION does not exist")
#                     check_has_failed_ids.append(active_id)
#                     continue
#                 xpath_bulk_service_id = f"//select[@name='param_check_has_subs_service']//option[@value='{bs_service_id}']"
#                 logger.info(f"Adding bulk service id: {bs_service_id} to step params of ({step_id}) CHECK_HAS_SUBSCRIPTION")
#                 wd.wait_until_element("xpath", xpath_bulk_service_id, "visible")
#                 wd.wait_until_element("xpath", nf.ADD_BTN_INPUT_2, "clickable")
#                 wd.driver.find_element(By.XPATH, xpath_bulk_service_id).click()
#                 wd.driver.find_element(By.XPATH, nf.ADD_BTN_INPUT_2).click()
#                 wd.wait_until_element("xpath", f"//td[@align='left' and normalize-space(text())='{bs_service_id}']", "visible")
#                 logger.info(f"Bulk Service Id: {bs_service_id} successfully added in Check Has id {active_id} CHECK_HAS_SUBSCRIPTION")
                
#             except TimeoutException as e:
#                 """"If the submit button is not loading properly or taking too long to be visible/clickable, retry process adding the service id"""
#                 logger.warning(f"Submit button is not loading properly, retrying..")
#                 logger.info(f"2nd Attempt: Adding bulk service id: {active_id} to step params..")
#                 wd.wait_until_element("xpath", nf.ADD_BTN_INPUT_2, "clickable")
#                 wd.driver.find_element(By.XPATH, xpath_bulk_service_id).click()
#                 wd.driver.find_element(By.XPATH, nf.ADD_BTN_INPUT_2).click()
#                 wd.wait_until_element("xpath", f"//td[@align='left' and normalize-space(text())='{active_id}']", "visible")
#                 logger.info(f"Bulk Service Id: {bs_service_id} successfully added in Check Has id {active_id} CHECK_HAS_SUBSCRIPTION")
#                 continue
#             except (Exception, NoSuchElementException) as e:
#                 logger.error(f"Unable to add service id '{active_id}' ID Element not found\nERROR:{e}")
#                 continue
        
#     except Exception:
#         logger.error("An error has occurred while adding service id to step params...")
#         raise


def _process_select_active_subscriptions(wd, bs_service_id, list_active_service_id):
    """Select step params for CHECK HAS SUBSCRIPTIONS"""
    logger.info(f"List of active service id/ids to be process: {list_active_service_id}")
    try:
        for active_id in list_active_service_id:
            try:
                logger.info(f"Adding bulk service id: {bs_service_id} to Check Has id: {active_id}")
                url = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=bulk_services&op=details&id={active_id}"
                step_id = _redirect_and_validate_to_check_has(wd, url)
                if not step_id:
                    logger.error(f"Failed to redirect to Check Has Subscription page for Check Has id: {active_id} CHECK_HAS_SUBSCRIPTION does not exist")
                    check_has_failed_ids.append(active_id)
                    continue
                
                xpath_bulk_service_id = f"//select[@name='param_check_has_subs_service']//option[@value='{bs_service_id}']"
                logger.info(f"Adding bulk service id: {bs_service_id} to step params of ({step_id}) CHECK_HAS_SUBSCRIPTION")
                
                try:
                    # First attempt
                    _add_service_to_check_has(wd, xpath_bulk_service_id, bs_service_id, active_id, step_id)
                except ServiceIdExistsException:
                    # Skip to next iteration if service already exists
                    continue
                except TimeoutException:
                    # Second attempt
                    logger.warning("Submit button is not loading properly, retrying..")
                    logger.info(f"2nd Attempt: Adding bulk service id: {active_id} to step params..")
                    try:
                        _add_service_to_check_has(wd, xpath_bulk_service_id, bs_service_id, active_id, step_id)
                    except ServiceIdExistsException:
                        # Skip to next iteration if service already exists
                        continue
                    except TimeoutException:
                        logger.error(f"Second attempt failed - Timeout when adding service id '{active_id}'")
                        check_has_failed_ids.append(active_id)
                        continue
                
                logger.info(f"Bulk Service Id: {bs_service_id} successfully added in Check Has id {active_id} CHECK_HAS_SUBSCRIPTION")
                
            except (Exception, NoSuchElementException) as e:
                logger.error(f"Unable to add service id '{active_id}' ID Element not found\nERROR:{e}")
                check_has_failed_ids.append(active_id)
                continue
        
    except Exception:
        logger.error("An error has occurred while adding service id to step params...")
        raise

def _add_service_to_check_has(wd, xpath_bulk_service_id, bs_service_id, active_id, step_id=None):
    """Helper function to add service to check has subscription"""
    #test_fail_xpath = f"//select[@name='param_check_has_subs_service']//option[@value='32232323']"
    wd.wait_until_element("xpath", xpath_bulk_service_id, "visible")
    wd.wait_until_element("xpath", nf.ADD_BTN_INPUT_2, "clickable")
    try:
        # Check if there's an existing service id in the list
        check_service_id_xpath = f"//td[@align='left' and normalize-space(text())='{bs_service_id}']"
        wd.driver.find_element(By.XPATH, check_service_id_xpath)
        logger.warning(f"Bulk Service ID {bs_service_id} already exists in Check Has id {active_id} = ({step_id}) CHECK_HAS_SUBSCRIPTION, skipping definition.")
        raise ServiceIdExistsException
    except NoSuchElementException:
        # If not, proceed to click and add the service id
        wd.driver.find_element(By.XPATH, xpath_bulk_service_id).click()
        wd.driver.find_element(By.XPATH, nf.ADD_BTN_INPUT_2).click()
        wd.wait_until_element("xpath", check_service_id_xpath, "visible")

def _redirect_and_validate_to_check_has(wd, url):
    step_name = "CHECK_HAS_SUBSCRIPTION"
    xpath_check_has_subscription = f"//td[@align='left' and contains(text(), ' {step_name} ')]/preceding::a[1]"
    # Redirect to Edit Bulk service page
    logger.info(f"Validating if step name {step_name} exists in Edit Bulk Service page")
    wd.redirect_to_page(url, nf.BS_EDIT_PAGE_REMINDER_MSG_BTN)

    # Validate if step name exist in edit page of Bulk Service
    try:
        step_id = wd.driver.find_element(By.XPATH, xpath_check_has_subscription).text.strip()
        wd.driver.find_element(By.XPATH, xpath_check_has_subscription).click()
        wd.wait_until_element("xpath", nf.ADD_BTN_INPUT_2, "clickable")
        logger.info(f"Step ({step_id}){step_name.upper()} exists in Edit Bulk Service page")
        return step_id
    except NoSuchElementException:
        logger.warning(f"Step name {step_name.upper()} does not exist in Edit Bulk Service page")
        return None