import datetime
from pathlib import Path
from typing import Callable, Literal, Optional

from CE2OCF import __version__ as version
from CE2OCF.datamap.crawler import traverse_datamap
from CE2OCF.datamap.loaders import (
    DEFAULT_CE_TO_OCF_DATAMAP_PREFERRED_STOCK_LEGEND_ONLY_PATH,
    DEFAULT_CE_TO_OCF_PREFERRED_STOCK_CLASS_ONLY_PATH,
    load_ce_to_ocf_issuer_datamap,
    load_ce_to_ocf_stakeholder_datamap,
    load_ce_to_ocf_stock_class_datamap,
    load_ce_to_ocf_stock_legend_datamap,
    load_ce_to_ocf_stock_plan_datamap,
    load_ce_to_ocf_vested_issuances_datamap,
    load_ce_to_ocf_vesting_issuances_datamap,
    load_vesting_events_driving_enums_datamap,
    load_vesting_schedule_driving_enums_datamap,
)
from CE2OCF.ocf.datamaps import (
    FullyVestedStockIssuanceDataMap,
    IssuerDataMap,
    RepeatableStockholderDataMap,
    StockClassDataMap,
    StockLegendDataMap,
    StockPlanDataMap,
    VestingScheduleInputsDataMap,
    VestingStockIssuanceDataMap,
)
from CE2OCF.ocf.generators.ocf_id_generators import (
    generate_vesting_start_id,
)
from CE2OCF.ocf.generators.ocf_vesting_events import (
    generate_vesting_start_event,
)
from CE2OCF.types.dictionaries import ContractExpressVarObj
from CE2OCF.types.enums import VestingTypesEnum
from CE2OCF.types.exceptions import VariableNotFound


def parse_ocf_issuer_from_ce_jsons(
    ce_jsons: list[ContractExpressVarObj],
    post_processors: Optional[dict[str, Callable]] = None,
    fail_on_missing_variable: bool = False,
    custom_datamap_path: Optional[Path] = None,
    value_overrides: Optional[dict[str, str]] = None,
    clear_old_post_processors: bool = True,
) -> dict:
    """
    By default, loads our default ce to ocf issuer datamap (though you can provide a path your own JSON datamap) and
    uses it to parse a valid OCF issuer object from a list of ce_json objects.

    Args:
        ce_jsons: List of CE Jsons matching schema defined in ContractExpressVarObj
        post_processors (optional): A dictionary mapping stock class object data field names to functions which
                                    you want to run on the parsed data - e.g. if your questionnaire has data that
                                    needs to be formatted or parsed.
        fail_on_missing_variable: Set to True if you want to get an error if any data fields are missing.
        custom_datamap_path: If you want to use a custom datamap, provide path to json file
        value_overrides: If provided, pass to underlying datamap crawler to override specified lookup values in dict
        clear_old_post_processors: If True, unregister all handlers for IssuerDataMap before registering any provided
                                   as post_processors

    Returns: Valid ocf issuer json

    """

    if clear_old_post_processors:
        IssuerDataMap.clear_handlers()

    if post_processors is not None:
        IssuerDataMap.register_handlers(post_processors)

    if value_overrides is None:
        value_overrides = {}

    issuer_datamap = load_ce_to_ocf_issuer_datamap(custom_datamap_path)
    parsed_issuer_ocf = traverse_datamap(
        issuer_datamap,
        None,
        ce_jsons,
        value_overrides={"PARSER_VERSION": version, **value_overrides},
        fail_on_missing_variable=fail_on_missing_variable,
    )

    # TODO - improve type checking to check for actual target OCF schema
    assert isinstance(parsed_issuer_ocf, dict), f"Expected parsed_issuer_ocf to be dict, got {type(parsed_issuer_ocf)}"
    return parsed_issuer_ocf


