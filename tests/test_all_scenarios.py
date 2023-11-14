import io
import itertools
import json
import logging
import os
import random
import tempfile
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from sympy import Float
from sympy.parsing.sympy_parser import parse_expr

from CE2OCF.__about__ import __version__ as PARSER_VERSION  # noqa
from CE2OCF.ce import extract_ce_variable_val
from CE2OCF.ce.mocks.objects import generate_mock_ce_json_str
from CE2OCF.datamap.definitions import RepeatableDataMap
from CE2OCF.datamap.loaders import (
    load_cic_event_definition,
    load_double_trigger_definitions,
)
from CE2OCF.datamap.parsers import (
    parse_ocf_issuer_from_ce_jsons,
    parse_ocf_stakeholders_from_ce_json,
    parse_ocf_stock_class_from_ce_jsons,
    parse_ocf_stock_issuances_from_ce_json,
    parse_ocf_stock_legend_from_ce_jsons,
    parse_ocf_vesting_events_from_ce_json,
    parse_ocf_vesting_schedules_from_ce_json,
)
from CE2OCF.ocf.datamaps import (
    AddressDataMap,
    PhoneDataMap,
    RepeatableVestingEventDriversDataMap,
    RepeatableVestingScheduleDriversDataMap,
    RepeatableVestingStockIssuanceDataMap,
    VestingScheduleInputsDataMap,
)
from CE2OCF.ocf.generators.ocf_id_generators import (
    generate_accel_trigger_termination_event_id,
    generate_cic_event_id,
    generate_time_based_accel_expiration_event_id,
    generate_vesting_start_id,
)
from CE2OCF.ocf.generators.ocf_vesting_conditions import (
    generate_cliff_vesting_condition_id,
    generate_monthly_vesting_condition_id,
)
from CE2OCF.ocf.generators.vesting_enums_to_ocf import (
    generate_ocf_vesting_schedule_from_vesting_drivers,
    generate_single_trigger_conditions_from_enumerations,
)
from CE2OCF.ocf.mocks.company import mock_company, mock_director
from CE2OCF.ocf.mocks.stockholders import mock_stockholder
from CE2OCF.ocf.pipeline import (
    package_ocf_files_contents_into_zip_archive,
    package_translated_ce_as_valid_ocf_files_contents,
    translate_ce_inc_questionnaire_datasheet_items_to_ocf,
)
from CE2OCF.ocf.postprocessors import (
    convert_phone_number_to_international_standard,
    convert_state_free_text_to_province_code,
    gunderson_repeat_var_processor,
)
from CE2OCF.ocf.validator import validate_ocf_file_instance
from CE2OCF.types.dictionaries import ContractExpressVarObj
from CE2OCF.types.enums import (
    DoubleTriggerTypesEnum,
    OcfVestingDayOfMonthEnum,
    PaidWithOptionsEnum,
    RepeatableFields,
    SingleTriggerTypesEnum,
    VestingTypesEnum,
)
from CE2OCF.types.models import Stockholder
from CE2OCF.utils.log_utils import logger

# Natural language definitions + datapoint drivers for double trigger and cic events
GD_DOUBLE_TRIGGER_ENUM_TO_OCF_GENERATOR_INPUTS = load_double_trigger_definitions()
GD_CIC_EVENT_DEFINITION = load_cic_event_definition()


