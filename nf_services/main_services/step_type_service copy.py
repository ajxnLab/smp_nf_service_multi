from selenium.webdriver.common.by import By
from utils import helpers as helper
from utils.helpers import retryable
from utils.env_loader import get_env_variable
from utils.logger import logger
from nf_services.nf_constants import FlowType
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

from config.config import nf

@dataclass
class StepResult:
    step_id: str
    step_name: str
    step_type: str

@dataclass
class StepConfig:
    name: str
    xpath: str
    step_type_value: str
    fields: Dict[str, Any] = None
    
class StepTypeService:
    def __init__(self, webdriver, gsheet, worksheets):
        self.wd = webdriver
        self.gs = gsheet
        self.worksheets = worksheets
        self.row = None
        self.flow_key = FlowType.BASE.value
        self.bs_row_data = None
        self.rpa_column = None
        self.url_step_page = None
        self.param_rows = []
        self.bs_rpa_remark_fail = {}
        self.param_rpa_remark_fail = {}
        
        # Step configurations
        self.step_configs = self._initialize_step_configs()

    def _initialize_step_configs(self) -> Dict[str, StepConfig]:
        """Initialize step configurations for different step types"""
        return {
            'in_charge': StepConfig(
                name="IN_CHARGE",
                xpath="//select[@id='dd_stype_id']//option[contains(text(), 'IN CHARGE') and @value='2']",
                step_type_value="2"
            ),
            'extend_first_expiry': StepConfig(
                name="EXTEND_FIRST_EXPIRY",
                xpath="//select[@id='dd_stype_id']//option[contains(text(), 'EXTEND FIRST EXPIRY') and @value='19']",
                step_type_value="19"
            ),
            'data_prov_keyword': StepConfig(
                name="DATA_PROV_WITH_KEYWORD_MAPPING",
                xpath="//select[@id='dd_stype_id']//option[@value='95']",
                step_type_value="95"
            ),
            'data_prov_extension': StepConfig(
                name="DATA_PROV_EXTENSION_WITH_KEYWORD_MAPPING",
                xpath="//select[@id='dd_stype_id']//option[@value='96']",
                step_type_value="96"
            ),
            'data_extend_wallet_expiry': StepConfig(
                name="DATA_EXTEND_WALLET_EXPIRY",
                xpath="//select[@id='dd_stype_id']//option[@value='128']",
                step_type_value="128"
            ),
            'hlr_ply': StepConfig(
                name="HLR_PLY",
                xpath="//select[@id='dd_stype_id']//option[contains(text(), 'HLR PLY') and @value='40']",
                step_type_value="40"
            ),
            'hlr_set_vssr': StepConfig(
                name="HLR_SET_VSSR_TPLID",
                xpath="//select[@id='dd_stype_id']//option[contains(text(), 'HLR SET VSSR TPLID') and @value='121']",
                step_type_value="121"
            ),
            'hlr_set_diamrrs': StepConfig(
                name="HLR_SET_DIAMRRS_TPLID",
                xpath="//select[@id='dd_stype_id']//option[contains(text(), 'HLR SET DIAMRRS TPLID') and @value='152']",
                step_type_value="152"
            ),
            'sdm_postpaid': StepConfig(
                name="SDM_POSTPAID_CREATE_SUBSCRIBER",
                xpath="//select[@id='dd_stype_id']//option[contains(text(), 'SDM POSTPAID CREATE SUBSCRIBER') and @value='144']",
                step_type_value="144"
            ),
            'check_has_subscription': StepConfig(
                name="CHECK_HAS_SUBSCRIPTION",
                xpath="//select[@id='dd_stype_id']//option[contains(text(), 'CHECK HAS SUBSCRIPTIONS') and @value='110']",
                step_type_value="110"
            )
        }

    def initial_setup(self, row, bs_row_data, bs_service_id, flow_key="base"):
        """Setup the reusable variables"""
        logger.info("Initializing Step Service..")
        self.row = row
        self.flow_key = flow_key
        self.bs_row_data = bs_row_data
        self.url_step_page = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
        
        # Set RPA column based on flow key
        self.rpa_column = self._get_rpa_column(flow_key)
        
        # Get ParamMatrix rows
        logger.info(f"Checking for ParamMatrix Values For this Service Name: {bs_row_data[nf.NF_INDEX_NAME]}")
        self.param_rows = self.gs.get_rows_by_name(self.worksheets["paramMatrix"], bs_row_data[nf.NF_INDEX_NAME])
        logger.info("Step Service Initialized.")

    def _get_rpa_column(self, flow_key: str) -> str:
        """Get RPA column based on flow key"""
        flow_columns = {
            "extend": nf.COLUMN_BULK_SERVICE_RPA_REMARKS_EXTEND_FLOW,
            "double": nf.COLUMN_BULK_SERVICE_RPA_REMARKS_DOUBLE_FLOW,
            "base": nf.BS_INDEX_RPA_REMARKS_BASE_FLOW
        }
        return flow_columns.get(flow_key, nf.BS_INDEX_RPA_REMARKS_BASE_FLOW)

    def _fill_default_step_fields(self, name_value: str, step_config: StepConfig, sms_voice: str = None):
        """Fill default values for step inputs"""
        try:
            logger.info("Filling up step fields..")
            logger.info(f"Input Name: {name_value}")
            self.wd.perform_action("xpath", nf.NF_INPUT_NAME, "sendkeys", name_value)
            
            logger.info(f"Select Step Type: {step_config.xpath}")
            self.wd.perform_action("xpath", step_config.xpath, "click")

            if sms_voice and "voice" in sms_voice and self.flow_key not in ["extend", "double"]:
                self.wd.perform_action("name", nf.NF_STEPS_FINAL_CHECKBOX, "click")

            self.wd.perform_action("name", nf.NF_STEPS_RETRY_INPUT, "sendkeys", 3)
        except Exception as e:
            logger.error(f"Error in _fill_default_step_fields: {e}")
            raise

    def _submit_and_get_step_id(self, step_name: str, bs_service_id: str) -> str:
        """Submit form and get step ID, with recovery fallback"""
        try:
            element_value = self.wd.submit_form(
                "xpath", nf.NF_ADD_BTN_INPUT, nf.STEP_SUCCESS_MESSAGE
            )
        except TimeoutException:
            raise
        except Exception:
            logger.error("Something went wrong while submitting..")
            raise
        
        return helper.get_after_word(element_value, "step")

    def _fill_param_matrix_charge_codes(self, worksheet, step_name: str):
        """Fill charge code parameters from param matrix"""
        logger.info("Filling sub-fields using ParamMatrix values...")
        for index, row in enumerate(self.param_rows, start=1):
            try:
                data = worksheet.row_values(row)
                self.wd.perform_action("xpath", "//a[@onclick='javascript: add_param_amount_chargecode_field();']", "click")
                
                fields = [
                    (f"param_amt_ccode[{index}][param]", data[nf.PARAMMATRIX_INDEX_PARAM]),
                    (f"param_amt_ccode[{index}][amount]", data[nf.PARAMMATRIX_INDEX_AMOUNT])
                ]
                
                if data[nf.PARAMMATRIX_INDEX_CHARGE_CODE]:
                    fields.append((f"param_amt_ccode[{index}][chargecode]", data[nf.PARAMMATRIX_INDEX_CHARGE_CODE]))
                
                for field_name, field_value in fields:
                    self.wd.perform_action("name", f"{field_name} type=", "sendkeys", field_value)
                    
            except Exception as e:
                logger.warning(f"Error with ParamMatrix row {row}: {e}")
                self.param_rpa_remark_fail[step_name] = "Failed"

    def step_type_in_charge(self, param_worksheet, bs_service_id) -> Optional[Dict]:
        """Execute process for step type IN CHARGE"""
        try:
            step_name = "EXTEND_CHARGE" if self.flow_key.lower() == "extend" else "IN_CHARGE"
            if self._step_validation(bs_service_id, step_name): return
            logger.info(f"Executing Step Type: {step_name}")
            
            self.wd.redirect_to_page(self.url_step_page, nf.NF_ADD_BTN_INPUT)

            # Get amount based on flow type
            param_amount = (
                self.bs_row_data[nf.NF_INDEX_EXTEND_AMOUNT]
                if self.flow_key.lower() == "extend"
                else self.bs_row_data[nf.NF_INDEX_DEFAULT_AMOUNT]
            )

            config = self.step_configs['in_charge']
            self._fill_default_step_fields(step_name, config)

            # Fill amount and charge code
            logger.info(f"Input Param Amount: {param_amount}")
            self.wd.perform_action("name", "param_amt_ccode[0][amount]", "sendkeys", param_amount)
            
            default_charge_code = self.bs_row_data[nf.BS_INDEX_DEFAULT_CHARGE_CODE]
            if default_charge_code:
                self.wd.perform_action("name", "param_amt_ccode[0][chargecode]", "sendkeys", default_charge_code)
                
            # Fill param matrix if available
            if self.param_rows and self.flow_key != "extend":
                self._fill_param_matrix_charge_codes(param_worksheet, step_name)

            step_id = self._submit_and_get_step_id(step_name, bs_service_id)
            
            result = {"in_charge_id": step_id, "in_charge_name": step_name}
            logger.info(f"Step type IN CHARGE created successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing Step Type {step_name}: {e}")
            self.bs_rpa_remark_fail[step_name] = "Failed"
            return None

    @retryable(max_retries=2)
    def step_type_extend_first_expiry(self, bs_service_id, param_worksheet) -> Optional[Dict]:
        """Execute process for step type EXTENDS FIRST EXPIRY"""
        try:
            step_name = "EXTEND_FIRST_EXPIRY"
            self.current_step_name = step_name
            if self._step_validation(bs_service_id, step_name): return
            logger.info(f"Executing Step Type: {step_name}")
            
            self.wd.redirect_to_page(self.url_step_page, nf.NF_ADD_BTN_INPUT)

            config = self.step_configs['extend_first_expiry']
            self._fill_default_step_fields(step_name, config)

            # Input default duration
            logger.info(f"Input Default Durations: {self.bs_row_data[nf.NF_INDEX_DEFAULT_DURATION_IN_DAYS]} (days)")
            self.wd.perform_action("xpath", "(//input[@name='durations[]'])[1]", "sendkeys", 
                                 self.bs_row_data[nf.NF_INDEX_DEFAULT_DURATION_IN_DAYS])

            # Fill param matrix data if available
            if self.param_rows:
                self._fill_extend_param_matrix(param_worksheet, bs_service_id)

            step_id = self._submit_and_get_step_id(step_name, bs_service_id)
            
            result = {"extend_first_expiry_id": step_id, "extend_first_expiry_name": step_name}
            logger.info(f"Step EXTENDS FIRST EXPIRY successful: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing Step Type EXTENDS FIRST EXPIRY: {e}")
            self.bs_rpa_remark_fail["EXTEND_FIRST_EXPIRY"] = "Failed"
            return None

    def _fill_extend_param_matrix(self, param_worksheet, bs_service_id: str):
        """Fill parameter matrix for extend first expiry"""
        logger.info("Filling up step type sub fields using ParamMatrix values..")
        try:
            for index, row in enumerate(self.param_rows, 2):
                row_param_data = param_worksheet.row_values(row)
                
                # Add new param & duration field
                self.wd.perform_action("xpath", "//a[@onclick='javascript: add_param_duration_field();']", "click")

                # Fill param and duration fields
                param_value = row_param_data[nf.PARAMMATRIX_INDEX_PARAM]
                duration_value = row_param_data[nf.PARAMMATRIX_INDEX_DURATION_IN_DAYS]
                
                logger.info(f"Input Param: {param_value}")
                self.wd.perform_action("xpath", f"(//input[@name='pars[]'])[{index}]", "sendkeys", param_value)
                
                logger.info(f"Input Duration: {duration_value} (days)")
                self.wd.perform_action("xpath", f"(//input[@name='durations[]'])[{index}]", "sendkeys", duration_value)

                # Update worksheet
                self.gs.update_row(row, nf.COLUMN_PARAM_MATRIX_SERVICE_ID, param_worksheet, bs_service_id)
                logger.info(f"Worksheet Updated: {param_worksheet} Row Updated: {row}")
                
        except Exception as e:
            logger.warning(f"Error using paramMatrix values: {e}")
            self.param_rpa_remark_fail["EXTEND_FIRST_EXPIRY"] = "Failed"

    @retryable(max_retries=2)
    def step_type_data_prov_process(self, bs_service_id, param_worksheet) -> Optional[Dict]:
        """Execute process for step type DATA PROV WITH KEYWORD MAPPING or DATA PROV EXTENSION"""
        try:
            logger.info("PROCESSING DATA PROV PROCESS")
            
            # Determine flow type and step configuration
            double_flow_true = self.flow_key == "double"
            
            step_type_name = {
                "double": "Data Prov Extension With Keyword Mapping",
                "extend": "Data Extend Wallet Expiry", 
                "base": "Data Prov With Keyword Mapping"
            }.get(self.flow_key, "Data Prov With Keyword Mapping")
            
            # Create wallet name with flow prefix
            bs_wallet = f"{self.flow_key.upper() + '_' if self.flow_key != 'base' else ''}{self.bs_row_data[nf.NF_INDEX_WALLET]}"
            if self._step_validation(bs_service_id, bs_wallet): return
            logger.info(f"Executing Step Type: {step_type_name.upper()}")
            self.wd.redirect_to_page(self.url_step_page, nf.NF_ADD_BTN_INPUT)
            
            # Fill default step fields
            step_type_value = 96 if double_flow_true else 95
            config = StepConfig(bs_wallet, f"//select[@id='dd_stype_id']//option[@value='{step_type_value}']", str(step_type_value))
            self._fill_default_step_fields(bs_wallet, config)
            
            # Fill wallet type dropdown
            self.wd.perform_action(
                "xpath",
                f"//select[@name='jnetx_wallet_type_id']//option[contains(text(), '{self.bs_row_data[nf.NF_INDEX_WALLET]}')][1]",
                "click"
            )
            
            # Fill default fields
            self._fill_data_prov_default_fields()
            
            # Fill param matrix if available
            if self.param_rows:
                self._fill_data_prov_param_matrix(param_worksheet)
            else:
                logger.info(f"No ParamMatrix found for service name {self.bs_row_data[nf.NF_INDEX_NAME]}")
            
            step_id = self._submit_and_get_step_id(bs_wallet, bs_service_id)
            
            result = {
                "data_prov_id": step_id,
                "data_prov_name": bs_wallet
            }
            
            logger.info(f"Step Type {step_type_name.upper()} successful: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing Step Type {step_type_name}: {e}")
            self.bs_rpa_remark_fail["DATA"] = "Failed"
            return None

    def _fill_data_prov_default_fields(self):
        """Fill default fields for data provisioning"""
        # Input Default Wallet Keyword Field
        logger.info("Input Default Param: DEFAULT")
        logger.info(f"Input Default Wallet Keyword: {self.bs_row_data[nf.NF_INDEX_WALLET]}")
        self.wd.perform_action(
            "xpath",
            "(//input[@name='jnetxprov_walletkeywords2[]'])[1]",
            "sendkeys",
            self.bs_row_data[nf.NF_INDEX_WALLET]
        )

        # Input Default Data Alloc Field
        # default_wallet_amount = int(self.bs_row_data[nf.NF_INDEX_DEFAULT_WALLET_AMOUNT])
        # data_alloc = f"{default_wallet_amount // 1024}GB" if default_wallet_amount > 1000 else f"{default_wallet_amount}MB"
        data_alloc = helper.convert_wallet_amount(self.bs_row_data[nf.NF_INDEX_DEFAULT_WALLET_AMOUNT])
        logger.info(f"Input Default Data Alloc: {data_alloc}")
        self.wd.perform_action(
            "xpath",
            "(//input[@name='jnetxprov_dataallocs2[]'])[1]",
            "sendkeys",
            data_alloc
        )

        # Input Default Wallet Amount Field
        wallet_amount = self.bs_row_data[nf.NF_INDEX_DEFAULT_WALLET_AMOUNT].upper().replace("KB", "").strip()
        logger.info(f"Input Default Wallet Amount: {self.bs_row_data[nf.NF_INDEX_DEFAULT_WALLET_AMOUNT]}")
        self.wd.perform_action(
            "xpath",
            "(//input[@name='jnetxprov_walletamounts2[]'])[1]",
            "sendkeys",
            wallet_amount   
        )

        # Input Default SDM Prov Keyword Field
        logger.info(f"Input Default SDM Prov Keyword: {self.bs_row_data[nf.NF_INDEX_DEFAULT_WALLET_KEYWORD]}")
        self.wd.perform_action(
            "xpath",
            "(//input[@name='jnetxprov_sdmprovkeyword2[]'])[1]",
            "sendkeys",
            self.bs_row_data[nf.NF_INDEX_DEFAULT_WALLET_KEYWORD]
        )

    def _fill_data_prov_param_matrix(self, param_worksheet):
        """Fill parameter matrix for data provisioning"""
        logger.info("Filling up step type sub fields using ParamMatrix values..")
        try:
            for index, row in enumerate(self.param_rows, 2):
                row_param_data = param_worksheet.row_values(row)
                data_alloc_param = helper.convert_wallet_amount(row_param_data[nf.PARAMMATRIX_INDEX_WALLET_AMOUNT])
                param_wallet_amount = row_param_data[nf.PARAMMATRIX_INDEX_WALLET_AMOUNT].upper().replace("KB", "").strip()

                
                # Add new parameter field
                self.wd.perform_action(
                    "xpath",
                    "//a[@onclick='javascript: add_param_walletkeyword_dataalloc_field_sdm_prov();']",
                    "click"
                )

                # Fill parameter fields
                fields_to_fill = [
                    ("jnetxprov_params2[]", row_param_data[nf.PARAMMATRIX_INDEX_PARAM], "Input Param"),
                    ("jnetxprov_walletkeywords2[]", self.bs_row_data[nf.NF_INDEX_WALLET], "Input Wallet Keyword"),
                    ("jnetxprov_dataallocs2[]", data_alloc_param, "Input Data Alloc"),
                    ("jnetxprov_walletamounts2[]", param_wallet_amount, "Input Wallet Amount"),
                    ("jnetxprov_sdmprovkeyword2[]", row_param_data[nf.PARAMMATRIX_INDEX_WALLET_KEYWORD], "Input SDM Prov Keyword")
                ]
                
                for field_name, field_value, log_message in fields_to_fill:
                    logger.info(f"{log_message}: {field_value}")
                    self.wd.perform_action(
                        "xpath",
                        f"(//input[@name='{field_name}'])[{index}]",
                        "sendkeys",
                        field_value
                    )
                
                # Handle data allocation separately (requires conversion)
                # param_wallet_amount = int(row_param_data[nf.PARAMMATRIX_INDEX_WALLET_AMOUNT])
                # data_alloc_param = f"{param_wallet_amount // 1024}GB" if param_wallet_amount > 1000 else f"{param_wallet_amount}MB"
                # logger.info(f"Input Data Alloc: {data_alloc_param}")
                # self.wd.perform_action(
                #     "xpath",
                #     f"(//input[@name='jnetxprov_dataallocs2[]'])[{index}]",
                #     "sendkeys",
                #     data_alloc_param
                # )
                
        except Exception as e:
            logger.warning(f"Error using paramMatrix values: {e}")
            self.param_rpa_remark_fail["DATA"] = "Failed"

    @retryable(max_retries=2)
    def step_type_data_extend_wallet_expiry(self, bs_service_id) -> Optional[Dict]:
        """Execute process for step type DATA EXTEND WALLET EXPIRY"""
        try:
            step_name = "DATA EXTEND WALLET EXPIRY"
            
            # Create wallet name with EXTEND prefix
            bs_wallet = f"EXTEND_{self.bs_row_data[nf.NF_INDEX_WALLET]}"
            if self._step_validation(bs_service_id, bs_wallet): return

            logger.info(f"Executing Step Type: {step_name}")
            
            self.wd.redirect_to_page(self.url_step_page, nf.NF_ADD_BTN_INPUT)            
            config = self.step_configs['data_extend_wallet_expiry']
            self._fill_default_step_fields(bs_wallet, config)

            # Input Jnetx Wallet Type Dropdown
            logger.info(f"Input Jnetx Wallet: {self.bs_row_data[nf.NF_INDEX_WALLET]}")
            self.wd.perform_action(
                "xpath",
                f"//select[@name='jnetx_wallet_type_id']//option[contains(text(), '{self.bs_row_data[nf.NF_INDEX_WALLET]}')][1]",
                "click"
            )

            # Input Expiry Field (convert days to hours)
            expiry_hours = int(self.bs_row_data[nf.NF_INDEX_EXTEND_DURATION_IN_DAYS]) * 24
            logger.info(f"Input Expiry: {expiry_hours}")
            self.wd.perform_action(
                "xpath",
                "(//input[@name='extend_step_expiries[]'])[1]", 
                "sendkeys",
                str(expiry_hours)
            )
            
            step_id = self._submit_and_get_step_id(bs_wallet, bs_service_id)
            
            result = {
                "data_prov_id": step_id,
                "data_prov_name": bs_wallet
            }
            
            logger.info(f"Step Type 'DATA EXTEND WALLET EXPIRY' successful: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in DATA EXTEND WALLET EXPIRY: {e}")
            self.bs_rpa_remark_fail["DATA"] = "Failed" 
            return None

    def _get_sms_voice_conditions(self, step_type_key: str = None) -> Dict[str, bool]:
        """Get SMS/Voice conditions based on step flow construct"""
        step_flow_construct = self.bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT].lower()
        check_value = step_type_key.lower() if step_type_key else step_flow_construct
        
        return {
            "unli_sms": "sms" in check_value,
            "unli_voice": "voice" in check_value
        }

    def _process_sms_voice_steps(self, bs_service_id: str, step_processor_func, step_type_key: str = None) -> Dict:
        """Generic processor for SMS/Voice step types"""
        result_data = {}
        sms_voice_conditions = self._get_sms_voice_conditions(step_type_key)
        
        for sms_voice_key, should_process in sms_voice_conditions.items():
            if should_process:
                try:
                    step_result = step_processor_func(sms_voice_key, bs_service_id)
                    if step_result:
                        result_data.update(step_result)
                except Exception as e:
                    logger.error(f"Error processing {sms_voice_key}: {e}")
                    self.bs_rpa_remark_fail[sms_voice_key.replace("unli_", "").upper()] = "Failed"
        
        return result_data

    @retryable(max_retries=2)
    def step_type_in_prov_service(self, bs_service_id, step_type_key=None) -> Dict:
        """Execute process for step type IN PROV SERVICE"""
        return self._process_sms_voice_steps(bs_service_id, self._create_in_prov_service_step, step_type_key)
    
    @retryable(max_retries=2)
    def step_type_in_add_wallet_fup(self, bs_service_id, step_type_key=None) -> Dict:
        """Execute process for step type IN ADD WALLET FUP"""
        return self._process_sms_voice_steps(bs_service_id, self._create_in_add_wallet_fup_step, step_type_key)

    @retryable(max_retries=2)  
    def step_type_in_extend_wallet_expiry(self, bs_service_id, step_type_key=None) -> Dict:
        """Execute process for step type IN EXTEND WALLET EXPIRY"""
        return self._process_sms_voice_steps(bs_service_id, self._create_in_extend_wallet_expiry_step, step_type_key)

    def _create_in_prov_service_step(self, sms_voice_key: str, bs_service_id: str) -> Dict:
        """Create individual IN PROV SERVICE step"""
        step_type_name, _ = helper.nf_get_in_prov_values(self.flow_key, sms_voice_key, "sms_voice_service")
        brand = self.bs_row_data[nf.NF_INDEX_BRAND].lower()
        
        if sms_voice_key == "unli_sms":
            step_name = "SMS_ALLNET_UNLI"
            amount_field_value = 500 if brand == "ghp" else 700
            service_id = 196
        else:
            step_name = "VOICE_ALLNET_UNLI"
            amount_field_value = 300 if brand == "ghp" else 200
            service_id = 197
        if self._step_validation(bs_service_id, step_name): return
        logger.info(f"Executing Step Type: {step_type_name.upper()}")
        
        self.wd.redirect_to_page(self.url_step_page, nf.NF_ADD_BTN_INPUT)
        
        # Fill default fields
        config = StepConfig(step_name, f"//select[@id='dd_stype_id']//option[@value='5']", "5")
        self._fill_default_step_fields(step_name, config, sms_voice=sms_voice_key)

        # Fill service and amount fields
        self.wd.perform_action("xpath", f"//select[@name='in_service_id']//option[@value='{service_id}']", "click")
        self.wd.perform_action("name", nf.NF_STEP_FUP_AMOUNT_FIELD, "sendkeys", amount_field_value)

        step_id = self._submit_and_get_step_id(step_name, bs_service_id)
        
        return {
            f"{sms_voice_key}_id": step_id,
            f"{sms_voice_key}_name": step_name
        }
    
    def _create_in_add_wallet_fup_step(self, sms_voice_key: str, bs_service_id: str) -> Dict:
        """Create individual IN ADD WALLET FUP step"""
        step_type_name, _ = helper.nf_get_in_prov_values(self.flow_key, sms_voice_key, "sms_voice_service")
        brand = self.bs_row_data[nf.NF_INDEX_BRAND].lower()
        
        if sms_voice_key == "unli_sms":
            step_name = "DOUBLE_SMS_ALLNET_UNLI"
            amount_field_value = 500 if brand == "ghp" else 700
            service_id = 196
        else:
            step_name = "DOUBLE_VOICE_ALLNET_UNLI" 
            amount_field_value = 300 if brand == "ghp" else 200
            service_id = 197
        if self._step_validation(bs_service_id, step_name): return
        logger.info(f"Executing Step Type: {step_type_name.upper()}")
        
        self.wd.redirect_to_page(self.url_step_page, nf.NF_ADD_BTN_INPUT)
        
        # Fill default fields (step type 129 = IN ADD WALLET FUP)
        config = StepConfig(step_name, "//select[@id='dd_stype_id']//option[@value='129']", "129")
        self._fill_default_step_fields(step_name, config, sms_voice=sms_voice_key)

        # Fill IN Service dropdown
        logger.info(f"Dropdown IN Service: {service_id}")
        self.wd.perform_action("xpath", f"//select[@name='in_fup_step_service']//option[@value='{service_id}']", "click")

        # Fill amount field
        logger.info(f"Input Amount: {amount_field_value}")
        self.wd.perform_action("name", nf.NF_STEP_AMOUNT_FIELD, "sendkeys", amount_field_value)

        step_id = self._submit_and_get_step_id(step_name, bs_service_id)
        
        return {
            f"{sms_voice_key}_id": step_id,
            f"{sms_voice_key}_name": step_name
        }

    def _create_in_extend_wallet_expiry_step(self, sms_voice_key: str, bs_service_id: str) -> Dict:
        """Create individual IN EXTEND WALLET EXPIRY step"""
        step_name = "EXTEND_VOICE_ALLNET_UNLI" if sms_voice_key == "unli_voice" else "EXTEND_SMS_ALLNET_UNLI"
        service_id = 197 if sms_voice_key == "unli_voice" else 196
        if self._step_validation(bs_service_id, step_name): return
        logger.info(f"Executing Step Type: IN EXTEND WALLET EXPIRY")
        
        self.wd.redirect_to_page(self.url_step_page, nf.NF_ADD_BTN_INPUT)
        
        # Fill default fields (assuming step type value from constants)
        config = StepConfig(step_name, nf.STEP_TYPE_IN_EXTEND_WALLET_EXPIRY, "")
        self._fill_default_step_fields(step_name, config, sms_voice=sms_voice_key)

        # Fill IN Service dropdown
        logger.info(f"Dropdown IN Service: {service_id}")
        self.wd.perform_action("xpath", f"//select[@name='in_service_id']//option[@value='{service_id}']", "click")

        # Input Expiry Field (convert days to hours)
        expiry_hours = int(self.bs_row_data[nf.NF_INDEX_EXTEND_DURATION_IN_DAYS]) * 24
        logger.info(f"Input Expiry: {expiry_hours}")
        self.wd.perform_action("xpath", "(//input[@name='extend_step_expiries[]'])[1]", "sendkeys", str(expiry_hours))

        step_id = self._submit_and_get_step_id(step_name, bs_service_id)
        
        return {
            f"{sms_voice_key}_id": step_id,
            f"{sms_voice_key}_name": step_name
        }

    @retryable(max_retries=2)
    def step_type_hlr_ply(self, bs_service_id) -> Optional[Dict]:
        """Execute process for step type HLR - PLY"""
        try:
            step_name = "HLR_PLY"
            if self._step_validation(bs_service_id, step_name): return
            logger.info(f"Executing Step Type: {step_name}")
            
            self.wd.redirect_to_page(self.url_step_page, nf.NF_ADD_BTN_INPUT)

            config = self.step_configs['hlr_ply']
            self._fill_default_step_fields(step_name, config)

            # Select HLR Ply Service based on brand
            service_value = "3" if self.bs_row_data[nf.NF_INDEX_BRAND].lower() == "ghp" else "2"
            self.wd.perform_action("xpath", f"//select[@name='hlr_ply_service_id']//option[@value='{service_value}']", "click")

            step_id = self._submit_and_get_step_id(step_name, bs_service_id)
            
            result = {"hlr_ply_id": step_id, "hlr_ply_name": step_name}
            logger.info(f"Step type 'HLR - PLY' successful: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process step type 'HLR PLY': {e}")
            self.bs_rpa_remark_fail["HLR"] = "Failed"
            return None

    @retryable(max_retries=2)
    def step_type_hlr_set_vssr_tplid(self, bs_service_id) -> Optional[Dict]:
        """Execute process for step type HLR SET VSSR TPLID"""
        try:
            step_name = "HLR_SET_VSSR_TPLID"
            if self._step_validation(bs_service_id, step_name): return
            logger.info(f"Executing Step Type: {step_name}")

            self.wd.redirect_to_page(self.url_step_page, nf.NF_ADD_BTN_INPUT)

            config = self.step_configs['hlr_set_vssr']
            self._fill_default_step_fields(step_name, config)

            self._submit_and_get_step_id(step_name, bs_service_id)

            result = {"hlr_set_vssr_name": step_name}
            logger.info(f"Step type HLR SET VSSR TPLID created successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing Step Type HLR SET VSSR TPLID: {e}")
            self.bs_rpa_remark_fail["HLR_VSSR"] = "Failed"
            return None

    @retryable(max_retries=2) 
    def step_type_hlr_set_diamrrs_tplid(self, bs_service_id) -> Optional[Dict]:
        """Execute process for step type HLR SET DIAMRRS TPLID"""
        try:
            step_name = "HLR_SET_DIAMRRS_TPLID" 
            if self._step_validation(bs_service_id, step_name): return
            logger.info(f"Executing Step Type: {step_name}")

            self.wd.redirect_to_page(self.url_step_page, nf.NF_ADD_BTN_INPUT)

            config = self.step_configs['hlr_set_diamrrs']
            self._fill_default_step_fields(step_name, config)

            # Set profile dropdown
            self.wd.perform_action("xpath", "//select[@name='hlr_diamrrs_profile']//option[@value='1']", "click")
            
            self._submit_and_get_step_id(step_name, bs_service_id)

            result = {"hlr_set_diamrrs_name": step_name}
            logger.info(f"Step type HLR SET DIAMRRS TPLID created successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing Step Type HLR SET DIAMRRS TPLID: {e}")
            self.bs_rpa_remark_fail["HLR_DIAMRRS"] = "Failed"
            return None

    @retryable(max_retries=2)
    def step_type_sdm_postpaid_create_subscriber(self, bs_service_id) -> Optional[Dict]:
        """Execute process for step type SDM POSTPAID CREATE SUBSCRIBER"""
        try:
            step_name = "SDM_POSTPAID_CREATE_SUBSCRIBER"
            if self._step_validation(bs_service_id, step_name): return
            logger.info(f"Executing Step Type: {step_name}")

            self.wd.redirect_to_page(self.url_step_page, nf.NF_ADD_BTN_INPUT)

            config = self.step_configs['sdm_postpaid']
            self._fill_default_step_fields(step_name, config)
            
            self._submit_and_get_step_id(step_name, bs_service_id)

            result = {"sdm_postpaid_name": step_name}
            logger.info(f"Step type SDM POSTPAID CREATE SUBSCRIBER created successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing Step Type SDM POSTPAID CREATE SUBSCRIBER: {e}")
            self.bs_rpa_remark_fail["SDM_POSTPAID"] = "Failed"
            return None
    
    @retryable(max_retries=2)
    def step_type_check_has_subscription(self, bs_service_id) -> Optional[Dict]:
        """Execute process for step type CHECK HAS SUBSCRIPTIONS"""
        try:
            step_name = "CHECK_HAS_SUBSCRIPTION"
            if self._step_validation(bs_service_id, step_name): return
            logger.info(f"Executing Step Type: CHECK HAS SUBSCRIPTIONS")
            
            self.wd.redirect_to_page(self.url_step_page, nf.NF_ADD_BTN_INPUT)

            config = self.step_configs['check_has_subscription']
            self._fill_default_step_fields(step_name, config)

            # Convert Check has ids from string to tuple
            list_active_service_id = [x.strip() for x in self.bs_row_data[nf.BS_INDEX_CHECK_HAS_IDS].split(",") if x.strip()]
            first_id = list_active_service_id.pop(0)
            self.wd.perform_action("xpath", f"//select[@name='check_has_subs_services[]']//option[@value='{first_id}']", "click")
            step_id = self._submit_and_get_step_id(step_name, bs_service_id)
        
            if len(list_active_service_id) > 1:
                self._select_active_subscriptions(bs_service_id, step_id, step_name, list_active_service_id)
            
            result = {"check_has_subscription_id": step_id, "check_has_subscription_name": step_name}
            logger.info(f"Step type 'CHECK HAS SUBSCRIPTIONS' successfully define: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process step type 'CHECK HAS SUBSCRIPTION': {e}")
            self.bs_rpa_remark_fail["CHECK_HAS_ADD"] = "Failed"
            return None
        
    def _select_active_subscriptions(self, service_id, step_id, step_name, list_active_service_id):
        """Select step params for CHECK HAS SUBSCRIPTIONS"""
        logger.info(f"Processing step params of CHECK HAS SUBSCRIPTIONS {step_id}")
        
        try:
            logger.info(f"List of active service id/ids to be added: {list_active_service_id}")
            self.wd.redirect_to_page(f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=details&id={step_id}", f"({nf.NF_ADD_BTN_INPUT})[2]")
            # self.wd.redirect_to_page(f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=bulk_services&op=details&id={service_id}", nf.BS_EDIT_PAGE_REMINDER_MSG_BTN)
            # self.wd.driver.find_element(By.XPATH, f"//td[@align='left' and contains(text(), ' {step_name} ')]/preceding::a[1]").click()
            for active_id in list_active_service_id: 
                try:
                    xpath_param_service_id = f"//select[@name='param_check_has_subs_service']//option[@value='{active_id}']"
                    logger.info(f"Adding service id: {active_id} to step params..")
                    self.wd.wait_until_element("xpath", xpath_param_service_id, "visible")
                    self.wd.wait_until_element("xpath", nf.ADD_BTN_INPUT_2, "clickable")
                    self.wd.driver.find_element(By.XPATH, xpath_param_service_id).click()
                    #self.wd.perform_action("xpath", nf.ADD_BTN_INPUT_2, "click")
                    self.wd.driver.find_element(By.XPATH, nf.ADD_BTN_INPUT_2).click()
                    #time.sleep(3)
                    self.wd.wait_until_element("xpath", f"//td[@align='left' and normalize-space(text())='{active_id}']", "visible")
                    logger.info(f"Service id: {active_id} successfully added for ({step_id}) CHECK_HAS_SUBSCRIPTION")
                    
                except NoSuchElementException as e:
                    logger.error(f"Unable to add service id '{active_id}' Error: Element not found\nERROR:{e}")
                    continue
                except TimeoutException as e:
                    logger.warning(f"Submit button is not loading properly, retrying..")
                    logger.info(f"2nd Attempt: Adding service id: {active_id} to step params..")
                    self.wd.wait_until_element("xpath", nf.ADD_BTN_INPUT_2, "clickable")
                    self.wd.driver.find_element(By.XPATH, xpath_param_service_id).click()
                    self.wd.driver.find_element(By.XPATH, nf.ADD_BTN_INPUT_2).click()
                    self.wd.wait_until_element("xpath", f"//td[@align='left' and normalize-space(text())='{active_id}']", "visible")
                    logger.info(f"Service id: {active_id} successfully added for ({step_id}) CHECK_HAS_SUBSCRIPTION")
                    continue
                #self.wd.perform_action("xpath", f"//select[@name='param_check_has_subs_service']//option[@value='{active_id}']", "click"
                
        except Exception:
            logger.error("An error has occurred while adding service id to step params...")

    def recover_step_data(self, step_name: str, service_id: str) -> Optional[str]:
        """Recover step data if submission fails"""
        try:
            self.wd.redirect_to_page(f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=bulk_services&op=details&id={service_id}", nf.BS_EDIT_PAGE_REMINDER_MSG_BTN)

            element_id = self.wd.driver.find_element(
                By.XPATH, 
                f"//td[@align='left' and contains(text(), ' {step_name} ')]/preceding::a[1]"
            )
            
            if not element_id:
                raise NoSuchElementException(f"Element still not found..")

            logger.info(f"Step id successfully recovered! {element_id.text}")
            return element_id.text
            
        except Exception as e:
            logger.error(f"Unable to find step name: {step_name} - {e}")
            return None
        
    def _step_validation(self, service_id, step_name):
        logger.info(f"Check if existing step {step_name}")
        # Redirect to Edit Bulk service page
        base_url = get_env_variable("WEBTOOL_BASE_URL")
        self.wd.redirect_to_page(f"{base_url}/nf/index.php?mod=bulk_services&op=details&id={service_id}", nf.BS_EDIT_PAGE_REMINDER_MSG_BTN)

        # Validate if step name exist in edit page of Bulk Service
        try:
            self.wd.driver.find_element(By.XPATH, f"//td[@align='left' and contains(text(), ' {step_name} ')]/preceding::a[1]")
            is_exist = True
        except NoSuchElementException:
            is_exist = False
        logger.info(f"Step '{step_name}' Exist?: {is_exist}")
        return is_exist
    
            