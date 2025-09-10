class SMPConstants:
    ROOT_LOG_FOLDER_ID="1taOVH9wxZc-Wvuv6Kwj5EOC2b19xiS4U"
    SERVICE_NAME="SMP"
    GSHEET="SMP_RolloutDeploymentRecords"
    GSHEET_ID="1oOQvejlcZkVY5nfK4fh5QYZoTYrFM6wvhga2e411nyk"
    WORKSHEET_TAB_CREDENTIAL="SMP_Creds"
    WORKSHEET_TAB_ADD_SERVICE="BulkService"

    SUBSCRIBER_SERVICES = "//a[normalize-space(.)='Services']"
    SUBSCRIBER_ADD_SERVICES = "//a[contains(normalize-space(.), 'Add Service')]"
    SUBSCRIBER_ADD_SERVICES_ID = '//input[@disabled and @type="text"]'
    SUBSCRIBER_ADD_SERVICES_ID_IN_GSHEET = "SMP ID"
    SUBSCRIBER_ADD_SERVICES_NAME = "SMP Name"
    SUBSCRIBER_ADD_SERVICES_NAME_ERROR = "ErrMsg"
    SUBSCRIBER_ADD_SERVICES_ACCESS_CODE = "ACCESS CODE"
    SUBSCRIBER_ADD_SERVICES_BTN = "btnSubmit"
    SUBSCRIBER_ADD_SERVICES_ACCESS_CODE_BTN = "//button[contains(@onclick, 'db_add_accesscode')]"
    SUBSCRIBER_GROUP_NAME = "Subscriber Group Name"
    SUBSCRIBER_GROUP = "//a[contains(normalize-space(.), 'Subscriber Groups')]"
    SUBSCRIBER_GROUP_ADD_SERVICE = "//a[contains(normalize-space(.), 'Add Service')]"
    SUBSCRIBER_GROUP_ADD_SERVICE_BTN = "btnSubmit"
    SUBSCRIBER_GROUP_VIEW = "//a[normalize-space(.)='View Groups']"
    LOGIN_FAILED='//td[@class="VTitle" and normalize-space(text())="Unauthorized User!"]'


    field_mapping = {
        'Name': ('name', 'name', 'text'),
        'URL': ('name', 'url', 'text'),
        'Thread Count': ('name', 'thread', 'text'),
        'Allow Multiple': ('name', 'allow_multiple', 'checkbox'),
        'Frontier URL': ('name', 'frontier_url', 'text'),
        'Frontier Filter': ('name', 'frontier_filter', 'text'),
        'Allow Queueing': ('name', 'allow_queueing', 'checkbox'),
        'Frontier Queued URL': ('name', 'frontier_queued_url', 'text'),
        'Frontier API URL': ('name', 'frontier_api_url', 'text'),
        'OCS URL': ('name', 'ocs_url', 'text'),
        'OCS API URL': ('name', 'ocs_api_url', 'text'),
        'Queued URL': ('name', 'queued_url', 'text'),
        'SMS Blockable': ('name', 'sms_blockable', 'checkbox'),
        'VOICE Blockable': ('name', 'voice_blockable', 'checkbox'),
        'Abuse Report Deprov Message': ('name', 'abr_deprov_mesg', 'textarea'),
        'Abuse Report Block Message': ('name', 'abr_block_mesg', 'textarea'),
        'Abuse Report Deprov Inst Note': ('name', 'abr_deprov_instnote', 'textarea'),
        'Abuse Report Block Inst Note': ('name', 'abr_block_instnote', 'textarea'),
        'Registrant Subscriber Category': ('name', 'ano_sub_category', 'select'),
        'Peer Subscriber Category': ('name', 'bno_sub_category', 'select'),
        
    }

    field_mapping_access_code = {
        'ACCESS CODE': ('name', 'access_code_criteria', 'text'),
    }

    field_mapping_add_subs_group = {
        'Subscriber Group Name': ('name', 'sgid', 'select'),
        'Service Name': ('name', 'svid', 'select'),
        
    }

    SMP_CONSTANT_VALUES = {
    "URL": "http://gcpdvlbthnfsms.globetel.com:8080/",
    "Thread Count": "1",
    "Frontier URL": "http://gcpdvlbthnfsms.globetel.com:8080/",
    "Frontier API URL": "http://gcpdvlbthnfapi.globetel.com:8082/"
    }

    ACCESS_CODE = "8080"
