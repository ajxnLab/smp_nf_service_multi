from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from utils.env_loader import get_env_variable
from utils.helpers import convert_string_hashmap
from utils.logger import logger
from config.config import nf
from nf_services.fallback_services.flow_fallback_service import FlowFlashbackService
from nf_services.main_services.modification_services.modify_step_service import ModifyStepService
from nf_services.fallback_services.bulk_service_fallback_service import process_bulk_service
from nf_services.main_services.step_type_service import StepTypeService
from nf_services.main_services.keyword_service import create_keyword
from nf_services.main_services.message_service import create_message
from nf_services.main_services.ssg_service import define_bs_simple_service_group
from nf_services.other_services.soc_to_nf_service import define_soc_to_nf
from nf_services.main_services.gyro_service import create_gyro_command
from nf_services.settings_service.wallet_empty_criteria_service import define_wallet_empty_criteria
from nf_services.main_services.modification_services.check_has_subscription_service import add_service_id_to_check_has
from nf_services.nf_constants import TackOn


class LogicFlow(Enum):
    """Enum for different logic flow types"""
    BULK_SERVICE = "bulk service"
    BASE = "base"
    DOUBLE = "double"
    EXTEND = "extend"
    KEYWORD_SERVICE = "keyword service"
    AUX = "aux"


@dataclass
class FlowConfig:
    """Configuration for flow processing"""
    key: str
    flow_type: LogicFlow
    column: int


