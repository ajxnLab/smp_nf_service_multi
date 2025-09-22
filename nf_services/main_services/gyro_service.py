from utils.env_loader import get_env_variable
from utils.logger import logger
from nf_services.nf_constants import NfConstants
from selenium.webdriver.common.by import By

from config.config import nf

# Function to Create Gyro Command
def create_gyro_command(command_string, bs_service_id, wd):
    try:
        logger.info("STARTING GYRO COMMAND PROCESS")

        # Declare variable
        url = get_env_variable("WEBTOOL_GYRO_COMMAND_ADD_FULL_URL")
        array_command = command_string.split(", ")

        # Loop array command values
        for command_value in array_command:

            # Redirect to Gyro Command Add page
            logger.info("Redirecting to Gyro Command Add Page...")
            wd.redirect_to_page(url, nf.NF_ADD_BTN_INPUT)
            #wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")

            logger.info(f"Adding Gyro Command: {command_value}")

            # Input Command Field
            wd.perform_action(
                "name", nf.GYRO_COMMAND_FIELD, "sendkeys", command_value
            )

            # Choose Current Bulk Service - Service ID
            wd.perform_action(
                "xpath",
                f"//select[@name='svc_id']//option[@value='{bs_service_id}']",
                "click",
            )

            # Click Add button
            logger.info("Saving gyro command...")
            element_text = wd.submit_form_and_wait_for_success(
                "xpath", nf.NF_ADD_BTN_INPUT, nf.SUCCESS_OR_EXIST
            )
            if "success" in element_text.lower():
                status_msg = f"Gyro Command '{command_value}' Successfully Created - For Service ID: {bs_service_id}"
            elif "already" in element_text.lower():
                status_msg = f"Gyro Command '{command_value}' already exist - For Service ID: {bs_service_id}"
            else:
                status_msg = f"Gyro Command '{command_value}' Failed to Create - For Service ID: {bs_service_id}"
                raise
            
            logger.info(status_msg)

    except Exception as e:
        logger.info(
            f"An error has occurred while defining gyro command\nERROR: {e}"
        )
        return {"GYRO: FAILED"}