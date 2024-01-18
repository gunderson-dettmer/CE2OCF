from __future__ import annotations

from CE2OCF.datamap.loaders import (
    load_cic_event_definition,
    load_double_trigger_definitions,
    load_single_trigger_definitions,
)
from CE2OCF.ocf.generators.ocf_id_generators import (
    generate_accel_trigger_termination_event_id,
    generate_cic_event_id,
    generate_time_based_accel_expiration_event_id,
    generate_vesting_start_id,
)
from CE2OCF.ocf.generators.ocf_vesting_conditions import (
    generate_cliff_vesting_condition_id,
    generate_event_based_vesting_condition,
    generate_monthly_vesting_condition_id,
    generate_time_based_ocf_vesting_conditions_with_time_served_credit_acceleration,
    generate_vesting_condition_relative_time_based,
    generate_vesting_start_condition,
)
from CE2OCF.ocf.generators.ocf_vesting_events import (
    cic_event_generator,
    generate_change_in_control_event,
    generate_vesting_termination_event,
)
from CE2OCF.types.dictionaries import (
    CicEventDefinition,
    TerminationDetails,
)
from CE2OCF.types.enums import (
    DoubleTriggerTypesEnum,
    OcfPeriodTypeEnum,
    SingleTriggerTypesEnum,
    VestingTypesEnum,
)
from CE2OCF.utils.log_utils import logger


