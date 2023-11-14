from typing import Any, Optional, TypedDict


class ContractExpressVarObj(TypedDict):
    name: str
    values: list[Any]
    repetition: Optional[str]


class OcfFileParts(TypedDict):
    file_name: str
    contents: dict
    bytes: bytes
    md5: str


class CicEventDefinition(TypedDict):
    description: str
    remainder: bool
    portion_numerator: int
    portion_denominator: int


class TimeBasedExpirationDetails(TypedDict):
    time_units: str
    time_unit_quantity: int
    time_period_repetition: int
    remainder: bool
    portion_numerator: int
    portion_denominator: int


class TerminationEventDetails(TypedDict):
    description: str
    remainder: bool
    portion_numerator: int
    portion_denominator: int


class TerminationDetails(TypedDict):
    time_based_expiration_details: Optional[TimeBasedExpirationDetails]
    termination_event_details: TerminationEventDetails


class TerminationInfo(TypedDict):
    N_A: None


class CE2OCFPipelineReturnType(TypedDict):
    """
    Intermediate return type for our pipeline function that parses lists of OCF objects from ce jsons
    """

    issuer_ocf: dict
    stock_classes_ocf: dict
    stakeholders_ocf: dict
    transactions_ocf: dict
    stock_plans_ocf: dict
    stock_legends_ocf: dict
    vesting_schedules_ocf: dict
    valuations_ocf: dict


class OcfFileContentsDict(TypedDict):
    OCF_STAKEHOLDERS_FILE: OcfFileParts
    OCF_STOCK_CLASSES_FILE: OcfFileParts
    OCF_STOCK_LEGEND_TEMPLATES_FILE: OcfFileParts
    OCF_STOCK_PLANS_FILE: OcfFileParts
    OCF_TRANSACTIONS_FILE: OcfFileParts
    OCF_VALUATIONS_FILE: OcfFileParts
    OCF_VESTING_TERMS_FILE: OcfFileParts
    OCF_MANIFEST_FILE: OcfFileParts


class VestingOcfFileContentsReturnType(TypedDict):
    items: list[dict]
    file_type: str


class TransactionOcfFileContentsReturnType(TypedDict):
    items: list[dict]
    file_type: str


class VestingAndTransactionReturnType(TypedDict):
    vesting_ocf: VestingOcfFileContentsReturnType
    transaction_ocf: TransactionOcfFileContentsReturnType
    # We need to not just look at vesting schedule but also the acceleration to determine uniqueness
    # This is a super rudimentary table that has resulting_ocf_id, vesting_schedule_id, single_trigger, double_trigger
    # in each "row"
    vesting_schedule_lookup_tbl: list[tuple[str, str, Optional[str], Optional[str], Optional[dict]]]
