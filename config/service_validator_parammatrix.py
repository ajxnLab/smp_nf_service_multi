from typing import Dict, List, Any, Optional
import re
from enum import Enum
from config.config import nf
# from nf_constants import NfConstants

# nf = NfConstants()

class ValidationResult:
    def __init__(self):
        self.is_valid = True
        self.errors = []
        self.warnings = []
    
    def add_error(self, field: str, message: str):
        self.is_valid = False
        self.errors.append(f"{field}: {message}")
    
    def add_warning(self, field: str, message: str):
        self.warnings.append(f"{field}: {message}")

class StepFlowType(Enum):
    TEST = "TEST"

    # Prepaid CTL Services
    PREPAID_CTL_DATA = "Prepaid CTL with Data"
    PREPAID_CTL_DATA_UNLI_SMS = "Prepaid CTL with Data and Unli SMS"
    PREPAID_CTL_UNLI_SMS_VOICE = "Prepaid CTL with Unli SMS and Unli Voice"
    PREPAID_CTL_DATA_SMS_VOICE = "Prepaid CTL with Data, Unli SMS and Unli Voice"
    
    # Prepaid OPM Services
    PREPAID_OPM_DATA = "Prepaid OPM with Data"
    PREPAID_OPM_DATA_UNLI_SMS = "Prepaid OPM with Data and Unli SMS"
    PREPAID_OPM_DATA_UNLI_VOICE = "Prepaid OPM with Data and Unli Voice"
    PREPAID_OPM_UNLI_SMS_VOICE = "Prepaid OPM with Unli SMS and Unli Voice"
    PREPAID_OPM_DATA_SMS_VOICE = "Prepaid OPM with Data, Unli SMS and Unli Voice"
    
    # Postpaid Services
    POSTPAID_RECURRING = "Postpaid Recurring"
    POSTPAID_ROLLOVER = "Postpaid Rollover"
    
    # Roaming Services
    ROAMING_PREPAID_TRIGGER = "Roaming Prepaid Trigger Service"
    ROAMING_POSTPAID_TRIGGER = "Roaming Postpaid Trigger Service"
    ROAMING_PREPAID_MAIN = "Roaming Prepaid Main Service"
    ROAMING_POSTPAID_MAIN = "Roaming Postpaid Main Service"
    
    # Bulk CTL Services
    PREPAID_CTL_DATA_BULK_SMS = "Prepaid CTL with Data and Bulk SMS"
    PREPAID_CTL_BULK_SMS_VOICE = "Prepaid CTL with Bulk SMS and Bulk Voice"
    PREPAID_CTL_DATA_BULK_SMS_VOICE = "Prepaid CTL with Data, Bulk SMS and Bulk Voice"

    # Bulk OPM Services
    PREPAID_OPM_DATA_BULK_SMS = "Prepaid OPM with Data and Bulk SMS"
    PREPAID_OPM_BULK_SMS_VOICE = "Prepaid OPM with Bulk SMS and Bulk Voice"
    PREPAID_OPM_DATA_BULK_SMS_VOICE = "Prepaid OPM with Data, Bulk SMS and Bulk Voice"

