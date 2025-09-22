from enum import Enum

class NfConstants:
    WORKSHEET_TAB_CREDENTIAL = "Creds"
    WORKSHEET_TAB_BULK_SERVICES = "BulkService"
    WORKSHEET_TAB_BULK_SERVICES_TAB_STEPS = "Steps"
    WORKSHEET_TAB_BULK_SERVICES_TAB_FLOWS = "Flows"
    WORKSHEET_TAB_BULK_SERVICES_TAB_PARAM_MATRIX = "ParamMatrix"
    WORKSHEET_TAB_BULK_SERVICES_TAB_KEYWORDS = "Keywords"
    WORKSHEET_TAB_BULK_SERVICES_TAB_MESSAGES = "Messages"
    WORKSHEET_TAB_BULK_SERVICES_TAB_EXPIRIES = "Expiries"
    WORKSHEET_TAB_BULK_SERVICES_TAB_EXTENSION_EXPIRIES = "ExtensionExpiries"
    WORKSHEET_TAB_BULK_SERVICES_TAB_REMINDER_MESSAGES = "ReminderMessages"
    # NF LOGIN PAGE
    NF_INPUT_USERNAME = "//input[@name='uname']"
    NF_INPUT_PASSWORD = "//input[@name='passwd']"
    NF_LOGIN_BUTTON = "login-button"

    # NF BULK SERVICES > ADD PAGE
    NF_INPUT_NAME = "//input[@name='name']"

    # ACCESS CODE
    ACCESS_CODE_INPUT = "access_code"

    # NF DATA INDEX VALUE
    NF_INDEX_SERVICE_ID = 0
    NF_INDEX_NAME = 1
    NF_INDEX_GROUP_STATUS_INQUIRY = 2
    NF_INDEX_WALLET_TYPE = 3
    NF_INDEX_WALLET = 4
    NF_INDEX_THREAD_COUNT = 5
    NF_INDEX_BRAND = 6
    NF_INDEX_SMP_NAME = 7
    NF_INDEX_DEPROV_ON_EMPTY = 8
    NF_INDEX_SUBSCRIPTION_LESS = 9
    NF_INDEX_MAX_DAILY_EXT = 10
    NF_INDEX_MAX_TOTAL_EXT = 11
    NF_INDEX_PROMO_NAME = 12
    NF_INDEX_STEP_AND_FLOW_CONSTRUCT = 13
    BS_INDEX_SMS_VALUE = 14
    BS_INDEX_VOICE_VALUE = 15
    BS_INDEX_TACKON = 16
    BS_INDEX_CHECK_HAS_IDS = 17
    NF_INDEX_DEFAULT_PARAM = 18
    NF_INDEX_DEFAULT_AMOUNT = 19
    NF_INDEX_DEFAULT_DURATION_IN_DAYS = 20
    NF_INDEX_DEFAULT_WALLET_KEYWORD = 21
    NF_INDEX_DEFAULT_WALLET_AMOUNT = 22
    BS_INDEX_DEFAULT_CHARGE_CODE = 23

    # FLOW LOGIC
    NF_INDEX_WITH_DOUBLE_FLOW = 24
    NF_INDEX_WITH_EXTEND_STEPS_AND_FLOW = 25
    NF_INDEX_EXTEND_AMOUNT = 26
    NF_INDEX_EXTEND_DURATION_IN_DAYS = 27
    BS_INDEX_EXTEND_KEYWORD = 28
    BS_INDEX_PROVISION_KEYWORD = 29
    BS_INDEX_DEPROVISION_KEYWORD = 30
    BS_INDEX_STATUS_KEYWORD = 31
    BS_INDEX_GYRO_COMMAND = 32

    # NEW SMP INDEX
    BS_INDEX_SOCID = 33
    BS_INDEX_SMP_ID = 34
    BS_INDEX_ALLOW_MULTIPLE = 35
    BS_INDEX_SUBSCRIBER_GROUP_NAME= 36

    # BULK SERVICE DATE AND RPA REMARKS
    NF_INDEX_DEPLOYMENT_DATE = 37
    BS_INDEX_RPA_REMARKS_SMP = 38
    BS_INDEX_RPA_REMARKS_BULK_SERVICE = 39
    BS_INDEX_RPA_REMARKS_BASE_FLOW = 40
    BS_INDEX_RPA_REMARKS_DOUBLE_FLOW = 41
    BS_INDEX_RPA_REMARKS_EXTEND_FLOW = 42
    BS_INDEX_RPA_REMARKS_KEYWORD = 43
    BS_INDEX_RPA_REMARKS_AUX_FLOW = 44

    # NF COLUMN BULK SERVICE
    COLUMN_BULK_SERVICE_DEPLOYMENT_DATE = 38
    COLUMN_BULK_SERVICE_SMP_RPA_REMARKS = 39
    COLUMN_BULK_SERVICE_RPA_REMARKS = 40
    COLUMN_BULK_SERVICE_RPA_REMARKS_BASE_FLOW = 41
    COLUMN_BULK_SERVICE_RPA_REMARKS_DOUBLE_FLOW = 42
    COLUMN_BULK_SERVICE_RPA_REMARKS_EXTEND_FLOW = 43
    COLUMN_BULK_SERVICE_RPA_REMARKS_KEYWORD = 44
    COLUMN_BULK_SERVICE_RPA_REMARKS_AUX_FLOW = 45

    # NF PARAM MATRIX INDEX VALUE
    PARAMMATRIX_INDEX_PARAM = 0
    PARAMMATRIX_INDEX_AMOUNT = 1
    PARAMMATRIX_INDEX_DURATION_IN_DAYS = 2
    PARAMMATRIX_INDEX_WALLET_KEYWORD = 3
    PARAMMATRIX_INDEX_WALLET_AMOUNT = 4
    PARAMMATRIX_INDEX_CHARGE_CODE = 5
    PARAMMATRIX_INDEX_SERVICE_NAME = 6
    PARAMMATRIX_INDEX_SERVICE_ID = 7

    # PARAM MATRIX COLUMN
    COLUMN_PARAM_MATRIX_SERVICE_NAME = 7
    COLUMN_PARAM_MATRIX_SERVICE_ID = 8
    COLUMN_PARAM_MATRIX_RPA_REMARKS = 9

    # NF BULK SERVICES > ADD PAGE
    NF_BS_NAME = "//input[@name='name']"
    BS_SERVICE_CLASS_BULK_SERVICE = "//input[@name='service_class' and @value='1']"
    BS_SERVICE_CLASS_SIMPLE_SERVICE_DATA = "//input[@name='service_class' and @value='3']"

    NF_BS_GROUP_STATUS_INQUIRY = "cb_allow_group_status"
    NF_WALLET_TYPE = "//input[@name='wallet_type' and "
    BS_WALLET_TYPE_SMSVOICE = "//input[@name='wallet_type' and @value='1']"
    BS_WALLET_TYPE_DATA = "//input[@name='wallet_type' and @value='29']"
    BS_WALLET_TYPE_SPS = "//input[@name='wallet_type' and @value='52']"
    BS_WALLET_TYPE_CPS = "//input[@name='wallet_type' and @value='3']"

    NF_BS_STATUS = "//select[@name='status']"
    BS_STATUS_ACTIVE = "//select[@name='status']//option[@value='1']"
    BS_STATUS_NOPROV = "//select[@name='status']//option[@value='2']"
    BS_STATUS_INACTIVE = "//select[@name='status']//option[@value='3']"

    # hardcode
    NF_BS_PRIORITY = "//select[@name='priority']//option[@value='1']"
    NF_BS_THREAD_COUNT_INPUT_NAME = "thread_count"
    NF_BS_TYPE_TIME_BASED = "//select[@name='btype']//option[@value='1']"
    NF_BS_TYPE_WALLET_BASED = "//select[@name='btype']//option[@value='2']"

    # brands-v1
    NF_BS_BRAND_GHP = "brand1"
    NF_BS_BRAND_TM = "brand2"
    NF_BS_BRAND_POSTPAID = "brand3"
    NF_BS_BRAND_DEEDSFOREIGN = "brand4"
    NF_BS_BRAND_DEEPLO = "brand5"
    NF_BS_BRAND_PW = "brand6"
    NF_BS_BRAND_PWN = "brand7"
    NF_BS_BRAND_TESTINGRBA = "brand8"
    BS_SDM_TO_FLOW_DEFAULT = "data_default_sdm_postpaid_create_subs"
    BS_SDM_TO_FLOW_API = "data_api_sdm_postpaid_create_subs"
    BS_SDM_TO_FLOW_WEB = "data_web_sdm_postpaid_create_subs"

    # BULK SERVICE > EDIT PAGE
    #BS_EDIT_PAGE_REMINDER_MSG_BTN = "//input[contains(@onclick, 'mod=reminder_messages')]"
    BS_EDIT_PAGE_REMINDER_MSG_BTN = "//input[contains(@onclick, 'mod=reminder_messages') and @value='Add']"

    # name #hardcode
    NF_BS_TIMEOUT_SEC = "timeout_seconds"

    NF_BS_STATUS_CHARGED_AMOUNT = "status_charge"
    NF_BS_BALANCE_CHARGED_AMOUNT = "balance_charge"

    # name
    NF_BS_SMP_NAME = "smp_name"

    # name
    NF_BS_DEFAULT_ACCESS_CODE = "access_code"

    # name #hardcode
    NF_BS_QUEUE_LIMIT = "queue_limit"
    NF_BS_DEPROV_ON_EMPTY_YES = "//input[@id='deprov_on_empty' and @value='1']"
    NF_BS_DEPROV_ON_EMPTY_NO = "//input[@id='notdeprov_on_empty' and @value='0']"

    # hardcode
    NF_BS_CANCEL_PRE_EXPIRY_YES = "//input[@id='cancel_preex_on_empty' and @value='1']"
    NF_BS_CANCEL_PRE_EXPIRY_NO = (
        "//input[@id='notcancel_preex_on_empty' and @value='0']"
    )

    # id
    NF_BS_SUBSCRIPTION_LESS = "subscriptionless"
    NF_BS_NOTSUBSCRIPTION_LESS = "notsubscriptionless"

    # hardcode #id
    NF_BS_MAX_RECURRENCE = "no_recurrence_limit"
    NF_MAX_NO_RECURRNECE = "no_recurrence"
    # name
    NF_MAX_RECURRENCE_VALUE = "max_recurrence_value"

    # name
    NF_BS_MAX_DAILY_EXTENSION = "max_daily_extensions"
    # name
    NF_BS_MAX_TOTAL_EXTENSION = "max_total_extensions"

    # name
    NF_BS_PROMO_NAME = "promo_name"

    # name
    NF_BS_COMM_POOL_YES = "//input[@name='is_comm_pool' and @value='1']"
    NF_BS_COMM_POOL_NO = "//input[@name='is_comm_pool' and @value='0']"

    NF_ADD_BTN_INPUT = "//input[@type='submit']"
    ADD_BTN_INPUT_2 = "(//input[@type='submit'])[2]"
    NF_STEP_ADD_BTN_INPUT = "//input[@type='submit' and @value='Add']"

    # DATA SERVICES > ADD PAGE
    NF_DATA_SERVICES_TITLE = "//div[@id='title']"
    NF_DATA_SERVICES_INPUT_NAME = "name"
    NF_DATA_SERVICE_TYPE_WALLET_BASED = "//select[@name='stype']//option[@value='2']"
    NF_DATA_SERVICES_COMMERCIAL_WALLET_NAME_INPUT = "commercial_wallet_name"
    NF_DATA_SERVICES_ADD_BUTTON_NAME = "submit"
    # DATA SERVICES > EDIT PAGE
    DATA_SERVICE_WALLET_KEYWORD = "sdm_wallet_keyword"
    DATA_SERVICE_UNITS_KB = "//select[@name='sdm_unit']//option[@value='1']"
    DATA_SERVICE_UNITS_SECONDS = "//select[@name='sdm_unit']//option[@value='2']"
    DATA_SERVICE_BASE_KEYWORD = "sdm_base_keyword"
    DATA_SERVICE_BASE_AMOUNT = "sdm_base_amount"
    DATA_SERVICE_SDM_WALLET_BTN = "(//input[@name='submit'])[3]"

    # SERVICES STEPS > ADD PAGE
    NF_STEPS_NAME_INPUT = "name"
    NF_STEPS_TYPE_DROPDOWN = "dd_stype_id"
    NF_STEP_TYPE_DATA_PROV_KEYWORD_MAPPING = (
        "//select[@id='dd_stype_id']//option[@value='95']"
    )
    NF_STEP_TYPE_DATA_PROV_EXTENSION_KEYWORD_MAPPING = (
        "//select[@id='dd_stype_id']//option[@value='96']"
    )

    STEP_TYPE_IN_PROV_SERVICE = "//select[@id='dd_stype_id']//option[@value='5']"
    STEP_TYPE_DATA_EXTEND_WALLET_EXPIRY = (
        "//select[@id='dd_stype_id']//option[@value='128']"
    )
    STEP_TYPE_IN_EXTEND_WALLET_EXPIRY = (
        "//select[@id='dd_stype_id']//option[@value='127']"
    )
    NF_STEPS_FINAL_CHECKBOX = "final"
    NF_STEPS_RETRY_INPUT = "retry"

    # SUCCESS MESSAGE ELEMENTS
    # COMMON
    SUCCESS_MESSAGE = "//div[@class='success']"    
    # FOR KEYWORD AND SERVICE EXPIRY
    CONTAINS_SUCCESS_OR_EXIST_MESSAGE = "//div[@id='content']//div[contains(text(), 'Success')] | //span[contains(text(), 'already has Regex')]"
    # FOR GYRO
    SUCCESS_OR_EXIST = "//span[contains(text(), 'already exist')] | //div[@id='content']//div[contains(text(), 'Success')]"
    # STEP SUCCESS and # FOR ACCESS CODE SUCCESS
    #STEP_SUCCESS_MESSAGE = "(//div[@id='content']//div)[1]"
    STEP_SUCCESS_MESSAGE = "//div[@id='content']//div[contains(text(), 'Success')]"
    ## FOR REMINDER MESSAGE
    REMINDER_MESSAGE_SUCCESS_OR_NOT = "//input[contains(@onclick, 'mod=reminder_messages') and @value='Add'] | //div[@class='error' and contains(text(), 'not saved')]"
    
    # STEP TYPE - IN PROV SERVICE
    NF_STEP_FUP_AMOUNT_FIELD = "fup_amount"
    NF_STEP_AMOUNT_FIELD = "in_fup_step_amount"
    # SERVICES FLOW > ADD PAGE
    NF_FLOWS_NAME_INPUT = "name"

    # SERVICES FLOW > EDIT PAGE
    FLOW_ID_PROD = "(//div)[82]"
    FLOW_ID_TESTBED = "(//div)[85]//div[2]"

    # SERVICES KEYWORDS > ADD PAGE
    NF_KEYWORDS_BULK_SERVICES_DROPDOWN = "svc_id"
    KEYWORD_REGEX_INPUT = "regex"
    NF_KEYWORDS_REPLY = "//input[@name='reply']"
    NF_KEYWORDS_REPLY_DISABLED = "//input[@name='reply' and @disabled]"
    KEYWORD_OPERATION = "//select[@name='op_id']"
    KEYWORD_OPERATION_PROVISION = "//select[@name='op_id']//option[@value='1']"
    KEYWORD_OPERATION_DEPROVISION = "//select[@name='op_id']//option[@value='2']"
    KEYWORD_OPERATION_STATUS = "//select[@name='op_id']//option[@value='3']"
    KEYWORD_OPERATION_EXTEND = "//select[@name='op_id']//option[@value='39']"

    # STEP TYPE EDIT PAGE
    EDIT_STEP_INPUT_FIELD_PARAM = "//input[@name='par']"
    EDIT_STEP_INPUT_FIELD_DURATION = "//input[@name='duration']"

    # SERVICE EXTENSION EXPIRY ADD PAGE
    SERVICE_PARAM_INPUT = "para"
    SERVICE_EXTENSION_EXPIRY_EXPIRY_INPUT = "expiry"

    # SIMPLE SERVICE GROUP DETAILS PAGE
    SSG_ADD_BTN_SIMPLE_SERVICES = "(//input[@type='submit'])[1]"
    SSG_ADD_BTN_ACCESS_CODE = "(//input[@type='submit'])[3]"
    SSG_PRIORITY_INPUT = "priority"

    # GYRO COMMAND ADD PAGE
    GYRO_COMMAND_FIELD = "command"

    # MESSAGES COLUMN COUNTS
    COLUMN_MESSAGES_SERVICE_ID = 13
    COLUMN_MESSAGES_RPA_REMARK = 14

    # MESSAGE INDEX
    NF_MSG_INDEX_REMARKS = 13
    NF_MSG_INDEX_SERVICE_ID = 12
    NF_MSG_INDEX_MESSAGE_TYPE = 0
    NF_MSG_INDEX_BRAND = 1
    NF_MSG_INDEX_CHANNEL = 2
    NF_MSG_INDEX_CATEGORY = 4
    NF_MSG_INDEX_TYPE = 5
    NF_MSG_INDEX_DESCRIPTION = 6
    NF_MSG_INDEX_SUBJECT = 7
    NF_MSG_INDEX_PUSH_NOTIF_CHANNEL = 8
    NF_MSG_INDEX_MESSAGE = 3
    NF_MSG_INDEX_SCHEDULE_REMINDER_HOURS = 9
    NF_MSG_INDEX_SCHEDULE_REMINDER_SETTING = 10

class StepType(Enum):
    DATA = "data"
    UNLI_SMS = "sms"
    UNLI_VOICE = "voice"

class FlowType(Enum):
    BASE = "base"
    DOUBLE = "double"
    EXTEND = "extend"

class TackOn(Enum):
    CHECK_HAS_ADD = "add check-has logic to this service"
    CHECK_HAS_OTHER = "add this service to other check-has logic"

class SMPConstants:
    GSHEET = "SMP_RolloutDeploymentRecords"
    GSHEET_ID = "1oOQvejlcZkVY5nfK4fh5QYZoTYrFM6wvhga2e411nyk"
    WORKSHEET_TAB_CREDENTIAL = "Creds"