def generate_single_trigger_conditions_from_enumerations(
    single_trigger_type: SingleTriggerTypesEnum | str,
    vesting_schedule_type: VestingTypesEnum | str,
    vesting_schedule_id: str,
    single_trigger_termination_details: dict[str, CicEventDefinition | None] | None = None,
) -> tuple[str, list[dict]]:
    """
    Generates required single trigger vesting conditions from our enums.

    :param single_trigger_type:
    :param vesting_schedule_type:
    :param vesting_schedule_id:
    :PARAM termination_details:
    :return: A tuple - element 0 is start condition of id of the generated schedule. Element 1 is the actual list of
            ocf objs.

    Args:
        termination_details:
    """

    if single_trigger_termination_details is None:
        single_trigger_termination_details = load_single_trigger_definitions()

    if isinstance(single_trigger_type, str):
        single_trigger_type = SingleTriggerTypesEnum(single_trigger_type)

    if isinstance(vesting_schedule_type, str):
        vesting_schedule_type = VestingTypesEnum(vesting_schedule_type)

    condition_ocf_objs = []
    start_condition_id = ""

    if vesting_schedule_type == VestingTypesEnum.CUSTOM:
        msg = "Custom vesting schedule with single trigger acceleration not implemented"
        raise ValueError(msg)

    if single_trigger_type == SingleTriggerTypesEnum.CUSTOM:
        msg = "Custom single trigger acceleration not implemented"
        raise ValueError(msg)

    single_trigger_vals = single_trigger_termination_details[single_trigger_type]
    assert single_trigger_vals is not None

    if single_trigger_type == SingleTriggerTypesEnum.ONE_HUNDRED_PERCENT_INVOLUNTARY_TERMINATION:
        msg = f"INFO - vesting_schedule_type arg {vesting_schedule_type} has no effect for {single_trigger_type} accel"
        logger.debug(msg)

        start_condition_id = generate_accel_trigger_termination_event_id(vesting_schedule_id, "Single")

        condition_ocf_objs.append(
            generate_event_based_vesting_condition(
                condition_id=start_condition_id,
                **single_trigger_vals,
            )
        )
    elif single_trigger_type == SingleTriggerTypesEnum.ONE_HUNDRED_PERCENT_ALL_TIMES:
        logger.debug(
            f"INFO - vesting_schedule_type arg {vesting_schedule_type} has no effect for {single_trigger_type} accel"
        )

        start_condition_id = generate_cic_event_id(vesting_schedule_id, "Single")
        condition_ocf_objs.append(
            generate_event_based_vesting_condition(
                condition_id=start_condition_id,
                **single_trigger_vals,
            )
        )
    else:
        # for acceleration where you get credited extra months of vesting... the resulting output
        # looks very different for a pure monthly schedule vs a schedule with a cliff.
        if vesting_schedule_type == VestingTypesEnum.FOUR_YR_NO_CLIFF:
            # These are CiC-based triggers
            if single_trigger_type == SingleTriggerTypesEnum.TWENTY_FOUR_MONTHS_ALL_TIMES:
                (
                    start_condition_id,
                    vest_cond_objs,
                ) = generate_time_based_ocf_vesting_conditions_with_time_served_credit_acceleration(
                    generate_vesting_start_id(vesting_schedule_id),
                    end_month=48,
                    cliff_month=0,
                    months_of_vest_credit_on_trigger=24,
                    ocf_event_generator=cic_event_generator,
                )

                condition_ocf_objs.extend(vest_cond_objs)

            elif single_trigger_type == SingleTriggerTypesEnum.TWELVE_MONTHS_ALL_TIMES:
                (
                    start_condition_id,
                    vest_cond_objs,
                ) = generate_time_based_ocf_vesting_conditions_with_time_served_credit_acceleration(
                    generate_vesting_start_id(vesting_schedule_id),
                    end_month=48,
                    cliff_month=0,
                    months_of_vest_credit_on_trigger=12,
                    ocf_event_generator=cic_event_generator,
                )

                condition_ocf_objs.extend(vest_cond_objs)

            elif single_trigger_type == SingleTriggerTypesEnum.SIX_MONTHS_ALL_TIMES:
                (
                    start_condition_id,
                    vest_cond_objs,
                ) = generate_time_based_ocf_vesting_conditions_with_time_served_credit_acceleration(
                    generate_vesting_start_id(vesting_schedule_id),
                    end_month=48,
                    cliff_month=0,
                    months_of_vest_credit_on_trigger=6,
                    ocf_event_generator=cic_event_generator,
                )

                condition_ocf_objs.extend(vest_cond_objs)
            elif single_trigger_type == SingleTriggerTypesEnum.SIX_MONTHS_INVOLUNTARY_TERMINATION:
                (
                    start_condition_id,
                    vest_cond_objs,
                ) = generate_time_based_ocf_vesting_conditions_with_time_served_credit_acceleration(
                    generate_vesting_start_id(vesting_schedule_id),
                    end_month=48,
                    cliff_month=0,
                    months_of_vest_credit_on_trigger=6,
                    ocf_event_generator=generate_vesting_termination_event,
                )

                condition_ocf_objs.extend(vest_cond_objs)

            elif single_trigger_type == SingleTriggerTypesEnum.TWELVE_MONTHS_INVOLUNTARY_TERMINATION:
                (
                    start_condition_id,
                    vest_cond_objs,
                ) = generate_time_based_ocf_vesting_conditions_with_time_served_credit_acceleration(
                    generate_vesting_start_id(vesting_schedule_id),
                    end_month=48,
                    cliff_month=0,
                    months_of_vest_credit_on_trigger=12,
                    ocf_event_generator=generate_vesting_termination_event,
                )

                condition_ocf_objs.extend(vest_cond_objs)

            elif single_trigger_type == SingleTriggerTypesEnum.TWENTY_FOUR_MONTHS_INVOLUNTARY_TERMINATION:
                (
                    start_condition_id,
                    vest_cond_objs,
                ) = generate_time_based_ocf_vesting_conditions_with_time_served_credit_acceleration(
                    generate_vesting_start_id(vesting_schedule_id),
                    end_month=48,
                    cliff_month=0,
                    months_of_vest_credit_on_trigger=24,
                    ocf_event_generator=generate_vesting_termination_event,
                )

                condition_ocf_objs.extend(vest_cond_objs)
            else:
                logger.debug("WARNING - Unexpected combination of acceleration and vesting...")

        elif vesting_schedule_type == VestingTypesEnum.FOUR_YR_1_YR_CLIFF:
            # Since these are OVER the cliff, we can just add 12/48 or 24/48 portion
            if single_trigger_type == SingleTriggerTypesEnum.TWENTY_FOUR_MONTHS_INVOLUNTARY_TERMINATION:
                (
                    start_condition_id,
                    vest_cond_objs,
                ) = generate_time_based_ocf_vesting_conditions_with_time_served_credit_acceleration(
                    generate_vesting_start_id(vesting_schedule_id),
                    end_month=48,
                    cliff_month=12,
                    months_of_vest_credit_on_trigger=24,
                    ocf_event_generator=generate_vesting_termination_event,
                )

                condition_ocf_objs.extend(vest_cond_objs)

            elif single_trigger_type == SingleTriggerTypesEnum.TWELVE_MONTHS_INVOLUNTARY_TERMINATION:
                (
                    start_condition_id,
                    vest_cond_objs,
                ) = generate_time_based_ocf_vesting_conditions_with_time_served_credit_acceleration(
                    generate_vesting_start_id(vesting_schedule_id),
                    end_month=48,
                    cliff_month=12,
                    months_of_vest_credit_on_trigger=12,
                    ocf_event_generator=generate_vesting_termination_event,
                )
                condition_ocf_objs.extend(vest_cond_objs)

            elif single_trigger_type == SingleTriggerTypesEnum.SIX_MONTHS_INVOLUNTARY_TERMINATION:
                (
                    start_condition_id,
                    vest_cond_objs,
                ) = generate_time_based_ocf_vesting_conditions_with_time_served_credit_acceleration(
                    generate_vesting_start_id(vesting_schedule_id),
                    end_month=48,
                    cliff_month=12,
                    months_of_vest_credit_on_trigger=6,
                    ocf_event_generator=generate_vesting_termination_event,
                )
                condition_ocf_objs.extend(vest_cond_objs)

            elif single_trigger_type == SingleTriggerTypesEnum.TWELVE_MONTHS_ALL_TIMES:
                (
                    start_condition_id,
                    vest_cond_objs,
                ) = generate_time_based_ocf_vesting_conditions_with_time_served_credit_acceleration(
                    generate_vesting_start_id(vesting_schedule_id),
                    end_month=48,
                    cliff_month=12,
                    months_of_vest_credit_on_trigger=12,
                    ocf_event_generator=cic_event_generator,
                )

                condition_ocf_objs.extend(vest_cond_objs)

            elif single_trigger_type == SingleTriggerTypesEnum.TWENTY_FOUR_MONTHS_ALL_TIMES:
                (
                    start_condition_id,
                    vest_cond_objs,
                ) = generate_time_based_ocf_vesting_conditions_with_time_served_credit_acceleration(
                    generate_vesting_start_id(vesting_schedule_id),
                    end_month=48,
                    cliff_month=12,
                    months_of_vest_credit_on_trigger=24,
                    ocf_event_generator=cic_event_generator,
                )

                condition_ocf_objs.extend(vest_cond_objs)

            elif single_trigger_type == SingleTriggerTypesEnum.SIX_MONTHS_ALL_TIMES:
                (
                    start_condition_id,
                    vest_cond_objs,
                ) = generate_time_based_ocf_vesting_conditions_with_time_served_credit_acceleration(
                    generate_vesting_start_id(vesting_schedule_id),
                    end_month=48,
                    cliff_month=12,
                    months_of_vest_credit_on_trigger=6,
                    ocf_event_generator=cic_event_generator,
                )
                condition_ocf_objs.extend(vest_cond_objs)
            else:
                logger.debug("WARNING - Unexpected combination of acceleration and vesting...")

        elif vesting_schedule_type == VestingTypesEnum.FULLY_VESTED:
            # shouldn't be vesting conditions
            pass
        else:
            logger.debug("WARNING - Unexpected combination of acceleration and vesting...")
            pass

    return start_condition_id, condition_ocf_objs