class ParamConfigValidator:
    def __init__(self):
        self.validation_rules = self._setup_validation_rules()
    
    def _setup_validation_rules(self) -> Dict[str, Dict]:
        """Define validation rules based on exact Step and Flow Construct matching"""
        return {
            # Exact match for specific step flow construct
            StepFlowType.TEST.value: {
                "required_fields": [
                    "SERVICE NAME", "SERVICE ID", "PARAM", "AMOUNT", "DURATION IN DAYS",
                    "WALLET KEYWORD", "WALLET AMOUNT (MB)", "Step and Flow Construct"
                ],
                "conditional_requirements": {
                    "With Double Flow": {
                        "Yes": ["Extend AMOUNT", "Extend Duration in Days"]
                    },
                    "With Extend Steps": {
                        "Yes": ["Extend Keyword"]
                    },
                    "Deprov on Empty": {
                        "Yes": ["Deprovision Keyword"]
                    }
                },
                "field_patterns": {
                    "SERVICE ID": r"^\d+$",
                    "PARAM": r"^[1-9]\d*$",
                    "AMOUNT": r"^\d+(\.\d{2})?$",
                    "DURATION IN DAYS": r"^[1-9]\d*$",
                    "WALLET AMOUNT (MB)": r"^[1-9]\d*$",
                    "SERVICE NAME": r"^P\d+_.*",  # Must start with P for prepaid
                    "WALLET KEYWORD": r"^[A-Z_]+.*"
                },
                "allowed_values": {
                    "Expiries RPA REMARKS": ["PARAM Successfully Defined", "Failed", "Pending", "In Progress"],
                    "With Double Flow": ["Yes", "No"],
                    "With Extend Steps": ["Yes", "No"],
                    "Deprov on Empty": ["Yes", "No"],
                    "Subscription-Less": ["Yes", "No"]
                },
                "business_rules": {
                    "ctl_data_sms_voice": True,
                    "requires_wallet_validation": True,
                    "supports_unli_features": True
                }
            },
            StepFlowType.ROAMING_POSTPAID_MAIN.value: {
                    "required_fields": [
                        nf.PARAMMATRIX_INDEX_PARAM, 
                        nf.PARAMMATRIX_INDEX_AMOUNT,
                        nf.PARAMMATRIX_INDEX_DURATION_IN_DAYS, 
                        nf.PARAMMATRIX_INDEX_WALLET_KEYWORD, 
                        nf.PARAMMATRIX_INDEX_WALLET_AMOUNT,
                        nf.PARAMMATRIX_INDEX_CHARGE_CODE,
                        nf.PARAMMATRIX_INDEX_SERVICE_NAME
                    ],
                    "field_patterns": {
                        #nf.PARAMMATRIX_INDEX_PARAM: r"^[1-9]\d*$",
                        nf.PARAMMATRIX_INDEX_AMOUNT: r"^\d+(\.\d{2})?$",
                        # nf.PARAMMATRIX_INDEX_DURATION_IN_DAYS: r"^[1-9]\d*$",
                    },
                    "allowed_values": {
                        "With Extend Flow": ["Yes", "No"],
                    },
            },
            # Category-based fallback rules
            "_category_rules": {
                "Bulk": {
                    "required_fields": [
                        nf.PARAMMATRIX_INDEX_PARAM, 
                        nf.PARAMMATRIX_INDEX_DURATION_IN_DAYS, 
                        nf.PARAMMATRIX_INDEX_WALLET_KEYWORD, 
                        nf.PARAMMATRIX_INDEX_WALLET_AMOUNT,
                        nf.PARAMMATRIX_INDEX_SERVICE_NAME,
                        nf.PARAMMATRIX_KEY_SMS_AMOUNT,
                        nf.PARAMMATRIX_KEY_VOICE_AMOUNT
                    ],
                    "field_patterns": {
                       # nf.PARAMMATRIX_INDEX_PARAM: r"^[1-9]\d*$",
                        nf.PARAMMATRIX_INDEX_AMOUNT: r"^\d+(\.\d{2})?$",
                    },
                },
                "Prepaid CTL": {
                    "required_fields": [
                        nf.PARAMMATRIX_INDEX_PARAM, 
                        nf.PARAMMATRIX_INDEX_AMOUNT, 
                        nf.PARAMMATRIX_INDEX_DURATION_IN_DAYS, 
                        nf.PARAMMATRIX_INDEX_WALLET_KEYWORD, 
                        nf.PARAMMATRIX_INDEX_WALLET_AMOUNT,
                        nf.PARAMMATRIX_INDEX_SERVICE_NAME
                    ],
                    "field_patterns": {
                        #nf.PARAMMATRIX_INDEX_PARAM: r"^[1-9]\d*$",
                        nf.PARAMMATRIX_INDEX_AMOUNT: r"^\d+(\.\d{2})?$",
                        nf.PARAMMATRIX_INDEX_DURATION_IN_DAYS: r"^[1-9]\d*$",
                    },
                    "allowed_values": {
                        "With Extend Flow": ["Yes", "No"],
                    },
                    "business_rules": {
                        "ctl_category": True,
                        #"naming_convention": "P_prefix"
                    }
                },
                "Prepaid OPM": {
                    "required_fields": [
                        nf.PARAMMATRIX_INDEX_PARAM, 
                        nf.PARAMMATRIX_INDEX_DURATION_IN_DAYS, 
                        nf.PARAMMATRIX_INDEX_WALLET_KEYWORD, 
                        nf.PARAMMATRIX_INDEX_WALLET_AMOUNT,
                        nf.PARAMMATRIX_INDEX_SERVICE_NAME
                    ],
                    # "conditional_requirements": {
                    #     "With Extend Flow": {
                    #         "Yes": [nf.PARAMMATRIX_INDEX_AMOUNT]
                    #     }
                    # },
                    "field_patterns": {
                        #nf.PARAMMATRIX_INDEX_PARAM: r"^[1-9]\d*$",
                        nf.PARAMMATRIX_INDEX_AMOUNT: r"^\d+(\.\d{2})?$",
                        nf.PARAMMATRIX_INDEX_DURATION_IN_DAYS: r"^[1-9]\d*$",
                    },
                    "allowed_values": {
                        "With Extend Flow": ["Yes", "No"],
                    },
                    "business_rules": {
                        "opm_category": True,
                        #"naming_convention": "P_prefix"
                    }
                },
                "Postpaid": {
                    "required_fields": [
                        nf.PARAMMATRIX_INDEX_PARAM, 
                        nf.PARAMMATRIX_INDEX_DURATION_IN_DAYS, 
                        nf.PARAMMATRIX_INDEX_WALLET_KEYWORD, 
                        nf.PARAMMATRIX_INDEX_WALLET_AMOUNT,
                        nf.PARAMMATRIX_INDEX_SERVICE_NAME
                    ],
                    "field_patterns": {
                        #nf.PARAMMATRIX_INDEX_PARAM: r"^[1-9]\d*$",
                        nf.PARAMMATRIX_INDEX_AMOUNT: r"^\d+(\.\d{2})?$",
                        #nf.PARAMMATRIX_INDEX_DURATION_IN_DAYS: r"^[1-9]\d*$",
                    },
                    "allowed_values": {
                        "With Extend Flow": ["Yes", "No"],
                    },
                    # "business_rules": {
                    #     "ctl_category": True,
                    #     "naming_convention": "P_prefix"
                    # }
                },
                "Roaming": {
                    "required_fields": [
                        nf.PARAMMATRIX_INDEX_PARAM, 
                        nf.PARAMMATRIX_INDEX_DURATION_IN_DAYS, 
                        nf.PARAMMATRIX_INDEX_WALLET_KEYWORD, 
                        nf.PARAMMATRIX_INDEX_WALLET_AMOUNT,
                        nf.PARAMMATRIX_INDEX_SERVICE_NAME
                    ],
                    "field_patterns": {
                        #nf.PARAMMATRIX_INDEX_PARAM: r"^[1-9]\d*$",
                        nf.PARAMMATRIX_INDEX_AMOUNT: r"^\d+(\.\d{2})?$",
                        #nf.PARAMMATRIX_INDEX_DURATION_IN_DAYS: r"^[1-9]\d*$",
                    },
                },
            }
        }
    
    def validate_param_config(self, data: Dict[str, Any]) -> ValidationResult:
        """Main validation function"""
        result = ValidationResult()
        
        # Get the step flow construct to determine validation rules
        step_flow_construct = data.get("Step and Flow Construct", "")
        
        if not step_flow_construct:
            result.add_error("Step and Flow Construct", "Field is required")
            return result
        
        # Try exact match first
        rules = self.validation_rules.get(step_flow_construct)
        category_rules = None
        
        # If no exact match, try category-based rules
        if not rules:
            category_rules = self._get_category_rules(step_flow_construct)
            if category_rules:
                rules = category_rules
            else:
                result.add_warning("Step and Flow Construct", 
                                 f"No specific validation rules defined for: {step_flow_construct}")
                # Use minimal generic validation
                rules = self._get_generic_rules()
        
        # Validate required fields
        self._validate_required_fields(data, rules, result)
        
        # Validate field patterns
        self._validate_field_patterns(data, rules, result)
        
        # Validate allowed values
        self._validate_allowed_values(data, rules, result)
        
        # Validate conditional requirements
        self._validate_conditional_requirements(data, rules, result)
        
        # Validate business rules
        self._validate_business_rules(data, step_flow_construct, result)
        
        # Apply category-specific business rules if using category rules
        if category_rules:
            self._validate_category_business_rules(data, step_flow_construct, rules, result)
        
        return result
    
    def _get_category_rules(self, step_flow_construct: str) -> Optional[Dict]:
        """Get validation rules based on category keywords in the construct"""
        category_rules = self.validation_rules.get("_category_rules", {})
        
        # Check each category to see if it matches the construct
        for category, rules in category_rules.items():
            if category in step_flow_construct:
                return rules
        
        return None
    
    def _validate_required_fields(self, data: Dict, rules: Dict, result: ValidationResult):
        """Validate that all required fields are present and not empty"""
        required_fields = rules.get("required_fields", [])
        
        for field in required_fields:
            value = data.get(field, "")
            if not value or str(value).strip() == "":
                result.add_error(field, "Field is required and cannot be empty")
    
    def _validate_field_patterns(self, data: Dict, rules: Dict, result: ValidationResult):
        """Validate field values against regex patterns"""
        patterns = rules.get("field_patterns", {})
        
        for field, pattern in patterns.items():
            value = str(data.get(field, ""))
            if value and not re.match(pattern, value):
                result.add_error(field, f"Value '{value}' does not match required pattern")
    
    def _validate_allowed_values(self, data: Dict, rules: Dict, result: ValidationResult):
        """Validate field values against allowed values"""
        allowed_values = rules.get("allowed_values", {})
        
        for field, allowed_list in allowed_values.items():
            value = data.get(field, "")
            if value and value not in allowed_list:
                result.add_error(field, 
                    f"Value '{value}' is not allowed. Allowed values: {', '.join(allowed_list)}")
    
    def _validate_conditional_requirements(self, data: Dict, rules: Dict, result: ValidationResult):
        """Validate conditional field requirements"""
        conditional_reqs = rules.get("conditional_requirements", {})
        
        for trigger_field, conditions in conditional_reqs.items():
            trigger_value = data.get(trigger_field, "")
            
            for condition_value, required_fields in conditions.items():
                if trigger_value == condition_value:
                    for required_field in required_fields:
                        field_value = data.get(required_field, "")
                        if not field_value or str(field_value).strip() == "":
                            result.add_error(required_field, 
                                f"Field is required when '{trigger_field}' is '{condition_value}'")
    
    def _validate_business_rules(self, data: Dict, step_flow_construct: str, result: ValidationResult):
        """Validate general business rules"""
        
        # Validate SERVICE ID is positive
        service_id = data.get("SERVICE ID", "")
        if service_id:
            try:
                sid = int(service_id)
                if sid <= 0:
                    result.add_error("SERVICE ID", "SERVICE ID must be a positive number")
            except ValueError:
                result.add_error("SERVICE ID", "SERVICE ID must be a valid number")
        
        # Validate AMOUNT is positive
        amount = data.get("AMOUNT", "")
        if amount:
            try:
                amt = float(amount)
                if amt <= 0:
                    result.add_error("AMOUNT", "AMOUNT must be greater than 0")
            except ValueError:
                result.add_error("AMOUNT", "AMOUNT must be a valid number")
        
        # Validate DURATION is positive
        # duration = data.get("DURATION IN DAYS", "")
        # if duration:
        #     try:
        #         dur = int(duration)
        #         if dur <= 0:
        #             result.add_error("DURATION IN DAYS", "Duration must be greater than 0")
        #     except ValueError:
        #         result.add_error("DURATION IN DAYS", "Duration must be a valid number")
        
        # Validate naming conventions for prepaid services
        # service_name = data.get("SERVICE NAME", "")
        # if "Prepaid" in step_flow_construct and service_name:
        #     if not service_name.startswith("P"):
        #         result.add_error("SERVICE NAME", "Prepaid service names must start with 'P'")
        #     if not re.match(r"^P\d+_.*", service_name):
        #         result.add_warning("SERVICE NAME", 
        #             "Service name should follow pattern: P + Numbers + Underscore + Description")
        
        # Validate wallet amount for data services
        if "Data" in step_flow_construct:
            wallet_amount = data.get("WALLET AMOUNT (MB)", "")
            if wallet_amount:
                try:
                    amount = int(wallet_amount)
                    if amount <= 0:
                        result.add_error("WALLET AMOUNT (MB)", "Wallet amount must be greater than 0")
                    elif amount < 10:
                        result.add_warning("WALLET AMOUNT (MB)", "Wallet amount seems low for a data service")
                except ValueError:
                    result.add_error("WALLET AMOUNT (MB)", "Wallet amount must be a valid number")
    
    def _validate_category_business_rules(self, data: Dict, step_flow_construct: str, 
                                        rules: Dict, result: ValidationResult):
        """Validate category-specific business rules"""
        business_rules = rules.get("business_rules", {})
        
        # CTL-specific validations
        if business_rules.get("ctl_category") or business_rules.get("ctl_data_sms_voice"):
            self._validate_ctl_specific_rules(data, step_flow_construct, result)
        
        # OPM-specific validations
        if business_rules.get("opm_category") or business_rules.get("opm_specific"):
            self._validate_omp_specific_rules(data, step_flow_construct, result)
        
        # Data service validations
        if business_rules.get("requires_wallet_validation"):
            self._validate_wallet_requirements(data, result)
    
    def _validate_ctl_specific_rules(self, data: Dict, step_flow_construct: str, result: ValidationResult):
        """Validate CTL-specific business rules"""
        # CTL services with Unli features should have specific configurations
        if "Unli SMS" in step_flow_construct or "Unli Voice" in step_flow_construct:
            # Check if SMS/Voice amounts are properly configured
            sms_amount = data.get("SMS BULK Amount (Number of Texts)", "")
            voice_amount = data.get("VOICE Amount (In Minutes)", "")
            
            if "Unli SMS" in step_flow_construct and sms_amount and sms_amount != "0":
                result.add_warning("SMS BULK Amount (Number of Texts)", 
                    "Unli SMS services typically don't specify bulk SMS amounts")
            
            if "Unli Voice" in step_flow_construct and voice_amount and voice_amount != "0":
                result.add_warning("VOICE Amount (In Minutes)", 
                    "Unli Voice services typically don't specify voice minutes")
        
        # CTL services should have appropriate wallet keywords
        wallet_keyword = data.get("WALLET KEYWORD", "")
        if wallet_keyword and not wallet_keyword.startswith("PR_"):
            result.add_warning("WALLET KEYWORD", 
                "CTL wallet keywords typically start with 'PR_'")
    
    def _validate_omp_specific_rules(self, data: Dict, step_flow_construct: str, result: ValidationResult):
        """Validate OPM-specific business rules"""
        # OPM services have different wallet keyword patterns
        wallet_keyword = data.get("WALLET KEYWORD", "")
        if wallet_keyword:
            if not re.match(r"^[A-Z_]+.*", wallet_keyword):
                result.add_warning("WALLET KEYWORD", 
                    "OPM wallet keywords should follow uppercase naming convention")
        
        # OPM param validation
        param = data.get("PARAM", "")
        if param:
            try:
                p = int(param)
                if p < 1:
                    result.add_error("PARAM", "OPM PARAM should be 1 or higher")
                elif p > 50:
                    result.add_warning("PARAM", "OPM PARAM seems unusually high")
            except ValueError:
                pass  # Pattern validation will catch this
    
    def _validate_wallet_requirements(self, data: Dict, result: ValidationResult):
        """Validate wallet-related requirements"""
        wallet_keyword = data.get("WALLET KEYWORD", "")
        wallet_amount = data.get("WALLET AMOUNT (MB)", "")
        
        if wallet_keyword and not wallet_amount:
            result.add_warning("WALLET AMOUNT (MB)", 
                "Wallet keyword specified but no wallet amount provided")
        
        if wallet_amount and not wallet_keyword:
            result.add_error("WALLET KEYWORD", 
                "Wallet amount specified but no wallet keyword provided")
    
    def _get_generic_rules(self) -> Dict:
        """Generic validation rules when specific construct rules don't exist"""
        return {
            "required_fields": ["SERVICE NAME", "SERVICE ID", "Step and Flow Construct"],
            "field_patterns": {
                "SERVICE ID": r"^\d+$",
                "PARAM": r"^\d+$"
            },
            "allowed_values": {
                "Expiries RPA REMARKS": ["PARAM Successfully Defined", "Failed", "Pending", "In Progress"]
            }
        }
    
    def validate_batch(self, data_list: List[Dict[str, Any]]) -> List[ValidationResult]:
        """Validate multiple parameter configurations"""
        results = []
        for i, data in enumerate(data_list):
            result = self.validate_param_config(data)
            # Add row information for easier tracking
            result.row_number = i + 1
            results.append(result)
        return results

