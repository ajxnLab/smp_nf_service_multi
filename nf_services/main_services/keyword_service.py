from utils.env_loader import get_env_variable
from utils.logger import logger
from nf_services.nf_constants import NfConstants

from config.config import nf

def create_keyword(bs_service_id, bs_row_data, wd, step_type_key=None, flow_key=None):
    logger.info("STARTING KEYWORD PROCESS")
    # Declare Keyword value and Operation
    url = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=service_keywords&op=add&details_id={bs_service_id}"
    provision_keyword_value = bs_row_data[nf.BS_INDEX_PROVISION_KEYWORD]
    deprovision_keyword_value = bs_row_data[nf.BS_INDEX_DEPROVISION_KEYWORD]
    status_keyword_value = bs_row_data[nf.BS_INDEX_STATUS_KEYWORD]
    extend_keyword_value = bs_row_data[nf.BS_INDEX_EXTEND_KEYWORD]
    

    if step_type_key:
        step_type_key_lower = step_type_key.lower()
        keyword_conditions = {
            "Provision": True if step_type_key_lower == "provision" else False,
            "Deprovision": True if step_type_key_lower == "deprovision" else False,
            "Status": True if step_type_key_lower == "status" else False,
            "Extend": (
                True if step_type_key_lower == "extend" else False
            ),
        }
    else:
        keyword_conditions = {
            "Provision": True if provision_keyword_value else False,
            "Deprovision": True if deprovision_keyword_value else False,
            "Status": True if status_keyword_value else False,
            "Extend": (
                True if extend_keyword_value and flow_key == "extend" else False
            ),
        }

    # Start Loop for each keyword that is set to True
    fail_remark = {}

    for keyword_key, keyword_true in keyword_conditions.items():
        try:
            # print(f"key: {keyword_key} = {keyword_true}")
            if keyword_true:

                logger.info(f"Creating Keyword: {keyword_key}")
                # Get keyword value and operiations by calling function get_keyword_operation
                keyword_value, selected_keyword_operation = get_keyword_operation(
                    keyword_key.lower(),
                    provision_keyword_value,
                    deprovision_keyword_value,
                    status_keyword_value,
                    extend_keyword_value,
                )

                logger.info(
                    f"Keyword Operation: {keyword_key} Keyword Value: {keyword_value}"
                )

                # Redirect to Keyword Add Page using bulk service id
                wd.redirect_to_page(url, nf.NF_ADD_BTN_INPUT)
                wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")

                # Section to fill up the fields
                # Dropdown Operation Field
                logger.info("Filling up keyword fields...")
                wd.perform_action("xpath", selected_keyword_operation, "click")

                # Input Regex Field
                logger.info(f"Input Regex: {keyword_value}")
                wd.perform_action(
                    "name", nf.KEYWORD_REGEX_INPUT, "sendkeys", keyword_value
                )
                
                # Click Submit Button
                wd.submit_form_and_wait_for_success(
                    "xpath",
                    nf.NF_ADD_BTN_INPUT,
                    nf.CONTAINS_SUCCESS_OR_EXIST_MESSAGE,
                    skip=True,
                )
                
                logger.info(
                    f"Service Keyword Successfully Defined for {keyword_key.upper()}"
                )

        except Exception as e:
            logger.warning(
                f"Failed to create keyword operation {keyword_key} \nERROR: {e}"
            )
            fail_remark[keyword_key] = "Failed"
            continue

    return fail_remark


def get_keyword_operation(
    keyword_key,
    provision_keyword_value,
    deprovision_keyword_value,
    status_keyword_value,
    extend_keyword_value,
):
    # For Extend Flow only
    if keyword_key == "extend":
        keyword_value = extend_keyword_value
        selected_keyword_operation = nf.KEYWORD_OPERATION_EXTEND

    # For Declaring Status Keyword and Operation
    elif keyword_key == "status":
        keyword_value = status_keyword_value
        selected_keyword_operation = nf.KEYWORD_OPERATION_STATUS

    # For Declaring Deprovision Keyword Declaration
    elif keyword_key == "deprovision":
        keyword_value = deprovision_keyword_value
        selected_keyword_operation = nf.KEYWORD_OPERATION_DEPROVISION

    # For Declaring Provision Keyword Declaration
    elif keyword_key == "provision":
        keyword_value = provision_keyword_value
        selected_keyword_operation = nf.KEYWORD_OPERATION_PROVISION

    return keyword_value, selected_keyword_operation
