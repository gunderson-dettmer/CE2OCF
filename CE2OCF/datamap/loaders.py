import json
from pathlib import Path
from typing import Optional

from CE2OCF.ocf.datamaps import (
    IssuerDataMap,
    RepeatableFullyVestedStockIssuanceDataMap,
    RepeatableStockholderDataMap,
    RepeatableVestingEventDriversDataMap,
    RepeatableVestingScheduleDriversDataMap,
    RepeatableVestingStockIssuanceDataMap,
    StockClassDataMap,
    StockLegendDataMap,
    StockPlanDataMap,
)
from CE2OCF.types.dictionaries import (
    CicEventDefinition,
    TerminationDetails,
)

MODULE_PATH = Path(__file__).parent
DEFAULTS_PATH = MODULE_PATH / "defaults"

# Default Configuration File Locations
DEFAULT_CIC_DEFS_PATH = DEFAULTS_PATH / "cic_event_definition.json"
DEFAULT_SINGLE_TRIG_DEFS_PATH = DEFAULTS_PATH / "single_trigger_acceleration.json"
DEFAULT_DOUBLE_TRIG_DEFS_PATH = DEFAULTS_PATH / "double_trigger_acceleration.json"

DEFAULT_CE_TO_OCF_COMMON_STOCK_CLASS_ONLY_PATH = DEFAULTS_PATH / "ce_to_ocf_common_stock_class_only.json"
DEFAULT_CE_TO_OCF_COMMON_STOCK_ISSUANCE_ONLY_PATH = DEFAULTS_PATH / "ce_to_ocf_common_stock_issuance_only.json"
DEFAULT_CE_TO_OCF_DATAMAP_COMMON_STOCK_LEGEND_ONLY_PATH = (
    DEFAULTS_PATH / "ce_to_ocf_datamap_common_stock_legend_only.json"
)
DEFAULT_CE_TO_OCF_DATAMAP_PREFERRED_STOCK_LEGEND_ONLY_PATH = (
    DEFAULTS_PATH / "ce_to_ocf_datamap_preferred_stock_legend_only.json"
)
DEFAULT_CE_TO_OCF_ISSUER_ONLY_PATH = DEFAULTS_PATH / "ce_to_ocf_issuer_only.json"
DEFAULT_CE_TO_OCF_PREFERRED_STOCK_CLASS_ONLY_PATH = DEFAULTS_PATH / "ce_to_ocf_preferred_stock_class_only.json"
DEFAULT_CE_TO_OCF_PREFERRED_STOCK_ISSUANCE_ONLY_PATH = DEFAULTS_PATH / "ce_to_ocf_preferred_stock_issuance_only.json"
DEFAULT_CE_TO_OCF_STOCK_PLAN_ONLY_PATH = DEFAULTS_PATH / "ce_to_ocf_stock_plan_only.json"
DEFAULT_CE_TO_OCF_STOCKHOLDERS_ONLY_PATH = DEFAULTS_PATH / "ce_to_ocf_stockholders_only.json"
DEFAULT_CE_ENUMS_TO_OCF_VESTING_SCHEDULE_ONLY_PATH = DEFAULTS_PATH / "ce_to_ocf_vesting_enums_events_only.json"
DEFAULT_CE_ENUMS_TO_OCF_VESTING_EVENTS_ONLY_PATH = DEFAULTS_PATH / "ce_to_ocf_vesting_enums_events_only.json"


########################################################################################################################
# Configuration File Loaders - Primary natural language definitions and quantitative cutoffs required to generate ocf
########################################################################################################################
def load_cic_event_definition(source_json: Path = DEFAULT_CIC_DEFS_PATH) -> CicEventDefinition:
    with source_json.open("r") as config_file:
        return json.loads(config_file.read())


def load_double_trigger_definitions(
    source_json: Path = DEFAULT_DOUBLE_TRIG_DEFS_PATH,
) -> dict[str, Optional[TerminationDetails]]:
    with source_json.open("r") as config_file:
        return json.loads(config_file.read())


def load_single_trigger_definitions(
    source_json: Path = DEFAULT_SINGLE_TRIG_DEFS_PATH,
) -> dict[str, Optional[CicEventDefinition]]:
    with source_json.open("r") as config_file:
        return json.loads(config_file.read())


########################################################################################################################
# Datamap Loaders
########################################################################################################################
def load_ce_to_ocf_issuer_datamap(source_json: Optional[Path] = None) -> IssuerDataMap:
    if source_json is None:
        source_json = DEFAULT_CE_TO_OCF_ISSUER_ONLY_PATH
    return IssuerDataMap.parse_file(source_json)


def load_ce_to_ocf_stock_class_datamap(source_json: Optional[Path] = None) -> StockClassDataMap:
    """
    Loads a StockClassDataMap from a json configuration file at source_json. Defaults to the defaults in
    config/defaults. WARNING - DEFAULT IS FOR COMMON

    Args: source_json: son configuration file mapping ocf fields to ce json data fields. Defaults to
    DEFAULT_CE_TO_OCF_COMMON_STOCK_CLASS_ONLY_PATH

    Returns: StockClassDataMap

    """
    if source_json is None:
        source_json = DEFAULT_CE_TO_OCF_COMMON_STOCK_CLASS_ONLY_PATH
    return StockClassDataMap.parse_file(source_json)


