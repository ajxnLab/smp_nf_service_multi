import logging
import os
import sys
import time
import traceback
from requests.exceptions import ConnectionError
from urllib3.exceptions import ProtocolError
from datetime import datetime
from utils.logger import setup_in_memory_logger

logger, log_stream = setup_in_memory_logger(service_name="helpers")

def get_datetime(format: str = "iso", tz=None) -> str:
    """
    Returns the current date/time in the requested format.
    
    Args:
        format: str - The format type ("iso", "date", "time", "custom")
        tz: timezone - Optional timezone (use from pytz or zoneinfo)
        
    Returns:
        str - formatted datetime string
    """
    now = datetime.now(tz)
    
    if format == "iso":
        return now.isoformat()
    elif format == "date":
        return now.strftime("%Y-%m-%d")
    elif format == "time":
        return now.strftime("%H:%M:%S")
    elif format == "full":
        return now.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(format, str):
        return now.strftime(format)
    else:
        raise ValueError("Unsupported format")

def duration_time(start_time, end_time):
    try:
        start_time_duration = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        end_time_duration = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        duration = end_time_duration - start_time_duration
        return duration
    except ValueError as ve:
        # Raised when strptime() fails to parse the datetime
        logger.error(f"Invalid date format: {ve}")
        return None
    
    except TypeError as te:
        # Raised if input is not a string
        logger.error(f"Type error in duration_time(): {te}")
        return None
    except Exception as e:
        # Catch-all for unexpected issues
        logger.error(f"Unexpected error in duration_time(): {e}")
        return None
    
def safe_click_with_refresh(
    wd,
    locator_type,
    element_value,
    logger,
    wait_target_locator_type=None,
    wait_target_value=None,
    gs=None,
    sheet_tab_retry=None,
    row_index_retry=None,
    retries=1,
    wait_after_refresh=5,
    post_refresh_action=None
):
    """
    Attempts to click an element. If it fails due to a timeout or connection issue,
    refreshes the page, waits for a target element, and retries the click.

    :param wd: WebDriver instance
    :param locator_type: Locator type for click target (e.g., 'xpath')
    :param element_value: Locator value for click target
    :param logger: Logger instance
    :param wait_target_locator_type: (Optional) Locator type to wait for after refresh
    :param wait_target_value: (Optional) Locator value to wait for after refresh
    :param gs: (Optional) GSheetClient instance
    :param sheet_tab: (Optional) GSheet tab name
    :param row_index: (Optional) Row index to log result to
    :param retries: Retry count
    :param wait_after_refresh: Seconds to wait after refresh (default: 5)
    """
    attempt = 0
    while attempt <= retries:
        try:
            wd.perform_action(locator_type, element_value, "click")
            logger.info(f"[safe_click] Click succeeded on attempt {attempt + 1}")
            return
        except (ConnectionError, ProtocolError, Exception) as e:
            logger.error(f"[safe_click] Attempt {attempt + 1} failed: {e}")
            logger.debug(traceback.format_exc())

            if attempt < retries:
                logger.info("[safe_click] Refreshing page and retrying click...")
                wd.driver.refresh()
                time.sleep(wait_after_refresh)

                if wait_target_locator_type and wait_target_value:
                    try:
                        wd.wait_until_element(wait_target_locator_type, wait_target_value, "visible")
                        logger.info("[safe_click] Page element visible after refresh.")
                    except Exception as wait_err:
                        logger.warning(f"[safe_click] Failed to wait for element after refresh: {wait_err}")

                if post_refresh_action:
                        try:
                            post_refresh_action()
                            logger.info("[safe_click] Post-refresh input re-applied.")
                        except Exception as input_err:
                            logger.error(f"[safe_click] Failed to reapply input after refresh: {input_err}")

                attempt += 1
            else:
                logger.error("[safe_click] Max retries reached. Click failed.")
                if gs and sheet_tab_retry and row_index_retry is not None:
                    gs.update_cell(sheet_tab_retry, row_index_retry, "RPA Remarks", "Click Failed")
                raise

def get_resource_path(filename):
    """Get path to resource whether running from source or PyInstaller .exe"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath("."), filename)

