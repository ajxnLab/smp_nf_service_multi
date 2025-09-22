from utils.env_loader import get_env_variable
from utils.logger import logger
from nf_services.nf_constants import NfConstants

from config.config import nf

# Function to Define Gyro Command
def create_access_code(bs_service_id, wd):
    try:
        logger.info("Defining Access Code..")

        # Declare variable
        url = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=access_codes&op=add&details_id={bs_service_id}"

        wd.redirect_to_page(url, nf.NF_ADD_BTN_INPUT)

        logger.info(f"Input Access Code: 8080")
        # Input Access Code
        wd.perform_action(
            "name", nf.ACCESS_CODE_INPUT, "sendkeys", 8080
        )

        # Click Add button
        wd.submit_form_and_wait_for_success(
            "xpath", nf.NF_ADD_BTN_INPUT, nf.STEP_SUCCESS_MESSAGE
        )
        logger.info(
            f"Access Code Successfully Define - For Service ID: {bs_service_id}"
        )

 
    except Exception as e:
        logger.info(
            f"An error has occurred while defining access code\nERROR: {e}"
        )