from config.service_validator_bulkservice import ServiceConfigValidator
from config.service_validator_parammatrix import ParamConfigValidator
from config.config import nf
from utils.logger import logger
import time
import sys


class NFServiceValidator:
    def __init__(self, gsheet, worksheets):
        self.gs = gsheet
        self.worksheets = worksheets
        self.error_count = 0
        self.bulk_validator = ServiceConfigValidator()
        self.param_validator = ParamConfigValidator()

    def start_validation_process(self):
        print("STARTING INPUT VALIDATION PROCESS")
        print("Fetching current date data..")
        list_bs_data = self.gs.fetch_current_date_data(self.worksheets["bulkService"])
        try:
            if not list_bs_data:
                logger.warning("No deployment today to work on, terminating bot...")
                raise
            print("Current data fetched!")
            for bs_row_data in list_bs_data:
                bs_name = bs_row_data[nf.NF_INDEX_NAME].strip()
                construct_value = bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT]
                with_extend_flow = bs_row_data[nf.NF_INDEX_WITH_EXTEND_STEPS_AND_FLOW]

                # Execute validation bulk service input
                self._handle_bulk_service_validation(bs_row_data, bs_name)

                # Execute validation parammatrix input
                list_param_data = self.gs.fetch_by_service_name(self.worksheets["paramMatrix"], bs_name)
                # if list_param_data:
                #     for param_data in list_param_data:
                #         self._handle_parammatrix_validation(param_data, construct_value, with_extend_flow, bs_name)

                if list_param_data:
                    # Process param data in smaller batches
                    for i in range(0, len(list_param_data), 5):
                        param_batch = list_param_data[i:i + 5]
                        for param_data in param_batch:
                            self._handle_parammatrix_validation(
                                param_data, 
                                construct_value,
                                with_extend_flow,
                                bs_name
                            )
                        time.sleep(1)  # Delay between param batches
            
            if self.error_count > 0:
                print("\n")
                logger.error("Validation input failed, please confirm input values, terminating bot..")
                raise

        except Exception:
            self._terminate_bot()
        
    def _handle_bulk_service_validation(self, bulk_service_data, bs_name):
        # Create validator and test
        result = self.bulk_validator.validate_service_config(bulk_service_data)
        
        error_msg = []
        print(f"\nRow: {bulk_service_data[nf.KEY_ROW_NUMBER]}\nVALIDATOR: BULK SERVICE")
        print(f"Bulk Service Name: {bs_name}")
        print(f"Step and Flow Construct: {bulk_service_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT]}")
        print(f"Validation Result: {'PASSED' if result.is_valid else 'FAILED'}")
        print(f"Errors: {len(result.errors)}")
        for error in result.errors:
            print(f"  - {error}")
            error_msg.append(error)

        print(f"Warnings: {len(result.warnings)}")
        for warning in result.warnings:
            print(f"  - {warning}")
        
        self.error_count = len(result.errors)
        if len(result.errors) > 0:
            rpa_remark_value = " | ".join(error_msg)
            self.gs.update_row(bulk_service_data[nf.KEY_ROW_NUMBER], nf.COLUMN_BULK_SERVICE_RPA_REMARKS, self.worksheets['bulkService'], f"Validation input failed | {rpa_remark_value}")
    
    def _handle_parammatrix_validation(self, param_data, construct_value, with_extend_flow_value, bs_name):
        # print("\n=== Testing Category Fallback (Prepaid OPM) ===")
        
        # Add step and flow construct and with extend flow value to param_data
        param_data['With Extend Flow'] = with_extend_flow_value
        param_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT] = construct_value
        result_category = self.param_validator.validate_param_config(param_data)

        error_msg = []
        print(f"\nRow: {param_data[nf.KEY_ROW_NUMBER]}\nVALIDATOR: PARAMMATRIX")
        print(f"Param: {param_data[nf.PARAMMATRIX_INDEX_PARAM]}\nService Name: {bs_name}")
        print(f"Validation Result: {'PASSED' if result_category.is_valid else 'FAILED'}")
        print(f"Errors: {len(result_category.errors)}")
        for error in result_category.errors:
            print(f"  - {error}")
            error_msg.append(error)
        print(f"Warnings: {len(result_category.warnings)}")
        for warning in result_category.warnings:
            print(f"  - {warning}")

        self.error_count += len(result_category.errors)
        # if len(result_category.errors) > 0:
        #     rpa_remark_value = " | ".join(error_msg)
        #     self.gs.update_row(param_data[nf.KEY_ROW_NUMBER], nf.COLUMN_PARAM_MATRIX_RPA_REMARKS, self.worksheets['paramMatrix'], f"Validation input failed | {rpa_remark_value}")
        
        if len(result_category.errors) > 0:
                rpa_remark_value = " | ".join(error_msg)
                # Add delay between API calls
                time.sleep(1)  # 1 second delay
                self.gs.update_row(param_data[nf.KEY_ROW_NUMBER], 
                                 nf.COLUMN_PARAM_MATRIX_RPA_REMARKS,
                                 self.worksheets['paramMatrix'], 
                                 f"Validation input failed | {rpa_remark_value}")


    def _terminate_bot(self):
        sys.exit()