def parse_stock_plan_from_ce_jsons(
    ce_jsons: list[ContractExpressVarObj],
    post_processors: Optional[dict[str, Callable]] = None,
    fail_on_missing_variable: bool = False,
    custom_datamap_path: Optional[Path] = None,
    value_overrides: Optional[dict[str, str]] = None,
    clear_old_post_processors: bool = True,
) -> dict:
    """
     By default, loads our default ce to ocf stock plan datamap (though you can provide a path your own JSON datamap)
     and uses it to parse a valid OCF stock plan object from a list of ce_json objects.

    :param ce_jsons:
    :param post_processors:
    :param fail_on_missing_variable:
    :param custom_datamap_path:
    :param value_overrides:
    :param clear_old_post_processors:
    :return: Valid OCF stock plan
    """

    if clear_old_post_processors:
        StockPlanDataMap.clear_handlers()

    if post_processors is not None:
        StockPlanDataMap.register_handlers(post_processors)

    if value_overrides is None:
        value_overrides = {}

    stock_plan_datamap = load_ce_to_ocf_stock_plan_datamap(custom_datamap_path)

    stock_plan_ocf = traverse_datamap(
        stock_plan_datamap,
        None,
        ce_jsons,
        value_overrides={"PARSER_VERSION": version, **value_overrides},
        fail_on_missing_variable=fail_on_missing_variable,
    )

    # TODO - improve type checking to check for actual target OCF schema
    assert isinstance(stock_plan_ocf, dict), f"Expected parsed_issuer_ocf to be dict, got {type(stock_plan_ocf)}"
    return stock_plan_ocf


def parse_ocf_stock_class_from_ce_jsons(
    ce_jsons: list[ContractExpressVarObj],
    common_or_preferred: Literal["COMMON", "PREFERRED"] = "COMMON",
    post_processors: Optional[dict[str, Callable]] = None,
    fail_on_missing_variable: bool = False,
    custom_datamap_path: Optional[Path] = None,
    value_overrides: Optional[dict[str, str]] = None,
    clear_old_post_processors: bool = True,
) -> dict:
    """
    By default, loads our default ce to ocf common stock class datamap (though you can provide a path your own JSON
    datamap) and uses it to parse a valid OCF issuer object from a list of ce_json objects. You can change the
    common_or_preferred argument to "PREFERRED" to get a preferred stock class.

    Args:
        ce_jsons: List of CE Jsons matching schema defined in ContractExpressVarObj
        common_or_preferred: Set to "COMMON" (default) to parse common stock and "PREFERRED" to parse preferred stock
        post_processors (optional): A dictionary mapping stock class object data field names to functions which
                                    you want to run on the parsed data - e.g. if your questionnaire has data that
                                    needs to be formatted or parsed.
        fail_on_missing_variable: Set to True if you want to get an error if any data fields are missing.
        custom_datamap_path: If you want to use a custom datamap, provide path to json file
        value_overrides: If provided, inject this into datamapper and look up values here first. If found, don't
                         check CE

    Returns: Valid ocf stock class json
    """

    if clear_old_post_processors:
        StockClassDataMap.clear_handlers()

    if post_processors is not None:
        StockClassDataMap.register_handlers(post_processors)

    if value_overrides is None:
        value_overrides = {}

    if common_or_preferred == "COMMON":
        stock_class_datamap = load_ce_to_ocf_stock_class_datamap(custom_datamap_path)
    elif common_or_preferred == "PREFERRED":
        stock_class_datamap = load_ce_to_ocf_stock_class_datamap(
            custom_datamap_path if custom_datamap_path else DEFAULT_CE_TO_OCF_PREFERRED_STOCK_CLASS_ONLY_PATH
        )
    else:
        raise ValueError("We only support COMMON or PREFERRED datamaps")

    stock_class_ocf = traverse_datamap(
        stock_class_datamap,
        None,
        ce_jsons,
        value_overrides={"PARSER_VERSION": version, **value_overrides},
        fail_on_missing_variable=fail_on_missing_variable,
    )

    # TODO - improve type checking to check for actual target OCF schema
    assert isinstance(stock_class_ocf, dict), f"Expected stock_class_ocf to be dict, got {type(stock_class_ocf)}"
    return stock_class_ocf