def generate_double_trigger_conditions_from_enumerations(
    double_trigger_type: DoubleTriggerTypesEnum,
    vesting_schedule_id: str,
    cic_event_definition: CicEventDefinition | None = None,
    double_trigger_termination_details: dict[str, TerminationDetails | None] | None = None,
) -> list[dict]:
    if cic_event_definition is None:
        cic_event_definition = load_cic_event_definition()

    if double_trigger_termination_details is None:
        double_trigger_termination_details = load_double_trigger_definitions()

    condition_ocf_objs: list[dict] = []

    if double_trigger_type not in double_trigger_termination_details:
        msg = (
            f"Provided double trigger value ({double_trigger_type}) not supported in "
            f"double_trigger_termination_details mapping object "
        )
        raise ValueError(msg)

    details = double_trigger_termination_details[double_trigger_type]

    # If mapping table maps to None don't generate anything...
    if details is None:
        return condition_ocf_objs

    cic_event_id = generate_cic_event_id(vesting_schedule_id, "Double")

    time_based_expiration_details = details["time_based_expiration_details"]
    time_based_expiration_event_id = (
        None
        if time_based_expiration_details is None
        else generate_time_based_accel_expiration_event_id(vesting_schedule_id, "Double")
    )

    termination_event_details = details["termination_event_details"]
    termination_event_id = generate_accel_trigger_termination_event_id(vesting_schedule_id, "Double")

    # generate the cic event first and set next_condition_ids to include the expiration event
    # if applicable, otherwise, just the termination event
    condition_ocf_objs.append(
        generate_change_in_control_event(
            vesting_schedule_id=vesting_schedule_id,
            cic_event_definition=cic_event_definition,
            next_condition_ids=[
                *([time_based_expiration_event_id] if time_based_expiration_event_id is not None else []),
                termination_event_id,
            ]
            if time_based_expiration_details is not None
            else [termination_event_id],
        )
    )

    # If there is a time-based expiration
    if time_based_expiration_details is not None:
        condition_ocf_objs.append(
            generate_vesting_condition_relative_time_based(
                relative_to_condition_id=cic_event_id,
                condition_id=time_based_expiration_event_id,
                **time_based_expiration_details,
            )
        )

    # Finally, generate the termination event condition
    condition_ocf_objs.append(
        generate_event_based_vesting_condition(condition_id=termination_event_id, **termination_event_details)
    )

    return condition_ocf_objs


