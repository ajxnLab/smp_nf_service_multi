from utils.env_loader import get_env_variable
from utils.logger import logger
from nf_services.nf_constants import NfConstants
from selenium.common.exceptions import TimeoutException
from utils.exceptions import ExpiryServiceError

from config.config import nf

# Function to define the Service Expiry of Bulk Services
def create_service_expiry(bs_row_data, service_id, param_worksheet, wd, gs):
    try:
        logger.info("STARTING EXPIRY SERVICE PROCESS")
        # # Declare ParamMatrix Worksheet
        # param_worksheet = gs.create_worksheet(
        #     nf.WORKSHEET_TAB_BULK_SERVICES_TAB_PARAM_MATRIX
        # )

        # Declare Default Duration in days
        default_duration_in_days_value = bs_row_data[
            nf.NF_INDEX_DEFAULT_DURATION_IN_DAYS
        ].lower()
        logger.info("Redirecting to Add Service Expiry Page")
        # wd.driver.get(
        #     f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=service_expiries&op=add&details_id={service_id}"
        # )
        url = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=service_expiries&op=add&details_id={service_id}"
        wd.redirect_to_page(url, nf.NF_ADD_BTN_INPUT)
        wd.wait_until_element(
            "xpath", nf.NF_ADD_BTN_INPUT, "clickable", timeout=60
        )

        # Section to Input Default Values
        # If Default Duration in Days value is No Expiry, choose radio button no expiry, else, multiple by 24
        logger.info("Filling up service expiry fields...")
        
        # Condition to click radio button 'No Expiry'
        if "no" in default_duration_in_days_value or "postpaid" in bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT].lower():
            wd.perform_action("id", "et_2", "click")
        else:
            # Input Expiry
            logger.info(f"Input Expiry: {int(default_duration_in_days_value) * 24}")
            wd.perform_action(
                "id",
                "expiry",
                "sendkeys",
                int(default_duration_in_days_value) * 24,
            )

        # Click Add Button
        wd.submit_form_and_wait_for_success(
            "xpath", nf.NF_ADD_BTN_INPUT, nf.CONTAINS_SUCCESS_OR_EXIST_MESSAGE, skip=True
        )

        # Section to Input Param Matrix Values
        list_param_data = gs.fetch_by_service_name(
            param_worksheet, bs_row_data[nf.NF_INDEX_NAME]
        )

        if len(list_param_data) != 0:
            for param_matrix_data in list_param_data:
                row = param_matrix_data[nf.KEY_ROW_NUMBER]
                logger.info(
                    "Found ParamMatrix inputs for service expiry, filling up Param fields..."
                )
                wd.redirect_to_page(url, nf.NF_ADD_BTN_INPUT)
                # wd.wait_until_element(
                #     "xpath", nf.NF_ADD_BTN_INPUT, "clickable", timeout=60
                # )
                logger.info(
                    f"Input Param Field: {param_matrix_data[nf.PARAMMATRIX_INDEX_PARAM]}"
                )
                # Clear Input Param Field
                wd.perform_action("name", nf.SERVICE_PARAM_INPUT, "clear")

                # Input Param Field
                wd.perform_action(
                    "name",
                    nf.SERVICE_PARAM_INPUT,
                    "sendkeys",
                    param_matrix_data[nf.PARAMMATRIX_INDEX_PARAM],
                )

                # Condition to click radio button 'No Expiry'
                duration_in_days = param_matrix_data[nf.PARAMMATRIX_INDEX_DURATION_IN_DAYS]
                if "no" in duration_in_days.lower() or "postpaid" in bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT].lower():
                    logger.info(
                    f"Input Expiry: {duration_in_days}"
                    )
                    wd.perform_action("id", "et_2", "click")
                else:
                    # Input Expiry
                    logger.info(f"Input Expiry: {int(duration_in_days) * 24}")
                    wd.perform_action(
                        "id",
                        "expiry",
                        "sendkeys",
                        int(duration_in_days) * 24,
                    )
        
                # Handle after submitting form.. If taking time to load and doesn't need to get the element success message...
                wd.submit_form_and_wait_for_success(
                    "xpath",
                    nf.NF_ADD_BTN_INPUT,
                    nf.CONTAINS_SUCCESS_OR_EXIST_MESSAGE,
                    skip=True,
                )
                # self._click_add_and_wait()

                logger.info("Service Expiry Successfully Created With Param Fields")
                gs.update_row(row, nf.COLUMN_PARAM_MATRIX_SERVICE_ID, param_worksheet, service_id)
                gs.update_row(row, nf.COLUMN_PARAM_MATRIX_RPA_REMARKS, param_worksheet, "PARAM Successful - Service Expiry")

        else:
            logger.info("No ParamMatrix Found for this Service name.")

        logger.info("Service Expiry Successfully Define")
        return True
    except ExpiryServiceError:
        return False
