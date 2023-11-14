from __future__ import annotations

import typing


def generate_vesting_start_id(schedule_id: str) -> str:
    return f"{schedule_id} | Start"


def generate_cic_event_id(
    vesting_schedule_id: str | int,
    trigger_type: typing.Literal["Single", "Double"] = "Double",
) -> str:
    return f"{vesting_schedule_id} | {trigger_type} Trigger CiC Event"


def generate_accel_trigger_termination_event_id(
    vesting_schedule_id: str | int,
    trigger_type: typing.Literal["Single", "Double"] = "Double",
) -> str:
    return f"{vesting_schedule_id} | {trigger_type} Trigger Termination Event"


def generate_time_based_accel_expiration_event_id(vesting_schedule_id: str | int, modifier: str = "") -> str:
    return f"{vesting_schedule_id} | Post-CiC Accel Exp{' ' if modifier != '' else ''}{modifier}"