def generate_ocf_vesting_schedule_from_enumerations(
    schedule_choice: str = VestingTypesEnum.FOUR_YR_1_YR_CLIFF,
    schedule_id: str = "",
    single_trigger: SingleTriggerTypesEnum | None = None,
    double_trigger: DoubleTriggerTypesEnum | None = None,
) -> dict | None:
    logger.debug(
        f"generate_ocf_vesting_schedule_from_gd_enumerations() - target gd type: _{schedule_choice}_ "
        f"(type {type(schedule_choice)})"
    )

    vesting_conditions: list[dict] = []

    if schedule_choice == VestingTypesEnum.FOUR_YR_1_YR_CLIFF:
        one_year_cliff_condition = generate_vesting_condition_relative_time_based(
            condition_id=generate_cliff_vesting_condition_id(schedule_id),
            relative_to_condition_id=generate_vesting_start_id(schedule_id),
            time_units=OcfPeriodTypeEnum.MONTHS,
            portion_numerator=12,
            portion_denominator=48,
            time_unit_quantity=12,
            time_period_repetition=1,
            next_condition_ids=[generate_monthly_vesting_condition_id(schedule_id)],
        )

        monthly_vesting_condition = generate_vesting_condition_relative_time_based(
            condition_id=generate_monthly_vesting_condition_id(schedule_id),
            relative_to_condition_id=generate_cliff_vesting_condition_id(schedule_id),
            time_units=OcfPeriodTypeEnum.MONTHS,
            portion_numerator=1,
            portion_denominator=48,
            time_unit_quantity=1,
            time_period_repetition=36,
        )

        vesting_start_condition = generate_vesting_start_condition(
            next_condition_ids=[generate_cliff_vesting_condition_id(schedule_id)],
            quantity=0,
            condition_id=generate_vesting_start_id(schedule_id),
        )
        vesting_conditions = [
            vesting_start_condition,
            one_year_cliff_condition,
            monthly_vesting_condition,
        ]

    elif schedule_choice == VestingTypesEnum.FOUR_YR_NO_CLIFF:
        vesting_start_condition = generate_vesting_start_condition(
            next_condition_ids=[generate_monthly_vesting_condition_id(schedule_id)],
            quantity=0,
            condition_id=generate_vesting_start_id(schedule_id),
        )

        monthly_vesting_condition = generate_vesting_condition_relative_time_based(
            condition_id=generate_monthly_vesting_condition_id(schedule_id),
            relative_to_condition_id=generate_vesting_start_id(schedule_id),
            time_units=OcfPeriodTypeEnum.MONTHS,
            portion_numerator=1,
            portion_denominator=48,
            time_unit_quantity=1,
            time_period_repetition=48,
        )
        vesting_conditions = [
            vesting_start_condition,
            monthly_vesting_condition,
        ]

    elif schedule_choice == VestingTypesEnum.FULLY_VESTED:
        return None

    else:
        msg = (
            f"Unsupported GD vesting enumeration {type(schedule_choice)}: {schedule_choice}. "
            f"Ocf conversion not supported."
        )
        raise ValueError(msg)

    # If we have to generate any kind of accel, first we need the cic event and we need to link it to vest start
    if double_trigger and double_trigger not in [
        DoubleTriggerTypesEnum.CUSTOM,
        DoubleTriggerTypesEnum.NA,
    ]:
        vesting_conditions = [
            *vesting_conditions,
            *generate_double_trigger_conditions_from_enumerations(
                double_trigger_type=double_trigger, vesting_schedule_id=schedule_id
            ),
        ]
        vesting_start_condition["next_condition_ids"] = [
            *vesting_start_condition["next_condition_ids"],
            generate_cic_event_id(schedule_id, "Double"),
        ]
        logger.debug(f"Generated double trigger vesting conditions: {vesting_conditions}")

    if single_trigger and single_trigger not in [
        SingleTriggerTypesEnum.CUSTOM,
        SingleTriggerTypesEnum.NA,
    ]:
        logger.debug(f"{single_trigger} and single_trigger not in Custom or NA")

        (
            start_vesting_condition_id,
            single_trig_vesting_conditions,
        ) = generate_single_trigger_conditions_from_enumerations(
            single_trigger_type=single_trigger,
            vesting_schedule_type=schedule_choice,
            vesting_schedule_id=schedule_id,
        )

        if start_vesting_condition_id != "":
            vesting_start_condition["next_condition_ids"] = [
                *vesting_start_condition["next_condition_ids"],
                start_vesting_condition_id,
            ]
            vesting_conditions = [*vesting_conditions, *single_trig_vesting_conditions]

        logger.debug("Generated single trigger vesting conditions...")

    return {
        "id": schedule_id,
        "object_type": "VESTING_TERMS",
        "name": schedule_choice,
        "description": schedule_choice,
        "allocation_type": "CUMULATIVE_ROUNDING",
        "vesting_conditions": vesting_conditions,
    }