def parse_ocf_stock_legend_from_ce_jsons(
    ce_jsons: list[ContractExpressVarObj],
    common_or_preferred: Literal["COMMON", "PREFERRED"] = "COMMON",
    post_processors: Optional[dict[str, Callable]] = None,
    fail_on_missing_variable: bool = False,
    custom_datamap_path: Optional[Path] = None,
    value_overrides: Optional[dict[str, str]] = None,
    clear_old_post_processors: bool = True,
) -> dict:
    """
    By default, loads our default ce to ocf common stock legend datamap (though you can provide a path your own JSON
    datamap) and uses it to parse a valid OCF stock legend object from a list of ce_json objects. You can change the
    common_or_preferred argument to "PREFERRED" to get a preferred stock legends.

    Args:
        ce_jsons: List of CE Jsons matching schema defined in ContractExpressVarObj
        common_or_preferred: Set to "COMMON" (default) to parse common legends and "PREFERRED" to parse preferred legend
        post_processors (optional): A dictionary mapping stock legend data field names to functions which
                                    you want to run on the parsed data
        fail_on_missing_variable: Set to True if you want to get an error if any data fields are missing.
        custom_datamap_path: If you want to use a custom datamap, provide path to json file
        value_overrides: If provided, inject this variable value lookup into parser which will override anything in CE

    Returns: Valid ocf stock legend json
    """

    if clear_old_post_processors:
        StockLegendDataMap.clear_handlers()

    if post_processors is not None:
        StockLegendDataMap.register_handlers(post_processors)

    if value_overrides is None:
        value_overrides = {}

    if common_or_preferred == "COMMON":
        stock_legend_datamap = load_ce_to_ocf_stock_legend_datamap(custom_datamap_path)
    elif common_or_preferred == "PREFERRED":
        stock_legend_datamap = load_ce_to_ocf_stock_legend_datamap(
            custom_datamap_path if custom_datamap_path else DEFAULT_CE_TO_OCF_DATAMAP_PREFERRED_STOCK_LEGEND_ONLY_PATH
        )
    else:
        raise ValueError("We only support COMMON or PREFERRED datamaps")

    ocf_stock_legend = traverse_datamap(
        stock_legend_datamap,
        None,
        ce_jsons,
        value_overrides={"PARSER_VERSION": version, **value_overrides},
        fail_on_missing_variable=fail_on_missing_variable,
    )

    # TODO - improve type checking to check for actual target OCF schema
    assert isinstance(ocf_stock_legend, dict), f"Expected ocf_stock_legend to be dict, got {type(ocf_stock_legend)}"
    return ocf_stock_legend


def parse_ocf_stakeholders_from_ce_json(
    ce_jsons: list[ContractExpressVarObj],
    post_processors: Optional[dict[str, Callable]] = None,
    clear_old_post_processors: bool = True,
    fail_on_missing_variable: bool = False,
    custom_datamap_path: Optional[Path] = None,
    value_overrides: Optional[dict[str, str]] = None,
) -> list[dict]:
    """
    By default, loads our default ce to ocf stakeholder datamap (though you can provide a path your own JSON datamap)
    and uses it to parse a list of valid OCF stakeholder objects from a list of ce_json objects.

    Args:
        ce_jsons: List of CE Jsons matching schema defined in ContractExpressVarObj
        clear_old_post_processors: If True, unregister all existing handlers to RepeatableStockholderDataMap before
                                    registering new post processors. Good idea generally to ensure no handlers
                                    remain registered from elsewhere in your code base and is True by default.
        post_processors (optional): A dictionary mapping stakeholder object data field names to functions which
                                    you want to run on the parsed data - e.g. if your questionnaire has data that
                                    needs to be formatted or parsed.
        fail_on_missing_variable: Set to True if you want to get an error if any data fields are missing.
        custom_datamap_path: If you want to use a custom datamap, provide path to json file
        value_overrides: If provided, inject this variable value lookup into parser which will override anything in CE

    Returns: List of valid ocf stakeholder objects

    """
    if clear_old_post_processors:
        RepeatableStockholderDataMap.clear_handlers()

    if post_processors is not None:
        RepeatableStockholderDataMap.register_handlers(post_processors)

    if value_overrides is None:
        value_overrides = {}

    stakeholder_datamap = load_ce_to_ocf_stakeholder_datamap(custom_datamap_path)

    stockholders_ocf = traverse_datamap(
        stakeholder_datamap,
        None,
        ce_jsons,
        value_overrides={"PARSER_VERSION": version, **value_overrides},
        fail_on_missing_variable=fail_on_missing_variable,
    )

    # TODO - improve type checking to check for actual target OCF schema
    assert isinstance(stockholders_ocf, list), (
        f"Expected stockholders_ocf to be list of dicts, " f"got {type(stockholders_ocf)}"
    )
    return stockholders_ocf


