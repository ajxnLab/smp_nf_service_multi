from utils.logger import logger
from nf_services.nf_constants import NfConstants
from utils.env_loader import get_env_variable

from config.config import nf

def define_wallet_empty_criteria(wd, service_id, bs_wallet):
    try:
        logger.info(f"Defining Wallet Empty Criteria for service id {service_id}")
        url = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=wallet_empty_crit&op=add"
        wd.redirect_to_page(url, nf.NF_ADD_BTN_INPUT)
        wd.perform_action("xpath", f"//select[@name='bulk_id']//option[@value='{service_id}']", "click")
        wd.perform_action("xpath", f"//select[@name='conn_type']//option[@value='29']", "click")
        wd.perform_action("xpath", f"//select[@name='jnetx_wallet_type_id']//option[contains(text(), ' {bs_wallet.upper()} ')]", "click")
        wd.submit_form_and_wait_for_success("xpath", nf.NF_ADD_BTN_INPUT, f"//input[@value='View Bulk Service Criteria'] | //span[@style='color:#990000 ']")
        
        logger.info(f"Service id {service_id} successfully define in Wallet Empty Criteria")
        return True
    except Exception:
        logger.error("Unexpected error occurred, failed defining Wallet Empty Criteria")
        return False
