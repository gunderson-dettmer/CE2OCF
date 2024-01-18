from __future__ import annotations

import datetime
import uuid

from CE2OCF.ocf.generators.ocf_id_generators import (
    generate_cic_event_id,
)
from CE2OCF.ocf.generators.ocf_vesting_conditions import (
    generate_event_based_vesting_condition,
)
from CE2OCF.types.dictionaries import CicEventDefinition


def cic_event_generator(
    period_number: int = 0,
    period_type: str = "MONTHS",
    on_or_after_fully_vested_cutoff: bool = False,
    portion_numerator: int = 0,
    portion_denominator: int = 0,
    id: str = "",
    **kwargs,
) -> dict:
    if on_or_after_fully_vested_cutoff:
        return generate_event_based_vesting_condition(
            condition_id=id,
            description=f"There is a change in control on or after {period_type} {period_number} of vesting",
            portion_denominator=portion_denominator,
            portion_numerator=portion_numerator,
        )
    else:
        return generate_event_based_vesting_condition(
            condition_id=id,
            description=f"There is a change in control during month {period_number} of vesting",
            portion_denominator=portion_denominator,
            portion_numerator=portion_numerator,
        )


def generate_vesting_start_event(
    vesting_commencement_date: datetime.date,
    issuance_id: str = "",
    vesting_start_condition_id: str = "",
) -> dict:
    return {
        "object_type": "TX_VESTING_START",
        "id": uuid.uuid4().__str__(),
        "security_id": issuance_id,
        "vesting_condition_id": vesting_start_condition_id,
        "date": vesting_commencement_date.isoformat(),
    }


def generate_vesting_termination_event(
    period_number: int = 0,
    period_type: str = "MONTHS",
    on_or_after_fully_vested_cutoff: bool = False,
    portion_numerator: int = 0,
    portion_denominator: int = 0,
    id: str = "",
    **kwargs,
) -> dict:
    if on_or_after_fully_vested_cutoff:
        return generate_event_based_vesting_condition(
            condition_id=id,
            description=f"Security holder terminated on or after {period_type} {period_number} of vesting",
            portion_denominator=portion_denominator,
            portion_numerator=portion_numerator,
        )
    else:
        return generate_event_based_vesting_condition(
            condition_id=id,
            description=f"Security holder terminated during month {period_number} of vesting",
            portion_denominator=portion_denominator,
            portion_numerator=portion_numerator,
        )


def generate_change_in_control_event(
    vesting_schedule_id: str,
    cic_event_definition: CicEventDefinition,
    next_condition_ids: list[str] = [],
) -> dict:
    cic_event_id = generate_cic_event_id(vesting_schedule_id)

    return generate_event_based_vesting_condition(
        condition_id=cic_event_id,
        **cic_event_definition,
        next_condition_ids=next_condition_ids,
    )