def parse_ocf_stock_issuances_from_ce_json(
    ce_jsons: list[ContractExpressVarObj],
    fail_on_missing_variable: bool = False,
    common_post_processors: Optional[dict[str, Callable]] = None,
    preferred_post_processors: Optional[dict[str, Callable]] = None,
    common_datamap_path: Optional[Path] = None,
    preferred_datamap_path: Optional[Path] = None,
    common_value_overrides: Optional[dict[str, str]] = None,
    preferred_value_overrides: Optional[dict[str, str]] = None,
    clear_old_post_processors: bool = True,
) -> list[dict]:
    """

    Args:
        ce_jsons:
        fail_on_missing_variable:
        common_post_processors:
        preferred_post_processors:
        common_datamap_path:
        common_value_overrides:
        preferred_datamap_path:
        preferred_value_overrides:
        clear_old_post_processors:
    Returns:

    """

    def drop_fully_vested_vest_term_id(val, ce_jsons) -> str:
        """
        Raise a VariableNotFound exception if fully vested which will cause
        the key to be dropped entirely.

        Args:
            val: Variable name
            ce_jsons: List of ce jsons

        Returns: Original value or, if fully vested, throw an error

        """
        if val.split("/")[0] == "Fully Vested":
            raise VariableNotFound
        else:
            return val

    if common_value_overrides is None:
        common_value_overrides = {}

    if preferred_value_overrides is None:
        preferred_value_overrides = {}

    if clear_old_post_processors:
        VestingStockIssuanceDataMap.clear_handlers()
        FullyVestedStockIssuanceDataMap.clear_handlers()

    if common_post_processors is not None:
        VestingStockIssuanceDataMap.register_handlers(common_post_processors)
    else:
        VestingStockIssuanceDataMap.register_handlers(
            {
                "vesting_terms_id": drop_fully_vested_vest_term_id,
            }
        )

    if preferred_post_processors is not None:
        FullyVestedStockIssuanceDataMap.register_handlers(preferred_post_processors)

    common_datamap = load_ce_to_ocf_vesting_issuances_datamap(common_datamap_path)
    common_issuances = traverse_datamap(
        common_datamap,
        None,
        ce_jsons,
        value_overrides={"PARSER_VERSION": version, **common_value_overrides},
        fail_on_missing_variable=fail_on_missing_variable,
    )
    # TODO - improve type checking to check for actual target OCF schema
    assert isinstance(common_issuances, list), (
        f"Expected common_issuances to be list of dicts, " f"got {type(common_issuances)}"
    )

    preferred_datamap = load_ce_to_ocf_vested_issuances_datamap(preferred_datamap_path)
    pref_issuances = traverse_datamap(
        preferred_datamap,
        None,
        ce_jsons,
        value_overrides={"PARSER_VERSION": version, **preferred_value_overrides},
        fail_on_missing_variable=fail_on_missing_variable,
    )
    assert isinstance(pref_issuances, list), (
        f"Expected pref_issuances to be list of dicts, " f"got {type(pref_issuances)}"
    )

    return [*common_issuances, *pref_issuances]


