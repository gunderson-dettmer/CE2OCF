from __future__ import annotations

import uuid
from typing import Any

from CE2OCF.types.enums import (
    OcfPeriodTypeEnum,
    OcfVestingDayOfMonthEnum,
)
from CE2OCF.types.protocols import OcfEventGeneratorFunctionSig
from CE2OCF.utils.log_utils import logger


def generate_event_based_vesting_condition(
    condition_id: str | None = None,
    next_condition_ids: list[str] | None = None,
    description: str = "",
    remainder: bool = False,
    portion_numerator: int | None = None,
    portion_denominator: int | None = None,
    quantity: int | None = None,
) -> dict:
    """

    Builds OCF for event-based vesting condition. Can we set to either a fixed quantity or
    portion of quantity - either remaining unvested (if remainder is True) or portion of original grant
    (if remainder is False).

    :param quantity: If you want to use an absolute quantity, set this BUT NOT portion_denominator and portion_numerator
    :param portion_denominator: If you want this to be determined as some fraction or percent of vesting shares set
                                this and portion_numerator - NOT quantity
    :param portion_numerator: If you want this to be determined as some fraction or percent of vesting shares set
                                this and portion_denominator - NOT quantity
    :param remainder: If false, the ratio is applied to the entire quantity of the security's issuance. If true,
                            it is applied to the amount that has yet to vest.
    :param condition_id: ID for this condition or, if none provider, random uuid v4 generated
    :param next_condition_ids: What are subsequent, dependent vesting conditions? Default is None
    :param description: Plain text description. Inclusion of specific legal language is suggested
    :return: OCF vesting condition dictionary matching specified parameters
    """

    logger.debug("Function: generate_event_based_vesting_condition")
    logger.debug("Arguments:")
    logger.debug(f"   condition_id: {condition_id}")
    logger.debug(f"   next_condition_ids: {next_condition_ids}")
    logger.debug(f"   description: {description}")
    logger.debug(f"   remainder: {remainder}")
    logger.debug(f"   portion_numerator: {portion_numerator}")
    logger.debug(f"   portion_denominator: {portion_denominator}")
    logger.debug(f"   quantity: {quantity}")

    if next_condition_ids is None:
        next_condition_ids = []

    if not condition_id:
        condition_id = uuid.uuid4().__str__()

    if (portion_numerator is not None or portion_denominator is not None) and not (
        isinstance(portion_denominator, int) and isinstance(portion_numerator, int)
    ):
        raise ValueError(
            "If you are going to use a portion, you need to provide portion_numerator and portion_denominator"
        )

    if quantity is not None and (portion_numerator or portion_denominator):
        raise ValueError(
            "If you use quantity (fixed number of security units) do not provide portion values or vice-versa"
        )

    if quantity is not None and (portion_numerator or portion_denominator):
        raise ValueError(
            "If you use quantity (fixed number of security units) do not provide portion values or vice-versa"
        )

    condition_ocf: dict[str, Any] = {
        "id": condition_id,
        "description": description,
        "next_condition_ids": next_condition_ids,
        "trigger": {"type": "VESTING_EVENT"},
    }

    if quantity is not None:
        condition_ocf["quantity"] = f"{quantity}"

    if isinstance(portion_numerator, int) and isinstance(portion_denominator, int):

        condition_ocf["portion"] = {
            "numerator": f"{portion_numerator}",
            "denominator": f"{portion_denominator}",
        }

        if remainder is not None:
            condition_ocf["portion"]["remainder"] = remainder

    return condition_ocf


