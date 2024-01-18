# Using pathlib to get proper paths to provide easier, cross-platform dir performance

# Validator for split schema files based on s1m0's answer @StackOverflow:
# https://stackoverflow.com/questions/42159346/jsonschema-refresolver-to-resolve-multiple-refs-in-python
# Further inspiration here on how to build a RefResolver against multiple ref files:
# https://stackoverflow.com/questions/31703752/python-jsonschema-validation-using-schema-list
# Ultimately found this, which I gleaned a couple further tweaks from and got the validator working:
# https://stackoverflow.com/questions/53968770/how-to-set-up-local-file-references-in-python-jsonschema-document
# Couple modifications:
#   1) I wanted multiple directories, not just one, so I made the input path argument an array of paths
#   2) Using a Draft7Validator instead of Draft4
import json
import os
from pathlib import Path
from typing import Optional

from jsonschema import (
    Draft7Validator,
    RefResolver,
    SchemaError,
    ValidationError,
)

from CE2OCF.types.exceptions import OCFValidationError
from CE2OCF.utils.log_utils import logger

manifest_schema_id = "https://schema.opencaptablecoalition.com/v/1.1.0/files/OCFManifestFile.schema.json"
parent_dir = Path(__file__).parent
schema_dir = parent_dir / "schema"
schema_dir_resolved = schema_dir.resolve()
file_type_to_ocf_id_dict = {
    "OCF_MANIFEST_FILE": "https://schema.opencaptablecoalition.com/v/1.1.0/files/OCFManifestFile.schema.json",
    "OCF_STAKEHOLDERS_FILE": "https://schema.opencaptablecoalition.com/v/1.1.0/files/StakeholdersFile.schema.json",
    "OCF_STOCK_CLASSES_FILE": "https://schema.opencaptablecoalition.com/v/1.1.0/files/StockClassesFile.schema.json",
    "OCF_STOCK_LEGEND_TEMPLATES_FILE": "https://schema.opencaptablecoalition.com/v/1.1.0/files"
    "/StockLegendTemplatesFile.schema.json",
    "OCF_STOCK_PLANS_FILE": "https://schema.opencaptablecoalition.com/v/1.1.0/files/StockPlansFile.schema.json",
    "OCF_TRANSACTIONS_FILE": "https://schema.opencaptablecoalition.com/v/1.1.0/files/TransactionsFile.schema.json",
    "OCF_VALUATIONS_FILE": "https://schema.opencaptablecoalition.com/v/1.1.0/files/ValuationsFile.schema.json",
    "OCF_VESTING_TERMS_FILE": "https://schema.opencaptablecoalition.com/v/1.1.0/files/VestingTermsFile.schema.json",
}


def load_schemas(directory=schema_dir_resolved, extension=".schema.json", verbose: bool = False):
    """
    :return: Dict of schema ids to jsonschemas
    """

    schemastore = {}

    extension = extension.lower()
    for dirpath, _, files in os.walk(directory):
        for name in files:
            if extension and name.lower().endswith(extension):
                if verbose:
                    logger.info(f"\tFound schema at path: {dirpath + '/' + name}")
                with open(dirpath + "/" + name) as schema_fd:
                    schema = json.load(schema_fd)
                    if "$id" in schema:
                        if verbose:
                            logger.info(f"\t\tSchema Id is: {schema['$id']}")
                        schemastore[schema["$id"]] = schema

    return schemastore


def get_validator(against_ocf_id: str = manifest_schema_id) -> Draft7Validator:
    schemastore = load_schemas()
    resolver = RefResolver.from_schema(schemastore[against_ocf_id], store=schemastore)
    validator = Draft7Validator(schemastore[against_ocf_id], resolver=resolver)
    return validator


def validate_snapshot(
    against_ocf_id: str = manifest_schema_id,
    ocf_instance: Optional[dict] = None,
):
    """

    Load the json file and validate against loaded schema

    :param against_ocf_id: The id of the schema file which describes the schema of the ocf file we want to validate.
    :param ocf_instance: Purported OCF json to validate against the schema.
    :return: True or raises error
    """
    if ocf_instance is None:
        ocf_instance = {}

    logger.info(f"Validate ocf instance: {ocf_instance}")

    try:
        validator = get_validator(against_ocf_id)
        validator.validate(ocf_instance)
        return True

    except ValidationError as error:
        logger.error(f"ValidationError: {error}")
        raise OCFValidationError(message="OCF Failed to Validate", validation_error=error.__str__()) from error

    except SchemaError as error:
        logger.error(f"SchemaError: {error}")
        raise error


def validate_ocf_file_instance(ocf_file_contents_json: Optional[dict] = None, verbose: bool = False) -> bool:
    if ocf_file_contents_json is None:
        ocf_file_contents_json = {}

    if verbose:
        logger.info(f"ocf_file_contents_json file_type is: {ocf_file_contents_json['file_type']}")

    if "file_type" not in ocf_file_contents_json:
        logger.warning(f"This failed validation for file_type: {json.dumps(ocf_file_contents_json, indent=4)}")
        msg = "This does not appear to be an ocf file JSON... it's missing the file_type property."
        raise ValueError(msg)

    target_id = file_type_to_ocf_id_dict[ocf_file_contents_json["file_type"]]

    validate_snapshot(ocf_instance=ocf_file_contents_json, against_ocf_id=target_id)
    return True
