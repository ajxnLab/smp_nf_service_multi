from typing import Dict, List, Any, Optional
import re
from datetime import datetime
from enum import Enum
from config.config import nf

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

    # Dummy Service
    DUMMY_SERVICE = "Dummy Service"

class ServiceConfigValidator:
    def __init__(self):
        self.validation_rules = self._setup_validation_rules()
    
    def _setup_validation_rules(self) -> Dict[str, Dict]:
        """Define validation rules based on Step and Flow Construct"""
        return {
            # Match Sepcific Step and flow construct
            StepFlowType.TEST.value: {
                "required_fields": [
                    "Name", "Wallet", "Brand", "SMP Name", "Promo Name",
                    "Default AMOUNT", "Default\nDuration in Days", 
                    "Default\nWallet Keyword", "Default\nWallet Amount (in MB)"
                ],
                "conditional_requirements": {
                    "With Double Flow": {
                        "Yes": ["Extend Amount (PARAM)", "Extend Duration in Days"]
                    },
                    "With Extend Steps and Flow": {
                        "Yes": ["Extend Keyword"]
                    },
                    "Deprov on Empty": {
                        "Yes": ["Deprovision Keyword"]
                    }
                },
                "field_patterns": {
                    "ServiceID": r"^\d+$",
                    "Default\nWallet Amount (in MB)": r"^\d+$",
                    "Thread Count": r"^\d+$",
                    "Max Daily Extensions": r"^\d+$",
                    "Max Total Extensions": r"^\d+$"
                },
                "allowed_values": {
                    "Wallet Type": ["Data", "Voice", "SMS", "Combo"],
                    "Include in Group Status Inquiry": ["Yes", "No"],
                    "Deprov on Empty": ["Yes", "No"],
                    "Subscription-Less": ["Yes", "No"],
                    "With Double Flow": ["Yes", "No"],
                    "With Extend Steps and Flow": ["Yes", "No"],
                    "Allow Multiple": ["Yes", "No"]
                }
            },
            
            StepFlowType.POSTPAID_RECURRING.value: {
                "required_fields": [
                    nf.NF_INDEX_NAME, 
                    nf.NF_INDEX_WALLET, 
                    nf.NF_INDEX_THREAD_COUNT, 
                    nf.NF_INDEX_BRAND, 
                    nf.NF_INDEX_SMP_NAME, 
                    nf.NF_INDEX_MAX_DAILY_EXT,
                    nf.NF_INDEX_MAX_TOTAL_EXT,
                    nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT,
                    nf.NF_INDEX_PROMO_NAME,
                    nf.NF_INDEX_DEFAULT_AMOUNT, 
                    nf.NF_INDEX_DEFAULT_DURATION_IN_DAYS,
                    nf.BS_INDEX_TACKON,
                    nf.NF_INDEX_DEFAULT_PARAM,
                    nf.NF_INDEX_DEFAULT_WALLET_KEYWORD,
                    nf.NF_INDEX_DEFAULT_WALLET_AMOUNT,
                    nf.BS_INDEX_SOCID
                ],
                "conditional_requirements": {
                    nf.BS_INDEX_TACKON: {
                        "Add Check-Has Logic to This Service": [nf.BS_INDEX_CHECK_HAS_IDS]
                    }
                },
                "field_patterns": {
                    nf.NF_INDEX_SERVICE_ID: r"^\d+$",  # Must be positive integer
                    nf.NF_INDEX_THREAD_COUNT: r"^[1-9]\d*$",  # Must be positive integer
                    nf.NF_INDEX_DEFAULT_AMOUNT: r"^[1-9]\d*$",  # Allow decimals for CTL
                    nf.NF_INDEX_DEFAULT_WALLET_AMOUNT: r"^[1-9]\d*$",
                    nf.NF_INDEX_MAX_DAILY_EXT: r"^\d+$",
                    nf.NF_INDEX_MAX_TOTAL_EXT: r"^\d+$"
                },
                "allowed_values": {
                    nf.NF_INDEX_WALLET_TYPE: ["Data", "Voice", "SMS", "Combo"],
                    nf.NF_INDEX_GROUP_STATUS_INQUIRY: ["Yes", "No"],
                    nf.NF_INDEX_DEPROV_ON_EMPTY: ["Yes", "No"],
                    nf.NF_INDEX_DEFAULT_PARAM: ["DEFAULT"],
                    nf.BS_INDEX_TACKON: ["None", "Add Check-Has Logic to This Service", "Add This Service to Other Check-Has Logic"],
                    nf.NF_INDEX_SUBSCRIPTION_LESS: ["Yes", "No"]
                },
            },
            StepFlowType.POSTPAID_ROLLOVER.value: {
                "required_fields": [
                    nf.NF_INDEX_NAME, 
                    nf.NF_INDEX_WALLET, 
                    nf.NF_INDEX_THREAD_COUNT, 
                    nf.NF_INDEX_BRAND, 
                    nf.NF_INDEX_SMP_NAME, 
                    nf.NF_INDEX_MAX_DAILY_EXT,
                    nf.NF_INDEX_MAX_TOTAL_EXT,
                    nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT,
                    nf.NF_INDEX_PROMO_NAME,
                    nf.NF_INDEX_DEFAULT_AMOUNT, 
                    nf.NF_INDEX_DEFAULT_DURATION_IN_DAYS,
                    nf.BS_INDEX_TACKON,
                    nf.NF_INDEX_DEFAULT_PARAM,
                    nf.NF_INDEX_DEFAULT_WALLET_KEYWORD,
                    nf.NF_INDEX_DEFAULT_WALLET_AMOUNT,
                    nf.BS_INDEX_SOCID
                ],
                "conditional_requirements": {
                    nf.BS_INDEX_TACKON: {
                        "Add Check-Has Logic to This Service": [nf.BS_INDEX_CHECK_HAS_IDS]
                    }
                },
                "field_patterns": {
                    nf.NF_INDEX_SERVICE_ID: r"^\d+$",  # Must be positive integer
                    nf.NF_INDEX_THREAD_COUNT: r"^[1-9]\d*$",  # Must be positive integer
                    nf.NF_INDEX_DEFAULT_AMOUNT: r"^[1-9]\d*$",  # Allow decimals for CTL
                    nf.NF_INDEX_DEFAULT_WALLET_AMOUNT: r"^[1-9]\d*$",
                    nf.NF_INDEX_MAX_DAILY_EXT: r"^\d+$",
                    nf.NF_INDEX_MAX_TOTAL_EXT: r"^\d+$"
                },
                "allowed_values": {
                    nf.NF_INDEX_WALLET_TYPE: ["Data", "Voice", "SMS", "Combo"],
                    nf.NF_INDEX_GROUP_STATUS_INQUIRY: ["Yes", "No"],
                    nf.NF_INDEX_DEPROV_ON_EMPTY: ["Yes", "No"],
                    nf.NF_INDEX_DEFAULT_PARAM: ["DEFAULT"],
                    nf.BS_INDEX_TACKON: ["None", "Add Check-Has Logic to This Service", "Add This Service to Other Check-Has Logic"],
                    nf.NF_INDEX_SUBSCRIPTION_LESS: ["Yes", "No"]
                },
            },

            StepFlowType.DUMMY_SERVICE.value: {
                "required_fields": [
                    nf.NF_INDEX_NAME, 
                    nf.NF_INDEX_WALLET, 
                    nf.NF_INDEX_THREAD_COUNT, 
                    nf.NF_INDEX_BRAND, 
                    nf.NF_INDEX_SMP_NAME, 
                    nf.NF_INDEX_MAX_DAILY_EXT,
                    nf.NF_INDEX_MAX_TOTAL_EXT,
                    nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT,
                    nf.NF_INDEX_PROMO_NAME,
                    nf.NF_INDEX_DEFAULT_DURATION_IN_DAYS,
                ],
                "field_patterns": {
                    nf.NF_INDEX_SERVICE_ID: r"^\d+$",  # Must be positive integer
                    nf.NF_INDEX_THREAD_COUNT: r"^[1-9]\d*$",  # Must be positive integer
                    nf.NF_INDEX_MAX_DAILY_EXT: r"^\d+$",
                    nf.NF_INDEX_MAX_TOTAL_EXT: r"^\d+$"
                },
                "allowed_values": {
                    nf.NF_INDEX_GROUP_STATUS_INQUIRY: ["No"],
                    nf.NF_INDEX_WALLET_TYPE: ["Data", "Voice", "SMS", "Combo"],
                    nf.NF_INDEX_SUBSCRIPTION_LESS: ["Yes", "No"]
                },
            },
            # Category-based rules - applies to all services containing these keywords
            "_category_rules": {
                StepFlowType.ROAMING_POSTPAID_MAIN.value: {
                    "required_fields": [
                        nf.NF_INDEX_NAME, 
                        nf.NF_INDEX_WALLET, 
                        nf.NF_INDEX_THREAD_COUNT, 
                        nf.NF_INDEX_BRAND, 
                        nf.NF_INDEX_SMP_NAME, 
                        nf.NF_INDEX_MAX_DAILY_EXT,
                        nf.NF_INDEX_MAX_TOTAL_EXT,
                        nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT,
                        nf.NF_INDEX_PROMO_NAME,
                        nf.NF_INDEX_DEFAULT_AMOUNT, 
                        nf.NF_INDEX_DEFAULT_DURATION_IN_DAYS,
                        nf.BS_INDEX_TACKON,
                        nf.NF_INDEX_DEFAULT_PARAM,
                        nf.NF_INDEX_DEFAULT_WALLET_KEYWORD,
                        nf.NF_INDEX_DEFAULT_WALLET_AMOUNT,
                        nf.BS_INDEX_DEFAULT_CHARGE_CODE
                    ],
                    "conditional_requirements": {
                        nf.BS_INDEX_TACKON: {
                            "Add Check-Has Logic to This Service": [nf.BS_INDEX_CHECK_HAS_IDS]
                        }
                    },
                    "field_patterns": {
                        nf.NF_INDEX_SERVICE_ID: r"^\d+$",  # Must be positive integer
                        nf.NF_INDEX_THREAD_COUNT: r"^[1-9]\d*$",  # Must be positive integer
                        nf.NF_INDEX_DEFAULT_AMOUNT: r"^[1-9]\d*$",  # Allow decimals for CTL
                        nf.NF_INDEX_DEFAULT_WALLET_AMOUNT: r"^[1-9]\d*$",
                        nf.NF_INDEX_MAX_DAILY_EXT: r"^\d+$",
                        nf.NF_INDEX_MAX_TOTAL_EXT: r"^\d+$"
                    },
                    "allowed_values": {
                        nf.NF_INDEX_WALLET_TYPE: ["Data", "Voice", "SMS", "Combo"],
                        nf.NF_INDEX_GROUP_STATUS_INQUIRY: ["Yes", "No"],
                        nf.NF_INDEX_DEPROV_ON_EMPTY: ["Yes", "No"],
                        nf.NF_INDEX_DEFAULT_PARAM: ["DEFAULT"],
                        nf.BS_INDEX_TACKON: ["None", "Add Check-Has Logic to This Service", "Add This Service to Other Check-Has Logic"],
                        nf.NF_INDEX_SUBSCRIPTION_LESS: ["Yes", "No"]
                    },
                },
                "Bulk": {
                    "required_fields": [
                        nf.NF_INDEX_NAME, 
                        nf.NF_INDEX_WALLET, 
                        nf.NF_INDEX_THREAD_COUNT, 
                        nf.NF_INDEX_BRAND, 
                        nf.NF_INDEX_SMP_NAME, 
                        nf.NF_INDEX_MAX_DAILY_EXT,
                        nf.NF_INDEX_MAX_TOTAL_EXT,
                        nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT,
                        nf.NF_INDEX_PROMO_NAME,
                        nf.NF_INDEX_DEFAULT_AMOUNT, 
                        nf.NF_INDEX_DEFAULT_DURATION_IN_DAYS,
                        nf.BS_INDEX_TACKON,
                        nf.NF_INDEX_DEFAULT_PARAM,
                        nf.NF_INDEX_DEFAULT_WALLET_KEYWORD,
                        nf.NF_INDEX_DEFAULT_WALLET_AMOUNT,
                        nf.BS_KEY_SMS_VOICE_NETWORK_TYPE,
                        nf.BS_KEY_SMS_AMOUNT,
                        nf.BS_KEY_VOICE_AMOUNT
                    ],
                    "conditional_requirements": {
                        nf.BS_INDEX_TACKON: {
                            "Add Check-Has Logic to This Service": [nf.BS_INDEX_CHECK_HAS_IDS]
                        }
                    },
                    "field_patterns": {
                        nf.NF_INDEX_SERVICE_ID: r"^\d+$",  # Must be positive integer
                        nf.NF_INDEX_THREAD_COUNT: r"^[1-9]\d*$",  # Must be positive integer
                        nf.NF_INDEX_DEFAULT_AMOUNT: r"^[1-9]\d*$",  # Allow decimals for CTL
                        nf.NF_INDEX_MAX_DAILY_EXT: r"^\d+$",
                        nf.NF_INDEX_MAX_TOTAL_EXT: r"^\d+$"
                    },
                    "allowed_values": {
                        nf.NF_INDEX_WALLET_TYPE: ["Data", "Voice", "SMS", "Combo"],
                        nf.NF_INDEX_GROUP_STATUS_INQUIRY: ["Yes", "No"],
                        nf.NF_INDEX_DEPROV_ON_EMPTY: ["Yes", "No"],
                        nf.NF_INDEX_DEFAULT_PARAM: ["DEFAULT"],
                        nf.BS_INDEX_TACKON: ["None", "Add Check-Has Logic to This Service", "Add This Service to Other Check-Has Logic"],
                        nf.BS_KEY_SMS_VOICE_NETWORK_TYPE: ["All Network", "Intra (Globe to Globe))"],
                        nf.NF_INDEX_SUBSCRIPTION_LESS: ["Yes", "No"]
                    },
                },
                "Prepaid CTL": {
                    "required_fields": [
                        nf.NF_INDEX_NAME, 
                        nf.NF_INDEX_WALLET, 
                        nf.NF_INDEX_THREAD_COUNT, 
                        nf.NF_INDEX_BRAND, 
                        nf.NF_INDEX_SMP_NAME, 
                        nf.NF_INDEX_MAX_DAILY_EXT,
                        nf.NF_INDEX_MAX_TOTAL_EXT,
                        nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT,
                        nf.NF_INDEX_PROMO_NAME,
                        nf.NF_INDEX_DEFAULT_AMOUNT, 
                        nf.NF_INDEX_DEFAULT_DURATION_IN_DAYS,
                        nf.BS_INDEX_TACKON,
                        nf.NF_INDEX_DEFAULT_PARAM,
                        nf.NF_INDEX_DEFAULT_WALLET_KEYWORD,
                        nf.NF_INDEX_DEFAULT_WALLET_AMOUNT
                    ],
                    "conditional_requirements": {
                        # "With Double Flow": {
                        #     "Yes": [nf.NF_INDEX_DEFAULT_AMOUNT]
                        # },
                        nf.NF_INDEX_WITH_EXTEND_STEPS_AND_FLOW: {
                            "Yes": [nf.NF_INDEX_EXTEND_AMOUNT, nf.NF_INDEX_EXTEND_DURATION_IN_DAYS]
                        },
                        nf.BS_INDEX_TACKON: {
                            "Add Check-Has Logic to This Service": [nf.BS_INDEX_CHECK_HAS_IDS]
                        }
                    },
                    "field_patterns": {
                        nf.NF_INDEX_SERVICE_ID: r"^\d+$",  # Must be positive integer
                        nf.NF_INDEX_THREAD_COUNT: r"^[1-9]\d*$",  # Must be positive integer
                        nf.NF_INDEX_DEFAULT_AMOUNT: r"^[1-9]\d*$",  # Allow decimals for CTL
                        nf.NF_INDEX_DEFAULT_DURATION_IN_DAYS: r"^[1-9]\d*$", # Must be positive
                        nf.NF_INDEX_DEFAULT_WALLET_AMOUNT: r"^[1-9]\d*$",
                        nf.NF_INDEX_MAX_DAILY_EXT: r"^\d+$",
                        nf.NF_INDEX_MAX_TOTAL_EXT: r"^\d+$"
                    },
                    "allowed_values": {
                        nf.NF_INDEX_WALLET_TYPE: ["Data", "Voice", "SMS", "Combo"],
                        nf.NF_INDEX_GROUP_STATUS_INQUIRY: ["Yes", "No"],
                        nf.NF_INDEX_DEPROV_ON_EMPTY: ["Yes", "No"],
                        nf.NF_INDEX_WITH_DOUBLE_FLOW: ["Yes", "No"],
                        nf.NF_INDEX_WITH_EXTEND_STEPS_AND_FLOW: ["Yes", "No"],
                        nf.NF_INDEX_DEFAULT_PARAM: ["DEFAULT"],
                        nf.BS_INDEX_TACKON: ["None", "Add Check-Has Logic to This Service", "Add This Service to Other Check-Has Logic"],
                        nf.BS_KEY_SMS_VOICE_NETWORK_TYPE: ["N/A"],
                        nf.NF_INDEX_SUBSCRIPTION_LESS: ["Yes", "No"]
                    },
                },
                "Prepaid OPM": {
                    "required_fields": [
                        nf.NF_INDEX_NAME, 
                        nf.NF_INDEX_WALLET, 
                        nf.NF_INDEX_THREAD_COUNT, 
                        nf.NF_INDEX_BRAND, 
                        nf.NF_INDEX_SMP_NAME, 
                        nf.NF_INDEX_MAX_DAILY_EXT,
                        nf.NF_INDEX_MAX_TOTAL_EXT,
                        nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT,
                        nf.NF_INDEX_PROMO_NAME,
                        nf.NF_INDEX_DEFAULT_DURATION_IN_DAYS,
                        nf.BS_INDEX_TACKON,
                        nf.NF_INDEX_DEFAULT_PARAM,
                        nf.NF_INDEX_DEFAULT_WALLET_KEYWORD,
                        nf.NF_INDEX_DEFAULT_WALLET_AMOUNT
                    ],
                    "conditional_requirements": {
                        # "With Double Flow": {
                        #     "Yes": [nf.NF_INDEX_DEFAULT_AMOUNT]
                        # },
                        nf.NF_INDEX_WITH_EXTEND_STEPS_AND_FLOW: {
                            "Yes": [nf.NF_INDEX_EXTEND_AMOUNT, nf.NF_INDEX_EXTEND_DURATION_IN_DAYS]
                        },
                        nf.BS_INDEX_TACKON: {
                            "Add Check-Has Logic to This Service": [nf.BS_INDEX_CHECK_HAS_IDS]
                        }
                    },
                    "field_patterns": {
                        nf.NF_INDEX_SERVICE_ID: r"^\d+$",  # Must be positive integer
                        nf.NF_INDEX_THREAD_COUNT: r"^[1-9]\d*$",  # Must be positive integer
                        nf.NF_INDEX_DEFAULT_AMOUNT: r"^[1-9]\d*$",  # Allow decimals for CTL
                        nf.NF_INDEX_DEFAULT_DURATION_IN_DAYS: r"^[1-9]\d*$", # Must be positive
                        nf.NF_INDEX_DEFAULT_WALLET_AMOUNT: r"^[1-9]\d*$",
                        nf.NF_INDEX_MAX_DAILY_EXT: r"^\d+$",
                        nf.NF_INDEX_MAX_TOTAL_EXT: r"^\d+$"
                    },
                    "allowed_values": {
                        nf.NF_INDEX_WALLET_TYPE: ["Data", "Voice", "SMS", "Combo"],
                        nf.NF_INDEX_GROUP_STATUS_INQUIRY: ["Yes", "No"],
                        nf.NF_INDEX_DEPROV_ON_EMPTY: ["Yes", "No"],
                        nf.NF_INDEX_WITH_DOUBLE_FLOW: ["Yes", "No"],
                        nf.NF_INDEX_WITH_EXTEND_STEPS_AND_FLOW: ["Yes", "No"],
                        nf.NF_INDEX_DEFAULT_PARAM: ["DEFAULT"],
                        nf.BS_INDEX_TACKON: ["None", "Add Check-Has Logic to This Service", "Add This Service to Other Check-Has Logic"],
                        nf.BS_KEY_SMS_VOICE_NETWORK_TYPE: ["N/A"],
                        nf.NF_INDEX_SUBSCRIPTION_LESS: ["Yes", "No"]
                    },
                    "business_rules": {
                        "opm_specific": True,
                        "requires_wallet": True,
                        "supports_extensions": True
                    }
                },
                "Postpaid": {
                    "required_fields": [
                        nf.NF_INDEX_NAME, 
                        nf.NF_INDEX_WALLET, 
                        nf.NF_INDEX_THREAD_COUNT, 
                        nf.NF_INDEX_BRAND, 
                        nf.NF_INDEX_SMP_NAME, 
                        nf.NF_INDEX_MAX_DAILY_EXT,
                        nf.NF_INDEX_MAX_TOTAL_EXT,
                        nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT,
                        nf.NF_INDEX_PROMO_NAME,
                        nf.NF_INDEX_DEFAULT_AMOUNT, 
                        nf.NF_INDEX_DEFAULT_DURATION_IN_DAYS,
                        nf.BS_INDEX_TACKON,
                        nf.NF_INDEX_DEFAULT_PARAM,
                        nf.NF_INDEX_DEFAULT_WALLET_KEYWORD,
                        nf.NF_INDEX_DEFAULT_WALLET_AMOUNT
                    ],
                    "conditional_requirements": {
                        nf.BS_INDEX_TACKON: {
                            "Add Check-Has Logic to This Service": [nf.BS_INDEX_CHECK_HAS_IDS]
                        }
                    },
                    "field_patterns": {
                        nf.NF_INDEX_SERVICE_ID: r"^\d+$",  # Must be positive integer
                        nf.NF_INDEX_THREAD_COUNT: r"^[1-9]\d*$",  # Must be positive integer
                        nf.NF_INDEX_DEFAULT_AMOUNT: r"^[1-9]\d*$",  # Allow decimals for CTL
                        #nf.NF_INDEX_DEFAULT_DURATION_IN_DAYS: r"^[1-9]\d*$", # Must be positive
                        nf.NF_INDEX_DEFAULT_WALLET_AMOUNT: r"^[1-9]\d*$",
                        nf.NF_INDEX_MAX_DAILY_EXT: r"^\d+$",
                        nf.NF_INDEX_MAX_TOTAL_EXT: r"^\d+$"
                    },
                    "allowed_values": {
                        nf.NF_INDEX_WALLET_TYPE: ["Data", "Voice", "SMS", "Combo"],
                        nf.NF_INDEX_GROUP_STATUS_INQUIRY: ["Yes", "No"],
                        nf.NF_INDEX_DEPROV_ON_EMPTY: ["Yes", "No"],
                        nf.NF_INDEX_DEFAULT_PARAM: ["DEFAULT"],
                        nf.BS_INDEX_TACKON: ["None", "Add Check-Has Logic to This Service", "Add This Service to Other Check-Has Logic"],
                        nf.BS_KEY_SMS_VOICE_NETWORK_TYPE: ["N/A"],
                        nf.NF_INDEX_SUBSCRIPTION_LESS: ["Yes", "No"]
                    },
                },
                "Roaming": {
                    "required_fields": [
                        nf.NF_INDEX_NAME, 
                        nf.NF_INDEX_WALLET, 
                        nf.NF_INDEX_THREAD_COUNT, 
                        nf.NF_INDEX_BRAND, 
                        nf.NF_INDEX_SMP_NAME, 
                        nf.NF_INDEX_MAX_DAILY_EXT,
                        nf.NF_INDEX_MAX_TOTAL_EXT,
                        nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT,
                        nf.NF_INDEX_PROMO_NAME,
                        #nf.NF_INDEX_DEFAULT_AMOUNT, 
                        nf.NF_INDEX_DEFAULT_DURATION_IN_DAYS,
                        nf.BS_INDEX_TACKON,
                        nf.NF_INDEX_DEFAULT_PARAM,
                        nf.NF_INDEX_DEFAULT_WALLET_KEYWORD,
                        nf.NF_INDEX_DEFAULT_WALLET_AMOUNT,
                        #nf.BS_INDEX_DEFAULT_CHARGE_CODE
                    ],
                    "conditional_requirements": {
                        nf.BS_INDEX_TACKON: {
                            "Add Check-Has Logic to This Service": [nf.BS_INDEX_CHECK_HAS_IDS]
                        }
                    },
                    "field_patterns": {
                        nf.NF_INDEX_SERVICE_ID: r"^\d+$",  # Must be positive integer
                        nf.NF_INDEX_THREAD_COUNT: r"^[1-9]\d*$",  # Must be positive integer
                        nf.NF_INDEX_DEFAULT_AMOUNT: r"^[1-9]\d*$",  # Allow decimals for CTL
                        #nf.NF_INDEX_DEFAULT_WALLET_AMOUNT: r"^[1-9]\d*$",
                        nf.NF_INDEX_MAX_DAILY_EXT: r"^\d+$",
                        nf.NF_INDEX_MAX_TOTAL_EXT: r"^\d+$"
                    },
                    "allowed_values": {
                        nf.NF_INDEX_WALLET_TYPE: ["Data", "Voice", "SMS", "Combo"],
                        nf.NF_INDEX_GROUP_STATUS_INQUIRY: ["Yes", "No"],
                        nf.NF_INDEX_DEPROV_ON_EMPTY: ["Yes", "No"],
                        nf.NF_INDEX_DEFAULT_PARAM: ["DEFAULT"],
                        nf.BS_INDEX_TACKON: ["None", "Add Check-Has Logic to This Service", "Add This Service to Other Check-Has Logic"],
                        nf.BS_KEY_SMS_VOICE_NETWORK_TYPE: ["N/A"],
                        nf.NF_INDEX_SUBSCRIPTION_LESS: ["Yes", "No"]
                    },
                },
            }
            # Add more step flow construct rules here
        }
    
    def validate_service_config(self, data: Dict[str, Any]) -> ValidationResult:
        """Main validation function"""
        result = ValidationResult()
        
        # Get the step flow construct to determine validation rules
        step_flow_construct = data.get("Step and Flow Construct", "")
        
        if not step_flow_construct:
            result.add_error("Step and Flow Construct", "Field is required")
            return result
        
        # Get validation rules for this construct type
        rules = self.validation_rules.get(step_flow_construct)
        category_rules = None
        
        # Check for category-based rules if no exact match
        if not rules:
            category_rules = self._get_category_rules(step_flow_construct)
            if category_rules:
                rules = category_rules
            else:
                result.add_warning("Step and Flow Construct", 
                                 f"No specific validation rules defined for: {step_flow_construct}")
                # Use generic validation
                rules = self._get_generic_rules()
        
        # Validate required fields
        self._validate_required_fields(data, rules, result)
        
        # Validate field patterns
        self._validate_field_patterns(data, rules, result)
        
        # Validate allowed values
        self._validate_allowed_values(data, rules, result)
        
        # Validate conditional requirements
        self._validate_conditional_requirements(data, rules, result)
        
        # Validate specific business rules
        self._validate_business_rules(data, step_flow_construct, result)
        
        # Apply category-specific business rules
        if category_rules:
            self._validate_category_business_rules(data, step_flow_construct, rules, result)
        
        return result
    
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
        """Validate specific business rules"""
        
        # Validate deployment date format
        deployment_date = data.get("Deployment Date", "")
        if deployment_date:
            try:
                datetime.strptime(deployment_date, "%Y-%m-%d")
            except ValueError:
                result.add_error("Deployment Date", 
                    "Date must be in YYYY-MM-DD format")
        
        # Validate naming conventions
        name = data.get("Name", "")
        smp_name = data.get("SMP Name", "")
        if name and smp_name:
            # if not name.startswith("P") or not smp_name.startswith("G"):
            #     result.add_warning("Name/SMP Name", 
            #         "Name should start with 'P' and SMP Name should start with 'G'")
            if name != smp_name:
                result.add_error("Name/SMP Name", 
                    f"Bulk service name ({name}) and SMP name ({smp_name}) are required to be identical.")
        
        # Validate wallet amount for data services
        if "Data" in step_flow_construct:
            wallet_amount = data.get("Default\nWallet Amount (in MB)", "")
            if wallet_amount:
                try:
                    amount = int(wallet_amount)
                    if amount <= 0:
                        result.add_error("Default\nWallet Amount (in MB)", 
                            "Amount must be greater than 0")
                except ValueError:
                    result.add_error("Default\nWallet Amount (in MB)", 
                        "Amount must be a valid number")
        
        # Validate keyword patterns
        keywords_to_check = [
            "Extend Keyword", "Provision Keyword", 
            "Deprovision Keyword", "Status Keyword"
        ]
        
        for keyword_field in keywords_to_check:
            keyword = data.get(keyword_field, "")
            if keyword and not self._is_valid_regex_pattern(keyword):
                result.add_warning(keyword_field, 
                    "Keyword appears to contain regex pattern - ensure it's valid")
    
    def _get_category_rules(self, step_flow_construct: str) -> Optional[Dict]:
        """Get validation rules based on category keywords in the construct"""
        category_rules = self.validation_rules.get("_category_rules", {})
        
        # Check each category to see if it matches the construct
        for category, rules in category_rules.items():
            if category in step_flow_construct:
                return rules
        
        return None
    
    def _validate_category_business_rules(self, data: Dict, step_flow_construct: str, 
                                        rules: Dict, result: ValidationResult):
        """Validate category-specific business rules"""
        business_rules = rules.get("business_rules", {})
        
        # CTL-specific validations
        if business_rules.get("ctl_specific"):
            self._validate_ctl_rules(data, result)
        
        # OPM-specific validations
        if business_rules.get("omp_specific"):
            self._validate_omp_rules(data, result)
        
        # Postpaid-specific validations
        if business_rules.get("postpaid_specific"):
            self._validate_postpaid_rules(data, result)
        
        # Trigger-specific validations
        if business_rules.get("trigger_specific"):
            self._validate_postpaid_rules(data, result)

        # Roaming-specific validations
        if business_rules.get("roaming_specific"):
            self._validate_roaming_rules(data, result)
        
        # Bulk-specific validations
        if business_rules.get("bulk_specific"):
            self._validate_bulk_rules(data, step_flow_construct, result)
    
    def _validate_ctl_rules(self, data: Dict, result: ValidationResult):
        """Validate CTL-specific business rules"""
        # CTL services typically don't use Gyro Command
        gyro_command = data.get("Gyro Command", "")
        if gyro_command and gyro_command.strip():
            result.add_warning("Gyro Command", 
                "CTL services typically don't require Gyro Command")
        
        # CTL services should have specific naming pattern
        name = data.get("Name", "")
        if name and not name.startswith("P"):
            result.add_error("Name", "CTL service names should start with 'P'")
    
    def _validate_omp_rules(self, data: Dict, result: ValidationResult):
        """Validate OMP-specific business rules"""
        # OMP services require wallet
        wallet = data.get("Wallet", "")
        if not wallet or wallet.strip() == "":
            result.add_error("Wallet", "OMP services require a wallet")
        
        # OMP services support extensions
        with_extend = data.get("With Extend Steps and Flow", "")
        if with_extend == "Yes":
            extend_keyword = data.get("Extend Keyword", "")
            if not extend_keyword:
                result.add_error("Extend Keyword", 
                    "OMP services with extensions require Extend Keyword")
    
    def _validate_postpaid_rules(self, data: Dict, result: ValidationResult):
        """Validate Postpaid-specific business rules"""
        # Postpaid requires SOCID
        # socid = data.get("SOCID", "")
        # if not socid or socid.strip() == "":
        #     result.add_error("SOCID", "Postpaid services require SOCID")
        
        # Postpaid shouldn't have extension features
        with_extend = data.get("With Extend Steps and Flow", "")
        if with_extend == "Yes":
            result.add_warning("With Extend Steps and Flow", 
                "Postpaid services typically don't support extensions")
        
        # Postpaid is never subscription-less
        subscription_less = data.get("Subscription-Less", "")
        if subscription_less == "Yes":
            result.add_error("Subscription-Less", 
                "Postpaid services cannot be subscription-less")
    
    def _validate_roaming_rules(self, data: Dict, result: ValidationResult):
        """Validate Roaming-specific business rules"""
        # Roaming services often have special pricing considerations
        default_amount = data.get("Default AMOUNT", "")
        if default_amount:
            try:
                amount = float(default_amount)
                if amount < 1:
                    result.add_warning("Default AMOUNT", 
                        "Roaming services typically have higher pricing")
            except ValueError:
                pass  # Let pattern validation handle this
    
    def _is_valid_regex_pattern(self, pattern: str) -> bool:
        """Check if a string is a valid regex pattern"""
        try:
            re.compile(pattern)
            return True
        except re.error:
            return False
        
        # Roaming services should specify network type
        # network_type = data.get("SMS Voice Network Type", "")
        # if not network_type or network_type == "N/A":
        #     result.add_warning("SMS Voice Network Type", 
        #         "Roaming services should specify network type")
    
    def _validate_bulk_rules(self, data: Dict, step_flow_construct: str, result: ValidationResult):
        """Validate Bulk service-specific business rules"""
        # Bulk SMS services must have SMS amount
        if "Bulk SMS" in step_flow_construct:
            sms_amount = data.get("SMS BULK Amount (Number of Texts)", "")
            if not sms_amount or sms_amount.strip() == "":
                result.add_error("SMS BULK Amount (Number of Texts)", 
                    "Bulk SMS services require SMS amount")
        
        # Bulk Voice services must have voice amount
        if "Bulk Voice" in step_flow_construct:
            voice_amount = data.get("VOICE Amount (In Minutes)", "")
            if not voice_amount or voice_amount.strip() == "":
                result.add_error("VOICE Amount (In Minutes)", 
                    "Bulk Voice services require voice amount")
        
        # Bulk services typically have higher thread counts
        thread_count = data.get("Thread Count", "")
        if thread_count:
            try:
                count = int(thread_count)
                if count < 2:
                    result.add_warning("Thread Count", 
                        "Bulk services typically require higher thread counts (≥2)")
            except ValueError:
                pass  # Let pattern validation handle this
    
    def _get_generic_rules(self) -> Dict:
        """Generic validation rules when specific construct rules don't exist"""
        return {
            "required_fields": ["Name", "Step and Flow Construct"],
            "field_patterns": {
                "Thread Count": r"^\d+$",
                "Default AMOUNT": r"^\d+$"
            },
            "allowed_values": {
                "Include in Group Status Inquiry": ["Yes", "No"],
                "Deprov on Empty": ["Yes", "No"],
                "Subscription-Less": ["Yes", "No"]
            }
        }
    
    def validate_batch(self, data_list: List[Dict[str, Any]]) -> List[ValidationResult]:
        """Validate multiple service configurations"""
        results = []
        for i, data in enumerate(data_list):
            result = self.validate_service_config(data)
            # Add row information for easier tracking
            if hasattr(result, 'row_number'):
                result.row_number = data.get('_row_number', i + 1)
            results.append(result)
        return results