#Example usage and testing
# if __name__ == "__main__":
#     # Sample data for exact match - "Prepaid CTL with Data, Unli SMS and Unli Voice"
#     sample_data_exact = {
#         'PARAM': '1', 
#         'AMOUNT': '25', 
#         'DURATION IN DAYS': '1', 
#         'WALLET KEYWORD': 'PR_COMBO_500MB1D_DVB', 
#         'WALLET AMOUNT (MB)': '500', 
#         'Chargcode': '', 
#         'SMS BULK Amount (Number of Texts)': '', 
#         'VOICE Amount (In Minutes)': '', 
#         'SERVICE NAME': 'P75000_500M01D25A01F', 
#         'SERVICE ID': '', 
#         'Expiries RPA REMARKS': 'PARAM Successfully Defined',
#         'With Extend Flow': "No",
#         "Step and Flow Construct": "Roaming Postpaid Main Service"
#     }
    
#     #Sample data for category fallback - different construct
#     sample_data_category = {
#         'PARAM': '2', 
#         'AMOUNT': '', 
#         'DURATION IN DAYS': '3', 
#         'WALLET KEYWORD': 'OPM_DATA_PROMO', 
#         'WALLET AMOUNT (MB)': '200', 
#         'Chargcode': '', 
#         'SMS BULK Amount (Number of Texts)': '', 
#         'VOICE Amount (In Minutes)': '', 
#         'SERVICE NAME': 'P80000_OPM_DATA_SPECIAL', 
#         'SERVICE ID': '', 
#         'Expiries RPA REMARKS': 'PARAM Successfully Defined',
#         'With Extend Flow': "No",
#         "Step and Flow Construct": "Prepaid OPM with Special Data Offer",  # No exact match
#     }
    
#     # Create validator and test both samples
#     validator = ParamConfigValidator()
    
#     print("=== Testing Exact Match (Step and Flow Construct) ===")
#     result_exact = validator.validate_param_config(sample_data_exact)
#     print(f"Validation Result: {'PASSED' if result_exact.is_valid else 'FAILED'}")
#     print(f"Errors: {len(result_exact.errors)}")
#     for error in result_exact.errors:
#         print(f"  - {error}")
#     print(f"Warnings: {len(result_exact.warnings)}")
#     for warning in result_exact.warnings:
#         print(f"  - {warning}")
    
#     print("\n=== Testing Category Fallback (Prepaid OPM) ===")
#     result_category = validator.validate_param_config(sample_data_category)
#     print(f"Validation Result: {'PASSED' if result_category.is_valid else 'FAILED'}")
#     print(f"Errors: {len(result_category.errors)}")
#     for error in result_category.errors:
#         print(f"  - {error}")
#     print(f"Warnings: {len(result_category.warnings)}")
#     for warning in result_category.warnings:
#         print(f"  - {warning}")