"""
Some out-of-the-box field pre-processors that seem like they'd be useful in almost any CE template. These help with
converting dates, phone numbers, province codes, and more.
"""
from __future__ import annotations

import datetime

import phonenumbers
import us

from CE2OCF.utils.log_utils import logger
from CE2OCF.utils.model_utils import is_iterable

GD_HUMAN_REPEAT_SELECTIONS_TO_VAR_NAMES = {
    "Paid With": "PaidWith",
    "Genus-level Description of Company Project": "BroadDescriptionAssignedTechnology",
    "Specific Description of Assigned Technology": "DescriptionAssignedTechnology",
    "Vesting Schedule": "Vesting",
    "Vesting Commencement Date": "VCD",
    "Single Trigger Acceleration Provision": "SingleTrigger",
    "Double Trigger Acceleration Provision": "DoubleTrigger",
}


def year_from_iso_date(val, *args) -> str | None:
    try:
        return str(datetime.date.fromisoformat(val).year)
    except Exception:
        return None


def convert_state_free_text_to_province_code(raw_state_name_input: str, *args) -> str | None:
    logger.debug(f"convert_state_free_text_to_province_code() - raw_state_name_input: {raw_state_name_input}")

    try:
        state = us.states.lookup(str(raw_state_name_input))
        logger.debug(f"convert_state_free_text_to_province_code() - Resulting state: {state}")
        return str(state.abbr)
    except Exception as e:
        logger.warning(
            f"convert_state_free_text_to_province_code() - could not resolve state code {raw_state_name_input} "
            f"(type {type(raw_state_name_input)}) due to unexpected error: {e}"
        )
        return None


def convert_phone_number_to_international_standard(raw_phone_number: str, *args) -> str:
    parsed_phone_number = None

    try:
        parsed_phone_number = phonenumbers.parse(raw_phone_number, None)
    except phonenumbers.phonenumberutil.NumberParseException:
        logger.debug(f"raw_phone_number {raw_phone_number} is NOT in international format... try US")
        try:
            parsed_phone_number = phonenumbers.parse(raw_phone_number, "US")
        except phonenumbers.phonenumberutil.NumberParseException:
            logger.debug(f"raw_phone_number {raw_phone_number} is NOT valid US format... ")

    if parsed_phone_number is not None:
        parsed_phone_number = (
            "+"
            + str(parsed_phone_number.country_code)
            + " "
            + str(parsed_phone_number.national_number)[:3]
            + " "
            + str(parsed_phone_number.national_number)[3:6]
            + " "
            + str(parsed_phone_number.national_number)[6:]
        )
        logger.info(f"parsed_phone_number: {parsed_phone_number}")
    else:
        parsed_phone_number = ""

    return parsed_phone_number


def gunderson_repeat_var_processor(x, ce_jsons):
    """
    In our templates, the repeated_variables values are human-friendly strings which don't map
    perfectly to actual variable names, so we first need to fetch the selected user choices for which
    variables to repeat and then map them to actual variable names

    Args:
        x:
        ce_jsons:

    Returns:

    """

    results = []
    logger.debug(f"X value is {type(x)}: {x}")
    if is_iterable(x):
        for val in x:
            if val in x:
                results.append(GD_HUMAN_REPEAT_SELECTIONS_TO_VAR_NAMES[val])
    elif isinstance(x, str):
        if x in GD_HUMAN_REPEAT_SELECTIONS_TO_VAR_NAMES:
            results.append(GD_HUMAN_REPEAT_SELECTIONS_TO_VAR_NAMES[x])

    return results
