

from selenium.common.exceptions import TimeoutException
from utils.logger import logger
from utils.env_loader import get_env_variable
from utils.login import login_credential
from smp.smp_constant import SMPConstants

# Instantiate constants
smp = SMPConstants()

def login_sequence( wd, gs):
        try:
            url_param = get_env_variable("SMP_WEBTOOL_URL")+ smp.SMP_LOGIN_URL
            logger.info("Account Authorized!, Logging into SMP Webtool..")
            logger.info(">>> Redirecting to SMP login page")

            wd.redirect_to_page(url_param)
            wd.wait_until_element("name", smp.SMP_LOGIN_USERNAME_NAME, "visible")

            username_field = wd.wait_until_element_with_refresh(
                "name", smp.SMP_LOGIN_USERNAME_NAME , "visible"
            )

            if not username_field:
                logger.error(
                    "SMP login unsuccessful, login username field did not appear after multiple attempts. "
                    "Please check SMP Webtool availability."
                )
                raise RuntimeError("SMP login failed: username field not found.")


            username, password = login_credential(smp.SERVICE_NAME, gs)

            # Fill in the login form and submit
            wd.perform_action("name", smp.SMP_LOGIN_USERNAME_NAME, "sendkeys", username)
            wd.perform_action("name", smp.SMP_LOGIN_PASSWORD_NAME, "sendkeys", password)
            wd.perform_action("name", smp.SMP_LOGIN_BUTTON, "click")

            try:
                try:
                    wd.wait_until_element("xpath", smp.SUBSCRIBER_SERVICES, "visible")
                    logger.info(">>> Login Success!")
                except TimeoutException:
                    logger.warning(">>> Could not find SUBSCRIBER_SERVICES, checking for unauthorized message...")
                    try:
                        wd.wait_until_element("xpath", smp.LOGIN_FAILED, "visible")
                        logger.error(">>> Unauthorized User!")
                        raise RuntimeError("Unauthorized User: Login failed.")
                    except TimeoutException:
                        logger.error(">>> Login failed: Unknown reason (neither SUBSCRIBER_SERVICES nor LOGIN_FAILED found).")
                        raise RuntimeError("Login failed: Neither success nor unauthorized message found.")
            except Exception as e:
                logger.exception(f"Exception during login process: {e}")
                raise


            logger.info(">>> Login sequence completed")

        except Exception as e:
            logger.error(f"Something went wrong in the Login Sequence: {repr(e)}")
            raise