def generate_ocf_vesting_schedule_from_vesting_drivers(vesting_schedule_inputs: dict, *args) -> dict | None:
    logger.debug(
        f"generate_ocf_vesting_schedule_from_vesting_drivers - vesting_schedule_inputs: {vesting_schedule_inputs}"
    )
    schedule_choice = vesting_schedule_inputs.get("vesting_schedule", None)
    logger.debug(f"generate_ocf_vesting_schedule_from_vesting_drivers  - schedule_choice: {schedule_choice}")

    single_trigger = vesting_schedule_inputs.get("single_trigger", None)
    try:
        single_trigger = SingleTriggerTypesEnum(single_trigger)
    except Exception as e:
        single_trigger = None
        logger.warning(
            f"generate_ocf_vesting_schedule_from_vesting_drivers() - Failed to parse SingleTriggerTypesEnum "
            f"from value {single_trigger}: {e}"
        )
    logger.debug(f"generate_ocf_vesting_schedule_from_vesting_drivers  - single_trigger: {single_trigger}")

    double_trigger = vesting_schedule_inputs.get("double_trigger", None)
    try:
        double_trigger = DoubleTriggerTypesEnum(double_trigger)
    except Exception as e:
        double_trigger = None
        logger.warning(
            f"generate_ocf_vesting_schedule_from_vesting_drivers() - Failed to parse DoubleTriggerTypesEnum "
            f"from value {double_trigger}: {e}"
        )
    logger.debug(f"generate_ocf_vesting_schedule_from_vesting_drivers  - double_trigger: {double_trigger}")

    schedule_id = f"{schedule_choice}/{single_trigger}/{double_trigger}"
    logger.debug(f"generate_ocf_vesting_schedule_from_vesting_drivers  - schedule_id: {schedule_id}")

    vesting_schedule_ocf = generate_ocf_vesting_schedule_from_enumerations(
        schedule_choice=schedule_choice,
        schedule_id=schedule_id,
        single_trigger=single_trigger,
        double_trigger=double_trigger,
    )
    return vesting_schedule_ocf
