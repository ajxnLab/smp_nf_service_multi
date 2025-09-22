from utils.logger import logger
from utils.env_loader import get_env_variable
from nf_services.nf_constants import NfConstants
from utils.exceptions import WalletError
import time

# Constants
from config.config import nf

def create_data_service(wd, wallet_name):
    try:
        logger.info(f"New Wallet To Define: {wallet_name}")
        wd.redirect_to_page(get_env_variable("WEBTOOL_DATA_SERVICES_ADD_FULL_URL"), nf.NF_ADD_BTN_INPUT)
        
        logger.info(f"Input Name: {wallet_name}")
        wd.perform_action("name", nf.NF_DATA_SERVICES_INPUT_NAME, "sendkeys", wallet_name)
        logger.info("Select Data Service Type: WALLET-BASED")
        wd.perform_action("xpath", nf.NF_DATA_SERVICE_TYPE_WALLET_BASED, "click")
        logger.info("Submitting..")
        wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")

        time.sleep(2)
        wd.wait_until_element("name", "submit", "visible")

        # Section to define SDM Wallet Definition
        logger.info("Defining SDM Wallet Definition..")
        logger.info(f"Input Wallet Keyword: {wallet_name}")
        wd.perform_action("name", nf.DATA_SERVICE_WALLET_KEYWORD, "sendkeys", wallet_name)
        logger.info(f"Select Unit: KB")
        wd.perform_action("xpath", nf.DATA_SERVICE_UNITS_KB, "click")
        logger.info(f"Input Base Keyword: {wallet_name}")
        wd.perform_action("name", nf.DATA_SERVICE_BASE_KEYWORD, "sendkeys", wallet_name)
        logger.info(f"Input Base Amount: {wallet_name}")
        wd.perform_action("name", nf.DATA_SERVICE_BASE_AMOUNT, "sendkeys", 1)
        wd.perform_action("xpath", nf.DATA_SERVICE_SDM_WALLET_BTN, "click")
        logger.info("Saving...")
        wd.wait_until_element("xpath", "//input[@value='Delete']", "visible")
        logger.info(f"Data Service '{wallet_name}' Successfully Added, continue bulk service creation..")

    except Exception as e:
        raise WalletError(f"Failed to create wallet {wallet_name}: {e}")