import io
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from CE2OCF import CAP_EXPRESS_ENGINE_VERSION, PARSER_OCF_VERSION
from CE2OCF.datamap import (
    parse_ocf_issuer_from_ce_jsons,
    parse_ocf_stakeholders_from_ce_json,
    parse_ocf_stock_class_from_ce_jsons,
    parse_ocf_stock_issuances_from_ce_json,
    parse_ocf_stock_legend_from_ce_jsons,
    parse_ocf_vesting_events_from_ce_json,
    parse_ocf_vesting_schedules_from_ce_json,
    parse_stock_plan_from_ce_jsons,
)
from CE2OCF.types.dictionaries import (
    CE2OCFPipelineReturnType,
    ContractExpressVarObj,
    OcfFileContentsDict,
)
from CE2OCF.utils.hash_utils import (
    calculate_bytes_hash,
    dump_ocf_json_to_bytes,
)


def translate_ce_inc_questionnaire_datasheet_items_to_ocf(
    datasheet_items: list[ContractExpressVarObj],
    formation_date: Optional[datetime] = None,
    currency: str = "USD",
    issuer_ocf_post_processors: Optional[dict[str, Callable]] = None,
    issuer_ocf_custom_datamap: Optional[Path] = None,
    issuer_value_overrides: Optional[dict[str, str]] = None,
    common_stock_class_custom_datamap: Optional[Path] = None,
    common_stock_class_custom_post_processors: Optional[dict[str, Callable]] = None,
    common_stock_class_custom_value_overrides: Optional[dict[str, str]] = None,
    common_stock_legend_custom_post_processors: Optional[dict[str, Callable]] = None,
    common_stock_legend_custom_datamap: Optional[Path] = None,
    common_stock_legend_custom_value_overrides: Optional[dict[str, str]] = None,
    pref_stock_legend_custom_post_processors: Optional[dict[str, Callable]] = None,
    pref_stock_legend_custom_datamap: Optional[Path] = None,
    pref_stock_legend_custom_value_overrides: Optional[dict[str, str]] = None,
    pref_stock_class_custom_datamap: Optional[Path] = None,
    pref_stock_class_custom_post_processors: Optional[dict[str, Callable]] = None,
    pref_stock_class_custom_value_overrides: Optional[dict[str, str]] = None,
    stock_plan_custom_datamap: Optional[Path] = None,
    stock_plan_custom_post_processors: Optional[dict[str, Callable]] = None,
    stock_plan_custom_value_overrides: Optional[dict[str, str]] = None,
    stakeholder_custom_datamap: Optional[Path] = None,
    stakeholder_custom_post_processors: Optional[dict[str, Callable]] = None,
    stakeholder_custom_value_overrides: Optional[dict[str, str]] = None,
    common_stock_issuance_custom_datamap: Optional[Path] = None,
    common_stock_issuance_custom_post_processors: Optional[dict[str, Callable]] = None,
    common_stock_issuance_custom_value_overrides: Optional[dict[str, str]] = None,
    pref_stock_issuance_custom_datamap: Optional[Path] = None,
    pref_stock_issuance_custom_post_processors: Optional[dict[str, Callable]] = None,
    pref_stock_issuance_custom_value_overrides: Optional[dict[str, str]] = None,
    vesting_event_custom_datamap: Optional[Path] = None,
    vesting_event_custom_post_processors: Optional[dict[str, Callable]] = None,
    vesting_event_custom_value_overrides: Optional[dict[str, str]] = None,
    vesting_schedule_custom_datamap: Optional[Path] = None,
    vesting_schedule_custom_post_processors: Optional[dict[str, Callable]] = None,
    vesting_schedule_custom_value_overrides: Optional[dict[str, str]] = None,
    global_value_overrides: Optional[dict[str, str]] = None,
) -> CE2OCFPipelineReturnType:
    if common_stock_class_custom_value_overrides is None:
        common_stock_class_custom_value_overrides = {}

    if issuer_value_overrides is None:
        issuer_value_overrides = {}

    if common_stock_legend_custom_value_overrides is None:
        common_stock_legend_custom_value_overrides = {}

    if pref_stock_legend_custom_value_overrides is None:
        pref_stock_legend_custom_value_overrides = {}

    if common_stock_class_custom_value_overrides is None:
        common_stock_class_custom_value_overrides = {}

    if pref_stock_class_custom_value_overrides is None:
        pref_stock_class_custom_value_overrides = {}

    if stock_plan_custom_value_overrides is None:
        stock_plan_custom_value_overrides = {}

    if stakeholder_custom_value_overrides is None:
        stakeholder_custom_value_overrides = {}

    if common_stock_issuance_custom_value_overrides is None:
        common_stock_issuance_custom_value_overrides = {}

    if pref_stock_issuance_custom_value_overrides is None:
        pref_stock_issuance_custom_value_overrides = {}

    if vesting_schedule_custom_value_overrides is None:
        vesting_schedule_custom_value_overrides = {}

    if vesting_event_custom_value_overrides is None:
        vesting_event_custom_value_overrides = {}

    if global_value_overrides is None:
        global_value_overrides = {}

    # Pass these down into every template so FORMATION_DATE and CURRENCY_TYPE can be set globally
    GLOBAL_OVERRIDES = {
        "FORMATION_DATE": (formation_date if formation_date is not None else datetime.now(tz=timezone.utc))
        .date()
        .isoformat(),
        "CURRENCY_TYPE": currency,
        "SEC_EXEMPTION": "4(a)2",
        **global_value_overrides,
    }

    issuer_ocf = parse_ocf_issuer_from_ce_jsons(
        datasheet_items,
        custom_datamap_path=issuer_ocf_custom_datamap,
        post_processors=issuer_ocf_post_processors,
        value_overrides={**GLOBAL_OVERRIDES, **issuer_value_overrides},
    )

    common_stock_legend_ocf = parse_ocf_stock_legend_from_ce_jsons(
        datasheet_items,
        post_processors=common_stock_legend_custom_post_processors,
        custom_datamap_path=common_stock_legend_custom_datamap,
        value_overrides={**GLOBAL_OVERRIDES, **common_stock_legend_custom_value_overrides},
    )
    pref_stock_legend_ocf = parse_ocf_stock_legend_from_ce_jsons(
        datasheet_items,
        common_or_preferred="PREFERRED",
        post_processors=pref_stock_legend_custom_post_processors,
        custom_datamap_path=pref_stock_legend_custom_datamap,
        value_overrides={**GLOBAL_OVERRIDES, **pref_stock_legend_custom_value_overrides},
    )
    stock_legends_ocf = {
        "file_type": "OCF_STOCK_LEGEND_TEMPLATES_FILE",
        "items": [pref_stock_legend_ocf, common_stock_legend_ocf],
    }

    common_stock_class_ocf = parse_ocf_stock_class_from_ce_jsons(
        datasheet_items,
        custom_datamap_path=common_stock_class_custom_datamap,
        post_processors=common_stock_class_custom_post_processors,
        value_overrides={**GLOBAL_OVERRIDES, **common_stock_class_custom_value_overrides},
    )
    pref_stock_class_ocf = parse_ocf_stock_class_from_ce_jsons(
        datasheet_items,
        common_or_preferred="PREFERRED",
        custom_datamap_path=pref_stock_class_custom_datamap,
        post_processors=pref_stock_class_custom_post_processors,
        value_overrides={**GLOBAL_OVERRIDES, **pref_stock_class_custom_value_overrides},
    )
    stock_classes_ocf = {
        "file_type": "OCF_STOCK_CLASSES_FILE",
        "items": [pref_stock_class_ocf, common_stock_class_ocf],
    }

    stock_plans_ocf = {
        "file_type": "OCF_STOCK_PLANS_FILE",
        "items": [
            parse_stock_plan_from_ce_jsons(
                datasheet_items,
                custom_datamap_path=stock_plan_custom_datamap,
                post_processors=stock_plan_custom_post_processors,
                value_overrides={
                    **GLOBAL_OVERRIDES,
                    **stock_plan_custom_value_overrides,
                },
            )
        ],
    }

    # logger.debug("\n----- Stakeholder Information -----------------------")

    # Loop over the number of stockholders (this is safer than checking for repetitions as, oddly, I see 4 repetitions
    # (with blank values) where I have specified NumberStockholders = 2. Must be something hard-coded somewhere. You
    # can go above 4, though, which is good, so the safe bet is just to check NumberStockholders and drive data
    # extraction logic based on that value

    stakeholders_ocf = {
        "file_type": "OCF_STAKEHOLDERS_FILE",
        "items": parse_ocf_stakeholders_from_ce_json(
            datasheet_items,
            custom_datamap_path=stakeholder_custom_datamap,
            post_processors=stakeholder_custom_post_processors,
            value_overrides={**GLOBAL_OVERRIDES, **stakeholder_custom_value_overrides},
        ),
    }

    issuance_event_ocf = parse_ocf_stock_issuances_from_ce_json(
        datasheet_items,
        common_datamap_path=common_stock_issuance_custom_datamap,
        common_post_processors=common_stock_issuance_custom_post_processors,
        common_value_overrides={**GLOBAL_OVERRIDES, **common_stock_issuance_custom_value_overrides},
        preferred_datamap_path=pref_stock_issuance_custom_datamap,
        preferred_post_processors=pref_stock_issuance_custom_post_processors,
        preferred_value_overrides={**GLOBAL_OVERRIDES, **pref_stock_issuance_custom_value_overrides},
    )
    vesting_event_ocf = parse_ocf_vesting_events_from_ce_json(
        datasheet_items,
        post_processors=vesting_event_custom_post_processors,
        custom_datamap_path=vesting_event_custom_datamap,
        value_overrides={**GLOBAL_OVERRIDES, **vesting_event_custom_value_overrides},
    )
    transactions_ocf = {
        "file_type": "OCF_TRANSACTIONS_FILE",
        "items": [*issuance_event_ocf, *vesting_event_ocf],
    }

    # Need to register {'vesting_schedule': generate_ocf_vesting_schedule_from_vesting_drivers},
    vesting_schedules_ocf = {
        "file_type": "OCF_VESTING_TERMS_FILE",
        "items": parse_ocf_vesting_schedules_from_ce_json(
            datasheet_items,
            post_processors=vesting_schedule_custom_post_processors,
            custom_datamap_path=vesting_schedule_custom_datamap,
            value_overrides={**GLOBAL_OVERRIDES, **vesting_schedule_custom_value_overrides},
        ),
    }

    # We don't collect this in incorporation questionnaires for obvious reasons. Most likely you won't need this.
    valuations_ocf = {
        "file_type": "OCF_VALUATIONS_FILE",
        "items": [],
    }

    # logger.debug("Returning ocf file contents...")

    return {
        "issuer_ocf": issuer_ocf,
        "stock_classes_ocf": stock_classes_ocf,
        "stakeholders_ocf": stakeholders_ocf,
        "transactions_ocf": transactions_ocf,
        "stock_plans_ocf": stock_plans_ocf,
        "stock_legends_ocf": stock_legends_ocf,
        "valuations_ocf": valuations_ocf,
        "vesting_schedules_ocf": vesting_schedules_ocf,
    }


