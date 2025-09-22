from nf_services.main_services.expiry_service import create_service_expiry
from nf_services.main_services.access_code_service import create_access_code
from utils.env_loader import get_env_variable
from nf_services.nf_constants import NfConstants
from nf_services.config.flow_mappings import get_flow_map
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from utils.logger import logger
from nf_services.nf_constants import NfConstants

from config.config import nf

def process_bulk_service(row_data, worksheets, wd, gs, key_remark):
    try:
        service_id = row_data[nf.NF_INDEX_SERVICE_ID]
        if "access" in key_remark.lower():
            create_access_code(service_id, wd)
            return True
        elif "expiry" in key_remark.lower():
            create_service_expiry(row_data, service_id, worksheets["paramMatrix"], wd, gs)
            return True
    except Exception:
        return False