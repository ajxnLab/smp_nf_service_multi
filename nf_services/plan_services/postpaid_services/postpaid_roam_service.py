from utils.logger import logger
from utils.helpers import convert_string_hashmap
from nf_services.nf_constants import NfConstants
from nf_services.main_services.step_type_service import StepTypeService

# Call Constants and StepType Class
from config.config import nf

class PostpaidRoamService:
    def __init__(self, webdriver, gsheet, worksheets):
        self.wd = webdriver
        self.gs = gsheet
        self.worksheets = worksheets
        self.dict_step_type_data = {}
        self.dict_incharge_extend_data = {}
        self.st = StepTypeService(webdriver, gsheet, worksheets)

    def process_step_postpaid_roam(self, bs_row_data, bs_service_id, row):
        self.st.initial_setup(row, bs_row_data, bs_service_id)
        self._process_sdm_postpaid_create_subscriber(bs_service_id)
        self._process_in_charge(bs_service_id, bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT])
        self._process_data_prov(bs_service_id)
        self._update_rpa_remarks(nf.COLUMN_BULK_SERVICE_RPA_REMARKS_BASE_FLOW, row)
        
    def _process_sdm_postpaid_create_subscriber(self, bs_service_id):
        self.st.step_type_sdm_postpaid_create_subscriber(bs_service_id)

    def _process_in_charge(self, bs_service_id, construct_value):
        if "trigger" in construct_value.lower():
            return
        self.st.step_type_in_charge(bs_service_id)

    def _process_data_prov(self, bs_service_id):
        self.st.step_type_data_prov_process(bs_service_id)

    def _update_rpa_remarks(self, rpa_column, row):
        try:
            if not self.st.bs_rpa_remark_fail:
                self.gs.update_row(row, rpa_column, self.worksheets["bulkService"], "Successful")
            else:
                remark = convert_string_hashmap(self.st.bs_rpa_remark_fail, "string")
                self.gs.update_row(row, rpa_column, self.worksheets["bulkService"], remark)
        except Exception as e:
            logger.error(f"Error updating Bulk Service RPA Remark: {e}")
