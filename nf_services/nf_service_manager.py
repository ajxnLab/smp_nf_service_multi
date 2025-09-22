from utils.web_driver import WebDriver
from utils.google_sheet import GSheetClient
from utils.logger import logger , finalize_log_upload
from utils.login import login_credential
from utils.env_loader import get_env_variable
from nf_services.main_services.bulk_service import BulkServices
from nf_services.controller.service_controller import ServiceController
from nf_services.controller.fallback_controller import FallbackController
from nf_services.nf_service_validator import NFServiceValidator
from config.config import WORKSHEET_CONFIG, nf
import datetime

class NFServiceManager:
    def __init__(self):
        self._initialize_components()
        self._initialize_services()
        self.start_time = datetime.datetime.now()

    def _initialize_components(self):
        """Initialize core components"""
        self.wd = WebDriver()
        self.gs = GSheetClient()
        self.worksheets = self.gs.create_worksheets(WORKSHEET_CONFIG)

    def _initialize_services(self):
        """Initialize service controllers"""
        self.bs = BulkServices(self.worksheets, self.wd, self.gs)
        self.sc = ServiceController(self.worksheets, self.wd, self.gs)
        self.fs = FallbackController(self.wd, self.gs, self.worksheets)
        self.sv = NFServiceValidator(self.gs, self.worksheets)

    def validator_sequence(self):
        self.sv.start_validation_process()

    def login_sequence(self):
        """Handle login to NF Webtool"""
        try:
            self._perform_login()
        except Exception as e:
            logger.error(f"Login sequence failed: {e}")
            raise

    def _perform_login(self):
        """Execute login steps"""
        url_param = get_env_variable("WEBTOOL_LOGIN_FULL_URL")
        logger.info(f"Redirecting to NF login page: {url_param}")
        
        self.wd.redirect_to_page(url_param)
        self.wd.wait_until_element("id", nf.NF_LOGIN_BUTTON, "clickable")

        username, password = login_credential("NF", self.gs)
        self._submit_login_credentials(username, password)

    def _submit_login_credentials(self, username: str, password: str):
        """Submit login credentials"""
        self.wd.perform_action("name", "uname", "sendkeys", username)
        self.wd.perform_action("name", "passwd", "sendkeys", password)
        self.wd.perform_action("id", nf.NF_LOGIN_BUTTON, "click")
        self.wd.wait_until_element("id", "content", "visible")
        logger.info("Login Successful!")

    def process_sequence(self):
        """Main processing sequence"""
        try:
            self.fs.start_nf_fallback_service()
            self.validator_sequence()
            list_success_data = self.bs.bulk_service_process()
            self.sc.start_service_controller(list_success_data)
        except Exception as e:
            logger.error(f"Process sequence failed: {e}")
            raise

    def cleanup_sequence(self):
        """Cleanup and logging"""
        self._log_completion_status()
        finalize_log_upload(get_env_variable("ROOT_LOG_FOLDER_ID"))
        self.wd.stop_process()

    def _log_completion_status(self):
        """Log completion status and timing information"""
        end_time = datetime.datetime.now()
        duration = end_time - self.start_time
        
        logger.info(
            f"\nTimestamp Report:"
            f"\nRPA Start Time: {self.start_time:%Y-%m-%d %H:%M:%S}"
            f"\nRPA End Time: {end_time:%Y-%m-%d %H:%M:%S}"
            f"\n--- Bot Duration: {duration} ---"
        )

    def run(self):
        """Main execution sequence"""
        try:
            self.login_sequence()
            self.process_sequence()
        except Exception as e:
            logger.error(f"Execution failed: {e}")
        finally:
            self.cleanup_sequence()