class TestCeToOcfConversion(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

        # Uncomment to capture library DEBUG logs
        self._caplog.set_level(logging.INFO)

    def setUp(self) -> None:

        AddressDataMap.register_handlers(
            {"country_subdivision": lambda x, _: convert_state_free_text_to_province_code(x)}
        )
        PhoneDataMap.register_handlers({"phone_number": lambda x, _: convert_phone_number_to_international_standard(x)})

        self.maxDiff = None
        self.formation_date = datetime.now(timezone.utc)

        self.dummy_company = mock_company()
        self.dummy_company.NumberStockholders = 3
        self.dummy_company.FFPreferred = True
        self.dummy_company.FFPreferredPricePerShare = 1.23
        self.dummy_company.FFPreferredSharesAuthorized = 1000000
        self.dummy_company.NumberDirectors = 2

        self.stockholder_1 = mock_stockholder()
        self.stockholder_1.id = "STOCKHOLDER.1"
        self.stockholder_1.FFPreferredShares = (
            None if not self.dummy_company.FFPreferred else random.randint(1, 1000) * 1000  # noqa
        )
        self.stockholder_1.SingleTrigger = SingleTriggerTypesEnum.ONE_HUNDRED_PERCENT_ALL_TIMES
        self.stockholder_1.DoubleTrigger = DoubleTriggerTypesEnum.ONE_HUNDRED_PERCENT_12_MONTHS
        self.stockholder_1.Shares = 10000
        self.stockholder_1.VCD = "2023-12-31"
        self.stockholder_1.Vesting = VestingTypesEnum.FOUR_YR_NO_CLIFF
        self.stockholder_1.PaidWith = PaidWithOptionsEnum.IP
        logger.info(f"Stockholder 1:\n{json.dumps(self.stockholder_1.dict(), indent=2)}")

        self.stockholder_2 = mock_stockholder()
        self.stockholder_2.id = "STOCKHOLDER.2"
        self.stockholder_2.FFPreferredShares = (
            None if not self.dummy_company.FFPreferred else random.randint(1000, 100000)  # noqa
        )
        self.stockholder_2.SingleTrigger = SingleTriggerTypesEnum.ONE_HUNDRED_PERCENT_ALL_TIMES
        self.stockholder_2.DoubleTrigger = DoubleTriggerTypesEnum.FIFTY_PERCENT_ANY_TIME
        self.stockholder_2.Shares = 10000
        self.stockholder_2.VCD = "2023-12-31"
        self.stockholder_2.Vesting = VestingTypesEnum.FOUR_YR_1_YR_CLIFF
        self.stockholder_2.PaidWith = PaidWithOptionsEnum.IP
        logger.info(f"Stockholder 2:\n{json.dumps(self.stockholder_2.dict(), indent=2)}")

        self.stockholder_3 = mock_stockholder()
        self.stockholder_3.id = "STOCKHOLDER.3"
        self.stockholder_3.FFPreferredShares = (
            None if not self.dummy_company.FFPreferred else random.randint(1000, 100000)  # noqa
        )
        self.stockholder_3.SingleTrigger = SingleTriggerTypesEnum.NA
        self.stockholder_3.DoubleTrigger = DoubleTriggerTypesEnum.FIFTY_PERCENT_12_MONTHS
        self.stockholder_3.Shares = 8000
        self.stockholder_3.VCD = "2023-12-31"
        self.stockholder_3.Vesting = VestingTypesEnum.FULLY_VESTED
        self.stockholder_3.PaidWith = PaidWithOptionsEnum.IP
        logger.info(f"Stockholder 3:\n{json.dumps(self.stockholder_3.dict(), indent=2)}")

        self.director_1 = mock_director()
        self.director_2 = mock_director()

        json_str = generate_mock_ce_json_str(
            company=self.dummy_company,
            stockholders=[
                self.stockholder_1,
                self.stockholder_2,
                self.stockholder_3,
            ],
            directors=[self.director_1, self.director_2],
            include_founder_pref=False,
            override_repeated_fields=[],
        )
        self.ce_jsons = json.loads(json_str)

        # I don't want this as a default post-processor as it's template specific
        # RepeatableDataMap.register_handlers({
        #     "repeated_variables": gunderson_repeat_var_processor
        # })

    def test_ce_to_ocf_issuer_parser(self):
        issuer_ocf = parse_ocf_issuer_from_ce_jsons(
            self.ce_jsons,
            value_overrides={
                "FORMATION_DATE": datetime.now(timezone.utc).date().isoformat(),
                "PARSER_VERSION": PARSER_VERSION,
            },
        )

        self.assertEqual(
            issuer_ocf["comments"][0],
            f"Auto-generated by CE2OCF Contract Express Parser v{PARSER_VERSION}",
        )

        issuer_ocf.pop("id")
        issuer_ocf.pop("comments")

        logger.info(f"Test issuer ocf:\n\n{json.dumps(issuer_ocf, indent=2)}")
        logger.info(f"For company: {self.dummy_company.json()}")

        self.assertEqual(
            issuer_ocf,
            {
                "object_type": "ISSUER",
                "legal_name": self.dummy_company.CompanyName,
                "dba": self.dummy_company.CompanyShortName,
                "formation_date": datetime.now(timezone.utc).date().isoformat(),
                "country_of_formation": "US",
                "country_subdivision_of_formation": "DE",
                "tax_ids": [],  # TODO - do we want to store EIN in the OCF export?
                "address": {
                    "address_type": "LEGAL",
                    "street_suite": self.dummy_company.CompanyStreet,
                    "city": self.dummy_company.CompanyCity,
                    "country_subdivision": self.dummy_company.CompanyState,
                    "country": "US",
                    "postal_code": self.dummy_company.CompanyZip,
                },
                "phone": {
                    "phone_type": "BUSINESS",
                    "phone_number": convert_phone_number_to_international_standard(
                        self.dummy_company.CompanyPhoneNumber
                    ),
                },
            },
        )

    # TODO - improve test - this is a placeholder
    def test_ce_to_stock_class(self):
        common_stock_ocf = parse_ocf_stock_class_from_ce_jsons(
            self.ce_jsons, value_overrides={"PARSER_VERSION": PARSER_VERSION}
        )
        pref_stock_ocf = parse_ocf_stock_class_from_ce_jsons(
            self.ce_jsons, common_or_preferred="PREFERRED", value_overrides={"PARSER_VERSION": PARSER_VERSION}
        )
        stock_classes_ocf = [common_stock_ocf, pref_stock_ocf]

        logger.info(f"Generated stock_class_ocf: \n\n{json.dumps(stock_classes_ocf, indent=2)}")

        self.assertEqual(2, len(stock_classes_ocf))

        for stock_class_ocf in stock_classes_ocf:
            self.assertEqual(
                stock_class_ocf["comments"][0],
                f"Auto-generated by CE2OCF Contract Express Parser v{PARSER_VERSION}",
            )

            stock_class_ocf.pop("id")
            stock_class_ocf.pop("comments")

    def test_ce_to_stock_legends_ocf(self):
        common_stock_legend_ocf = parse_ocf_stock_legend_from_ce_jsons(
            self.ce_jsons, value_overrides={"PARSER_VERSION": PARSER_VERSION}
        )
        pref_stock_legend_ocf = parse_ocf_stock_legend_from_ce_jsons(
            self.ce_jsons, common_or_preferred="PREFERRED", value_overrides={"PARSER_VERSION": PARSER_VERSION}
        )
        legend_ocf_items = [common_stock_legend_ocf, pref_stock_legend_ocf]

        logger.info(f"Generated stock legends ocf: \n\n{json.dumps(legend_ocf_items, indent=2)}")

        self.assertEqual(
            legend_ocf_items,
            [
                {
                    "id": "COMMON.legend",
                    "comments": [
                        "Gunderson Language Version 2022-05-12",
                        f"Auto-generated by CE2OCF Contract Express Parser v{PARSER_VERSION}",
                    ],
                    "object_type": "STOCK_LEGEND_TEMPLATE",
                    "name": "Founder Common Stock Legend",
                    "text": "\nTHE SHARES REPRESENTED HEREBY MAY NOT BE SOLD, ASSIGNED, TRANSFERRED, ENCUMBERED OR IN "
                    "ANY MANNER DISPOSED OF, EXCEPT\nIN COMPLIANCE WITH THE TERMS OF A WRITTEN AGREEMENT "
                    "BETWEEN THE COMPANY AND THE REGISTERED HOLDER OF THE SHARES (OR THE\n PREDECESSOR IN "
                    "INTEREST TO THE SHARES). SUCH AGREEMENT GRANTS TO THE COMPANY CERTAIN RIGHTS OF FIRST "
                    "REFUSAL UPON AN\n ATTEMPTED TRANSFER OF THE SHARES AND CERTAIN REPURCHASE RIGHTS UPON "
                    "TERMINATION OF SERVICE WITH THE COMPANY. THE\n SECRETARY OF THE COMPANY WILL UPON WRITTEN "
                    "REQUEST FURNISH A COPY OF SUCH AGREEMENT TO THE HOLDER HEREOF WITHOUT\n CHARGE. THE "
                    "SHARES REPRESENTED HEREBY HAVE NOT BEEN REGISTERED UNDER THE SECURITIES ACT OF 1933, "
                    "AS AMENDED, AND\nMAY NOT BE SOLD, PLEDGED, OR OTHERWISE TRANSFERRED WITHOUT AN EFFECTIVE "
                    "REGISTRATION THEREOF UNDER SUCH ACT OR AN\nOPINION OF COUNSEL, SATISFACTORY TO THE "
                    "COMPANY AND ITS COUNSEL, THAT SUCH REGISTRATION IS NOT REQUIRED.\n",
                },
                {
                    "id": "FFPREFERRED.legend",
                    "comments": [
                        "Gunderson Language Version 2022-05-12",
                        f"Auto-generated by CE2OCF Contract Express Parser v{PARSER_VERSION}",
                    ],
                    "object_type": "STOCK_LEGEND_TEMPLATE",
                    "name": "Founder Preferred Stock Legend",
                    "text": "\nTHE SHARES REPRESENTED HEREBY MAY NOT BE SOLD, ASSIGNED, TRANSFERRED, ENCUMBERED OR IN "
                    "ANY MANNER DISPOSED OF, EXCEPT\nIN COMPLIANCE WITH THE TERMS OF A WRITTEN AGREEMENT "
                    "BETWEEN THE COMPANY AND THE REGISTERED HOLDER OF THE SHARES (OR THE\nPREDECESSOR IN "
                    "INTEREST TO THE SHARES). SUCH AGREEMENT GRANTS TO THE COMPANY CERTAIN RIGHTS OF FIRST "
                    "REFUSAL UPON AN\nATTEMPTED TRANSFER OF THE SHARES. THE SECRETARY OF THE COMPANY WILL "
                    "UPON WRITTEN REQUEST FURNISH A COPY OF SUCH\nAGREEMENT TO THE HOLDER HEREOF WITHOUT "
                    "CHARGE. THE SHARES REPRESENTED HEREBY HAVE NOT BEEN REGISTERED UNDER THE\nSECURITIES ACT "
                    "OF 1933, AS AMENDED, AND MAY NOT BE SOLD, PLEDGED, OR OTHERWISE TRANSFERRED WITHOUT AN "
                    "EFFECTIVE\nREGISTRATION THEREOF UNDER SUCH ACT OR AN OPINION OF COUNSEL, SATISFACTORY TO "
                    "THE COMPANY AND ITS COUNSEL, THAT SUCH\nREGISTRATION IS NOT REQUIRED.\n",
                },
            ],
        )

    def test_ce_to_stakeholders_ocf(self):
        stakeholder_ocf = parse_ocf_stakeholders_from_ce_json(
            self.ce_jsons, value_overrides={"PARSER_VERSION": PARSER_VERSION}
        )
        logger.info(f"stakeholder_file_ocf: {json.dumps(stakeholder_ocf, indent=2)}")

        for index, sh_ocf in enumerate(stakeholder_ocf):
            this_stockholder_ocf = {**sh_ocf}
            this_stockholder_ocf.pop("id")
            stakeholder_obj: Stockholder = getattr(self, f"stockholder_{index + 1}")
            self.assertEqual(
                {
                    "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{PARSER_VERSION}"],
                    "object_type": "STAKEHOLDER",
                    "name": {
                        "legal_name": stakeholder_obj.Stockholder,
                    },
                    "stakeholder_type": "INDIVIDUAL",
                    "issuer_assigned_id": f"STOCKHOLDER.{index + 1}",
                    "current_relationship": "FOUNDER",
                    "primary_contact": {
                        "name": {"legal_name": stakeholder_obj.Stockholder},
                        "emails": [
                            {
                                "email_type": "PERSONAL",
                                "email_address": stakeholder_obj.EmailAddress,
                            }
                        ],
                        "phone_numbers": [
                            {
                                "phone_type": "HOME",
                                "phone_number": convert_phone_number_to_international_standard(
                                    stakeholder_obj.PhoneNumber
                                ),
                            }
                        ],
                    },
                    "addresses": [
                        {
                            "address_type": "CONTACT",
                            "street_suite": stakeholder_obj.StockholderStreet,
                            "city": stakeholder_obj.StockholderCity,
                            "country_subdivision": stakeholder_obj.StockholderState,
                            "country": "US",  # doesn't look like we support non-US addresses
                            "postal_code": stakeholder_obj.StockholderZip,
                        }
                    ],
                    "tax_ids": [],
                },
                this_stockholder_ocf,
            )

    def test_sh_equity_issuances(self):

        # Utility function for this test
        def get_list_of_repeated_variable_roots(
            ce_response_objs: list[ContractExpressVarObj],
        ) -> list[str]:

            repeated_ce_var_objs = extract_ce_variable_val("StockholderInfoSame", ce_response_objs)
            logger.info(f"repeated_ce_var_objs: {repeated_ce_var_objs}")
            #
            # if isinstance(repeated_ce_var_objs, str):
            #     repeated_ce_var_objs = [repeated_ce_var_objs]
            # repeated_ce_var_objs = gunderson_repeat_var_processor(repeated_ce_var_objs, ce_response_objs)
            # logger.info(f"repeated_ce_var_objs post-processed: {repeated_ce_var_objs}")

            if isinstance(repeated_ce_var_objs, list):
                return repeated_ce_var_objs
            elif isinstance(repeated_ce_var_objs, str):
                return [repeated_ce_var_objs]
            return []

        # We're going to use the repeat values enum to drive
        possibly_repeated_fields = list(RepeatableFields)
        possible_repeat_field_combinations = []
        for r in range(len(possibly_repeated_fields) + 1):
            possible_repeat_field_combinations.extend(list(itertools.combinations(possibly_repeated_fields, r)))

        # FIRST, let's create ce jsons with NO repeats and ensure that we get the equity issuance values
        # we'd expect in the OCF for each resulting object. The repeated fields mean that the value for
        # applicable field should be pulled from stockholder #1 for all subsequent stockholders. This is a
        # convenience in the underlying template made to make it easier
        logger.info(
            f"Test that repeat value parser works... need to test {len(possible_repeat_field_combinations)} "
            f"combinations"
        )
        for repeat_field_combination in possible_repeat_field_combinations:

            json_str = generate_mock_ce_json_str(
                company=self.dummy_company,
                stockholders=[
                    self.stockholder_1,
                    self.stockholder_2,
                    self.stockholder_3,
                ],
                directors=[self.director_1, self.director_2],
                include_founder_pref=False,
                override_repeated_fields=list(repeat_field_combination),
            )
            ce_jsons = json.loads(json_str)

            stakeholders_ocf = parse_ocf_stakeholders_from_ce_json(self.ce_jsons)
            self.assertEqual(3, len(stakeholders_ocf))
            logger.info(f"Parsed stakeholder ocf:\n{json.dumps(stakeholders_ocf, indent=2)}")

            # Parse CE Jsons to see what the list of variables to repeat is (pulled from
            # shareholder #1 for ALL shareholders in which case you should ignore and override
            # any values in the applicable data fields for shareholders 2:n)
            logger.info(f"repeat_field_combination: {repeat_field_combination}")
            repeated_vars_list = get_list_of_repeated_variable_roots(ce_response_objs=ce_jsons)
            repeated_vars_list = gunderson_repeat_var_processor(repeated_vars_list, [])

            # Make sure that list of shareholder data fields that we generated for repetition (pulled from
            # shareholder #1 for ALL shareholders) are the same as what we parsed from the resulting
            # CE Jsons.
            self.assertEqual({e.value for e in repeat_field_combination}, set(repeated_vars_list))
            logger.info("repeat_field_combination re-parsed successfully via repeated_vars_list")

            # Want to clear residual handlers on the repeat datamap for isuances which may be acting
            # on
            # RepeatableVestingStockIssuanceDataMap.clear_handlers()
            # RepeatableFullyVestedStockIssuanceDataMap.clear_handlers()

            issuances_ocf = parse_ocf_stock_issuances_from_ce_json(ce_jsons)
            logger.info(f"Stockholder 1 vesting: {self.stockholder_1.Vesting}")
            logger.info(f"Stockholder 2 vesting: {self.stockholder_2.Vesting}")
            logger.info(f"Stockholder 3 vesting: {self.stockholder_3.Vesting}")
            logger.info(f"Repeated fields: {list(repeat_field_combination)}")
            logger.info(f"Issuances OCF:\n{json.dumps(issuances_ocf, indent=2)}")

            # Want to clear any post processors from relevant datamaps
            RepeatableVestingScheduleDriversDataMap.clear_handlers()
            VestingScheduleInputsDataMap.clear_handlers()

            # Then we want to register a post processor for vesting_schedule to map to ocf and another for our
            # usual Gunderson repeat variables
            RepeatableVestingScheduleDriversDataMap.register_handlers(
                {"repeated_variables": gunderson_repeat_var_processor}
            )

            vesting_schedule_ocf = parse_ocf_vesting_schedules_from_ce_json(
                ce_jsons,
                post_processors={"vesting_schedule": generate_ocf_vesting_schedule_from_vesting_drivers},
                fail_on_missing_variable=False,
            )
            logger.info(
                f"{len(vesting_schedule_ocf)} Vesting schedules ocf:\n{json.dumps(vesting_schedule_ocf, indent=2)}"
            )

            RepeatableVestingEventDriversDataMap.register_handlers(
                {"repeated_variables": gunderson_repeat_var_processor}
            )
            vesting_events_ocf = parse_ocf_vesting_events_from_ce_json(ce_jsons)
            logger.info(f"{len(vesting_events_ocf)} Vesting events ocf:\n{json.dumps(vesting_events_ocf, indent=2)}")
            logger.info(f"Stockholder 1 vesting: {self.stockholder_1.Vesting}")
            logger.info(f"Stockholder 2 vesting: {self.stockholder_2.Vesting}")
            logger.info(f"Stockholder 3 vesting: {self.stockholder_3.Vesting}")

            # For each stakeholder object, let's make sure we parsed the ocf values that match the source stakeholders
            # used to generate the CE JSONs (to simulate what we'd get from the API)
            for index, stakeholder_obj in enumerate([self.stockholder_1, self.stockholder_2, self.stockholder_3]):

                logger.info(f"\n\n######### PROCESS STAKEHOLDER {index} ########################3")
                # logger.info(f"Analyze issuances for stakeholder #{index+1}:")
                # logger.info(f"Issuer OCF:\n\n{json.dumps(stakeholder, indent=8)}")
                # logger.info(f"\n\nIssuer Obj:\n\n{stakeholder_obj.json()}")

                # What was issued to the stockholder in question?
                my_issuances = [
                    issuance
                    for issuance in issuances_ocf
                    if "stakeholder_id" in issuance and issuance["stakeholder_id"] == f"STOCKHOLDER.{index + 1}"
                ]

                # Narrow to common and preferred so we can test these for each stockholder
                pref_issuances = [iss for iss in my_issuances if iss["stock_class_id"] == "FFPREFERRED"]
                if (
                    self.dummy_company.FFPreferred
                    and self.dummy_company.FFPreferredPricePerShare
                    and stakeholder_obj.FFPreferredShares
                    and int(stakeholder_obj.FFPreferredShares) > 0
                ):
                    logger.info(f"Analyze Stockholder {index + 1}:\n{json.dumps(stakeholder_obj.dict(), indent=2)}")
                    self.assertEqual(1, len(pref_issuances))
                    total_consideration_value = parse_expr(
                        f"{float(self.dummy_company.FFPreferredPricePerShare)} * "
                        f"{int(stakeholder_obj.FFPreferredShares)}"
                    )
                    if isinstance(total_consideration_value, Float):
                        total_consideration_value = f"{total_consideration_value:.{10}g}"

                    pref_ocf_issuance = {**pref_issuances[0]}
                    pref_ocf_issuance.pop("id")
                    self.assertEqual(
                        {
                            "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{PARSER_VERSION}"],
                            "object_type": "TX_STOCK_ISSUANCE",
                            "date": self.formation_date.strftime("%Y-%m-%d"),
                            "security_id": f"FFPREFERRED.ISSUANCE.{index + 1}",
                            "custom_id": f"FF-{index + 1}",
                            "stakeholder_id": stakeholder_obj.id,
                            "board_approval_date": self.formation_date.strftime("%Y-%m-%d"),
                            "consideration_text": f"{total_consideration_value} USD; Consideration: "
                            f"{stakeholder_obj.PaidWith.value}",
                            "security_law_exemptions": [],
                            "stock_class_id": "FFPREFERRED",
                            "share_price": {
                                "amount": str(self.dummy_company.FFPreferredPricePerShare),
                                "currency": "USD",
                            },
                            "quantity": str(stakeholder_obj.FFPreferredShares),
                            "cost_basis": {
                                "amount": f"{total_consideration_value}",
                                "currency": "USD",
                            },
                            "stock_legend_ids": ["FFPREFERRED.legend"],
                        },
                        pref_ocf_issuance,
                    )

                common_issuances = [iss for iss in my_issuances if iss["stock_class_id"] == "COMMON"]
                self.assertEqual(1, len(common_issuances))

                logger.info(F"Look for issuance: {common_issuances[0]}")
                common_vest_trans = [
                    vest_event_ocf
                    for vest_event_ocf in vesting_events_ocf
                    if (
                        vest_event_ocf["object_type"] == "TX_VESTING_START"
                        and "security_id" in vest_event_ocf
                        and vest_event_ocf["security_id"] == common_issuances[0]["security_id"]
                    )
                ]
                assert len(common_vest_trans) <= 1

                common_ocf_issuance = {**common_issuances[0]}
                common_ocf_vesting_start = {**(common_vest_trans[0] if len(common_vest_trans) == 1 else {})}

                logger.info(f"\nTest common_ocf_issuance: {common_ocf_issuance}\n")
                logger.info(f"\nVesting start for common: {common_ocf_vesting_start}\n")

                common_ocf_issuance.pop("id")
                if common_ocf_vesting_start != {}:
                    common_ocf_vesting_start.pop("id")

                total_consideration_value = parse_expr(
                    f"{float(self.dummy_company.PricePerShare)} * " f"{int(stakeholder_obj.Shares)}"
                )
                # Limit to 10 decimal places if we have a float (OCF max)
                if isinstance(total_consideration_value, Float):
                    total_consideration_value = f"{total_consideration_value:.{10}g}"

                ########################################################################################################
                # Handle repeated fields...
                if RepeatableFields.PAID_WITH in repeat_field_combination:
                    logger.info(f"Consideration is repeated - use: {stakeholder_obj.PaidWith.value}")
                    consideration_text = (
                        f"{total_consideration_value} USD; Consideration: {self.stockholder_1.PaidWith.value}"
                    )
                else:
                    logger.info(f"Consideration is not repeated - use: {stakeholder_obj.PaidWith.value}")
                    consideration_text = (
                        f"{total_consideration_value} USD; Consideration: {stakeholder_obj.PaidWith.value}"
                    )

                if RepeatableFields.SINGLE_TRIGGER_ACCEL in repeat_field_combination:
                    single_trigger = self.stockholder_1.SingleTrigger.value
                else:
                    single_trigger = stakeholder_obj.SingleTrigger.value

                if RepeatableFields.DOUBLE_TRIGGER in repeat_field_combination:
                    double_trigger = self.stockholder_1.DoubleTrigger.value
                else:
                    double_trigger = stakeholder_obj.DoubleTrigger.value

                logger.info(
                    f"Is Vesting in repeat_field_combination: {repeat_field_combination} - "
                    f"{RepeatableFields.VESTING_SCHEDULE in repeat_field_combination}"
                )
                if RepeatableFields.VESTING_SCHEDULE in repeat_field_combination:
                    vesting_schedule = self.stockholder_1.Vesting.value
                    logger.info(f"Vesting schedule repeated from: {vesting_schedule}")
                else:
                    vesting_schedule = stakeholder_obj.Vesting.value
                    logger.info(f"Vesting schedule NOT repeated: {vesting_schedule}")

                if RepeatableFields.VCD in repeat_field_combination:
                    vcd = self.stockholder_1.VCD
                else:
                    vcd = stakeholder_obj.VCD

                logger.info(f"vesting_schedule_ocf: {json.dumps(vesting_schedule_ocf, indent=2)}")
                matching_vesting_schedules = [
                    sched
                    for sched in vesting_schedule_ocf
                    if sched["id"] == f"{vesting_schedule}/{single_trigger}/{double_trigger}"
                ]

                ########################################################################################################
                # Look up vesting schedule id based on potentially unique attrs
                logger.info(
                    f"Look for vesting schedule that matches attrs: "
                    f"{(vesting_schedule, single_trigger, double_trigger)}"
                )

                # For each unique combination of values of vesting_schedule, single_trigger and double_trigger,
                # there should be exactly one match
                if vesting_schedule == VestingTypesEnum.FULLY_VESTED.value:
                    logger.info(
                        "Vesting type is Fully Vested... should be no generated schedules for 'Fully Vested' and no "
                        "vesting start transaction"
                    )
                    self.assertEqual(0, len(matching_vesting_schedules))
                    self.assertEqual(0, len(common_vest_trans))
                else:
                    self.assertEqual(1, len(matching_vesting_schedules))
                    self.assertEqual(1, len(common_vest_trans))

                    logger.info(f"common_ocf_issuance: {common_ocf_issuance}")
                    logger.info(f"Matching vesting schedule:\n{matching_vesting_schedules[0]}")

                    target_ocf_vesting_schedule = {**matching_vesting_schedules[0]}
                    logger.info(f"target_ocf_vesting_schedule: {target_ocf_vesting_schedule}")

                    target_vesting_schedule_id = target_ocf_vesting_schedule.pop("id")

                    # Let's check the top-level vesting schedule object first... so pop off the conditions
                    # and save those for later. They'll be a LOT harder to test.
                    actual_vesting_conditions_ocf = target_ocf_vesting_schedule.pop("vesting_conditions")
                    logger.info(f"Popped off vesting conditions for subsequent test: {actual_vesting_conditions_ocf}")

                    # Check top-level properties of vesting terms object
                    self.assertEqual(
                        {
                            "object_type": "VESTING_TERMS",
                            "name": f"{vesting_schedule}",
                            "description": f"{vesting_schedule}",
                            "allocation_type": "CUMULATIVE_ROUNDING",
                        },
                        target_ocf_vesting_schedule,
                    )

                    # Check that the vesting conditions match our expectations...
                    start_condition_ocf = {}
                    expected_vesting_conditions_ocf = []

                    if vesting_schedule == VestingTypesEnum.FOUR_YR_NO_CLIFF:
                        start_condition_ocf = {
                            "id": generate_vesting_start_id(target_vesting_schedule_id),
                            "trigger": {"type": "VESTING_START_DATE"},
                            "next_condition_ids": [f"{target_vesting_schedule_id} | Monthly Vesting"],
                            "quantity": "0",
                        }
                        monthly_condition_ocf = {
                            "id": generate_monthly_vesting_condition_id(target_vesting_schedule_id),
                            "description": f"GD Autogenerated Time-Based Vesting Condition occurring every 1 MONTHS, "
                            f"48 times, after {target_vesting_schedule_id} | Start",
                            "trigger": {
                                "type": "VESTING_SCHEDULE_RELATIVE",
                                "period": {
                                    "length": 1,
                                    "type": "MONTHS",
                                    "occurrences": 48,
                                    "day_of_month": "VESTING_START_DAY_OR_LAST_DAY_OF_MONTH",
                                },
                                "relative_to_condition_id": f"{target_vesting_schedule_id} | Start",
                            },
                            "next_condition_ids": [],
                            "portion": {"numerator": "1", "denominator": "48"},
                        }
                        expected_vesting_conditions_ocf.append(monthly_condition_ocf)

                    elif vesting_schedule == VestingTypesEnum.FOUR_YR_1_YR_CLIFF:
                        start_condition_ocf = {
                            "id": generate_vesting_start_id(target_vesting_schedule_id),
                            "trigger": {"type": "VESTING_START_DATE"},
                            "next_condition_ids": [f"{target_vesting_schedule_id} | Monthly Vesting"],
                            "quantity": "0",
                        }
                        cliff_condition_ocf = {
                            "id": generate_cliff_vesting_condition_id(target_vesting_schedule_id),
                            "description": f"GD Autogenerated Time-Based Vesting Condition occurring every 12 MONTHS,"
                            f" 1 times, after {target_vesting_schedule_id} | Start",
                            "trigger": {
                                "type": "VESTING_SCHEDULE_RELATIVE",
                                "period": {
                                    "length": 12,
                                    "type": "MONTHS",
                                    "occurrences": 1,
                                    "day_of_month": "VESTING_START_DAY_OR_LAST_DAY_OF_MONTH",
                                },
                                "relative_to_condition_id": f"{target_vesting_schedule_id} | Start",
                            },
                            "next_condition_ids": f"{target_vesting_schedule_id} | Monthly Vesting",
                        }
                        monthly_condition_ocf = {
                            "id": generate_monthly_vesting_condition_id(target_vesting_schedule_id),
                            "description": f"GD Autogenerated Cliff Condition occurring every 1 MONTHS, 48 times, "
                            f"after {target_vesting_schedule_id} | Cliff Vest",
                            "trigger": {
                                "type": "VESTING_SCHEDULE_RELATIVE",
                                "period": {
                                    "length": 1,
                                    "type": "MONTHS",
                                    "occurrences": 48,
                                    "day_of_month": "VESTING_START_DAY_OR_LAST_DAY_OF_MONTH",
                                },
                                "relative_to_condition_id": f"{target_vesting_schedule_id} | Cliff Vest",
                            },
                            "next_condition_ids": [],
                            "portion": {"numerator": "1", "denominator": "48"},
                        }
                        expected_vesting_conditions_ocf.extend(
                            [
                                cliff_condition_ocf,
                                monthly_condition_ocf,
                            ]
                        )
                    else:
                        logger.info("Unsupported vesting or vesting with no actual conditions detected")

                    # Mix in double trigger acceleration and test accordingly (unless it's one of the unsupported double
                    # trigger tpes)
                    if double_trigger and double_trigger not in [
                        DoubleTriggerTypesEnum.NA,
                        DoubleTriggerTypesEnum.CUSTOM,
                    ]:

                        # Grab details from our datamaps
                        details = GD_DOUBLE_TRIGGER_ENUM_TO_OCF_GENERATOR_INPUTS[DoubleTriggerTypesEnum(double_trigger)]
                        assert details is not None

                        # Generate expected condition events and load specific properties from datamap
                        cic_event_id = generate_cic_event_id(target_vesting_schedule_id, "Double")
                        cic_event_details: dict[str, Any] = {**GD_CIC_EVENT_DEFINITION}

                        time_based_expiration_details = details["time_based_expiration_details"]
                        time_based_expiration_event_id = (
                            None
                            if time_based_expiration_details is None
                            else generate_time_based_accel_expiration_event_id(target_vesting_schedule_id, "Double")
                        )

                        termination_event_details = details["termination_event_details"]
                        termination_event_id = generate_accel_trigger_termination_event_id(
                            target_vesting_schedule_id, "Double"
                        )

                        start_condition_ocf = {
                            **start_condition_ocf,
                            "next_condition_ids": [*start_condition_ocf["next_condition_ids"], cic_event_id],
                        }

                        # Generate the OCF types for the vesting conditions
                        expected_vesting_conditions_ocf.append(
                            {
                                "id": cic_event_id,
                                "description": cic_event_details["description"],
                                "next_condition_ids": [
                                    *(
                                        [time_based_expiration_event_id]
                                        if time_based_expiration_event_id is not None
                                        else []
                                    ),
                                    termination_event_id,
                                ]
                                if time_based_expiration_details is not None
                                else [termination_event_id],
                                "trigger": {"type": "VESTING_EVENT"},
                                "portion": {
                                    "remainder": cic_event_details["remainder"],
                                    "numerator": str(cic_event_details["portion_numerator"]),
                                    "denominator": str(cic_event_details["portion_denominator"]),
                                },
                            }
                        )

                        if time_based_expiration_event_id is not None and time_based_expiration_details is not None:
                            expected_vesting_conditions_ocf.append(
                                {
                                    "id": time_based_expiration_event_id,
                                    "description": f"GD Autogenerated Time-Based Vesting Condition occurring every "
                                    f"{time_based_expiration_details['time_unit_quantity']} "
                                    f"{time_based_expiration_details['time_units']}, "
                                    f"{time_based_expiration_details['time_period_repetition']} times, "
                                    f"after {cic_event_id}",
                                    "trigger": {
                                        "type": "VESTING_SCHEDULE_RELATIVE",
                                        "period": {
                                            "length": time_based_expiration_details["time_unit_quantity"],
                                            "type": time_based_expiration_details["time_units"],
                                            "occurrences": time_based_expiration_details["time_period_repetition"],
                                            "day_of_month": OcfVestingDayOfMonthEnum.VESTING_START_DAY_OR_LAST_DAY_OF_MONTH,  # noqa
                                        },
                                        "relative_to_condition_id": cic_event_id,
                                    },
                                    "portion": {"denominator": "1", "numerator": "0", "remainder": True},
                                    "next_condition_ids": [],
                                }
                            )

                        expected_vesting_conditions_ocf.append(
                            {
                                "id": termination_event_id,
                                "portion": {
                                    "numerator": str(termination_event_details["portion_numerator"]),
                                    "denominator": str(termination_event_details["portion_denominator"]),
                                    "remainder": termination_event_details["remainder"],
                                },
                                "next_condition_ids": [],
                                "trigger": {"type": "VESTING_EVENT"},
                                "description": termination_event_details["description"],
                            }
                        )

                        logger.info(f"Vesting conditions ocf:\n\n{actual_vesting_conditions_ocf}")
                        actual_start_condition = [
                            vc
                            for vc in actual_vesting_conditions_ocf
                            if vc["id"] == generate_vesting_start_id(target_vesting_schedule_id)
                        ]
                        self.assertTrue(len(actual_start_condition) == 1)

                        expected_cliff_condition = [
                            vc
                            for vc in expected_vesting_conditions_ocf
                            if vc["id"] == generate_cliff_vesting_condition_id(target_vesting_schedule_id)
                        ]
                        actual_cliff_condition = [
                            vc
                            for vc in actual_vesting_conditions_ocf
                            if vc["id"] == generate_cliff_vesting_condition_id(target_vesting_schedule_id)
                        ]
                        self.assertEqual(len(expected_cliff_condition), len(actual_cliff_condition))
                        self.assertTrue(0 <= len(actual_cliff_condition) <= 1)

                        expected_monthly_condition = [
                            vc
                            for vc in expected_vesting_conditions_ocf
                            if vc["id"] == generate_monthly_vesting_condition_id(target_vesting_schedule_id)
                        ]
                        actual_monthly_condition = [
                            vc
                            for vc in actual_vesting_conditions_ocf
                            if vc["id"] == generate_monthly_vesting_condition_id(target_vesting_schedule_id)
                        ]
                        self.assertEqual(len(expected_monthly_condition), len(actual_monthly_condition))
                        self.assertTrue(0 <= len(actual_monthly_condition) <= 1)

                        #######################################################################
                        # Test for double trigger cic condition
                        expected_double_trigger_cic_condition = [
                            vc
                            for vc in expected_vesting_conditions_ocf
                            if vc["id"] == generate_cic_event_id(target_vesting_schedule_id, "Double")
                        ]
                        actual_double_trigger_cic_condition = [
                            vc
                            for vc in actual_vesting_conditions_ocf
                            if vc["id"] == generate_cic_event_id(target_vesting_schedule_id, "Double")
                        ]
                        self.assertEqual(
                            len(expected_double_trigger_cic_condition),
                            len(actual_double_trigger_cic_condition),
                        )
                        self.assertTrue(0 <= len(actual_double_trigger_cic_condition) <= 1)

                        logger.info(f"actual_double_trigger_cic_condition: {actual_double_trigger_cic_condition[0]}")
                        logger.info(
                            f"expected_double_trigger_cic_condition: {expected_double_trigger_cic_condition[0]}"
                        )
                        if len(actual_double_trigger_cic_condition) == 1:
                            self.assertEqual(
                                actual_double_trigger_cic_condition[0],
                                expected_double_trigger_cic_condition[0],
                            )

                        #######################################################################
                        # Test for double trigger expiration conditions
                        expected_double_trigger_expiration_condition = [
                            vc
                            for vc in expected_vesting_conditions_ocf
                            if vc["id"]
                            == generate_time_based_accel_expiration_event_id(target_vesting_schedule_id, "Double")
                        ]
                        actual_double_trigger_expiration_condition = [
                            vc
                            for vc in actual_vesting_conditions_ocf
                            if vc["id"]
                            == generate_time_based_accel_expiration_event_id(target_vesting_schedule_id, "Double")
                        ]
                        self.assertEqual(
                            len(expected_double_trigger_expiration_condition),
                            len(actual_double_trigger_expiration_condition),
                        )
                        self.assertTrue(0 <= len(actual_double_trigger_expiration_condition) <= 1)
                        if len(actual_double_trigger_expiration_condition) == 1:
                            self.assertEqual(
                                actual_double_trigger_expiration_condition[0],
                                expected_double_trigger_expiration_condition[0],
                            )

                        #######################################################################
                        # Test for double trigger termination conditions
                        expected_double_trigger_termination_condition = [
                            vc
                            for vc in expected_vesting_conditions_ocf
                            if vc["id"]
                            == generate_accel_trigger_termination_event_id(target_vesting_schedule_id, "Double")
                        ]
                        actual_double_trigger_termination_condition = [
                            vc
                            for vc in actual_vesting_conditions_ocf
                            if vc["id"]
                            == generate_accel_trigger_termination_event_id(target_vesting_schedule_id, "Double")
                        ]
                        self.assertEqual(
                            len(expected_double_trigger_termination_condition),
                            len(actual_double_trigger_termination_condition),
                        )
                        self.assertTrue(0 <= len(actual_double_trigger_termination_condition) <= 1)
                        if len(actual_double_trigger_termination_condition) == 1:
                            self.assertEqual(
                                actual_double_trigger_termination_condition[0],
                                expected_double_trigger_termination_condition[0],
                            )

                    # Note single trigger is extremely complex - too complex to put here
                    if single_trigger and single_trigger not in [
                        SingleTriggerTypesEnum.NA,
                        SingleTriggerTypesEnum.CUSTOM,
                    ]:
                        (
                            single_trigger_conditions_start_id,
                            single_trigger_conditions_ocf,
                        ) = generate_single_trigger_conditions_from_enumerations(
                            single_trigger_type=single_trigger,
                            vesting_schedule_type=vesting_schedule,
                            vesting_schedule_id=target_vesting_schedule_id,
                        )

                        logger.info(
                            f"Add single trigger {single_trigger} start id to vest start condition: "
                            f"{single_trigger_conditions_start_id}"
                        )
                        logger.info(f"Add single trigger conditions: {single_trigger_conditions_ocf}")
                        start_condition_ocf = {
                            **start_condition_ocf,
                            "next_condition_ids": [
                                *start_condition_ocf["next_condition_ids"],
                                single_trigger_conditions_start_id,
                            ],
                        }

                        expected_vesting_conditions_ocf.extend(single_trigger_conditions_ocf)

                    logger.info(f"Add start_condition_ocf to expected vesting conditions: {start_condition_ocf}")
                    expected_vesting_conditions_ocf.append(start_condition_ocf)

                    logger.info(f"From {vesting_schedule} / {single_trigger} / {double_trigger}:")
                    logger.info(f"expected_vesting_conditions_ocf:\n{expected_vesting_conditions_ocf}")
                    logger.info(f"actual_vesting_conditions_ocf:\n{actual_vesting_conditions_ocf}")

                    expected_cond_ids = [cond["id"] for cond in expected_vesting_conditions_ocf]
                    actual_cond_ids = [cond["id"] for cond in actual_vesting_conditions_ocf]

                    logger.info(f"{len(expected_cond_ids)} expected_vesting_conditions ids:\n{expected_cond_ids}")
                    logger.info(f"{len(actual_cond_ids)} actual_vesting_conditions_ocf ids:\n{actual_cond_ids}")
                    logger.info(f"Difference: {set(actual_cond_ids).difference(set(expected_cond_ids))}")

                    # Check that vesting condition length is what we'd expect (sanity check)
                    self.assertEqual(len(expected_vesting_conditions_ocf), len(actual_vesting_conditions_ocf))

                    # Check that VCD is what we'd expect (including whether it's repeated properly, depending on repeat
                    # field inputs
                    self.assertEqual(common_ocf_vesting_start["date"], vcd)

                    # Check that id returned in generated vesting table matches the actual target object we
                    # retrieved from ocf
                    logger.info(f"matching_vesting_schedules: {matching_vesting_schedules}")
                    self.assertEqual(
                        f"{matching_vesting_schedules[0]['id']} | Start",
                        f"{target_vesting_schedule_id} | Start",
                    )

                # Check that common issuance object is as we'd expect
                self.assertEqual(
                    {
                        "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{PARSER_VERSION}"],
                        "object_type": "TX_STOCK_ISSUANCE",
                        "date": self.formation_date.strftime("%Y-%m-%d"),
                        "security_id": f"COMMON.ISSUANCE.{index + 1}",
                        "custom_id": f"CS-{index + 1}",
                        "stakeholder_id": stakeholder_obj.id,
                        "board_approval_date": self.formation_date.strftime("%Y-%m-%d"),
                        "consideration_text": consideration_text,
                        "security_law_exemptions": [],
                        "stock_class_id": "COMMON",
                        "share_price": {
                            "amount": f"{self.dummy_company.PricePerShare}",
                            "currency": "USD",
                        },
                        "quantity": f"{stakeholder_obj.Shares}",
                        "cost_basis": {
                            "amount": f"{total_consideration_value}",
                            "currency": "USD",
                        },
                        "stock_legend_ids": ["COMMON.legend"],
                        **(
                            {}
                            if vesting_schedule == VestingTypesEnum.FULLY_VESTED.value
                            else {"vesting_terms_id": f"{vesting_schedule}/{single_trigger}/{double_trigger}"}
                        ),
                    },
                    common_ocf_issuance,
                )

            # Now, since we did all of our tests for each object that was extracted, let's do the same thing again
            # BUT for the packger
            # Call translate_ce_inc_questionnaire_datasheet_items_to_ocf() with ce_jsons
            # TODO - I think we do want parent values to persist unless explicitly overriden by child class...
            #  that's what I need to register same handler for parent and child.
            RepeatableDataMap.register_handlers({"repeated_variables": gunderson_repeat_var_processor})
            RepeatableVestingStockIssuanceDataMap.register_handlers(
                {"repeated_variables": gunderson_repeat_var_processor}
            )
            AddressDataMap.register_handlers(
                {"country_subdivision": lambda x, _: convert_state_free_text_to_province_code(x)}
            )
            PhoneDataMap.register_handlers(
                {"phone_number": lambda x, _: convert_phone_number_to_international_standard(x)}
            )

            translated_data = translate_ce_inc_questionnaire_datasheet_items_to_ocf(
                ce_jsons,
                pref_stock_issuance_custom_post_processors={"repeated_variables": gunderson_repeat_var_processor},
                common_stock_class_custom_post_processors={"repeated_variables": gunderson_repeat_var_processor},
                vesting_schedule_custom_post_processors={
                    "vesting_schedule": generate_ocf_vesting_schedule_from_vesting_drivers
                },
            )

            # Call package_translated_ce_as_valid_ocf_files_contents() with translated_data
            ocf_files_contents = package_translated_ce_as_valid_ocf_files_contents(translated_data)

            # Call package_ocf_files_contents_into_zip_archive() with ocf_files_contents
            zip_archive_bytes = package_ocf_files_contents_into_zip_archive(ocf_files_contents)

            # Reopen the zip file from the resulting bytes
            zip_file = zipfile.ZipFile(io.BytesIO(zip_archive_bytes))

            # Extract the contents to a temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_file.extractall(path=temp_dir)

                # For each file inside the loaded zip, pass contents to validate_ocf_file_instance() and
                # assert result is True
                for filename in os.listdir(temp_dir):
                    with open(os.path.join(temp_dir, filename)) as file:
                        file_contents = file.read()

                    assert validate_ocf_file_instance(json.loads(file_contents)) is True

        # TODO - reactivate
        # def test_invalid_generate_vesting_start_condition(self):
        #     # Can't have both portion and quantity values
        #     with self.assertRaises(ValueError):
        #         generate_vesting_start_condition(portion_numerator=1, portion_denominator=1, quantity=1000)
        #
        #     # Portion-based definition needs numerator and denominator
        #     with self.assertRaises(ValueError):
        #         generate_vesting_start_condition(
        #             portion_numerator=1,
        #         )
        #
        #     # Need to define quantity somehow... cannot have no arguments
        #     with self.assertRaises(ValueError):
        #         generate_vesting_start_condition()
        #
        # def test_generate_vesting_start_condition(self):
        #
        #     # Test quantity-based
        #     condition = generate_vesting_start_condition(quantity=1000)
        #     condition.pop("id")
        #     self.assertEqual(
        #         {
        #             "trigger": {"type": "VESTING_START_DATE"},
        #             "next_condition_ids": [],
        #             "quantity": "1000",
        #         },
        #         condition,
        #     )
        #
        #     # Test portion-based
        #     condition = generate_vesting_start_condition(portion_numerator=1, portion_denominator=1)
        #     condition.pop("id")
        #     self.assertEqual(
        #         {
        #             "trigger": {"type": "VESTING_START_DATE"},
        #             "next_condition_ids": [],
        #             "portion": {"numerator": "1", "denominator": "1"},
        #         },
        #         condition,
        #     )
        #
        #     # Test portion with remainder
        #     condition = generate_vesting_start_condition(portion_numerator=1, portion_denominator=1, remainder=True)
        #     condition.pop("id")
        #     self.assertEqual(
        #         {
        #             "trigger": {"type": "VESTING_START_DATE"},
        #             "next_condition_ids": [],
        #             "portion": {"numerator": "1", "denominator": "1", "remainder": True},
        #         },
        #         condition,
        #     )
        #
        # def test_generate_event_based_vesting_condition(self):
        #
        #     # Test portion-based (int args)
        #     condition = generate_event_based_vesting_condition(
        #         portion_denominator=1,
        #         portion_numerator=1,
        #         description="Woah such event, very happening, so driven.",
        #     )
        #     condition.pop("id")
        #     self.assertEqual(
        #         {
        #             "trigger": {"type": "VESTING_EVENT"},
        #             "description": "Woah such event, very happening, so driven.",
        #             "next_condition_ids": [],
        #             "portion": {"numerator": "1", "denominator": "1", "remainder": False},
        #         },
        #         condition,
        #     )
        #
        #     # Test portion-based (string args)
        #     condition = generate_event_based_vesting_condition(
        #         portion_denominator=1,
        #         portion_numerator=1,
        #         remainder=True,
        #         description="Woah such event, very happening, so driven.",
        #     )
        #     condition.pop("id")
        #     self.assertEqual(
        #         {
        #             "trigger": {"type": "VESTING_EVENT"},
        #             "description": "Woah such event, very happening, so driven.",
        #             "next_condition_ids": [],
        #             "portion": {"numerator": "1", "denominator": "1", "remainder": True},
        #         },
        #         condition,
        #     )

    def test_generate_single_trigger_acceleration_conditions(self):

        sample_dir = Path("tests/fixtures/ocf_vesting_schedules/")

        for scenario in [
            "FOUR_YR_1_YR_CLIFF.ONE_HUNDRED_PERCENT_INVOLUNTARY_TERMINATION",
            "FOUR_YR_1_YR_CLIFF.ONE_HUNDRED_PERCENT_ALL_TIMES",
            "FOUR_YR_1_YR_CLIFF.SIX_MONTHS_ALL_TIMES",
            "FOUR_YR_1_YR_CLIFF.SIX_MONTHS_INVOLUNTARY_TERMINATION",
            "FOUR_YR_1_YR_CLIFF.TWELVE_MONTHS_ALL_TIMES",
            "FOUR_YR_1_YR_CLIFF.TWELVE_MONTHS_INVOLUNTARY_TERMINATION",
            "FOUR_YR_1_YR_CLIFF.TWENTY_FOUR_MONTHS_ALL_TIMES",
            "FOUR_YR_1_YR_CLIFF.TWENTY_FOUR_MONTHS_INVOLUNTARY_TERMINATION",
            "FOUR_YR_NO_CLIFF.ONE_HUNDRED_PERCENT_INVOLUNTARY_TERMINATION",
            "FOUR_YR_NO_CLIFF.ONE_HUNDRED_PERCENT_ALL_TIMES",
            "FOUR_YR_NO_CLIFF.SIX_MONTHS_ALL_TIMES",
            "FOUR_YR_NO_CLIFF.SIX_MONTHS_INVOLUNTARY_TERMINATION",
            "FOUR_YR_NO_CLIFF.TWELVE_MONTHS_ALL_TIMES",
            "FOUR_YR_NO_CLIFF.TWELVE_MONTHS_INVOLUNTARY_TERMINATION",
            "FOUR_YR_NO_CLIFF.TWENTY_FOUR_MONTHS_ALL_TIMES",
            "FOUR_YR_NO_CLIFF.TWENTY_FOUR_MONTHS_INVOLUNTARY_TERMINATION",
        ]:
            logger.info(f"test_generate_single_trigger_acceleration_conditions() - Test scenario: {scenario}")

            # Made a mistake when generating samples so use this id for now:
            vesting_schedule_id = "4_yr_12mos_cliff_single_trigger_6_mos_accel.json"

            with open(sample_dir / f"{scenario}.json") as ocf_test_file:
                vesting_enum, single_trigger_enum = scenario.split(".")
                single_trigger = getattr(SingleTriggerTypesEnum, single_trigger_enum)
                vesting_schedule = getattr(VestingTypesEnum, vesting_enum)
                expected_vesting_conditions = json.loads(ocf_test_file.read())
                _, generated_conditions = generate_single_trigger_conditions_from_enumerations(
                    single_trigger_type=single_trigger,
                    vesting_schedule_type=vesting_schedule,
                    vesting_schedule_id=vesting_schedule_id,
                )
                self.assertEqual(expected_vesting_conditions, generated_conditions)
