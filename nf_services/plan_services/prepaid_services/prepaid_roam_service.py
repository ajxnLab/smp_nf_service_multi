from utils.logger import logger
from utils.helpers import convert_string_hashmap
from nf_services.nf_constants import NfConstants
from nf_services.main_services.step_type_service import StepTypeService

# Call Constants and StepType Class
from config.config import nf

class PrepaidRoamService:
    def __init__(self, webdriver, gsheet, worksheets):
        self.wd = webdriver
        self.gs = gsheet
        self.worksheets = worksheets
        self.dict_step_type_data = {}
        self.dict_incharge_extend_data = {}
        self.st = StepTypeService(webdriver, gsheet, worksheets)

    def process_step_prepaid_roam(self, bs_row_data, bs_service_id, row):
        self.st.initial_setup(row, bs_row_data, bs_service_id)
        self._process_hlr_set(bs_service_id)
        self._process_extend_first_expiry(bs_row_data)
        self._process_data_prov_process(bs_service_id)
        self._update_rpa_remarks(nf.COLUMN_BULK_SERVICE_RPA_REMARKS_BASE_FLOW, row)

    def _process_hlr_set(self, bs_service_id):
        self.st.step_type_hlr_set_vssr_tplid(bs_service_id)
        self.st.step_type_hlr_set_diamrrs_tplid(bs_service_id)
    
    def _process_extend_first_expiry(self, bs_row_data):
        construct_value = bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT]
        if "trigger" in construct_value.lower():
            logger.info("Skipping Extend First Expiry")
            return
        self.st.step_type_extend_first_expiry(bs_row_data, self.worksheets["paramMatrix"])

    def _process_data_prov_process(self, bs_service_id):
        self.st.step_type_data_prov_process(bs_service_id)

    def _update_rpa_remarks(self, rpa_column, row):
        try:
            print(f"CHECK UPDATER RPA: {self.st.bs_rpa_remark_fail}")
            if not self.st.bs_rpa_remark_fail:
                self.gs.update_row(row, rpa_column, self.worksheets["bulkService"], "Successful")
            else:
                remark = convert_string_hashmap(self.st.bs_rpa_remark_fail, "string")
                self.gs.update_row(row, rpa_column, self.worksheets["bulkService"], remark)
        except Exception as e:
            logger.error(f"Error updating Bulk Service RPA Remark: {e}")
