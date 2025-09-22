from utils.google_sheet import GSheetClient
from utils.env_loader import get_env_variable
from utils.web_driver import WebDriver
from utils.logger import logger, finalize_log_upload
from config.config import WORKSHEET_CONFIG, nf
from nf_services.controller.service_controller import ServiceController
import sys


def login_sequence(wd, credential):
    url_login = get_env_variable("WEBTOOL_LOGIN_FULL_URL")
    logger.info(f"2ND PROCESS: Redirecting to NF login page: {url_login}")
    wd.redirect_to_page(url_login)
    wd.wait_until_element("id", nf.NF_LOGIN_BUTTON, "clickable")        
    wd.perform_action("name", "uname", "sendkeys", credential['username'])
    wd.perform_action("name", "passwd", "sendkeys", credential['password'])
    wd.perform_action("id", nf.NF_LOGIN_BUTTON, "click")
    wd.wait_until_element("id", "content", "visible")
    logger.info("2ND PROCESS: Login Successful!")

def stop_secondary_process(event_done, wd):
    logger.info("Terminating bot secondary process..")
    finalize_log_upload()
    wd.driver.quit()
    event_done.set()
    sys.exit()

def execute_new_aux_instance_process(row_data: dict, row: int, aux_done, credential):
    """Process 2: Handles auxiliary flows and services"""
    gs = GSheetClient()
    try:
        wd = WebDriver()
        # Initialize service controller for this process
        worksheets = gs.create_worksheets(WORKSHEET_CONFIG)
        controller = ServiceController(worksheets, wd, gs)
        
        # Execute Login Sequence for secondary process
        login_sequence(wd, credential)

        # Execute auxiliary processes
        bs_service_id = row_data[nf.NF_INDEX_SERVICE_ID]            
        controller._handle_wallet_empty(bs_service_id, row_data)
        controller._handle_gyro_command(row_data, bs_service_id)
        controller._handle_ssg(row, row_data, bs_service_id)
        controller._update_messages_tab(row, row_data, bs_service_id)
        controller._handle_aux_flow(row, row_data)
        
        # Signal auxiliary process is done
        # Wait for main process
        # logger.info("Auxiliary process waiting for main process...")
        # main_done.wait()

    except Exception as e:
        logger.error(f"2ND PROCESS: Something went wrong - Failed to process: {e}")
        aux_done.set()  # Signal even on error
    finally:
        stop_secondary_process(aux_done, wd)


    def execute_new_service_expiry_instance_process(param_data: dict, row: int, aux_done, credential):
        """Process 2: Handles auxiliary flows and services"""
        gs = GSheetClient()
        try:
            wd = WebDriver()
            # Initialize service controller for this process
            worksheets = gs.create_worksheets(WORKSHEET_CONFIG)
            controller = ServiceController(worksheets, wd, gs)
            
            # Execute Login Sequence for secondary process
            login_sequence(wd, credential)

            # Execute auxiliary processes
            bs_service_id = param_data[nf.NF_INDEX_SERVICE_ID]            
            controller._handle_wallet_empty(bs_service_id, param_data)
            controller._handle_gyro_command(param_data, bs_service_id)
            controller._handle_ssg(row, param_data, bs_service_id)
            controller._update_messages_tab(row, param_data, bs_service_id)
            controller._handle_aux_flow(row, param_data)
            
            # Signal auxiliary process is done
            # Wait for main process
            # logger.info("Auxiliary process waiting for main process...")
            # main_done.wait()

        except Exception as e:
            logger.error(f"2ND PROCESS: Something went wrong - Failed to process: {e}")
            aux_done.set()  # Signal even on error
        finally:
            stop_secondary_process(aux_done, wd)