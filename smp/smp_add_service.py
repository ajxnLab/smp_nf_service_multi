from dataclasses import asdict
import json
import re
import time
from smp.smp_constant import SMPConstants
from utils.helpers import wait
from selenium.common.exceptions import TimeoutException
from utils.logger import logger
from utils.web_driver import WebDriver
from utils.env_loader import get_env_variable
from smp.smp_model import map_to_smp_row
from smp.login import login_sequence



# Instantiate constants
smp = SMPConstants()

class SMP_AddService:
    def __init__(self, gs, data):
        self.gs = gs
        self.data = data
        self.wd = WebDriver()
        self.logged_in = False

    def run_service(self, data_type: str, dataset: list):
        try:
            # Login only if not already logged in
            if not self.logged_in:
                login_sequence(self.wd, self.gs)
                self.logged_in = True
                logger.info("Login completed")

            if data_type == "service":
                logger.info(f"Processing Add Service")
                self.smp_add_service_process(dataset)

            elif data_type == "access_code":
                logger.info(f"Processing Add Access Code")
                self.smp_add_access_code_process(dataset)

            elif data_type == "subs_group":
                logger.info(f"Processing Subscriber Group Service")
                self.smp_add_subs_group_process(dataset)

            else:
                raise ValueError(f"Unsupported run_service type: {data_type}")

        except Exception as e:
            logger.error(f"Error in SMP run_service ({data_type}): {repr(e)}")


    def smp_add_service_process(self , data_add_service):

        smp_data  = [map_to_smp_row(row) for row in data_add_service]

        for row in smp_data:
            
            try:
                self.service_id = row.service_id
                self.smp_name = row.smp_name
                self.deployment_date = row.deployment_date
                access_code = row.access_code
                subs_group = row.subscriber_group_name

                conditions = {
                    "ServiceID": self.service_id,
                    "SMP Name": self.smp_name,
                    "Deployment Date": self.deployment_date,
                }

                self.result_index = self.gs.find_row_index_multi(self.data, conditions)
                
                logger.info(f"Processing SMP Name '{self.smp_name}' — adding SMP service")

                self.wd.redirect_to_page(get_env_variable("SMP_WEBTOOL_URL") + smp.SMP_ADD_SERVICE_URL)
        
                smp_add_element = self.wd.wait_until_element_with_refresh(
                    "xpath", smp.ADD_SERVICE_DETAILS_DASHBOARD, "visible"
                )

                if not smp_add_element:
                    logger.error(
                        "SMP Service Details dashboard field did not appear after multiple attempts. "
                        "Please check SMP Webtool availability."
                    )
                    raise RuntimeError("SMP Service failed: dashboard details field not found.")

                self.fill_fields(row)

                add_condition = [
                        ("xpath", smp.SUBSCRIBER_ADD_SERVICES_ID),
                        ("classname", "ErrMsg")
                ]
                    
                loc_type, loc_value, elem  = self.wd.wait_any_of( 
                    add_condition, 
                    timeout=60, retries=3, 
                    refresh_on_fail=True , 
                    post_refresh_action=lambda: self.fill_fields(row),
                    wait_target_locator_type = "xpath",
                    wait_target_value = smp.ADD_SERVICE_DETAILS_DASHBOARD

                )

                append_service_remarks = False

                if loc_type == "classname" and loc_value == "ErrMsg":

                    error_text = self.wd.get_element_content(locator="classname", locator_value="ErrMsg" , mode="text")

                    normalized = re.sub(r"\s+", " ", error_text).strip()
                    
                    if "Service name already exists." in normalized:
                        logger.warning(f"SMP Service creation skipped: '{self.smp_name}' already exists. Message: {normalized}")

                        self.wd.redirect_to_page(get_env_variable("SMP_WEBTOOL_URL") + smp.SMP_ADD_SERVICE_LIST_URL)
        
                        self.wd.wait_until_dom_loaded()
                        logger.info("SMP Service List page loaded successfully.")

                        self.wd.field_types("name", "svc_name", "text", self.smp_name)
                        self.wd.perform_action("name", "bntSearch", "click")
                        logger.info(f"Searched for existing SMP Service: '{self.smp_name}'")


                        xpath = f"//a[contains(normalize-space(.),'{self.smp_name.strip()}')]"

                        smp_add_element = self.wd.wait_until_element_with_refresh(
                            "xpath", xpath, "visible"
                        )
                        if smp_add_element:
                            self.wd.perform_action("xpath", xpath, "click")
                            logger.info(f"Opened details page for SMP Service '{self.smp_name}'")
                            append_service_remarks = True
                        else:
                            logger.error(f"Failed to locate SMP Service '{self.smp_name}' in the list. Check SMP Webtool availability.")

                    else:    
                        self.gs.update_cell(
                            smp.WORKSHEET_TAB_ADD_SERVICE, 
                            self.result_index, "SMP RPA Remarks", 
                            f"Failed - Service {normalized}", 
                            replace_match="Failed - Service",
                            append_line=1
                            )
                        continue

            
                #Get ID after creation of SMP sevice
                self.wd.wait_until_dom_loaded()
                smp_id = self.wd.get_element_content("xpath", smp.SUBSCRIBER_ADD_SERVICES_ID, mode="value")
                self.gs.update_cell(smp.WORKSHEET_TAB_ADD_SERVICE, self.result_index, "SMP ID", smp_id)
                logger.info(f"Google Sheet updated with SMP ID.")
                self.gs.update_cell(smp.WORKSHEET_TAB_ADD_SERVICE, self.result_index, "SMP RPA Remarks", "Success - Service added", replace_match="Failed - Service", append_line=1)

                if append_service_remarks:
                    self.gs.update_cell(smp.WORKSHEET_TAB_ADD_SERVICE, self.result_index, "SMP RPA Remarks", f"Remarks - Service {normalized}", append=True)

                logger.info(f"Successfully created SMP Service for {self.smp_name}")
                
                access_code_success = self.add_access_code(access_code, smp_id)

                if access_code_success:
                    logger.info(f"Access code '{access_code}' added successfully.")
                else:
                    logger.info(f"Access code '{access_code}' failed, continuing with Subscriber Groups.")

                self.add_subs_group(subs_group, self.smp_name)
                logger.info(f"Processed Subscriber Groups for SMP Service '{self.smp_name}'")

            
            except Exception as e:
                logger.warning(f"Something went wrong in the SMP Process Sequence: {repr(e)}")
                continue

    def smp_add_access_code_process(self, data_add_access_code = None):
      
        smp_data_access  = [map_to_smp_row(row) for row in data_add_access_code]

        for row in smp_data_access:
            smp_id = row.smp_id
            service_id = row.service_id
            self.smp_name = row.smp_name
            deployment_date = row.deployment_date

            need_url = True

            access_code = row.access_code
            
            conditions = {
                        "ServiceID": service_id,
                        "SMP Name": self.smp_name,
                        "Deployment Date": deployment_date
                    }

            self.result_index = self.gs.find_row_index_multi(self.data, conditions)

            self.add_access_code(access_code,smp_id, need_url)

    
    def smp_add_subs_group_process(self, data_add_subs_group):

        smp_data_subs_group = [map_to_smp_row(row) for row in data_add_subs_group]

        for row in smp_data_subs_group:
            service_id = row.service_id
            subscriber_group_name = row.subscriber_group_name
            service_name = row.smp_name
            deployment_date = row.deployment_date
            
            conditions = {
                        "ServiceID": service_id,
                        "SMP Name": service_name,
                        "Deployment Date": deployment_date,
                        "Subscriber Group Name": subscriber_group_name
                    }


            self.result_index = self.gs.find_row_index_multi(self.data, conditions)

            self.add_subs_group(subscriber_group_name, service_name)

            
    def fill_fields(self, row):
        row_dict = asdict(row)
        for col, val in row_dict.items():
            if col in smp.field_mapping:
                loc, elem, typ = smp.field_mapping[col]
                self.wd.field_types(loc, elem, typ, val)
        self.wd.perform_action("name" , "btnSubmit" , "click")

    def add_access_code(self, access_code, smp_id, login=False, retry=False):
        try:
            # Locators
            xpath = (
                "//div[@id='access_code']//table//tr"
                f"[td[normalize-space()='{access_code}']]"
                "//button[normalize-space()='Edit']"
            )
            xpath_errmsg = "//div[@id='access_code']//span[@class='ErrMsg']"

            access_code_condition = [

                ("xpath", xpath_errmsg),
                ("xpath", xpath)
            ]

            locator, element, input_type = smp.field_mapping_access_code["access_code"]

            # Navigate if needed
            if login:
                self.wd.redirect_to_page(
                    f"{get_env_variable('SMP_WEBTOOL_URL')}{smp.SMP_ADD_ACCESS_CODE_URL}?id={smp_id}"
                )
                self.wd.wait_until_element_with_refresh("xpath", smp.SUBSCRIBER_ADD_SERVICES_ACCESS_CODE_BTN, "visible")

            self.wd.field_types(locator, element, input_type, access_code)
            self.wd.wait_until_dom_loaded()
            self.wd.perform_action("xpath", smp.SUBSCRIBER_ADD_SERVICES_ACCESS_CODE_BTN, "click")

            # Wait for result
            loc_type_acc, loc_value_acc, elem = self.wd.wait_any_of(
                access_code_condition,
                timeout=60, 
                retries=3,
                refresh_on_fail=True,
                post_refresh_action=lambda: (
                    self.wd.field_types(locator, element, input_type, access_code),
                    self.wd.perform_action("xpath", smp.SUBSCRIBER_ADD_SERVICES_ACCESS_CODE_BTN, "click")
                ),
                wait_target_locator_type="xpath",
                wait_target_value=smp.SERVICE_DETAILS_DASHBOARD,
                url= f"{get_env_variable('SMP_WEBTOOL_URL')}{smp.SMP_ADD_ACCESS_CODE_URL}?id={smp_id}"
            )
            

            if loc_type_acc == "xpath" and loc_value_acc == xpath_errmsg:
                error_text = self.wd.get_element_content("xpath", xpath_errmsg, mode="text")
                
                normalized = re.sub(r"\s+", " ", error_text).strip()

                if "The access code already exists." in normalized:
                    logger.info(f"Access code {access_code} already exists for '{self.smp_name}'")
                    self.gs.update_cell(
                    smp.WORKSHEET_TAB_ADD_SERVICE,
                    self.result_index,
                    "SMP RPA Remarks",
                    "Success - Access Code added",
                    replace_match="Failed - Access Code",
                    append_line=2
                    )
                    self.gs.update_cell(
                    smp.WORKSHEET_TAB_ADD_SERVICE,
                    self.result_index,
                    "SMP RPA Remarks",
                    f"Remarks - Access Code {normalized}",
                    append = True
                    )
                    logger.info(f"Updated GSheet row {self.result_index} with warning status")
                    return True
                else:
                    logger.warning(f"Failed to add access code {access_code} for '{self.smp_name}': {normalized}")
                    self.gs.update_cell(
                        smp.WORKSHEET_TAB_ADD_SERVICE,
                        self.result_index,
                        "SMP RPA Remarks",
                        f"Failed - Access Code {normalized}",
                        replace_match="Failed - Access Code",
                        append_line=2
                    )
                    logger.info(f"Updated GSheet row {self.result_index} with Failed status")
                    return False

            elif loc_type_acc == "xpath" and loc_value_acc == xpath:
                logger.info(f"Successfully added Access Code {access_code} to {self.smp_name} service")
                self.gs.update_cell(
                    smp.WORKSHEET_TAB_ADD_SERVICE,
                    self.result_index,
                    "SMP RPA Remarks",
                    "Success - Access Code added",
                    replace_match="Failed - Access Code",
                    append_line=2
                )
                logger.info(f"Updated GSheet row {self.result_index} with Success status")
                return True

            elif not retry:
                # retry once without recursion explosion
                return self.add_access_code(access_code, smp_id, login=False, retry=True)

            else:
                logger.error(f"Access Code add failed for {access_code} on {self.smp_name} (no match found)")
                return False

        except Exception as e:
            logger.error(f"Failed to add Access Code {access_code} to {self.smp_name} service: {e}")
            return False


    def add_subs_group(self, subscriber_group_name, service_name, retry=False):
        try:
                         # Clean and split the raw subscriber group string into individual group names
            groups = [
                item.strip()                                                                # Remove leading/trailing whitespace
                for item in re.split(r'[\n,;;]+', subscriber_group_name)                          # Split on comma
                if item.strip()                                                             # Exclude empty or whitespace-only entries
            ]

            #Fill the service name
            locator_service_name, element_service_name, input_type_service_name = smp.field_mapping_add_subs_group["Service Name"]
            self.wd.redirect_to_page(f"{get_env_variable('SMP_WEBTOOL_URL')}{smp.SMP_ADD_SUBS_GROUP_URL}")
            self.wd.wait_until_element_with_refresh("name", smp.SUBSCRIBER_GROUP_ADD_SERVICE_BTN, "visible")
            success_element = self.wd.field_types(locator_service_name, element_service_name, input_type_service_name, service_name)

            if not success_element:
                logger.warning(f"Skipping submit Dropdown '{service_name}' value not found.")
                self.gs.update_cell(
                                smp.WORKSHEET_TAB_ADD_SERVICE,
                                self.result_index,
                                "SMP RPA Remarks",
                                f"Failed - Subscriber Group Service Dropdown '{service_name}' value not found.",
                                replace_match="Failed - Subscriber Group Service",
                                append_line=3
                            )
                logger.info(f"Updated GSheet row {self.result_index} with Failed status")
                return False
            
            record_exist = []
            value_not_found = []
                
            for group in groups:
                # Fill the Subscriber Group Name
                locator, element, input_type = smp.field_mapping_add_subs_group["Subscriber Group Name"]
                self.wd.wait_until_element_with_refresh("name", smp.SUBSCRIBER_GROUP_ADD_SERVICE_BTN, "visible")
                success_subs_element = self.wd.field_types(locator, element, input_type, group)

                if success_subs_element:
                    time.sleep(2)

                    self.wd.perform_action("name" , smp.SUBSCRIBER_GROUP_ADD_SERVICE_BTN , "click")

                    add_condition = [
                        ("xpath", "//td[@class='ErrMsg' and normalize-space()='New Subscriber Group Service added.']"),
                        ("classname", "ErrMsg")
                    ]
                    
                    loc_type, loc_value, elem  = self.wd.wait_any_of( 
                        add_condition, 
                        timeout=60, retries=3, 
                        refresh_on_fail=True , 
                        post_refresh_action=lambda: (
                            self.wd.field_types(locator_service_name, element_service_name, input_type_service_name, service_name),
                            self.wd.field_types(locator, element, input_type, group),
                            self.wd.perform_action("name" , smp.SUBSCRIBER_GROUP_ADD_SERVICE_BTN , "click")),
                        wait_target_locator_type = "xpath",
                        wait_target_value = smp.ADD_NEW_SUBSCRIBER_GROUP_SERVICE_DASHBOARD

                    )

                    if loc_type == "classname" and loc_value == "ErrMsg":

                        error_text = self.wd.get_element_content(locator="classname", locator_value="ErrMsg" , mode="text")

                        normalized = re.sub(r"\s+", " ", error_text).strip()
                        
                        if "New Subscriber Group Service added.".strip() in normalized: 
                            logger.info(f"Group {group}: {normalized}")

                        elif "Record already exists!".strip() in normalized:
                            logger.warning(f"Subscriber Group creation failed {group}: {normalized}")
                            record_exist.append(group)

                        else:
                            logger.error(f"Subscriber Group creation failed: {normalized}")
                            self.gs.update_cell(
                                smp.WORKSHEET_TAB_ADD_SERVICE,
                                self.result_index,
                                "SMP RPA Remarks",
                                f"Failed - Subscriber Group Service {normalized}",
                                replace_match="Failed - Subscriber Group Service",
                                append_line=3
                            )
                            logger.info(f"Updated GSheet row {self.result_index} with Failed status")
                            continue
                          
                else:
                    logger.warning(f"Skipping submit Dropdown '{group}' value not found.")
                    value_not_found.append(group)


            if record_exist:
                wait(1)
                formatted_groups = ", ".join([f"'{g}'" for g in record_exist])
                self.gs.update_cell(
                    smp.WORKSHEET_TAB_ADD_SERVICE,
                    self.result_index,
                    "SMP RPA Remarks",
                    f"Remarks - Subscriber Group Service {formatted_groups} records already exists!.",
                    append=True
             )
            if value_not_found:
                wait(1)
                formatted_groups = ", ".join([f"'{g}'" for g in value_not_found])
                self.gs.update_cell(smp.WORKSHEET_TAB_ADD_SERVICE, self.result_index, "SMP RPA Remarks", f"Remarks - Subscriber Group Service {formatted_groups} value not found." , append =True)
                logger.info(f"Updated GSheet row {self.result_index} with Warning status")

            logger.info(f"Subscriber Group creation succeeded")
            self.gs.update_cell(
                smp.WORKSHEET_TAB_ADD_SERVICE,
                self.result_index,
                "SMP RPA Remarks",
                "Success - Subscriber Group Service added",
                replace_match="Failed - Subscriber Group Service",
                append_line=3
            )
            logger.info(f"Updated GSheet row {self.result_index} with Success status")  


        except Exception as e:
            logger.error(f"Failed to add Subscriber Group  to {service_name} service: {e}")
            return False