def generate_vesting_start_condition(
    next_condition_ids: list[str] | None = None,
    portion_numerator: int | None = None,
    portion_denominator: int | None = None,
    quantity: int | None = None,
    condition_id: str | None = None,
    remainder: bool | None = None,
) -> dict:

    logger.debug("Function: generate_vesting_start_condition()")
    logger.debug("Arguments:")
    logger.debug(f"   next_condition_ids: {next_condition_ids}")
    logger.debug(f"   portion_numerator: {portion_numerator}")
    logger.debug(f"   portion_denominator: {portion_denominator}")
    logger.debug(f"   quantity: {quantity}")
    logger.debug(f"   condition_id: {condition_id}")
    logger.debug(f"   remainder: {remainder}")

    if (portion_numerator is not None or portion_denominator is not None) and not (
        isinstance(portion_denominator, int) and isinstance(portion_numerator, int)
    ):
        raise ValueError(
            "If you are going to use a portion, you need to provide portion_numerator and portion_denominator"
        )

    if quantity is not None and (portion_numerator or portion_denominator):
        raise ValueError(
            "If you use quantity (fixed number of security units) do not provide portion values or vice-versa"
        )

    if quantity == portion_numerator == portion_denominator is None:
        raise ValueError("You need to define either a portion or quantity based amount")

    if next_condition_ids is None:
        next_condition_ids = []

    if not condition_id:
        condition_id = uuid.uuid4().__str__()

    condition: dict[str, Any] = {
        "id": condition_id,
        "trigger": {"type": "VESTING_START_DATE"},
        "next_condition_ids": next_condition_ids,
    }

    if quantity is not None:
        condition["quantity"] = f"{quantity}"

    if portion_numerator and portion_denominator:
        condition["portion"] = {
            "numerator": f"{portion_numerator}",
            "denominator": f"{portion_denominator}",
        }

        if remainder is not None:
            condition["portion"]["remainder"] = remainder

    return condition


def generate_cliff_vesting_condition_id(schedule_id: str) -> str:
    return f"{schedule_id} | Cliff Vest"


def generate_monthly_vesting_condition_id(schedule_id, modifier: str = "") -> str:
    return f"{schedule_id} | Monthly Vesting{' ' if modifier != '' else ''}{modifier}"


def generate_vesting_condition_relative_time_based(
    relative_to_condition_id: str = "",
    condition_id: str | None = None,
    time_units: str | OcfPeriodTypeEnum = OcfPeriodTypeEnum.YEARS,
    time_unit_quantity: int = 1,
    time_period_repetition: int = 1,
    portion_numerator: int | str | None = None,
    portion_denominator: int | str | None = None,
    quantity: int | str | None = None,
    next_condition_ids: list[str] | None = None,
    vesting_day_of_month: OcfVestingDayOfMonthEnum = OcfVestingDayOfMonthEnum.VESTING_START_DAY_OR_LAST_DAY_OF_MONTH,
    remainder: bool | None = None,
) -> dict:

    if next_condition_ids is None:
        next_condition_ids = []

    if not condition_id:
        condition_id = uuid.uuid4().__str__()

    if (portion_numerator is not None or portion_denominator is not None) and not (
        isinstance(portion_denominator, (str, int)) and isinstance(portion_numerator, (str, int))
    ):
        raise ValueError(
            "If you are going to use a portion, you need to provide portion_numerator and portion_denominator"
        )

    if quantity is not None and (portion_numerator or portion_denominator):
        raise ValueError(
            "If you use quantity (fixed number of security units) do not provide portion values or vice-versa - "
            f"| provided quantity {quantity} portion_numerator {portion_numerator} | "
            f"portion_denominator: {portion_denominator}"
        )

    condition: dict[str, Any] = {
        "id": condition_id,
        "description": f"GD Autogenerated Time-Based Vesting Condition occurring every "
        f"{time_unit_quantity} {time_units}, "
        f"{time_period_repetition} times, after {relative_to_condition_id}",
        "trigger": {
            "type": "VESTING_SCHEDULE_RELATIVE",
            "period": {
                "length": time_unit_quantity,
                "type": time_units,
                "occurrences": time_period_repetition,
                "day_of_month": vesting_day_of_month,
            },
            "relative_to_condition_id": relative_to_condition_id,
        },
        "next_condition_ids": next_condition_ids,
    }

    if quantity is not None:
        condition["quantity"] = f"{quantity}"
    else:
        condition["portion"] = {
            "numerator": f"{portion_numerator}",
            "denominator": f"{portion_denominator}",
        }

        if remainder is not None:
            condition["portion"]["remainder"] = remainder

    return condition


