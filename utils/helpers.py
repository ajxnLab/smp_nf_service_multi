from datetime import datetime
import logging
from itertools import zip_longest
import os
import sys
from typing import List, Dict, Any
import time


logger = logging.getLogger(__name__)


# Function to get the value after the given word
def get_after_word(sentence, word):
    """
    Extracts the text immediately following a specific word in a sentence.

    Args:
        sentence: The input sentence (string).
        word: The word to search for (string).

    Returns:
        The text immediately following the word, or None if the word is not found
        or if it's the last word in the sentence.
    """
    index = sentence.find(word)
    if index == -1:
        return None  # Word not found

    index += len(word)

    if index >= len(sentence) or sentence[index : index + 1] == "":
        return None

    remaining_sentence = sentence[index:].strip()
    next_word = remaining_sentence.split(" ")[0]

    return next_word


# def convert_string_hashmap(value: str | Dict, convert_to: str) -> Dict | str:
#     # Convert string to dict
#     if convert_to == "dict":
#         string_replaced = value.replace(" | ", ",").replace(": ", ",")
#         list_value = string_replaced.split(",")
#         hashmap = {
#             list_value[i]: list_value[i + 1] for i in range(0, len(list_value), 2)
#         }
#         logger.info(f"Converted from String to Dictionary: {hashmap}")
#         return hashmap

#     # Convert dict back to original string format
#     elif convert_to == "string":
#         converted_string = " | ".join(f"{key}: {value}" for key, value in value.items())
#         logger.info(f"Converted from Dictionary to String: {converted_string}")
#         return converted_string

def convert_string_hashmap(value: str | Dict, convert_to: str, is_check_has: bool = False) -> Dict | str:
    """
    Convert between string and dictionary formats with special handling for CHECK_HAS cases.
    
    Args:
        value: String to convert to dict, or dict to convert to string
        convert_to: Either "dict" or "string"
        is_check_has: Flag to indicate if this is a CHECK_HAS conversion
    """
    # Convert string to dict
    if convert_to == "dict":
        try:
            if "CHECK_HAS_OTHER" in value:
                # Special handling for CHECK_HAS format
                key = "CHECK_HAS_OTHER"
                # Extract everything after the colon
                failed_value = value.split(":", 1)[1].strip()
                return {key: failed_value}
            else:
                # Standard processing for other cases
                string_replaced = value.replace(" | ", ",").replace(": ", ",")
                list_value = string_replaced.split(",")
                hashmap = {
                    list_value[i]: list_value[i + 1] 
                    for i in range(0, len(list_value), 2)
                }
                logger.info(f"Converted from String to Dictionary: {hashmap}")
                return hashmap

        except Exception as e:
            logger.error(f"Error converting string to dictionary: {e}")
            return {}

    # Convert dict back to string
    elif convert_to == "string":
        try:
            if not isinstance(value, dict):
                return str(value)
                
            converted_string = " | ".join(f"{key}: {val}" for key, val in value.items())
            logger.info(f"Converted from Dictionary to String: {converted_string}")
            return converted_string
            
        except Exception as e:
            logger.error(f"Error converting dictionary to string: {e}")
            return ""


def nf_get_in_prov_values(prefix_value, sms_voice_key, step_type):
    sms_voice_value = "Unli SMS" if sms_voice_key == "unli_sms" else "Unli Voice"
    double_flow_true = True if prefix_value == "double" else False

    if "data_prov" == step_type:
        step_type_name = (
            "Data Prov Extension With Keyword Mapping"
            if prefix_value == "double"
            else (
                "Data Extend Wallet Expiry"
                if prefix_value == "extend"
                else "Data Prov With Keyword Mapping"
            )
        )
    elif "sms_voice_service" == step_type:
        step_type_name = (
            f"In Add Wallet FUP - {sms_voice_value}"
            if prefix_value == "double"
            else (
                f"In Extend Wallet Expiry - {sms_voice_value}"
                if prefix_value == "extend"
                else f"In Prov Service - {sms_voice_value}"
            )
        )

    return step_type_name, double_flow_true

# def retryable(max_retries=2, delay=2):
#     def decorator(func):
#         def wrapper(*args, **kwargs):
#             for attempt in range(1, max_retries + 1):
#                 try:
#                     return func(*args, **kwargs)
#                 except Exception as e:
#                     if attempt == max_retries:
#                         raise
#                     logger.warning(f"Retry {attempt}/{max_retries} failed: {e}, retrying...")
#                     time.sleep(delay)
#         return wrapper
#     return decorator

def retryable(max_retries=2, delay=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            self = args[0]  # capture the class instance
            step_name = None

            # Try to retrieve step_name if provided inside kwargs or from the object later
            # If the wrapped method defines step_name internally, we’ll catch it after failure
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Try to get step_name dynamically if function set it
                    try:
                        step_name = getattr(self, 'current_step_name', None) or kwargs.get('step_name')
                    except:
                        pass

                    if attempt == max_retries:
                        logger.error(f"Max retries reached for {func.__name__}: {e}")
                        # Mark as failed if we have step_name
                        if step_name:
                            self.bs_rpa_remark_fail[step_name] = "Failed"
                        raise
                    else:
                        logger.warning(f"Retry {attempt}/{max_retries} failed: {e}, retrying...")
                        time.sleep(delay)
        return wrapper
    return decorator

def convert_wallet_amount(wallet_amount: str) -> str:
    """
    Convert wallet amount to appropriate data allocation format
    
    Args:
        wallet_amount: String containing number or number with unit (e.g. '1024' or '50KB')
    Returns:
        Formatted data allocation string (e.g. '1GB' or '50KB')
    """
    try:
        # Remove any whitespace
        wallet_amount = str(wallet_amount).strip()
        
        # If amount already has KB/MB/GB suffix, return as is
        if any(unit in wallet_amount.upper() for unit in ['KB', 'MB', 'GB']):
            return wallet_amount.upper()
            
        # Convert numeric amount to int
        amount = int(wallet_amount)
        
        # Convert to appropriate unit
        if amount >= 1024:
            return f"{amount // 1024}GB"
        else:
            return f"{amount}MB"
            
    except ValueError as e:
        logger.error(f"Invalid wallet amount format: {wallet_amount}")
        raise ValueError(f"Wallet amount must be a number or include KB/MB/GB units: {e}")
    
#SMP

def get_datetime(format: str = "iso", tz=None) -> str:
    """
    Returns the current date/time in the requested format.
    
    Args:
        format: str - The format type ("iso", "date", "time", "custom")
        tz: timezone - Optional timezone (use from pytz or zoneinfo)
        
    Returns:
        str - formatted datetime string
    """
    now = datetime.now(tz)
    
    if format == "iso":
        return now.isoformat()
    elif format == "date":
        return now.strftime("%Y-%m-%d")
    elif format == "time":
        return now.strftime("%H:%M:%S")
    elif format == "full":
        return now.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(format, str):
        return now.strftime(format)
    else:
        raise ValueError("Unsupported format")

def duration_time(start_time, end_time):
    try:
        start_time_duration = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        end_time_duration = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        duration = end_time_duration - start_time_duration
        return duration
    except ValueError as ve:
        # Raised when strptime() fails to parse the datetime
        logger.error(f"Invalid date format: {ve}")
        return None
    
    except TypeError as te:
        # Raised if input is not a string
        logger.error(f"Type error in duration_time(): {te}")
        return None
    except Exception as e:
        # Catch-all for unexpected issues
        logger.error(f"Unexpected error in duration_time(): {e}")
        return None


def wait(seconds):
    time.sleep(seconds)

