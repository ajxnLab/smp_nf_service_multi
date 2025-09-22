from utils.env_loader import get_env_variable
from utils.logger import logger
from nf_services.nf_constants import NfConstants
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from config.config import nf


def create_message(wd, gs, bs_service_name, fallback=False, message_fail = False):
    message_worksheet = gs.create_worksheet(nf.WORKSHEET_TAB_BULK_SERVICES_TAB_MESSAGES)
    list_current_data = gs.fetch_by_service_name(message_worksheet, bs_service_name)
    if not list_current_data:
        return
    logger.info("STARTING MESSAGE PROCESS")
    #all_rows = message_worksheet.get_all_values()
    # for row_index, row_data in enumerate(all_rows[1:], start=2):
    for row_index, row_data in enumerate(list_current_data):
        row = row_data[nf.KEY_ROW_NUMBER]
        bs_service_id = row_data.get(nf.NF_MSG_INDEX_SERVICE_ID, '')
        remarks = row_data.get(nf.NF_MSG_INDEX_REMARKS, '')

        if "success" in remarks.strip().lower() or not bs_service_id:
            msg = f"Service ID is blank for this row {row}, skipping.." if not bs_service_id else f"Row {row} already defined"
            logger.warning(msg)
            continue
        try:
            message_type = row_data[nf.NF_MSG_INDEX_MESSAGE_TYPE].strip()
            brand = row_data[nf.NF_MSG_INDEX_BRAND].strip()
            channel = row_data[nf.NF_MSG_INDEX_CHANNEL].strip()
            schedule_reminder = row_data[nf.NF_MSG_INDEX_SCHEDULE_REMINDER_HOURS]
            sched_reminder_setting = row_data[nf.NF_MSG_INDEX_SCHEDULE_REMINDER_SETTING]
            category = row_data[nf.NF_MSG_INDEX_CATEGORY]
            notif_type = row_data[nf.NF_MSG_INDEX_TYPE]
            description = row_data[nf.NF_MSG_INDEX_DESCRIPTION]
            subject = row_data[nf.NF_MSG_INDEX_SUBJECT]
            push_channel = row_data[nf.NF_MSG_INDEX_PUSH_NOTIF_CHANNEL]

            # Check data keyword in message
            message = _handle_data_keyword(wd, row_data[nf.NF_MSG_INDEX_MESSAGE], bs_service_id)

            logger.info(
                f"Processing Message row {row} for Service ID: {bs_service_id}, Type: {message_type}"
            )

            if message_type == "Reminder Message":

                url_service_msg = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=reminder_messages&op=add&svc_id={bs_service_id}"
                wd.redirect_to_page(url_service_msg, nf.NF_ADD_BTN_INPUT)
                wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")

                wd.perform_action(
                    "xpath",
                    f"//select[@name='brand_id']/option[contains(text(), '{brand}')]",
                    "click",
                )
                wd.perform_action("name", "time_diff", "clear")
                wd.perform_action("name", "time_diff", "sendkeys", schedule_reminder)
                wd.perform_action(
                    "xpath",
                    f"//select[@name='reference_event']/option[contains(text(), '{sched_reminder_setting}')]",
                    "click",
                )
                wd.perform_action(
                    "xpath",
                    f"//select[@name='channel']/option[contains(text(), '{channel}')]",
                    "click",
                )

                if channel.lower() == "globe one notification":
                    wd.perform_action("name", "category", "sendkeys", category)
                    wd.perform_action("name", "type", "sendkeys", notif_type)
                    wd.perform_action("name", "description", "sendkeys", description)
                    wd.perform_action("name", "subject", "sendkeys", subject)
                    wd.perform_action(
                        "name", "push_notif_channel", "sendkeys", push_channel
                    )

                wd.perform_action("name", "notif_text", "sendkeys", message)
                logger.info(
                    f"Message has been successfully created for Row: {row_index}"
                )
                # wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
                msg = wd.submit_form_and_wait_for_success(
                    "xpath",
                    nf.NF_ADD_BTN_INPUT,
                    nf.REMINDER_MESSAGE_SUCCESS_OR_NOT,
                )
            else:

                url = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=service_msgs&op=add&details_id={bs_service_id}"
                wd.redirect_to_page(url, nf.NF_ADD_BTN_INPUT)
                # wd.wait_until_element("name", "mtype", "visible")
                wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")

                wd.perform_action(
                    "xpath",
                    f"//select[@name='mtype']/option[normalize-space(text())='{message_type}']",
                    "click",
                )
                wd.perform_action(
                    "xpath",
                    f"//select[@name='brand_id']/option[contains(text(), '{brand}')]",
                    "click",
                )
                wd.perform_action(
                    "xpath",
                    f"//select[@name='channel']/option[contains(text(), '{channel}')]",
                    "click",
                )

                if channel.lower() == "globe one notification":
                    wd.perform_action("name", "category", "sendkeys", category)
                    wd.perform_action("name", "type", "sendkeys", notif_type)
                    wd.perform_action("name", "description", "sendkeys", description)
                    wd.perform_action("name", "subject", "sendkeys", subject)
                    wd.perform_action(
                        "name", "push_notif_channel", "sendkeys", push_channel
                    )

                wd.perform_action("name", "message", "sendkeys", message)
             
                msg = wd.submit_form_and_wait_for_success(
                    "xpath",
                    nf.NF_ADD_BTN_INPUT,
                    "//div[contains(@class, 'success') or contains(@class, 'error')]",
                    skip=True,
                )

            # Declare final remark
            rpa_remark = f"Failed | {msg}" if "failed" in msg.lower() else f"Success | {msg}" if "already has message" in msg.lower() else f"Failed | {msg}" if "not saved" in msg.lower() else "Success"
            gs.update_row(
            row,
            nf.COLUMN_MESSAGES_RPA_REMARK,
            message_worksheet,
            rpa_remark,
            )

        except Exception as inner_e:
            logger.warning("An error has occurred while creating message, continue..")
            gs.update_row(
                row,
                nf.COLUMN_MESSAGES_RPA_REMARK,
                message_worksheet,
                f"Failed | Unexpected error has occurred: {inner_e}",
            )
            message_fail = True
            continue

    return message_fail