class FallbackController:
    """
    Handles fallback processing for failed network services.
    
    This controller processes different types of service flows (base, double, extend, 
    keyword, aux) and attempts to retry failed operations.
    """
    
    # Flow mapping configuration using index
    FLOW_MAPPING = {
        nf.BS_INDEX_RPA_REMARKS_AUX_FLOW: LogicFlow.AUX,
        nf.BS_INDEX_RPA_REMARKS_KEYWORD: LogicFlow.KEYWORD_SERVICE,
        nf.BS_INDEX_RPA_REMARKS_EXTEND_FLOW: LogicFlow.EXTEND,
        nf.BS_INDEX_RPA_REMARKS_DOUBLE_FLOW: LogicFlow.DOUBLE,
        nf.BS_INDEX_RPA_REMARKS_BASE_FLOW: LogicFlow.BASE,
    }
    
    def __init__(self, webdriver, gsheet, worksheets):
        self.wd = webdriver
        self.gs = gsheet
        self.worksheets = worksheets
        self.nf = nf
        
        # Current processing state
        self.bs_current_row: Optional[int] = None
        self.row_data: Optional[List] = None
        self.step: Optional[StepTypeService] = None
        self.dict_rpa_remark: Dict[str, str] = {}
        
        # Services
        self.ffs = FlowFlashbackService(webdriver, gsheet, worksheets)

    def start_nf_fallback_service(self) -> None:
        """
        Main entry point for the fallback service.
        Processes all pending rows that have failed or current date status.
        """
        try:
            logger.info("STARTING FALLBACK PROCESS")
            
            list_failed_data = self._get_all_failed_data()
            #logger.info(f"FALLBACK PENDING ROWS: {pending_rows}")
            if not list_failed_data:
                logger.warning("Fallback Service: No current date or failed services found")
                return

            self._process_failed_data(list_failed_data)
            
        except Exception as e:
            logger.error(f"Unexpected error in fallback service: {e}")
            raise

    def _get_all_failed_data(self) -> List[int]:
        """Get rows that need fallback processing"""
        return self.gs.fetch_failed_rpa_records(self.worksheets["bulkService"])

    def _process_failed_data(self, list_failed_data: List[int]) -> None:
        """Process each pending row for fallback"""
        
        for row_data in list_failed_data:
            row = str(row_data[nf.KEY_ROW_NUMBER])
            self.row_data = row_data
            logger.info(f"Processing row: {row}")
            self.bs_current_row = row
            try:
                self.process_fallback_row()
            except Exception as e:
                logger.error(f"Error processing row {row}: {e}")
                continue

    def process_fallback_row(self) -> None:
        """
        Process a single fallback row by checking all flow types.
        """
        try:
            #self._initialize_row_data()
            bs_service_id = self.row_data[self.nf.NF_INDEX_SERVICE_ID]
            print(bs_service_id)
            if not bs_service_id:
                logger.warning(f"No service ID found for this row, skipping row {self.bs_current_row} process")
                return
            
            self._initialize_step_service(bs_service_id)
            
            # # Setup range to process
            # flow_range = range(
            #     self.nf.BS_INDEX_RPA_REMARKS_BULK_SERVICE, 
            #     self.nf.BS_INDEX_RPA_REMARKS_AUX_FLOW + 1
            # )
            # print
            rpa_columns_to_check = (
                "Base Flow RPA Remarks",
                "Double Flow RPA Remarks", 
                "Extend Flow RPA Remarks", 
                "Keyword RPA Remarks", 
                "AUXILIARY RPA Remarks"
            )
            
            for rpa_column_key in rpa_columns_to_check:
                flow_config = self._get_flow_config(rpa_column_key)
                if not flow_config:
                    continue
                # Start process of the main flow of fallback
                self._process_flow(flow_config, bs_service_id)

        except KeyError:
            logger.warning(f"Current {flow_config.flow_type.value} RPA remark is blank, no need to process")
            return

        except Exception as e:
            logger.error(f"Error in process_fallback_row: {e}")
            raise

    def _initialize_row_data(self) -> None:
        """Initialize row data for current processing row"""
        self.row_data = self.worksheets["bulkService"].row_values(self.bs_current_row)

    def _initialize_step_service(self, bs_service_id: str) -> None:
        """Initialize step type service"""
        print("INITIALIZE STEP")
        url = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
        self.step = StepTypeService(self.wd, self.gs, self.worksheets)

    def _get_flow_config(self, rpa_column_key: int) -> Optional[FlowConfig]:
        """Get flow configuration for given index"""
        flow_type = self.FLOW_MAPPING.get(rpa_column_key, LogicFlow.BULK_SERVICE)
        
        column_mapping = {
            LogicFlow.BASE: self.nf.COLUMN_BULK_SERVICE_RPA_REMARKS_BASE_FLOW,
            LogicFlow.DOUBLE: self.nf.COLUMN_BULK_SERVICE_RPA_REMARKS_DOUBLE_FLOW,
            LogicFlow.EXTEND: self.nf.COLUMN_BULK_SERVICE_RPA_REMARKS_EXTEND_FLOW,
            LogicFlow.KEYWORD_SERVICE: self.nf.COLUMN_BULK_SERVICE_RPA_REMARKS_KEYWORD,
            LogicFlow.AUX: self.nf.COLUMN_BULK_SERVICE_RPA_REMARKS_AUX_FLOW,
        }
        
        column = column_mapping.get(flow_type, self.nf.COLUMN_BULK_SERVICE_RPA_REMARKS)
        
        return FlowConfig(key=rpa_column_key, flow_type=flow_type, column=column)

    def _process_flow(self, flow_config: FlowConfig, bs_service_id: str) -> None:
        """Process a specific flow type"""
        print(f"CURRENT FLOW CONFIG: {flow_config}")
        rpa_remarks_value = self.row_data[flow_config.key]
        logger.info(f"CHECK RPA: {rpa_remarks_value}")
        if not self._should_process_flow(rpa_remarks_value, flow_config.flow_type):
            return
            
        logger.info(f"Processing {flow_config.flow_type.value.upper()} flow: {rpa_remarks_value}")
        
        # Convert RPA remark string to dictionary

        self.dict_rpa_remark = convert_string_hashmap(rpa_remarks_value, "dict")
        print(f"DICT RPA REMARK: {self.dict_rpa_remark}")
        
        # Process based on flow type
        if flow_config.flow_type == LogicFlow.BULK_SERVICE:
            self._process_bulk_service_flow()
        elif flow_config.flow_type == LogicFlow.KEYWORD_SERVICE:
            self._process_keyword_flow(bs_service_id)
        elif flow_config.flow_type == LogicFlow.AUX:
            self._process_aux_flow(bs_service_id)
        else:
            # Standard step creation (base, double, extend)
            self._process_standard_flow(flow_config.flow_type, bs_service_id)
            
        self._update_rpa_remarks(flow_config)

    def _should_process_flow(self, rpa_remarks_value: str, flow_type: LogicFlow) -> bool:
        """Check if flow should be processed"""
        if not rpa_remarks_value:
            logger.warning(f"{flow_type.value.upper()} RPA remark has no value")
            return False
            
        #if "failed" not in rpa_remarks_value.lower():
        if not any(remark in rpa_remarks_value.lower() for remark in ("failed", "pending")):
            logger.warning(f"{flow_type.value.upper()} RPA remark has no failed service")
            return False
            
        return True

    def _process_bulk_service_flow(self) -> None:
        """Process bulk service flow"""
        logger.info("PROCESSING BULK SERVICE FALLBACK")
        
        for key, value in self.dict_rpa_remark.items():
            # if "failed" in value.lower() or "pending" in value.lower():
            if any(status in value.lower() for status in ("pending", "failed")):
                logger.info(f"Processing failed bulk service: {key} = {value}")
                is_success = process_bulk_service(self.row_data, self.worksheets, self.wd, self.gs, key)
                remark_value = "Success" if is_success else "Failed"
                self.dict_rpa_remark[key] = remark_value

    def _process_keyword_flow(self, bs_service_id: str) -> None:
        """Process keyword service flow"""
        logger.info("Processing keyword service flow...")
        
        for key, value in self.dict_rpa_remark.items():
            if "failed" in value.lower():
                logger.info(f"Processing failed keyword: {key} = {value}")
                
                dict_fail_keyword = create_keyword(
                    bs_service_id, self.row_data, self.wd, step_type_key=key
                )
                
                if not dict_fail_keyword:
                    self.dict_rpa_remark[key] = "Success"
                else:
                    self.dict_rpa_remark.update(dict_fail_keyword)

    def _process_aux_flow(self, bs_service_id: str) -> None:
        """Process auxiliary service flow"""
        logger.info("Processing auxiliary service flow...")
        for key, value in self.dict_rpa_remark.items():
            if "failed" not in value.lower():
                continue
                
            logger.info(f"Processing failed aux service => {key} = {value}")
            
            if "message" in key.strip().lower():
                self._process_message_service(key)
            elif "gyro" in key.strip().lower():
                self._process_gyro_service(key, bs_service_id)
            elif "soc" in key.strip().lower():
                self._process_soc_to_nf_service(key, bs_service_id)
            elif "ssg" in key.strip().lower():
                self._process_ssg_service(key, bs_service_id)
            elif "criteria" in key.strip().lower():
                self._process_wallet_empty_criteria(bs_service_id, self.row_data(self.nf.NF_INDEX_WALLET))
            elif "check_has" in key.strip().lower():
                self._process_check_has_subscription_aux(value)

    def _process_message_service(self, key: str) -> None:
        """Process message service"""
        service_name = self.row_data[self.nf.NF_INDEX_NAME].strip()
        message_failed = create_message(self.wd, self.gs, service_name)
        status = "Failed" if message_failed else "Success"
        self.dict_rpa_remark[key] = status

    def _process_gyro_service(self, key: str, bs_service_id: str) -> None:
        """Process gyro command service"""
        gyro_command = self.row_data[self.nf.BS_INDEX_GYRO_COMMAND]
        gyro_remark = create_gyro_command(gyro_command, bs_service_id, self.wd)
        
        if gyro_remark:
            self.dict_rpa_remark.update(gyro_remark)
        else:
            self.dict_rpa_remark["GYRO"] = "Success"

    def _process_soc_to_nf_service(self, key: str, bs_service_id: str) -> None:
        """Process noc to nf mapping service"""
        is_success = define_soc_to_nf(bs_service_id, self.row_data[self.nf.BS_INDEX_SOCID], self.wd)
        soc_remark = "Success" if is_success else "Failed"
        self.dict_rpa_remark["SOC to NF"] = soc_remark

    def _process_ssg_service(self, key: str, bs_service_id: str) -> None:
        """Process simple service group"""
        ssg_remark = define_bs_simple_service_group(bs_service_id, self.row_data[self.nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT], self.wd)
        
        if ssg_remark:
            self.dict_rpa_remark.update(ssg_remark)
        else:
            self.dict_rpa_remark["SSG"] = "Success"

    def _process_wallet_empty_criteria(self, service_id, bs_wallet):
        """Process simple service group"""  
        is_success = define_wallet_empty_criteria(self.wd, service_id, bs_wallet)
        wallet_empty_criteria_remark = "Success" if is_success else "Failed"
        self.dict_rpa_remark["WALLET EMPTY CRITERIA"] = wallet_empty_criteria_remark

    def _process_check_has_subscription_aux(self, rpa_remark_aux_value=None) -> None:
        """Process check has subscription step type"""
        print(f"CHECK HAS RPA REMARK VALUE: {rpa_remark_aux_value}")
        
        def extract_failed_ids(error_string: str) -> str:
            """Extract failed IDs from error string and return as comma-separated string"""
            # Extract content within parentheses using string operations
            start_idx = error_string.find('(')
            end_idx = error_string.find(')')
            
            if start_idx == -1 or end_idx == -1:
                logger.info("Extracted failed IDs: None")
                return ""
                
            # Get content between parentheses and clean up
            ids_string = error_string[start_idx + 1:end_idx]
            # Clean and format IDs
            failed_ids = ", ".join(id.strip() for id in ids_string.split(','))
            
            logger.info(f"Extracted failed IDs: {failed_ids}")
            return failed_ids

        tackon_value_lower = self.row_data[self.nf.BS_INDEX_TACKON].lower()
        string_of_remaining_service_id = extract_failed_ids(rpa_remark_aux_value)
        
        # Check to determine what CHECK HAS SUBSCRIPTION to process
        if tackon_value_lower == TackOn.CHECK_HAS_OTHER.value:
            check_has_fail_ids = add_service_id_to_check_has(self.wd, self.gs, self.row_data, string_of_remaining_service_id)

            # Update the RPA remark for check has subscription
            status_msg = f"Failed {check_has_fail_ids}" if check_has_fail_ids else "Success"
            dict_check_has = {"CHECK_HAS_OTHER": status_msg}
            self.dict_rpa_remark.update(dict_check_has)
        else:
            logger.warning(f"Validation tack-on value error: {tackon_value_lower} is not a valid CHECK HAS SUBSCRIPTION value")

    def _process_standard_flow(self, flow_type: LogicFlow, bs_service_id: str) -> None:
        """Process standard flows (base, double, extend)"""
        logger.info(f"Processing {flow_type.value} flow...")
        
        # Process step creation
        failed_steps = {k: v for k, v in self.dict_rpa_remark.items() if "failed" in v.lower()}
        
        for step_key in failed_steps:
            logger.info(f"Processing failed step: {step_key}")
            self._process_fallback_step_type(flow_type.value, step_key)
            
        # Process flow path definition
        for step_key in failed_steps:
            self.ffs.process_fallback_flow(
                flow_type.value, bs_service_id, self.row_data, step_key
            )

    def _update_rpa_remarks(self, flow_config: FlowConfig) -> None:
        """Update RPA remarks in the spreadsheet"""
        rpa_remark_final_string = convert_string_hashmap(self.dict_rpa_remark, "string")
        rpa_remark_final = rpa_remark_final_string if self.dict_rpa_remark else "Success"
        
        logger.info(f"Updating RPA Remark for {flow_config.flow_type.value.upper()} flow")
        self.gs.update_row(
            self.bs_current_row,
            flow_config.column,
            self.worksheets["bulkService"],
            rpa_remark_final,
        )

    def process_fallback_step_type(self, logic_flow: str, step_type: str) -> None:
        """
        Process fallback for specific step types.
        
        Args:
            logic_flow: The type of flow being processed
            step_type: The specific step type to process
        """
        logger.info("Executing Fallback => Step Type Process Creation")
        bs_service_id = self.row_data[self.nf.NF_INDEX_SERVICE_ID]
        
        logger.info(f"Processing fallback for Step Type: {step_type.upper()} - Logic Flow: {logic_flow.upper()}")
        
        try:
            self._initialize_step_processing(bs_service_id, logic_flow)
            self._execute_step_type_processing(logic_flow, step_type, bs_service_id)
            
            self.dict_rpa_remark[step_type] = "Success"
            logger.info(f"Fallback step creation success: {step_type.upper()}")
            
        except TypeError as e:
            logger.error(f"Type error in step processing: {e}")
            self.dict_rpa_remark[step_type] = "Fallback Failed - Please check Input"
            
        except Exception as e:
            logger.error(f"Error processing step type {step_type}: {e}")
            self.dict_rpa_remark[step_type] = "Fallback Failed - Please check Input"

    def _initialize_step_processing(self, bs_service_id: str, logic_flow: str) -> None:
        """Initialize step processing"""
        self.step.initial_setup(
            self.bs_current_row, self.row_data, bs_service_id, logic_flow
        )

    def _execute_step_type_processing(self, logic_flow: str, step_type: str, bs_service_id: str) -> None:
        """Execute the appropriate step type processing based on step type"""
        logger.info(f"Creating Step Type => {logic_flow.upper()} FLOW - {step_type.upper()}")
        
        step_type_lower = step_type.lower()
        
        if "charge" in step_type_lower:
            self._process_charge_step(bs_service_id)
        elif "check" in step_type_lower:
            self._process_check_has_subscription_step()
        elif "extend_first_expiry" in step_type_lower:
            self._process_extend_first_expiry_step(bs_service_id, logic_flow)
        elif "data" in step_type_lower:
            self._process_data_step(logic_flow, bs_service_id)
        elif "sms" in step_type_lower or "voice" in step_type_lower:
            self._process_sms_voice_step(logic_flow, bs_service_id, step_type)

    def _process_charge_step(self, bs_service_id: str) -> None:
        """Process charge step type"""
        self.step.step_type_in_charge(bs_service_id)

    def _process_check_has_subscription_step(self) -> None:
        """Process check has subscription step type"""
        bs_service_id = self.row_data[self.nf.NF_INDEX_SERVICE_ID]
        is_success = self.step.step_type_check_has_subscription(bs_service_id)
        status_msg = "Success" if is_success else "Failed"
        dict_check_has = {"CHECK_HAS_SUBSCRIPTION": status_msg}
        self.dict_rpa_remark.update(dict_check_has)

    def _process_extend_first_expiry_step(self, bs_service_id: str, logic_flow: str) -> None:
        self.ms = ModifyStepService(self.wd, self.gs)
        """Process extend first expiry step type"""
        if "extend" in logic_flow:
            self.ms.modify_extend_first_expiry(self.row_data)
        else:
            self.step.step_type_extend_first_expiry(self.row_data, self.worksheets["paramMatrix"])

    def _process_data_step(self, logic_flow: str, bs_service_id: str) -> None:
        """Process data step type"""
        if logic_flow == "extend":
            self.step.step_type_data_extend_wallet_expiry(bs_service_id)
        else:
            self.step.step_type_data_prov_process(bs_service_id)

    def _process_sms_voice_step(self, logic_flow: str, bs_service_id: str, step_type: str) -> None:
        """Process SMS or voice step type"""
        if logic_flow == "double":
            logger.info("Processing IN ADD WALLET FUP")
            self.step.step_type_in_add_wallet_fup(bs_service_id, step_type)
        elif logic_flow == "extend":
            logger.info("Processing IN EXTEND WALLET EXPIRY")
            self.step.step_type_in_extend_wallet_expiry(bs_service_id, step_type)
        else:
            logger.info("Processing IN PROV SERVICE")
            self.step.step_type_in_prov_service(bs_service_id, step_type)

    # Alias for backward compatibility
    def _process_fallback_step_type(self, logic_flow: str, step_type: str) -> None:
        """Alias for process_fallback_step_type for internal use"""
        self.process_fallback_step_type(logic_flow, step_type)