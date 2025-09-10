import platform
from selenium.webdriver.support.ui import Select
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from utils.logger import setup_in_memory_logger

logger,log_stream = setup_in_memory_logger(__name__)

# Optional: You can set this globally or make it a class attribute
DEFAULT_WAIT_TIME = 60

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
        self.select_value = None

    def create_chrome_driver(self):
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            options.add_experimental_option("detach", True)
            options.add_argument("--no-sandbox")
            options.add_argument("--ignore-ssl-errors=yes")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--log-level=3")  
            options.add_argument("--headless")

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
    def wait_until_element(self, locator_type: str, element_value: str, condition: str, timeout: int = DEFAULT_WAIT_TIME):
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
            logger.info(f"Timeout waiting for element: ({locator_type}, {element_value}) with condition '{condition}'\nERROR: {e}")
            raise

        except NoSuchElementException as e:
            logger.info(f"Element not found! Locator: ({locator_type}, {element_value})\nERROR: {e}")
            raise

        except Exception as e:
            logger.exception(f"Unexpected error occurred while waiting for element: ({locator_type}, {element_value})\nERROR: {e}")
            raise

    # Method to find element with action.
    def perform_action(self, locator, element, action, variable=None):
        try:
            by = LOCATOR_MAP.get(locator.lower())
            if not by:
                raise ValueError(f"Unsupported locator type: {locator}")

            element = self.driver.find_element(by, element)
            actions = ActionChains(self.driver)

            if action == "click":
                element.click()
            elif action == "sendkeys":
                element.clear()  # optional: clear before typing
                element.send_keys(variable)
            elif action == "clear":
                element.clear()
            elif action == "hover":
                actions.move_to_element(element).perform()

        except NoSuchElementException as e:
            logger.error(f"Element not found: {locator}={element}. ERROR: {e}")
            raise
        except Exception as e:
            logger.error(f"Action '{action}' failed on element: {locator}={element}. ERROR: {e}")
            raise

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
                    logger.info(f"Value matched in dropdown")
                    select_element.select_by_visible_text(matched_option)
                else:
                    self.select_value = 0
                    logger.info(f"Value not found in dropdown: {value.strip()}")

        except Exception as e:
            logger.info(f"Failed to handle field {value}: {e}")
        
    def get_input_value(self, locator, locator_value):
        """
            Extracts the 'value' from a <input> element.

            Args:
                driver: Selenium WebDriver instance.
                locator: Selenium By strategy (e.g., By.ID, By.XPATH, By.CSS_SELECTOR).
                locator_value: The locator value string corresponding to the strategy.

            Returns:
                The value of the input field, or None if not found.
        """
        try:
            by = LOCATOR_MAP.get(locator.lower())
            if not by:
                raise ValueError(f"Unsupported locator type: {locator}")

            element = self.driver.find_element(by, locator_value)
            return element.get_attribute("value")
        except NoSuchElementException:
            print(f"Element not found using {by}: {locator}")
            return None
        
    def get_element_text(self, locator, locator_value) -> str | None:
        """
        Gets the visible text from an element using a specified locator.

        Args:
            locator: The type of locator (e.g., 'class_name', 'xpath', etc.)
            locator_value: The value of the locator.

        Returns:
            The text of the element, or None if not found.
        """
        try:
            by = LOCATOR_MAP.get(locator.lower())
            if not by:
                raise ValueError(f"Unsupported locator type: {locator}")

            element = self.driver.find_element(by, locator_value)
            return element.text.strip()
        except NoSuchElementException:
            logger.warning(f"Element not found: {locator} = {locator_value}")
            return None

    # Redirect to  Login page
    def redirect_nf_login_page(self, url):
        try:
           self.driver.get(url)
        except Exception as e:
            logger.info(f"Unable to access website\nERROR: {e}")

    def stop_process(self):
        self.driver.quit()
        #sys.exit("Exiting script after closing browser.")