def _handle_data_keyword(wd, message, service_id):
    logger.info(f"Check message: {message}")
    data_keyword = "<DATA_DYN_WALLET_AMOUNT_TBD>"
    if data_keyword not in message:
        logger.info("Data keyword not found in message")
        return message
    logger.info("Data keyword '<DATA_DYN_WALLET_AMOUNT_TBD>' found in message")
    wallet_id = _get_data_wallet_id(wd, service_id)
    if not wallet_id:
        return message
    updated_message = _update_wallet_amount(message, wallet_id)
    logger.info(f"Message updated with wallet id: {updated_message}, continue process..")
    return updated_message

def _get_data_wallet_id(wd, service_id):
    logger.info(f"Retrieving data wallet id...")
    # Redirect to Edit Bulk service page
    base_url = get_env_variable("WEBTOOL_BASE_URL")
    wd.redirect_to_page(f"{base_url}/nf/index.php?mod=bulk_services&op=details&id={service_id}", "//input[contains(@onclick, 'mod=reminder_messages')]")
    # wd.wait_until_element(
    #     "xpath", "//input[contains(@onclick, 'mod=reminder_messages')]", "clickable"
    # )

    # Get wallet element text and get wallet id
    try:
        wallet_text = wd.driver.find_element(By.XPATH, "//div[@class='form_field'][normalize-space(text())='Wallet']/following-sibling::div[1]").text
        wallet_id = extract_id_from_string(wallet_text)
        logger.info(f"Wallet id retrieved: {wallet_id}")
        return wallet_id
    except NoSuchElementException:
        logger.warning("No wallet found in edit page bulk service")
        return None

def _update_wallet_amount(message, wallet_id):
    """
    Replace <DATA_DYN_WALLET_AMOUNT_TBD> with the specific wallet ID.
    
    Args:
        message (str): The original message string
        wallet_id (str): The wallet ID to replace TBD with
        
    Returns:
        str: Updated message with the wallet ID
    """
    return message.replace('<DATA_DYN_WALLET_AMOUNT_TBD>', f'<DATA_DYN_WALLET_AMOUNT_{wallet_id}>')

import re
def extract_id_from_string(text):
    """
    Extract the ID number from inside parentheses at the beginning of a string.
    
    Args:
        text (str): The input string containing ID in parentheses
        
    Returns:
        int: The extracted ID number, or None if no valid ID found
        
    Examples:
        >>> extract_id_from_string("(245) DATA_VOLUME_BULK")
        245
        >>> extract_id_from_string("(3382) PR_REWARDALL_OA_DVB")
        3382
    """
    # Use regex to find numbers inside parentheses at the start of the string
    match = re.match(r'\((\d+)\)', text.strip())
    
    if match:
        return int(match.group(1))
    else:
        return None