def load_ce_to_ocf_stock_legend_datamap(source_json: Optional[Path] = None) -> StockLegendDataMap:
    """
    Loads a StockLegendDataMap from a json configuration file at source_json. Defaults to the defaults in
    config/defaults. WARNING - DEFAULT IS FOR GUNDERSON COMMON LEGENDS

    Args: source_json: Json configuration file mapping ocf fields to ce json data fields. Defaults to
    DEFAULT_CE_TO_OCF_DATAMAP_COMMON_STOCK_LEGEND_ONLY_PATH

    Returns: StockLegendDataMap

    """
    if source_json is None:
        source_json = DEFAULT_CE_TO_OCF_DATAMAP_COMMON_STOCK_LEGEND_ONLY_PATH

    return StockLegendDataMap.parse_file(source_json)


def load_ce_to_ocf_stock_plan_datamap(source_json: Optional[Path] = None) -> StockPlanDataMap:
    """
    Loads a StockPlanDataMap from a json configuration file at source_json. Defaults to the default datamap in
    config/defaults.

    :param source_json:Json configuration file mapping ocf fields to ce json data fields. Defaults to
    DEFAULT_CE_TO_OCF_STOCK_PLAN_ONLY_PATH

    :return: StockPlanDataMap
    """

    if source_json is None:
        source_json = DEFAULT_CE_TO_OCF_STOCK_PLAN_ONLY_PATH

    return StockPlanDataMap.parse_file(source_json)


def load_ce_to_ocf_stakeholder_datamap(source_json: Optional[Path] = None) -> RepeatableStockholderDataMap:
    """
    Loads a RepeatableStockholderDataMap from a json configuration file at source_json. Defaults to the defaults in
    config/defaults.

    Args: source_json: Json configuration file mapping ocf fields to ce json data fields. Defaults to
    DEFAULT_CE_TO_OCF_STOCKHOLDERS_ONLY_PATH

    Returns: RepeatableStockholderDataMap

    """
    if source_json is None:
        source_json = DEFAULT_CE_TO_OCF_STOCKHOLDERS_ONLY_PATH

    return RepeatableStockholderDataMap.parse_file(source_json)


def load_ce_to_ocf_vesting_issuances_datamap(
    source_json: Optional[Path] = None,
) -> RepeatableVestingStockIssuanceDataMap:
    """
    Loads a RepeatableVestingStockIssuanceDataMap from a json configuration file at source_json. Defaults to
    the defaults in config/defaults. Meant for use with issuances that can vest. Typically founder common.

    Args: source_json: Json configuration file mapping ocf fields to ce json data fields. Defaults to
    DEFAULT_CE_TO_OCF_COMMON_STOCK_ISSUANCE_ONLY_PATH

    Returns: RepeatableVestingStockIssuanceDataMap
    """
    if source_json is None:
        source_json = DEFAULT_CE_TO_OCF_COMMON_STOCK_ISSUANCE_ONLY_PATH

    return RepeatableVestingStockIssuanceDataMap.parse_file(source_json)


def load_ce_to_ocf_vested_issuances_datamap(
    source_json: Optional[Path] = None,
) -> RepeatableFullyVestedStockIssuanceDataMap:
    """
    Loads a RepeatableFullyVestedStockIssuanceDataMap from a json configuration file at source_json. Defaults to
        the defaults in config/defaults. Meant for use with issuances that don't vest. Typically, founder preferred.

    Args: source_json: Json configuration file mapping ocf fields to ce json data fields. Defaults to
    DEFAULT_CE_TO_OCF_PREFERRED_STOCK_ISSUANCE_ONLY_PATH

    Returns: RepeatableFullyVestedStockIssuanceDataMap
    """
    if source_json is None:
        source_json = DEFAULT_CE_TO_OCF_PREFERRED_STOCK_ISSUANCE_ONLY_PATH

    return RepeatableFullyVestedStockIssuanceDataMap.parse_file(source_json)


def load_vesting_schedule_driving_enums_datamap(
    source_jsons: Optional[Path] = None,
) -> RepeatableVestingScheduleDriversDataMap:
    """
    Loads a RepeatableVestingScheduleDriversDataMap from data map in source_jsons path. If none provided, use the
    default datamap in DEFAULT_CE_ENUMS_TO_OCF_VESTING_SCHEDULE_ONLY_PATH.

    Args:
        source_jsons: Json configuration file mapping ocf fields to ce json data fields. Defaults to
            DEFAULT_CE_ENUMS_TO_OCF_VESTING_SCHEDULE_ONLY_PATH

    Returns: RepeatableVestingScheduleDriversDataMap
    """
    if source_jsons is None:
        source_jsons = DEFAULT_CE_ENUMS_TO_OCF_VESTING_SCHEDULE_ONLY_PATH
    return RepeatableVestingScheduleDriversDataMap.parse_file(source_jsons)


def load_vesting_events_driving_enums_datamap(
    source_jsons: Optional[Path] = None,
) -> RepeatableVestingEventDriversDataMap:
    """
    Loads a RepeatableVestingEventDriversDataMap from data map in source_jsons path. If none provided, use the
    default datamap in DEFAULT_CE_ENUMS_TO_OCF_VESTING_SCHEDULE_ONLY_PATH.

    Args:
        source_jsons: Json configuration file mapping ocf fields to ce json data fields. Defaults to
            DEFAULT_CE_ENUMS_TO_OCF_VESTING_EVENTS_ONLY_PATH

    Returns: RepeatableVestingEventDriversDataMap

    """
    if source_jsons is None:
        source_jsons = DEFAULT_CE_ENUMS_TO_OCF_VESTING_EVENTS_ONLY_PATH
    return RepeatableVestingEventDriversDataMap.parse_file(source_jsons)
