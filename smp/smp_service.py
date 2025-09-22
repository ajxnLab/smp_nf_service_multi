from datetime import datetime
import re
import utils.helpers
from utils.logger import logger
from utils.google_sheet import GSheetClient
from smp.smp_constant import SMPConstants
from smp.smp_add_service import SMP_AddService
from utils.logger import finalize_log_upload



# Instantiate constants
smp = SMPConstants()
logger.name = "SMP"

class SMPService:
    def __init__(self):

        # Google Sheets client
        self.gs = GSheetClient()

        # Start datetime
        self.start_time = utils.helpers.get_datetime("full")
        self.today_date = utils.helpers.get_datetime("date")

    def run(self):
        logger.info(">>> Starting SMP process sequence")
        try:
            logger.info(f"Start Time: {self.start_time}")

            self.smp_filtered_data()

            # Call login and service creation
            #self.login_sequence()
            #self.add_smp_service()

            

        except Exception as e:
            logger.error(f"Error in SMP process: {repr(e)}")
        finally:
            finalize_log_upload(smp.ROOT_LOG_FOLDER_ID)
            # End datetime and log duration
            end_time = utils.helpers.get_datetime("full")
            duration = utils.helpers.duration_time(self.start_time, end_time)
            logger.info(f"End Time: {end_time}")
            logger.info(f"Duration: {duration}")

        
    def smp_filtered_data(self):
        smp_valid_remarks = {
            "Success - Service added",
            "Success - Access Code added",
            "Success - Subscriber Group Service added"
        }

        data = self.gs.get_sheet_data(smp.WORKSHEET_TAB_ADD_SERVICE)
        data = self.data_strip(data)
        data_add_service, data_add_subs_group, data_add_access_code = self.filter_remarks(data, smp_valid_remarks)

        if not data_add_service and not data_add_access_code and not data_add_subs_group:
            logger.info("No rows for SMP to process.")
            return

        smp_add_service = SMP_AddService(self.gs, data)

        datasets = [
            ("service", data_add_service),
            ("access_code", data_add_access_code),
            ("subs_group", data_add_subs_group),
        ]
        try:
            for data_type, dataset in datasets:
                if not dataset:
                    continue
                smp_add_service.run_service(data_type, dataset)

        finally:
            # Stop the WebDriver after all datasets processed
            if hasattr(smp_add_service, "wd") and smp_add_service.wd is not None:
                try:
                    smp_add_service.wd.stop_process_wd()
                    logger.info("WebDriver stopped successfully for SMP.")
                except Exception as e:
                    logger.warning(f"Failed to stop WebDriver: {e}")


    def data_strip(self, data):
        cleaned_data = []
        for row in data:
            cleaned_row = {}
            for k, v in row.items():
                # Handle None keys
                key = k.strip() if isinstance(k, str) else str(k or "").strip()
                # Handle None values
                val = v.strip() if isinstance(v, str) else str(v or "").strip()
                cleaned_row[key] = val
            cleaned_data.append(cleaned_row)
        return cleaned_data
    
    def filter_remarks(self, rows: list[dict], valid_remarks: set[str]) -> list[dict]:
        filtered_add_service = []
        filtered_add_access_code = []
        filtered_add_subs_group = []

        
        for row in rows:
            deployment_date = row.get("Deployment Date")

            # Normalize deployment_date to YYYY-MM-DD string
            if isinstance(deployment_date, datetime):
                deployment_date_str = deployment_date.strftime("%Y-%m-%d")
            elif deployment_date:
                deployment_date_str = str(deployment_date).split(" ")[0]
            else:
                continue  # skip rows with no date

            # Skip if not today
            if deployment_date_str != self.today_date:
                continue

            def_remarks = (row.get("SMP RPA Remarks") or "").strip()
            
            if not def_remarks:
                filtered_add_service.append(row)  # No remark, append
                continue

            # Check valid remarks
            has_service_added = "Success - Service added" in def_remarks
            has_subscriber_group_added = "Success - Subscriber Group Service added" in def_remarks
            has_access_code_added = "Success - Access Code added" in def_remarks

            if has_service_added and has_access_code_added and has_subscriber_group_added:
                continue  # skip if both present

            if not has_service_added:
                filtered_add_service.append(row) 
                
            if not has_access_code_added :
                filtered_add_access_code.append(row) 

            if not has_subscriber_group_added :
                filtered_add_subs_group.append(row)  
                
        logger.info(f" Service {len(filtered_add_service)} Access code {len(filtered_add_access_code)} Subscriber Group {len(filtered_add_subs_group)} ")
        return filtered_add_service , filtered_add_subs_group, filtered_add_access_code
    