def parse_ocf_vesting_schedules_from_ce_json(
    ce_jsons: list[ContractExpressVarObj],
    post_processors: Optional[dict[str, Callable]] = None,
    fail_on_missing_variable: bool = False,
    custom_datamap_path: Optional[Path] = None,
    clear_old_post_processors: bool = True,
    value_overrides: Optional[dict[str, str]] = None,
) -> list[dict]:
    """

    Loads a Ce2OCF datamap and parses CE JSONs using the datamap.

    Args:
        ce_jsons: List of ContractExpressVarObj retrieved from CE API
        post_processors: Post processors to register with top-level FieldPostProcessorDataMap
        fail_on_missing_variable: If True, throw an error if we can't find a given CE variable name
        custom_datamap_path: If you provide a Path, load the datamap from path instead of default
        clear_old_post_processors: If True, clear pre-existing post processors on top-level FieldPostProcessorDataMap
        value_overrides:
    Returns: OCF Jsons for Vesting Schedule Objects, Deduped

    """

    # We're going to filter out schedules with duplicate IDs as our datamap approach has no way to guarantee produced
    # OCF has unique IDs.

    if clear_old_post_processors:
        VestingScheduleInputsDataMap.clear_handlers()

    if post_processors is not None:
        VestingScheduleInputsDataMap.register_handlers(post_processors)

    if value_overrides is None:
        value_overrides = {}

    ce_to_vesting_enums_datamap = load_vesting_schedule_driving_enums_datamap(custom_datamap_path)

    vesting_schedle_ocfs = traverse_datamap(
        ce_to_vesting_enums_datamap,
        None,
        ce_jsons,
        value_overrides={"PARSER_VERSION": version, **value_overrides},
        fail_on_missing_variable=fail_on_missing_variable,
    )
    # TODO - improve OCF dict typing
    assert isinstance(vesting_schedle_ocfs, list)
    # print(f"Raw vesting schedules: {json.dumps(vesting_schedle_ocfs, indent=2)}")

    processed = list(
        {
            sched["vesting_schedule"]["id"]: sched["vesting_schedule"]
            for sched in vesting_schedle_ocfs
            if isinstance(sched["vesting_schedule"], dict) and "id" in sched["vesting_schedule"]
        }.values()
    )
    # print(f"Processed {len(processed)} {[sched['id'] for sched in processed]}: {processed}")

    # Use a dict to de-dupe by id.
    return processed


def parse_ocf_vesting_events_from_ce_json(
    ce_jsons: list[ContractExpressVarObj],
    post_processors: Optional[dict[str, Callable]] = None,
    fail_on_missing_variable: bool = False,
    custom_datamap_path: Optional[Path] = None,
    clear_old_post_processors: bool = True,
    value_overrides: Optional[dict[str, str]] = None,
) -> list[dict]:

    """

    Using vesting enums for each stockholder, drive creation of any necessary vesting

    Args:
        ce_jsons:
        post_processors:
        fail_on_missing_variable:
        custom_datamap_path:
        clear_old_post_processors:
        value_overrides:
    Returns:

    """
    if clear_old_post_processors:
        VestingScheduleInputsDataMap.clear_handlers()

    if post_processors is not None:
        VestingScheduleInputsDataMap.register_handlers(post_processors)

    if value_overrides is None:
        value_overrides = {}

    ce_vesting_enums_datamap = load_vesting_events_driving_enums_datamap(custom_datamap_path)

    # This is going to give us, for each stockholder_id - here just indicated by their index count but we typically
    # build the ids by STAKEHOLDER.{{index}}, so this'll be easy.  - which we can then use to generate required start
    # events
    sh_vesting_selections = traverse_datamap(
        ce_vesting_enums_datamap,
        None,
        ce_jsons,
        value_overrides={"PARSER_VERSION": version, **value_overrides},
        fail_on_missing_variable=fail_on_missing_variable,
    )

    # TODO - improve ocf object typing
    assert isinstance(sh_vesting_selections, list)

    generated_events = []
    for vesting_inputs in sh_vesting_selections:

        assert isinstance(vesting_inputs, dict)  # vesting_inputs must be dict, Hard to type dynamically extracted data

        vesting_inputs = vesting_inputs["vesting_schedule"]
        if vesting_inputs["vesting_schedule"] == VestingTypesEnum.FULLY_VESTED:
            print(f"Skip fully vested schedule for stakeholder {vesting_inputs['stockholder_id']}")
            continue

        # print(f"Generate vesting start events for values: {vesting_inputs}")
        generated_events.append(
            generate_vesting_start_event(
                vesting_commencement_date=datetime.date.fromisoformat(vesting_inputs["vesting_commencement_date"]),
                issuance_id=f"COMMON.ISSUANCE.{vesting_inputs['stockholder_id']}",
                vesting_start_condition_id=generate_vesting_start_id(
                    vesting_inputs["vesting_schedule"]
                    + "/"
                    + vesting_inputs["single_trigger"]
                    + "/"
                    + vesting_inputs["double_trigger"]
                ),
            )
        )
    # print(f"Generated events {generated_events}")

    return generated_events
