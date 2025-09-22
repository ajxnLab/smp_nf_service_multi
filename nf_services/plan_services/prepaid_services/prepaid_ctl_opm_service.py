from utils.logger import logger
from utils.helpers import convert_string_hashmap
from nf_services.nf_constants import FlowType, StepType, TackOn
from nf_services.main_services.step_type_service import StepTypeService
from nf_services.main_services.modification_services.modify_step_service import ModifyStepService

# Call Constants and StepType Class
from config.config import nf


class PrepaidCTLOPMService:
    def __init__(self, webdriver, gsheet, worksheets):
        self.wd = webdriver
        self.gs = gsheet
        self.worksheets = worksheets
        self.st = StepTypeService(webdriver, gsheet, worksheets)
        self.ms = ModifyStepService(webdriver, gsheet)

    def start_prepaid_ctl_opm_process(
        self,
        flow_key,
        bs_service_id,
        bs_row_data,
        param_worksheet,
        row,
    ):
        try:
            step_flow_construct_value = bs_row_data[
                nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT
            ].lower()

            rpa_column = self._get_rpa_column(flow_key)
            self.st.initial_setup(row, bs_row_data, bs_service_id, flow_key)
            self._process_check_has_subscription(bs_service_id, bs_row_data, flow_key)
            self._process_in_charge_and_extend(
                step_flow_construct_value,
                flow_key,
                param_worksheet,
                bs_service_id,
                bs_row_data,
            )
            self._process_data_step_type(
                step_flow_construct_value,
                flow_key,
                param_worksheet,
                bs_service_id,
            )
            self._process_unli_services(
                step_flow_construct_value, flow_key, bs_service_id
            )
            self._process_hlr_ply(step_flow_construct_value, flow_key, bs_service_id)
            self._update_rpa_remarks(row, rpa_column)

        except Exception as e:
            logger.error(f"Something went wrong on prepaid service process\nERROR: {e}")
            raise

    # ----------------------------------------
    def _get_rpa_column(self, flow_type):
        if flow_type == FlowType.EXTEND.value:
            return nf.COLUMN_BULK_SERVICE_RPA_REMARKS_EXTEND_FLOW
        elif flow_type == FlowType.DOUBLE.value:
            return nf.COLUMN_BULK_SERVICE_RPA_REMARKS_DOUBLE_FLOW
        else:
            return nf.COLUMN_BULK_SERVICE_RPA_REMARKS_BASE_FLOW
    
    def _process_check_has_subscription(self, service_id, bs_row_data, flow_type):
        tackon_value = bs_row_data[nf.BS_INDEX_TACKON]
        tackon_active_ids = bs_row_data[nf.BS_INDEX_CHECK_HAS_IDS]
        # if tackon_value.lower() == TackOn.CHECK_HAS_ADD.value and flow_type == FlowType.BASE.value:
        #     self.st.step_type_check_has_subscription(service_id)
        
        if tackon_value.lower() != TackOn.CHECK_HAS_ADD.value or not tackon_active_ids:
            if tackon_value.lower() == "none": return
            msg = "Validation input error, no active service ids to add for CHECK HAS SUBSCRIPTIONS, please check input, skipping process.." if not tackon_active_ids else "Tack-On option 'Add Check-Has Logic to This Service' is not selected, skipping process.."
            logger.warning(msg)
            return
        
        # Start the process step creation for CHECK HAS SUBSCRIPTIONS
        self.st.step_type_check_has_subscription(service_id)

    def _process_in_charge_and_extend(
        self,
        step_flow: str,
        flow_type: str,
        param_worksheet,
        service_id,
        bs_row_data,
    ):
        if (
            ("prepaid ctl" in step_flow and flow_type != FlowType.DOUBLE.value)
            or ("prepaid opm" in step_flow and flow_type == FlowType.EXTEND.value)
        ):
            self.st.step_type_in_charge(service_id)
        else:
            logger.info("Skipping IN CHARGE - No creation needed for this Flow")

        if flow_type != FlowType.DOUBLE.value:
            if flow_type != FlowType.EXTEND.value:
                self.st.step_type_extend_first_expiry(bs_row_data, param_worksheet)
            else:
                self.ms.modify_extend_first_expiry(bs_row_data)
        else:
            logger.info("Skipping EXTEND FIRST EXPIRY - No creation needed for this Flow")

    def _process_data_step_type(self, step_flow: str, flow_type: str, worksheet, service_id):
        if StepType.DATA.value in step_flow:
            if flow_type == FlowType.EXTEND.value:
                self.st.step_type_data_extend_wallet_expiry(service_id)
            else:
                self.st.step_type_data_prov_process(service_id)
        else:
            logger.info("Skipping DATA step type - No creation needed")

    def _process_unli_services(self, step_flow: str, flow_type: str, service_id):
        if StepType.BULK_SMS.value in step_flow or StepType.BULK_VOICE.value in step_flow and flow_type != "extend":
            self.st.step_type_bulk_sms(service_id)
    
        elif StepType.UNLI_SMS.value in step_flow or StepType.UNLI_VOICE.value in step_flow:
            if flow_type == "double":
                self.st.step_type_in_add_wallet_fup(service_id)
            elif flow_type == "extend":
                self.st.step_type_in_extend_wallet_expiry(service_id)
            else:
                self.st.step_type_in_prov_service(service_id)
        else:
            logger.info("Skipping Unli SMS/VOICE step types - No creation needed")

    def _process_hlr_ply(self, step_flow: str, flow_type: str, service_id):
        if "voice" in step_flow and flow_type not in ("double", "extend"):
            self.st.step_type_hlr_ply(service_id)
        else:
            logger.info("Skipping HLR PLY - No creation needed")

    def _update_rpa_remarks(self, row, rpa_column):
        try:
            if not self.st.bs_rpa_remark_fail:
                self.gs.update_row(row, rpa_column, self.worksheets["bulkService"], "Successful")
            else:
                remark = convert_string_hashmap(self.st.bs_rpa_remark_fail, "string")
                self.gs.update_row(row, rpa_column, self.worksheets["bulkService"], remark)
        except Exception as e:
            logger.error(f"Error updating Bulk Service RPA Remark: {e}")

        try:
            if self.st.param_data:
                if not self.st.param_rpa_remark_fail:
                    for data in self.st.param_data:
                        param_row = data[nf.KEY_ROW_NUMBER]
                        self.gs.update_row(
                            param_row,
                            nf.COLUMN_PARAM_MATRIX_RPA_REMARKS,
                            self.worksheets["paramMatrix"],
                            "PARAM Successfully Defined",
                        )
                else:
                    remark = convert_string_hashmap(self.st.param_rpa_remark_fail, "string")
                    for data in self.st.param_data:
                        param_row = data[nf.KEY_ROW_NUMBER]
                        self.gs.update_row(
                            param_row,
                            nf.COLUMN_PARAM_MATRIX_RPA_REMARKS,
                            self.worksheets["paramMatrix"],
                            remark,
                        )
            else:
                logger.info("No ParamMatrix remarks to update.")
        except Exception as e:
            logger.error(f"Error updating ParamMatrix RPA Remark: {e}")

