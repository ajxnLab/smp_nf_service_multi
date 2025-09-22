class SMPConstants:
    ROOT_LOG_FOLDER_ID="1iPMYJiVLJcwGNVqfaumgdk9tT2LBN0Tn"
    SERVICE_NAME="SMP"
    GSHEET_ID="1oOQvejlcZkVY5nfK4fh5QYZoTYrFM6wvhga2e411nyk"
    WORKSHEET_TAB_CREDENTIAL="SMP_Creds"
    WORKSHEET_TAB_ADD_SERVICE="BulkService SMP"

    SMP_LOGIN_URL="/isoladm/webtool/index.php"
    SMP_ADD_SERVICE_URL = "/isoladm/webtool/add_svc.php" 
    SMP_ADD_SERVICE_LIST_URL = "/isoladm/webtool/list_svc.php"
    SMP_ADD_ACCESS_CODE_URL = "/isoladm/webtool/svc_details.php"
    SMP_ADD_SUBS_GROUP_URL = "/isoladm/webtool/add_sub_svc.php"

        
    ADD_SERVICE_DETAILS_DASHBOARD='//input[@name="btnSubmit"]'
    ADD_SERVICE_ACCESS_CODE ="access_code"
    
    SERVICE_DETAILS_DASHBOARD="//td[@class='VdCat' and normalize-space()='Service Details']"
    ADD_NEW_SERVICE_DETAILS_DASHBOARD="//td[@class='VdCat' and normalize-space()='Add New Service']"
    ADD_NEW_SUBSCRIBER_GROUP_SERVICE_DASHBOARD="//td[@class='VdCat' and normalize-space()='Add New Subscriber Group Service']"

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

    #Element ID in Login page
    SMP_LOGIN_USERNAME_NAME = "usr"
    SMP_LOGIN_PASSWORD_NAME = "pwd"
    SMP_LOGIN_BUTTON="Submit"


    field_mapping = {
        'smp_name': ('name', 'name', 'text'),
        'url': ('name', 'url', 'text'),
        'thread_count': ('name', 'thread', 'text'),
        'allow_multiple': ('name', 'allow_multiple', 'checkbox'),
        'frontier_url': ('name', 'frontier_url', 'text'),
        'frontier_api_url': ('name', 'frontier_api_url', 'text')

    }

    field_mapping_access_code = {
        'access_code': ('name', 'access_code_criteria', 'text'),
    }

    field_mapping_add_subs_group = {
        'Subscriber Group Name': ('name', 'sgid', 'select'),
        'Service Name': ('name', 'svid', 'select'),
        
    }

    SMP_CONSTANT_VALUES = {
    "URL": "http://gcpdvlbthnfsms.globetel.com:8080/",
    "Thread Count": "1",
    "Frontier URL": "http://gcpdvlbthnfsms.globetel.com:8080/",
    "Frontier API URL": "http://gcpdvlbthnfapi.globetel.com:8082/",
    "Access Code" : "8080"
    }