def generate_time_based_ocf_vesting_conditions_with_time_served_credit_acceleration(
    vesting_start_condition_id: str,
    end_month: int = 48,
    cliff_month: int | None = 12,
    months_of_vest_credit_on_trigger: int = 6,
    ocf_event_generator: OcfEventGeneratorFunctionSig | None = None,
) -> tuple[str, list[dict]]:
    """

    This can be used to generate schedules with or without cliffs. For simplicity's sake, it must be
    expressed in months. "Time-Served" acceleration is basically where you say that someone's vesting should be
    calculated as if they served additional months.

    :param vesting_start_condition_id: To tie into any other parts of the vesting schedule, what is the vesting start
                                        condition this should be dependent upon. Could technically be any vesting
                                        condition id you want this to be based off of.
    :param end_month: How many months is the vesting schedule total.
    :param cliff_month: Must be before the end month - e.g. a cliff on month 498 or 49 or a 48-month schedule is stupid.
    :param months_of_vest_credit_on_trigger: If we're giving extra months to time served calculation, how many? This
                                            cannot be more credit months than you can use. E.g. if there's a cliff
                                            at 12 months and a 48-month vesting schedule, you can offer a max of 35
                                            months credit.
    :param ocf_event_generator: Callable to generate OCF events. You may want to use your own function if our default
                                signature doesn't match what you need
    :return: a tuple, with element 0 being the id of the first vesting condition and element 1 being list of ocf
             conditions.


    """

    vesting_period_type = "MONTHS"
    start_condition_id = ""
    conditions = []

    if isinstance(cliff_month, int):
        if cliff_month >= end_month:
            raise ValueError("Sorry, cliff month must be before the end month (or 0 for no cliff)")

        if months_of_vest_credit_on_trigger > end_month - cliff_month:
            raise ValueError(
                "Sorry, it doesn't make sense to acceleration give you more months credit than it's possible "
                "to actually use (e.g. a 13 month vesting credit on a 12 month vesting schedule is not allowed). "
            )

    if cliff_month is None:
        shares_start_vesting_in_month_n = 0
    else:
        shares_start_vesting_in_month_n = cliff_month - months_of_vest_credit_on_trigger
    logger.debug(f"Shares start vesting in month {shares_start_vesting_in_month_n}")

    if shares_start_vesting_in_month_n < 0:
        shares_start_vesting_in_month_n = 0
        logger.debug(f"Shares start vesting adjusted to {shares_start_vesting_in_month_n}")

    months_fully_vested = end_month - months_of_vest_credit_on_trigger
    logger.debug(f"Months fully vested: {months_fully_vested}")

    if cliff_month is not None and shares_start_vesting_in_month_n > 0:
        start_condition_id = "PRE-CLIFF-VEST-PERIOD"
        conditions.extend(
            [
                {
                    "id": "PRE-CLIFF-VEST-PERIOD",
                    "description": "Period during which no shares will vest, even with acceleration",
                    "portion": {"numerator": "0", "denominator": "0"},
                    "trigger": {
                        "type": "VESTING_SCHEDULE_RELATIVE",
                        "period": {
                            "length": cliff_month - months_of_vest_credit_on_trigger,
                            "type": vesting_period_type,
                            "occurrences": 1,
                            "day_of_month": "VESTING_START_DAY_OR_LAST_DAY_OF_MONTH",
                        },
                        "relative_to_condition_id": vesting_start_condition_id,
                    },
                    "next_condition_ids": [
                        f"MONTH-{shares_start_vesting_in_month_n}-TO-{shares_start_vesting_in_month_n + 1}-ACCELERATED-"
                        "AMT-VEST-PERIOD",
                    ],
                }
            ]
        )

    logger.debug(f"Starting conditions:\n{conditions}")

    for i in range(shares_start_vesting_in_month_n, months_fully_vested + 1):

        logger.debug(f"\tCalculate vesting for month {i} - {i + 1}")

        if i == shares_start_vesting_in_month_n:
            if shares_start_vesting_in_month_n > 0:
                relative_to_condition_id = "PRE-CLIFF-VEST-PERIOD"
            else:
                relative_to_condition_id = vesting_start_condition_id
        else:
            relative_to_condition_id = f"MONTH-{i - 1}-TO-{i}-ACCELERATED-AMT-VEST-PERIOD"

        logger.debug(f"\t\tPrevious condition: {relative_to_condition_id}")

        new_conditions = []

        if i < months_fully_vested:

            if i == shares_start_vesting_in_month_n:
                start_condition_id = f"MONTH-{i}-TO-{i + 1}-ACCELERATED-AMT-VEST-PERIOD"

            logger.debug(f"\t\tI is {i}")

            logger.debug(f"\t\tPortion {i + months_of_vest_credit_on_trigger} / {end_month}")
            new_conditions = [
                {
                    "id": f"MONTH-{i}-TO-{i + 1}-ACCELERATED-AMT-VEST-PERIOD",
                    "description": f"Amount of shares that vest for single trigger acceleration on month {i} of "
                    f"vesting schedule",
                    "portion": {"numerator": "0", "denominator": "0"},
                    "trigger": {
                        "type": "VESTING_SCHEDULE_RELATIVE",
                        "period": {
                            "length": 1,
                            "type": vesting_period_type,
                            "occurrences": 1,
                            "day_of_month": "VESTING_START_DAY_OR_LAST_DAY_OF_MONTH",
                        },
                        "relative_to_condition_id": relative_to_condition_id,
                    },
                    "next_condition_ids": [
                        f"MONTH-{i + 1}-TO-{i + 2}-ACCELERATED-AMT-VEST-PERIOD",
                        f"MONTH-{i}-TO-{i + 1}-ACCEL-VEST-AMOUNT",
                    ]
                    if i < months_fully_vested - 1
                    else [
                        f"POST-MONTH-{i + 1}-ACCELERATED-AMT-VEST-PERIOD",
                        f"MONTH-{i}-TO-{i + 1}-ACCEL-VEST-AMOUNT",
                    ],
                },
                {
                    "id": f"MONTH-{i}-TO-{i + 1}-ACCEL-VEST-AMOUNT",
                    "description": f"Holder is terminated during month {i} of vesting",
                    "portion": {
                        "numerator": str(i + months_of_vest_credit_on_trigger),
                        "denominator": str(end_month),
                    },
                    "trigger": {"type": "VESTING_EVENT"},
                    "next_condition_ids": [],
                }
                if ocf_event_generator is None
                else ocf_event_generator(
                    period_number=i,
                    period_type="MONTHS",
                    on_or_after_fully_vested_cutoff=False,
                    portion_numerator=i + months_of_vest_credit_on_trigger,
                    portion_denominator=end_month,
                    id=f"MONTH-{i}-TO-{i + 1}-ACCEL-VEST-AMOUNT",
                ),
            ]

        elif i == months_fully_vested:

            logger.debug(f"\t\t💣 💣 Detected we are at month {months_fully_vested} - fully vested")
            logger.debug(f"\t\t\tPortion {end_month} / {end_month}")

            if i == shares_start_vesting_in_month_n:
                start_condition_id = f"MONTH-{i}-AND-LATER-ACCEL-VEST-AMOUNT"

            new_conditions = [
                {
                    "id": f"MONTH-{i}-AND-LATER-ACCEL-VEST-AMOUNT",
                    "description": f"Holder is terminated on or after month #{i} of vesting",
                    "portion": {"numerator": str(end_month), "denominator": str(end_month)},
                    "trigger": {"type": "VESTING_EVENT"},
                    "next_condition_ids": [],
                }
                if ocf_event_generator is None
                else ocf_event_generator(
                    period_number=i,
                    period_type="MONTHS",
                    on_or_after_fully_vested_cutoff=True,
                    portion_numerator=end_month,
                    portion_denominator=end_month,
                    id=f"MONTH-{i}-AND-LATER-ACCEL-VEST-AMOUNT",
                ),
                {
                    "id": f"POST-MONTH-{i}-ACCELERATED-AMT-VEST-PERIOD",
                    "description": f"Accelerated vesting is fully vested on or after month {i} of vesting schedule",
                    "portion": {"numerator": "0", "denominator": "0"},
                    "trigger": {
                        "type": "VESTING_SCHEDULE_RELATIVE",
                        "period": {
                            "length": end_month - months_fully_vested,
                            "type": vesting_period_type,
                            "occurrences": 1,
                            "day_of_month": "VESTING_START_DAY_OR_LAST_DAY_OF_MONTH",
                        },
                        "relative_to_condition_id": f"MONTH-{i}-ACCEL-VEST-AMOUNT",
                    },
                    "next_condition_ids": [f"MONTH-{i}-AND-LATER-ACCEL-VEST-AMOUNT"],
                },
            ]
        else:
            pass
        logger.debug(f"\t\tNew conditions: {new_conditions}")
        conditions.extend(new_conditions)

    return start_condition_id, conditions
