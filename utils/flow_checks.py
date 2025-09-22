import logging
from nf_services.nf_constants import NfConstants


from config.config import nf

logger = logging.getLogger(__name__)

def should_skip_successful_flow(rpa_remark_value, current_flow) -> bool:
    """Check if the current flow is already marked as successful."""
    try:
        if "success" in rpa_remark_value.lower():
            logger.warning(f"Current Flow {current_flow.upper()} is already successful, skipping..")
            return True
    except KeyError:
        pass
    return False