def package_translated_ce_as_valid_ocf_files_contents(
    ocf_obj: CE2OCFPipelineReturnType, additional_comments: Optional[list[str]] = None
) -> OcfFileContentsDict:
    if additional_comments is None:
        additional_comments = []

    stakeholders_file_path = "stakeholders.ocf.json"
    stakeholders_file_json_contents = ocf_obj["stakeholders_ocf"]
    stakeholders_file_bytes = dump_ocf_json_to_bytes(stakeholders_file_json_contents)
    stakeholders_file_md5 = calculate_bytes_hash(stakeholders_file_bytes)

    stock_classes_file_path = "stock_classes.ocf.json"
    stock_classes_file_json_contents = ocf_obj["stock_classes_ocf"]
    stock_classes_file_bytes = dump_ocf_json_to_bytes(stock_classes_file_json_contents)
    stock_classes_file_md5 = calculate_bytes_hash(stock_classes_file_bytes)

    stock_legends_file_path = "stock_legends.ocf.json"
    stock_legends_file_json_contents = ocf_obj["stock_legends_ocf"]
    stock_legends_file_bytes = dump_ocf_json_to_bytes(stock_legends_file_json_contents)
    stock_legends_file_md5 = calculate_bytes_hash(stock_legends_file_bytes)

    stock_plans_file_path = "stock_plans.ocf.json"
    stock_plans_file_json_contents = ocf_obj["stock_plans_ocf"]
    stock_plans_file_bytes = dump_ocf_json_to_bytes(stock_plans_file_json_contents)
    stock_plans_file_md5 = calculate_bytes_hash(stock_plans_file_bytes)

    transactions_file_path = "transactions.ocf.json"
    transactions_file_json_contents = ocf_obj["transactions_ocf"]
    transactions_file_bytes = dump_ocf_json_to_bytes(transactions_file_json_contents)
    transactions_file_md5 = calculate_bytes_hash(transactions_file_bytes)

    vesting_schedules_file_path = "vesting_schedules.ocf.json"
    vesting_schedules_file_json_contents = ocf_obj["vesting_schedules_ocf"]
    vesting_schedules_file_bytes = dump_ocf_json_to_bytes(vesting_schedules_file_json_contents)
    vesting_schedules_file_md5 = calculate_bytes_hash(vesting_schedules_file_bytes)

    valuations_file_path = "valuations.ocf.json"
    valuations_file_json_contents = ocf_obj["valuations_ocf"]
    valuations_file_bytes = dump_ocf_json_to_bytes(valuations_file_json_contents)
    valuations_file_md5 = calculate_bytes_hash(valuations_file_bytes)

    manifest_file_path = "manifest.ocf.json"
    manifest_file_json_contents = {
        "file_type": "OCF_MANIFEST_FILE",
        "ocf_version": PARSER_OCF_VERSION,
        "issuer": ocf_obj["issuer_ocf"],
        "as_of": datetime.now(tz=timezone.utc).date().isoformat(),
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "comments": [
            f"Auto-generated by Gunderson Dettmer Contract Express Parser v{CAP_EXPRESS_ENGINE_VERSION}",
            *additional_comments,
        ],
        "stock_plans_files": [{"filepath": stock_plans_file_path, "md5": stock_plans_file_md5}],
        "stock_legend_templates_files": [{"filepath": stock_legends_file_path, "md5": stock_legends_file_md5}],
        "stock_classes_files": [{"filepath": stock_classes_file_path, "md5": stock_classes_file_md5}],
        "vesting_terms_files": [{"filepath": vesting_schedules_file_path, "md5": vesting_schedules_file_md5}],
        "valuations_files": [],
        "transactions_files": [{"filepath": transactions_file_path, "md5": transactions_file_md5}],
        "stakeholders_files": [{"filepath": stakeholders_file_path, "md5": stakeholders_file_md5}],
    }
    manifest_file_bytes = dump_ocf_json_to_bytes(manifest_file_json_contents)
    manifest_file_md5 = calculate_bytes_hash(manifest_file_bytes)

    return {
        "OCF_STAKEHOLDERS_FILE": {
            "file_name": stakeholders_file_path,
            "contents": stakeholders_file_json_contents,
            "bytes": stakeholders_file_bytes,
            "md5": stakeholders_file_md5,
        },
        "OCF_STOCK_CLASSES_FILE": {
            "file_name": stock_classes_file_path,
            "contents": stock_classes_file_json_contents,
            "bytes": dump_ocf_json_to_bytes(stock_classes_file_json_contents),
            "md5": stock_classes_file_md5,
        },
        "OCF_STOCK_LEGEND_TEMPLATES_FILE": {
            "file_name": stock_legends_file_path,
            "contents": stock_legends_file_json_contents,
            "bytes": stock_legends_file_bytes,
            "md5": stock_legends_file_md5,
        },
        "OCF_STOCK_PLANS_FILE": {
            "file_name": stock_plans_file_path,
            "contents": stock_plans_file_json_contents,
            "bytes": stock_plans_file_bytes,
            "md5": stock_plans_file_md5,
        },
        "OCF_TRANSACTIONS_FILE": {
            "file_name": transactions_file_path,
            "contents": transactions_file_json_contents,
            "bytes": transactions_file_bytes,
            "md5": transactions_file_md5,
        },
        "OCF_VALUATIONS_FILE": {
            "file_name": valuations_file_path,
            "contents": valuations_file_json_contents,
            "bytes": valuations_file_bytes,
            "md5": valuations_file_md5,
        },
        "OCF_VESTING_TERMS_FILE": {
            "file_name": vesting_schedules_file_path,
            "contents": vesting_schedules_file_json_contents,
            "bytes": vesting_schedules_file_bytes,
            "md5": vesting_schedules_file_md5,
        },
        "OCF_MANIFEST_FILE": {
            "file_name": manifest_file_path,
            "contents": manifest_file_json_contents,
            "bytes": manifest_file_bytes,
            "md5": manifest_file_md5,
        },
    }


def package_ocf_files_contents_into_zip_archive(
    ocf_file_contents: OcfFileContentsDict,
) -> bytes:
    """

    Args:
        ocf_file_contents: Dict mapping ocf file type enums to OcfFileParts Dict:

            class OcfFileParts(TypedDict):
                file_name: str
                contents: dict
                bytes: bytes
                md5: str

    Returns:

    """

    zip_bytes = io.BytesIO()
    zip_file = zipfile.ZipFile(zip_bytes, mode="w", compression=zipfile.ZIP_DEFLATED)

    for _, contents in ocf_file_contents.items():
        if not isinstance(contents, dict):
            msg = f"Expected OcfFileParts, got {type(contents)}"
            raise ValueError(msg)
        file_name = contents["file_name"]
        bytes_content = contents["bytes"]
        zip_file.writestr(file_name, bytes_content)

    zip_file.close()
    zip_bytes.seek(0)
    return zip_bytes.getvalue()
