import json
import logging
import os
import unittest

from jsonschema import Draft7Validator

from CE2OCF.ocf.validator import (
    get_validator,
    load_schemas,
    schema_dir,
    validate_ocf_file_instance,
)
from tests import ocf_sample_dir

logger = logging.getLogger(__name__)


class TestOcfValidator(unittest.TestCase):
    def __load_example_ocf(
        self,
        examples_path: str = ocf_sample_dir.resolve().__str__(),
        ocf_extension: str = ".ocf.json",
        verbose: bool = False,
    ):

        ocf_example_store = {}

        extension = ocf_extension.lower()
        for dirpath, _, files in os.walk(examples_path):
            for name in files:
                if extension and name.lower().endswith(extension):
                    if verbose:
                        logger.info(f"\tFound example ocf at path: {dirpath + '/' + name}")
                    with open(dirpath + "/" + name) as schema_fd:
                        schema = json.load(schema_fd)
                        if "file_type" in schema:
                            ocf_example_store[schema["file_type"]] = schema

        return ocf_example_store

    def test_load_schemas(self):
        """
        Test that we can load the OCF schemas into a schema store
        :return: No Return
        """
        schema_store = load_schemas()
        logger.info(f"Load schemas from path: {schema_dir}")
        logger.info(len(schema_store))
        self.assertIsInstance(schema_store, dict)
        self.assertTrue(len(schema_store) > 0)

        logger.info("Test some schema ids are present")
        self.assertTrue(
            "https://schema.opencaptablecoalition.com/v/1.1.0/enums/VestingTriggerType.schema.json" in schema_store
        )
        logger.info("Found https://schema.opencaptablecoalition.com/v/1.1.0/enums/VestingTriggerType.schema.json ")

    def test_load_validator(self):
        """
        Test that we can create an instance of our Python OCF validator.
        :return: No Return
        """
        logger.info("Test get_validator() produces a valid Draft7Validator obj")
        validator = get_validator()
        self.assertIsInstance(validator, Draft7Validator)
        logger.info("SUCCESS!")

    def test_known_valid_ocf(self):

        """
        Make sure our implementation of OCF validation works as expected. Sample file loaded from the OCF repo
        should valid properly.
        :return: No Return
        """

        logger.debug("----- Test that known valid OCF properly validates with the validator --------------------------")
        logger.debug(f"\tLoad sample valid ocf from dir: {ocf_sample_dir}")
        ocf_examples = self.__load_example_ocf()
        self.assertIsInstance(ocf_examples, dict)
        self.assertTrue(len(ocf_examples) == 8)
        logger.debug("\tSuccessfully loaded 8 sample file types... test contents")

        for file_type, file_contents_json in ocf_examples.items():
            logger.debug(f"\t\tTest validator for file type {file_type}")
            validate_ocf_file_instance(file_contents_json)
            logger.debug("\t\t\tSUCCESS!")