# # Example usage and testing
# if __name__ == "__main__":
#     # Sample data
#     sample_data = {
#         "ServiceID": "2032",
#         "Name": "P70000_100M01D08A01F",
#         "Include in Group Status Inquiry": "Yes",
#         "Wallet Type": "Data",
#         "Wallet": "PR_REWARDALL_OA_TEST",
#         "Thread Count": "4",
#         "Brand": "GHP",
#         "SMP Name": "P70000_100M01D08A01F",
#         "Deprov on Empty": "Yes",
#         "Subscription-Less": "No",
#         "Max Daily Extensions": "0",
#         "Max Total Extensions": "0",
#         "Promo Name": "REWCOMBO105G",
#         "Step and Flow Construct": "Prepaid CTL with Data, Unli SMS and Unli Voice",
#         "SMS Voice Network Type": "N/A",
#         "SMS BULK Amount (Number of Texts)": "",
#         "VOICE Amount (In Minutes)": "",
#         "Tack-On Type": "None",
#         "Check Has Service ID": "",
#         "Default\nPARAM": "DEFAULT",
#         "Default AMOUNT": "30",
#         "Default\nDuration in Days": "1",
#         "Default\nWallet Keyword": "PR_REWARDALL_100MB1D_DVB",
#         "Default\nWallet Amount (in MB)": "100",
#         "Default Chargecode": "",
#         "With Double Flow": "No",
#         "With Extend Steps and Flow": "Yes",
#         "Extend Amount (PARAM)": "10",
#         "Extend Duration in Days": "5",
#         "Extend Keyword": "^(EXTEND_STOP)$",
#         "Provision Keyword": "",
#         "Deprovision Keyword": "^(REWTXT5G_TM STOP)$",
#         "Status Keyword": "^(REWTXT5G_TM STATUS)$",
#         "Gyro Command": "",
#         "SOCID": "",
#         "SMP ID": "",
#         "Allow Multiple": "Yes",
#         "Subscriber Group Name": "GHP,\nDORITOS_UNLI115/225_PLAN,\nDORITOS_6MONTH_PLAN",
#         "Deployment Date": "2025-09-01",
#         "_row_number": 59,
#     }
    
#     # Create validator and test
#     # validator = ServiceConfigValidator()
#     # result = validator.validate_service_config(sample_data)
    
#     # print(f"Validation Result: {'PASSED' if result.is_valid else 'FAILED'}")
#     # print(f"Errors: {len(result.errors)}")
#     # for error in result.errors:
#     #     print(f"  - {error}")
    
#     # print(f"Warnings: {len(result.warnings)}")
#     # for warning in result.warnings:
#     #     print(f"  - {warning}")