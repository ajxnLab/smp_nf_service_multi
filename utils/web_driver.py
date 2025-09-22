from utils.logger import logger
import platform
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from requests.exceptions import ReadTimeout
import time

# logger = logging.getLogger(__name__)

# Optional: You can set this globally or make it a class attribute
DEFAULT_WAIT_TIME = 60
MAX_RETRIES = 2
# Mapping of string locator types to Selenium By types
LOCATOR_MAP = {
    "id": By.ID,
    "name": By.NAME,
    "classname": By.CLASS_NAME,
    "xpath": By.XPATH,
    "css": By.CSS_SELECTOR,
    "tag": By.TAG_NAME,
    "link": By.LINK_TEXT,
    "partial_link": By.PARTIAL_LINK_TEXT,
}

# Mapping of string wait conditions to Selenium EC functions
WAIT_CONDITION_MAP = {
    "presence": EC.presence_of_element_located,
    "visible": EC.visibility_of_element_located,
    "clickable": EC.element_to_be_clickable,
}


class WebDriver:

    def __init__(self):
        self.driver = self.create_chrome_driver()

    def create_chrome_driver(self):
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            options.page_load_strategy = "none"
            options.add_experimental_option("detach", True)
            options.add_argument("--no-sandbox")
            options.add_argument("--ignore-ssl-errors=yes")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--log-level=3")
            #options.add_argument("--headless")

            if platform.system() == "Linux":
                options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")

            service = Service(ChromeDriverManager().install())
            chrome_driver = webdriver.Chrome(service=service, options=options)
            return chrome_driver

        except Exception as e:
            logger.info(f"Failed to create chrome driver. Error: {e}")
            raise

    # Function to wait until element to be visible.
    def wait_until_element(
        self,
        locator_type: str,
        element_value: str,
        condition: str,
        timeout: int = DEFAULT_WAIT_TIME,
    ):
        try:
            by_type = LOCATOR_MAP.get(locator_type.lower())
            if by_type is None:
                raise ValueError(f"Invalid locator type: {locator_type}")

            wait_condition = WAIT_CONDITION_MAP.get(condition.lower())
            if wait_condition is None:
                raise ValueError(f"Invalid wait condition: {condition}")

            driver_wait = WebDriverWait(self.driver, timeout)
            return driver_wait.until(wait_condition((by_type, element_value)))

        except TimeoutException as e:
            logger.warning(
                f"Timeout waiting for element: ({locator_type}, {element_value}) with condition '{condition}'"
            )
            raise

        except NoSuchElementException as e:
            logger.warning(
                f"Element not found! Locator: ({locator_type}, {element_value})\nERROR: {e}"
            )
            raise

        except Exception as e:
            logger.exception(
                f"Unexpected error occurred while waiting for element: ({locator_type}, {element_value})\nERROR: {e}"
            )
            raise

    # Method to find element with action.
    def perform_action(self, locator, element, action, variable=None, wait_time=0, parent=None, check_alert=False, alert_timeout=2):
        try:
            by = LOCATOR_MAP.get(locator.lower())
            if not by:
                raise ValueError(f"Unsupported locator type: {locator}")

            # Determine search context: parent or driver
            search_context = parent if parent else self.driver

            # Wait if requested
            if wait_time > 0:
                element = WebDriverWait(search_context, wait_time).until(
                    EC.presence_of_element_located((by, element))
                )
            else:
                element = search_context.find_element(by, element)

            actions = ActionChains(self.driver)

            if action == "click":
                element.click()
            elif action == "sendkeys":
                element.clear()  # optional: clear before typing
                element.send_keys(variable)
            elif action == "executescript":
                # Set value instantly for speed
                self.driver.execute_script("arguments[0].value = arguments[1];", element, variable)
                # Optional: fire events so page reacts like it was typed
                self.driver.execute_script("""
                    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                """, element)
            elif action == "find":
                logger.info(f"Element found: {locator}={element}")
                return element  # Just return the element
            elif action == "clear":
                element.clear()
            elif action == "hover":
                actions.move_to_element(element).perform()
            elif action == 'select':
                target_text = " ".join(variable.strip().split())

                # Find dropdown element if locator string was given
                if not isinstance(element, WebElement):
                    dropdown_el = search_context.find_element(by, element)
                else:
                    dropdown_el = element
                dropdown_el.click()
                WebDriverWait(dropdown_el, 10).until(
                    lambda el: el.find_element(
                        By.XPATH, f".//option[normalize-space(.)='{target_text}']"
                    ).is_displayed()
                )

                select_element = Select(dropdown_el)
                options = [opt.text.strip() for opt in select_element.options]
                matched_option = next((opt for opt in options if opt.lower() == target_text.lower()), None)

                if matched_option:
                    self.select_value = 1
                    select_element.select_by_visible_text(matched_option)
                else:
                    self.select_value = 0
                    logger.info(f"Value not found in dropdown: {variable.strip()}")
                            
                return matched_option is not None


            elif action == 'checkbox':
                if str(variable).lower() in ['yes', 'true', '1'] and not element.is_selected():
                    element.click()
                elif str(variable).lower() in ['no', 'false', '0'] and element.is_selected():
                    element.click()

        except TimeoutException:
            logger.error(f"Timed out after {wait_time}s waiting for element: {locator}={element}")
            return None  # or False to indicate failure
        except NoSuchElementException as e:
            logger.error(f"Element not found: {locator}={element}. ERROR: {e}")
            raise
        except Exception as e:
            logger.error(f"Action '{action}' failed on element: {locator}={element}. ERROR: {e}")
            raise

    def stop_process(self, second=False):
        msg = "Terminating bot secondary process.." if second else "Terminating bot main process.."
        self.driver.quit()
        logger.info(msg)
        sys.exit()

    def redirect_to_page(self, url, xpath_btn_element=None):
        max_retries = 5
        # original_timeout = self.driver.timeouts.page_load
        logger.info(f"Redirecting to Page {url}")

        # We'll set a higher page load timeout to not interfere
        # self.driver.set_page_load_timeout(80)

        for attempt in range(1, max_retries + 1):
            logger.info(f"Loading page... (Attempts {attempt}/{max_retries})")

            try:
                load_start = time.time()
                self.driver.get(url)
                if not xpath_btn_element:
                    return

                self.wait_until_element("xpath", xpath_btn_element, "clickable")
                logger.info("Site has been reached")
                break  # success

            except TimeoutException as e:
                logger.warning(
                    f"Attempt {attempt} timed out (Selenium timeout), refreshing..."
                )
                self.driver.execute_script("window.stop();")
                self.driver.refresh()

            except Exception as e:
                logger.warning(f"Unexpected error: {e}")
                # If stuck too long, stop the load manually
                if time.time() - load_start > 30:
                    logger.warning("Manually stopping load due to long hang.")
                    self.driver.execute_script("window.stop();")
                if attempt == max_retries:
                    logger.error("Max retries reached. Giving up.")
                    raise Exception(
                        f"Page load failed after {max_retries} attempts\nERROR: {e}"
                    )
                else:
                    logger.info("Refreshing and retrying...")
                    self.driver.refresh()

            # finally:
            #     self.driver.set_page_load_timeout(original_timeout)

    # currently using
    def submit_form_and_wait_for_success(
        self,
        locator,
        element_button,
        success_xpath,
        max_retries=2,
        wait_timeout=120,
        max_total_time=180,
        skip=False,
    ):
        start_time = time.time()
        logger.info(f"Submitting button...")
        by_type = LOCATOR_MAP.get(locator.lower())
        button = self.driver.find_element(by_type, element_button)
        #self.driver.execute_script("arguments[0].click();", button)
        button.click()

        for attempt in range(1, max_retries + 1):
            try:
                elapsed = time.time() - start_time
                if elapsed > max_total_time:
                    raise TimeoutException(
                        f"Total time {elapsed:.1f}s exceeded max {max_total_time}s"
                    )
                #logger.info(f"Polling up to {wait_timeout}s for success message...")
                logger.info(
                    f"Fetching/Validating return message.. (Attempts {attempt}/{max_retries})"
                )
                success_found = False
                poll_start = time.time()

                while time.time() - poll_start < wait_timeout:
                    try:
                        element_success = self.driver.find_element(
                            By.XPATH, success_xpath
                        )
                        if element_success.is_displayed():
                            logger.info("Return message found!")
                            self.driver.execute_script(
                                "window.stop();"
                            )  # Stop loading ASAP
                            logger.info(f"Return message text = {element_success.text}")
                            return element_success.text

                    except (Exception, TimeoutError, ReadTimeout):
                        # If Element not found yet, catch exception, pass, then re-loop
                        pass

                    time.sleep(5)

                logger.warning(f"Attempt {attempt} timed out waiting for success.")
                self.driver.execute_script("window.stop();")
                if attempt < max_retries:
                    logger.warning("Refreshing page for next attempt...")
                    self.driver.refresh()
                    time.sleep(2)
                else:
                    logger.error("Max retries reached. No success message found.")
                    raise TimeoutException(
                        "Failed to detect success message after retries."
                    )

            except Exception as e:
                logger.warning(f"Unexpected error on attempt {attempt}: {e}")
                self.driver.execute_script("window.stop();")
                if attempt < max_retries:
                    self.driver.refresh()
                    time.sleep(2)
                else:
                    raise

    def submit_form(
        self,
        locator: str,
        element_button: str,
        success_xpath: str,
        wait_timeout: int = 120,
        ) -> str:
        """
        Submit form and wait for success message with simple timeout handling
        
        Args:
            locator: Type of locator (xpath, id, etc)
            element_button: Button element to click
            success_xpath: XPath to success message element
            wait_timeout: Timeout for waiting for success message
            
        Returns:
            str: Success message text
            
        Raises:
            TimeoutException: When timeout occurs during form submission
        """
        try:
            # Find and click submit button
            by_type = LOCATOR_MAP.get(locator.lower())
            button = self.driver.find_element(by_type, element_button)
            # self.driver.execute_script("arguments[0].click();", button)
            button.click()

            logger.info("Waiting for success message...")
            poll_start = time.time()

            # Poll for success message
            while time.time() - poll_start < wait_timeout:
                try:
                    element_success = self.driver.find_element(By.XPATH, success_xpath)
                    if element_success.is_displayed():
                        logger.info("Success message found!")
                        logger.info(f"Return message text = {element_success.text}")
                        self.driver.execute_script("window.stop();")
                        return element_success.text

                except NoSuchElementException:
                    time.sleep(3)
                    continue

            # Timeout occurred
            logger.warning(f"Timeout after {wait_timeout}s waiting for success message")
            raise TimeoutException("Failed to detect success message")

        except Exception as e:
            logger.error(f"Form submission failed: {str(e)}")
            self.driver.execute_script("window.stop();")
            raise TimeoutException(f"Form submission failed: {str(e)}")
    
    def wait_staleness_of(self, xpath_element, timeout=10):
        try:
            element = self.driver.find_element(By.XPATH, xpath_element)
            self.driver.refresh()
            WebDriverWait(self.driver, timeout).until(EC.staleness_of(element))
            self.wait_until_element("xpath", xpath_element, "clickable")
        except TimeoutException:
            logger.warning("Timeout waiting for element to become stale.")
            raise

    #SMP

    def wait_until_element_with_refresh(self, locator_type: str, element_value: str, condition: str, timeout: int = DEFAULT_WAIT_TIME, max_retries: int = MAX_RETRIES):
        """
        Waits for an element up to 'timeout' seconds.
        If not found, refreshes the page and retries (max_retries times).
        """
        by_type = LOCATOR_MAP.get(locator_type.lower())
        if by_type is None:
            raise ValueError(f"Invalid locator type: {locator_type}")

        wait_condition = WAIT_CONDITION_MAP.get(condition.lower())
        if wait_condition is None:
            raise ValueError(f"Invalid wait condition: {condition}")

        for attempt in range(max_retries + 1):  # initial try + retries
            try:
                driver_wait = WebDriverWait(self.driver, timeout)
                return driver_wait.until(wait_condition((by_type, element_value)))

            except TimeoutException:
                logger.warning(f"[Try {attempt + 1}] Element not found after {timeout} seconds.")
                if attempt < max_retries:
                    logger.info("Refreshing the page and retrying...")
                    self.driver.refresh()
                    time.sleep(3)  # slight delay to let page load
                else:
                    logger.warning(f"Element not found after {max_retries + 1} attempts.")
                    return None

            except Exception as e:
                logger.exception(f"Unexpected error occurred: {e}")
                return None
    
    # Handle different field types
    def field_types(self, locator, locator_value, input_type, value):
        try:
            by = LOCATOR_MAP.get(locator.lower())
            if not by:
                raise ValueError(f"Unsupported locator type: {locator}")

            element = self.driver.find_element(by, locator_value)

            if input_type == 'text' or input_type == 'textarea':
                element.clear()
                element.send_keys(str(value))
            elif input_type == 'checkbox':
                if str(value).lower() in ['yes', 'true', '1'] and not element.is_selected():
                    element.click()
                elif str(value).lower() in ['no', 'false', '0'] and element.is_selected():
                    element.click()
            elif input_type == 'select':
                select_element = Select(element)

                # Use JavaScript to get the trimmed options quickly
                options = self.driver.execute_script("""
                    let select = arguments[0];
                    return Array.from(select.options).map(o => o.text.trim());
                """, element)

                # Match the value ignoring case and extra whitespace
                matched_option = next((opt for opt in options if opt.lower() == value.strip().lower()), None)

                if matched_option:
                    self.select_value = 1
                    select_element.select_by_visible_text(matched_option)
                    return True
                else:
                    self.select_value = 0
                    logger.info(f"Value not found in dropdown: {value.strip()}")
                    return False

        except Exception as e:
            logger.info(f"Failed to handle field {value}: {e}")

    def get_element_content(self, locator: str, locator_value: str, mode: str = "auto") -> str | None:
        """
        Retrieves content (visible text or input value) from an element.

        Args:
            locator: The locator type (e.g., 'id', 'xpath', 'class_name', etc.)
            locator_value: The locator value for finding the element.
            mode: 'text' to force element.text,
                'value' to force get_attribute("value"),
                'auto' (default) to pick based on element tag.

        Returns:
            The extracted text/value, or None if not found.
        """
        try:
            by = LOCATOR_MAP.get(locator.lower())
            if not by:
                raise ValueError(f"Unsupported locator type: {locator}")

            element = self.driver.find_element(by, locator_value)

            if mode == "text":
                return element.text.strip() or None
            elif mode == "value":
                return element.get_attribute("value") or None
            else:  # auto mode
                tag = element.tag_name.lower()
                if tag in ["input", "textarea", "select"]:
                    return element.get_attribute("value") or None
                else:
                    return element.text.strip() or None

        except NoSuchElementException:
            logger.warning(f"Element not found: {locator} = {locator_value}")
            return None
        except Exception as e:
            logger.error(f"Failed to get content from element {locator}={locator_value}: {e}")
            return None

            
    def wait_any_of(
            self,
            locators,
            timeout=30,
            condition="visible",
            retries=3,
            refresh_on_fail=True,
            post_refresh_action=None,
            wait_target_locator_type = None,
            wait_target_value = None,
            url=None
        ):
            """
            Wait until the first of multiple locators appears.

            Args:
                locators: list of tuples (locator_type, locator_value)
                timeout: wait time per attempt
                condition: "visible" or "present"
                retries: how many times to retry with refresh
                refresh_on_fail: whether to refresh page on failure

            Returns:
                (locator_type, locator_value, element)
            """
            for attempt in range(1, retries + 1):
                try:
                    wait = WebDriverWait(self.driver, timeout)

                    wrapped_conditions = []
                    for loc_type, loc_value in locators:
                        by = LOCATOR_MAP.get(loc_type.lower())
                        if not by:
                            raise ValueError(f"Unsupported locator type: {loc_type}")

                        if condition == "visible":
                            base_cond = EC.visibility_of_element_located((by, loc_value))
                        else:
                            base_cond = EC.presence_of_element_located((by, loc_value))

                        def wrapped(driver, bc=base_cond, lt=loc_type, lv=loc_value):
                            elem = bc(driver)
                            if elem:
                                return (lt, lv, elem)
                            return False

                        wrapped_conditions.append(wrapped)

                    result = wait.until(EC.any_of(*wrapped_conditions))
                    return result  # (loc_type, loc_value, element)

                except TimeoutException:
                    logger.warning(f"wait_any_of attempt {attempt}/{retries} timed out.")
                    # Handle confirm form resubmission if visible
                    try:
                        alert = self.driver.switch_to.alert
                        logger.info("Confirm Form Resubmission alert detected — accepting...")
                        alert.accept()  # or alert.dismiss()
                    except Exception:
                        pass

                    if refresh_on_fail and attempt < retries:
                        logger.info("Refreshing page and retrying...")
                        self.driver.refresh()
                        time.sleep(2)  # let DOM settle

                        if wait_target_locator_type and wait_target_value:
                            try:
                                if url:
                                    self.redirect_to_page(url)
                                    self.wait_until_dom_loaded()

                                self.wait_until_element(wait_target_locator_type, wait_target_value, "visible")
                                logger.info("Page element visible after refresh.")
                            except Exception as wait_err:
                                last_error = wait_err 
                                logger.warning(f"Failed to wait for element after refresh: {wait_err}")
                                continue

                        if post_refresh_action:
                            try:
                                logger.info("Post-refresh applying.")
                                post_refresh_action()
                                logger.info("Post-refresh input re-applied.")
                            except Exception as input_err:
                                logger.error(f"Failed to reapply input after refresh: {input_err}")
                        
                        continue
                    else:
                        logger.error(
                            f"wait_any_of failed after {retries} attempts.\n"
                            f"Locators tried: {locators}\n"
                            f"Last error: {last_error}"
                        )
                        raise

    def wait_until_dom_loaded(self, timeout=60):
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
    )        

    def stop_process_wd(self):
        self.driver.quit()           