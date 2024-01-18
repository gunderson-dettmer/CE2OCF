import json
import logging
import unittest
from datetime import datetime, timezone

import pytest

from CE2OCF import __version__ as GD_PARSER_VERSION  # noqa
from CE2OCF.datamap import (
    parse_stock_plan_from_ce_jsons,
    traverse_datamap,
)
from CE2OCF.datamap.definitions import RepeatableDataMap
from CE2OCF.datamap.loaders import (
    load_ce_to_ocf_issuer_datamap,
    load_vesting_schedule_driving_enums_datamap,
)
from CE2OCF.ocf.datamaps import (
    AddressDataMap,
    PhoneDataMap,
    RepeatableFullyVestedStockIssuanceDataMap,
    RepeatableStockholderDataMap,
    RepeatableVestingScheduleDriversDataMap,
    RepeatableVestingStockIssuanceDataMap,
    StockClassDataMap,
    StockLegendDataMap,
    StockPlanDataMap,
    VestingScheduleInputsDataMap,
)
from CE2OCF.ocf.generators.vesting_enums_to_ocf import (
    generate_ocf_vesting_schedule_from_vesting_drivers,
)
from CE2OCF.ocf.postprocessors import (
    convert_phone_number_to_international_standard,
    convert_state_free_text_to_province_code,
    gunderson_repeat_var_processor,
    year_from_iso_date,
)
from CE2OCF.types.dictionaries import ContractExpressVarObj
from CE2OCF.types.exceptions import VariableNotFoundError
from CE2OCF.utils.log_utils import logger
from tests import fixture_dir

RepeatableDataMap.register_handlers({"repeated_variables": gunderson_repeat_var_processor})

RepeatableFullyVestedStockIssuanceDataMap.register_handlers({"repeated_variables": gunderson_repeat_var_processor})

RepeatableVestingStockIssuanceDataMap.register_handlers({"repeated_variables": gunderson_repeat_var_processor})

AddressDataMap.register_handlers({"country_subdivision": lambda x, _: convert_state_free_text_to_province_code(x)})

PhoneDataMap.register_handlers({"phone_number": lambda x, _: convert_phone_number_to_international_standard(x)})


class TestRepeatObjectExtractionWithCE2OCF(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

        # Non-equity-related OCF objects
        self.stockholder_datamap = fixture_dir / "datamap_samples" / "ce_to_ocf_stockholders_only.json"
        self.issuer_datamap = fixture_dir / "datamap_samples" / "ce_to_ocf_issuer_only.json"

        # Common stock related objects
        self.common_stock_datamap = fixture_dir / "datamap_samples" / "ce_to_ocf_common_stock_class_only.json"
        self.common_stock_issuance_datamap = (
            fixture_dir / "datamap_samples" / "ce_to_ocf_common_stock_issuance_only.json"
        )
        self.common_stock_legend_datamap = (
            fixture_dir / "datamap_samples" / "ce_to_ocf_datamap_common_stock_legend_only.json"
        )

        # Founder preferred related objects
        self.preferred_stock_datamap = fixture_dir / "datamap_samples" / "ce_to_ocf_preferred_stock_class_only.json"
        self.preferred_stock_issuance_datamap = (
            fixture_dir / "datamap_samples" / "ce_to_ocf_preferred_stock_issuance_only.json"
        )
        self.preferred_stock_legend_datamap = (
            fixture_dir / "datamap_samples" / "ce_to_ocf_datamap_preferred_stock_legend_only.json"
        )

        # Stock plan related objects
        self.stock_plan_datamap = fixture_dir / "datamap_samples" / "ce_to_ocf_stock_plan_only.json"

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

        # Uncomment to capture library DEBUG logs
        self._caplog.set_level(logging.INFO)

    # TODO - check larger percentage of resulting ocf for correctness based on hand-mapping

    def test_parse_stockholder_info(self):
        logger.debug(
            "----- Test Stockholder Info Extraction ----------------------------------------------------------------"
        )

        with open(fixture_dir / "ce_datasheet_items_five_stockholders_full_answers.json") as ce_data:
            ce_json: list[ContractExpressVarObj] = json.loads(ce_data.read())
            stockholder_datamap = RepeatableStockholderDataMap.parse_file(self.stockholder_datamap)
            resulting_ocf = traverse_datamap(
                stockholder_datamap, None, ce_json, value_overrides={"PARSER_VERSION": GD_PARSER_VERSION}
            )
            assert isinstance(resulting_ocf, list)

            # Should be five iterations based on our datamap
            assert len(resulting_ocf) == 5
            for i, stakeholder in enumerate(resulting_ocf):
                if i == 0:
                    self.assertEqual(stakeholder["name"], {"legal_name": "Bob Smith"})
                elif i == 1:
                    self.assertEqual(stakeholder["name"], {"legal_name": "Janice L"})
                elif i == 2:
                    self.assertEqual(stakeholder["name"], {"legal_name": "Person 3"})
                elif i == 3:
                    self.assertEqual(stakeholder["name"], {"legal_name": "Fourth Guy"})
                elif i == 4:
                    self.assertEqual(stakeholder["name"], {"legal_name": "Fifth Person"})

    def test_parse_stockholder_info_when_repetition_omitted(self):
        """

        There is a variable in our templates called StockholderInfoSame that has a list of variable names that are
        "repeated". If the user doesn't answer the question about what info is repeated (presumably meaning none is),
        this value is not added to the JSON export. Worse, in the Json, the first stockholders var name goes from
        Stockholder_S1 to Stockholder. The repetition value flips from null to "[1]".

        We need to make sure that, either way, we get the values we're expecting.

        :return:
        """

        logger.debug(
            "----- Test Stockholder Info Extraction When Repetition Control Question Omitted --------------------------"
        )

        with open(fixture_dir / "ce_datasheet_no_repetition.json") as ce_data:
            ce_json: list[ContractExpressVarObj] = json.loads(ce_data.read())
            stockholder_datamap = RepeatableStockholderDataMap.parse_file(self.stockholder_datamap)
            resulting_ocf = traverse_datamap(
                stockholder_datamap, None, ce_json, value_overrides={"PARSER_VERSION": GD_PARSER_VERSION}
            )
            assert isinstance(resulting_ocf, list)

            self.assertEqual(2, len(resulting_ocf))

            stockholder_one = resulting_ocf[0]
            logger.debug(f"\t1)\tStockholder one info: {stockholder_one}")
            self.assertEqual(stockholder_one["name"], {"legal_name": "Garcon de Place"})

            stockholder_two = resulting_ocf[1]
            logger.debug(f"\t2)\tStockholder two info: {stockholder_two}")
            self.assertEqual(stockholder_two["name"], {"legal_name": "SJD"})
            logger.debug("SUCCESS")

    def test_parse_issuer_ocf(self):
        issuer_datamap = load_ce_to_ocf_issuer_datamap()

        with open(fixture_dir / "ce_datasheet_no_repetition.json") as ce_data:
            ce_jsons: list[ContractExpressVarObj] = json.loads(ce_data.read())
            issuer_ocf = traverse_datamap(
                issuer_datamap,
                None,
                ce_jsons,
                value_overrides={
                    "PARSER_VERSION": GD_PARSER_VERSION,
                    "FORMATION_DATE": datetime.now(timezone.utc).date().isoformat(),
                },
            )

            assert isinstance(issuer_ocf, dict)
            issuer_ocf.pop("id", None)  # Id is autogenerated uuid. Can't predict ahead of time.

            logger.debug(f"Issuer ocf:\n{json.dumps(issuer_ocf, indent=4)}")

            self.assertEqual(
                issuer_ocf,
                {
                    "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}"],
                    "object_type": "ISSUER",
                    "legal_name": "darkpillar.ai, Inc. (COPY)",
                    "dba": "darkpillar.ai",
                    "formation_date": datetime.now(timezone.utc).date().isoformat(),
                    "country_of_formation": "US",
                    "country_subdivision_of_formation": "DE",
                    "tax_ids": [],
                    "address": {
                        "address_type": "LEGAL",
                        "street_suite": None,
                        "city": "Eureka",
                        "country_subdivision": "NV",
                        "country": "US",
                        "postal_code": None,
                    },
                    "phone": {
                        "phone_type": "BUSINESS",
                        "phone_number": "+1 123 456 7890",
                    },
                },
            )
            logger.debug("NON-REPEATED ISSUER OCF IS CORRECT!")

        with open(fixture_dir / "ce_datasheet_items_five_stockholders_full_answers.json") as ce_data:
            datasheet_items: list[ContractExpressVarObj] = json.loads(ce_data.read())

            issuer_ocf = traverse_datamap(
                issuer_datamap,
                None,
                datasheet_items,
                value_overrides={
                    "PARSER_VERSION": GD_PARSER_VERSION,
                    "FORMATION_DATE": datetime.now(timezone.utc).date().isoformat(),
                },
            )
            # TODO - improve ocf typing
            assert isinstance(issuer_ocf, dict)
            issuer_ocf.pop("id", None)  # ID is autogenerated uuid. Can't predict ahead of time.

            self.assertEqual(
                {
                    "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}"],
                    "object_type": "ISSUER",
                    "legal_name": "This is totally a company",
                    "dba": "OMG, they're writing it ",
                    "formation_date": datetime.now(timezone.utc).date().isoformat(),
                    "country_of_formation": "US",
                    "country_subdivision_of_formation": "DE",
                    "tax_ids": [],
                    "address": {
                        "address_type": "LEGAL",
                        "street_suite": "Place of being\n",
                        "city": "City of Being",
                        "country_subdivision": "NY",
                        "country": "US",
                        "postal_code": "10004",
                    },
                    "phone": {
                        "phone_type": "BUSINESS",
                        "phone_number": "+1 123 456 7890",
                    },
                },
                issuer_ocf,
            )
            logger.debug("REPEATED ISSUER OCF IS CORRECT")

    def test_parse_common_stock_class_ocf(self):
        logger.debug(
            "----- Test Parse Stock Classes (Common Only) ----------------------------------------------------------"
        )
        with open(fixture_dir / "ce_datasheet_no_repetition.json") as ce_data:
            datasheet_items: list[ContractExpressVarObj] = json.loads(ce_data.read())
            common_stock_datamap = StockClassDataMap.parse_file(self.common_stock_datamap)
            common_stock_ocf = traverse_datamap(
                common_stock_datamap, None, datasheet_items, value_overrides={"PARSER_VERSION": GD_PARSER_VERSION}
            )

        self.assertEqual(
            {
                "id": "COMMON",
                "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}"],
                "object_type": "STOCK_CLASS",
                "name": "Common Stock",
                "class_type": "COMMON",
                "default_id_prefix": "CS-",
                "initial_shares_authorized": "10000000",
                "board_approval_date": datetime.now(timezone.utc).date().isoformat(),
                "votes_per_share": "1",
                "par_value": {"amount": "0.0001", "currency": "USD"},
                "price_per_share": {"amount": "0.0001", "currency": "USD"},
                "seniority": "1",
                "conversion_rights": [],
                "liquidation_preference_multiple": "1",
                "participation_cap_multiple": "1",
            },
            common_stock_ocf,
        )
        logger.debug("\tSUCCESS!")

    def test_parse_founder_pref_class_ocf(self):
        logger.debug(
            "----- Test Parse Stock Classes (Founder Pref Only) ------------------------------------------------------"
        )

        with open(fixture_dir / "ce_datasheet_items_with_founder_preferred.json") as ce_data:
            datasheet_items: list[ContractExpressVarObj] = json.loads(ce_data.read())
            pref_stock_datamap = StockClassDataMap.parse_file(self.preferred_stock_datamap)
            pref_stock_ocf = traverse_datamap(
                pref_stock_datamap, None, datasheet_items, value_overrides={"PARSER_VERSION": GD_PARSER_VERSION}
            )

            self.assertEqual(
                {
                    "id": "FFPREFERRED",
                    "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}"],
                    "object_type": "STOCK_CLASS",
                    "name": "Founder Preferred Stock",
                    "class_type": "PREFERRED",
                    "default_id_prefix": "FF-",
                    "initial_shares_authorized": "1000000",
                    "board_approval_date": datetime.now(timezone.utc).date().isoformat(),
                    "votes_per_share": "1",
                    "par_value": {"amount": "0.0001", "currency": "USD"},
                    "price_per_share": {"amount": "0.0002", "currency": "USD"},
                    "seniority": "1",
                    "conversion_rights": [
                        {
                            "converts_to_future_round": True,
                            "conversion_mechanism": {
                                "type": "RATIO_CONVERSION",
                                "conversion_price": {"amount": "0.0002", "currency": "USD"},
                                "rounding_type": "NORMAL",
                                "ratio": {"numerator": "1", "denominator": "1"},
                            },
                        }
                    ],
                    "liquidation_preference_multiple": "1",
                    "participation_cap_multiple": "1",
                },
                pref_stock_ocf,
            )
        logger.debug("\tSUCCESS!")

    def test_parse_stock_legends_ocf(self):
        logger.debug(
            "----- Test parse stock legends for common only questionairre ----------------------------------------"
        )
        with open(fixture_dir / "ce_datasheet_no_repetition.json") as ce_data:
            datasheet_items: list[ContractExpressVarObj] = json.loads(ce_data.read())
            common_stock_legend_datamap = StockLegendDataMap.parse_file(self.common_stock_legend_datamap)
            stock_legends_ocf = traverse_datamap(
                common_stock_legend_datamap,
                None,
                datasheet_items,
                value_overrides={"PARSER_VERSION": GD_PARSER_VERSION},
            )

            self.assertEqual(
                {
                    "id": "COMMON.legend",
                    "comments": [
                        "Gunderson Language Version 2022-05-12",
                        f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}",
                    ],
                    "object_type": "STOCK_LEGEND_TEMPLATE",
                    "name": "Founder Common Stock Legend",
                    "text": "\nTHE SHARES REPRESENTED HEREBY MAY NOT BE SOLD, ASSIGNED, TRANSFERRED, "
                    "ENCUMBERED OR IN ANY MANNER DISPOSED OF, EXCEPT\nIN COMPLIANCE WITH THE TERMS "
                    "OF A WRITTEN AGREEMENT BETWEEN THE COMPANY AND THE REGISTERED HOLDER OF THE SHARES"
                    " (OR THE\n PREDECESSOR IN INTEREST TO THE SHARES). SUCH AGREEMENT GRANTS TO "
                    "THE COMPANY CERTAIN RIGHTS OF FIRST REFUSAL UPON AN\n ATTEMPTED TRANSFER OF THE SHARES"
                    " AND CERTAIN REPURCHASE RIGHTS UPON TERMINATION OF SERVICE WITH THE COMPANY. "
                    "THE\n SECRETARY OF THE COMPANY WILL UPON WRITTEN REQUEST FURNISH A COPY OF SUCH "
                    "AGREEMENT TO THE HOLDER HEREOF WITHOUT\n CHARGE. THE SHARES REPRESENTED HEREBY "
                    "HAVE NOT BEEN REGISTERED UNDER THE SECURITIES ACT OF 1933, AS AMENDED, AND\nMAY "
                    "NOT BE SOLD, PLEDGED, OR OTHERWISE TRANSFERRED WITHOUT AN EFFECTIVE REGISTRATION "
                    "THEREOF UNDER SUCH ACT OR AN\nOPINION OF COUNSEL, SATISFACTORY TO THE COMPANY AND "
                    "ITS COUNSEL, THAT SUCH REGISTRATION IS NOT REQUIRED.\n",
                },
                stock_legends_ocf,
            )
            logger.debug("\tSUCCESSFULLY HANDLED COMMON ONLY LEGENDS")

        logger.debug("----- Test Parse Legends for Founder Pref ------------------------------------------------")
        with open(fixture_dir / "ce_datasheet_items_with_founder_preferred.json") as ce_data:
            datasheet_items_with_ffpreferred: list[ContractExpressVarObj] = json.loads(ce_data.read())
            preferred_stock_legend_datamap = StockLegendDataMap.parse_file(self.preferred_stock_legend_datamap)
            stock_legends_ocf = traverse_datamap(
                preferred_stock_legend_datamap,
                None,
                datasheet_items_with_ffpreferred,
                value_overrides={"PARSER_VERSION": GD_PARSER_VERSION},
            )
            self.assertEqual(
                {
                    "id": "FFPREFERRED.legend",
                    "comments": [
                        "Gunderson Language Version 2022-05-12",
                        f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}",
                    ],
                    "object_type": "STOCK_LEGEND_TEMPLATE",
                    "name": "Founder Preferred Stock Legend",
                    "text": "\nTHE SHARES REPRESENTED HEREBY MAY NOT BE SOLD, ASSIGNED, TRANSFERRED, "
                    "ENCUMBERED OR IN ANY MANNER DISPOSED OF, EXCEPT\nIN COMPLIANCE WITH THE TERMS OF "
                    "A WRITTEN AGREEMENT BETWEEN THE COMPANY AND THE REGISTERED HOLDER OF THE SHARES "
                    "(OR THE\nPREDECESSOR IN INTEREST TO THE SHARES). SUCH AGREEMENT GRANTS TO THE "
                    "COMPANY CERTAIN RIGHTS OF FIRST REFUSAL UPON AN\nATTEMPTED TRANSFER OF THE SHARES."
                    " THE SECRETARY OF THE COMPANY WILL UPON WRITTEN REQUEST FURNISH A COPY OF SUCH\n"
                    "AGREEMENT TO THE HOLDER HEREOF WITHOUT CHARGE. THE SHARES REPRESENTED HEREBY HAVE "
                    "NOT BEEN REGISTERED UNDER THE\nSECURITIES ACT OF 1933, AS AMENDED, AND MAY NOT BE"
                    " SOLD, PLEDGED, OR OTHERWISE TRANSFERRED WITHOUT AN EFFECTIVE\nREGISTRATION "
                    "THEREOF UNDER SUCH ACT OR AN OPINION OF COUNSEL, SATISFACTORY TO THE COMPANY AND "
                    "ITS COUNSEL, THAT SUCH\nREGISTRATION IS NOT REQUIRED.\n",
                },
                stock_legends_ocf,
            )
            logger.debug("\tSUCCESS!")

    def test_parse_stakeholder_ocf(self):
        logger.debug("----- Test parse stakeholders with no repetition -----------------------------------------------")

        stockholder_datamap = RepeatableStockholderDataMap.parse_file(self.stockholder_datamap)

        with open(fixture_dir / "ce_datasheet_no_repetition.json") as ce_data:
            ce_json: list[ContractExpressVarObj] = json.loads(ce_data.read())
            stakeholders_ocf = traverse_datamap(
                stockholder_datamap, None, ce_json, value_overrides={"PARSER_VERSION": GD_PARSER_VERSION}
            )
            logger.debug(f"test_parse_stakeholder_ocf - stakeholders_ocf: {json.dumps(stakeholders_ocf, indent=2)}")

            self.assertEqual(
                [
                    {
                        "id": "STOCKHOLDER.1",
                        "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}"],
                        "object_type": "STAKEHOLDER",
                        "name": {"legal_name": "Garcon de Place"},
                        "stakeholder_type": "INDIVIDUAL",
                        "issuer_assigned_id": "STOCKHOLDER.1",
                        "current_relationship": "FOUNDER",
                        "primary_contact": {
                            "name": {"legal_name": "Garcon de Place"},
                            "emails": [
                                {
                                    "email_type": "PERSONAL",
                                    "email_address": "robbie@darkpillar.ai",
                                }
                            ],
                            "phone_numbers": [
                                {
                                    "phone_type": "HOME",
                                    "phone_number": "+1 123 456 7890",
                                }
                            ],
                        },
                        "addresses": [
                            {
                                "address_type": "CONTACT",
                                "street_suite": None,
                                "city": "Eureka",
                                "country_subdivision": "NV",
                                "country": "US",
                                "postal_code": None,
                            }
                        ],
                        "tax_ids": [],
                    },
                    {
                        "id": "STOCKHOLDER.2",
                        "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}"],
                        "object_type": "STAKEHOLDER",
                        "name": {"legal_name": "SJD"},
                        "stakeholder_type": "INDIVIDUAL",
                        "issuer_assigned_id": "STOCKHOLDER.2",
                        "current_relationship": "FOUNDER",
                        "primary_contact": {
                            "name": {"legal_name": "SJD"},
                            "emails": [
                                {
                                    "email_type": "PERSONAL",
                                    "email_address": "jeffrey@darkpillar.ai",
                                }
                            ],
                            "phone_numbers": [
                                {
                                    "phone_type": "HOME",
                                    "phone_number": "+1 123 456 7890",
                                }
                            ],
                        },
                        "addresses": [
                            {
                                "address_type": "CONTACT",
                                "street_suite": None,
                                "city": "Eureka",
                                "country_subdivision": "NV",
                                "country": "US",
                                "postal_code": None,
                            }
                        ],
                        "tax_ids": [],
                    },
                ],
                stakeholders_ocf,
            )
            logger.debug("\tSUCCESS!")

        logger.debug(
            "----- Test parse stakeholders with repetitions---------------------------------------------------------"
        )
        with open(fixture_dir / "ce_datasheet_items_with_founder_preferred.json") as ce_data:
            ffpreferred_ce_json: list[ContractExpressVarObj] = json.loads(ce_data.read())

            stakeholders_ocf = traverse_datamap(
                stockholder_datamap, None, ffpreferred_ce_json, value_overrides={"PARSER_VERSION": GD_PARSER_VERSION}
            )
            self.assertEqual(
                [
                    {
                        "id": "STOCKHOLDER.1",
                        "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}"],
                        "object_type": "STAKEHOLDER",
                        "name": {"legal_name": "Bob Smith"},
                        "stakeholder_type": "INDIVIDUAL",
                        "issuer_assigned_id": "STOCKHOLDER.1",
                        "current_relationship": "FOUNDER",
                        "primary_contact": {
                            "name": {"legal_name": "Bob Smith"},
                            "emails": [
                                {
                                    "email_type": "PERSONAL",
                                    "email_address": "Cool.Runnings@chill.com",
                                }
                            ],
                            "phone_numbers": [
                                {
                                    "phone_type": "HOME",
                                    "phone_number": "+1 123 456 7890",
                                }
                            ],
                        },
                        "addresses": [
                            {
                                "address_type": "CONTACT",
                                "street_suite": "123 Place Town St",
                                "city": "Place Town",
                                "country_subdivision": "NY",
                                "country": "US",
                                "postal_code": "10004",
                            }
                        ],
                        "tax_ids": [],
                    },
                    {
                        "id": "STOCKHOLDER.2",
                        "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}"],
                        "object_type": "STAKEHOLDER",
                        "name": {"legal_name": "Janice L"},
                        "stakeholder_type": "INDIVIDUAL",
                        "issuer_assigned_id": "STOCKHOLDER.2",
                        "current_relationship": "FOUNDER",
                        "primary_contact": {
                            "name": {"legal_name": "Janice L"},
                            "emails": [
                                {
                                    "email_type": "PERSONAL",
                                    "email_address": "almost.a.friend@friends.co",
                                }
                            ],
                            "phone_numbers": [
                                {
                                    "phone_type": "HOME",
                                    "phone_number": "+1 123 456 7890",
                                }
                            ],
                        },
                        "addresses": [
                            {
                                "address_type": "CONTACT",
                                "street_suite": "Someplace in New York",
                                "city": "New York Town",
                                "country_subdivision": "GA",
                                "country": "US",
                                "postal_code": "84534",
                            }
                        ],
                        "tax_ids": [],
                    },
                    {
                        "id": "STOCKHOLDER.3",
                        "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}"],
                        "object_type": "STAKEHOLDER",
                        "name": {"legal_name": "Person 3"},
                        "stakeholder_type": "INDIVIDUAL",
                        "issuer_assigned_id": "STOCKHOLDER.3",
                        "current_relationship": "FOUNDER",
                        "primary_contact": {
                            "name": {"legal_name": "Person 3"},
                            "emails": [
                                {
                                    "email_type": "PERSONAL",
                                    "email_address": "p3@people.co",
                                }
                            ],
                            "phone_numbers": [
                                {
                                    "phone_type": "HOME",
                                    "phone_number": "+1 333 333 3333",
                                }
                            ],
                        },
                        "addresses": [
                            {
                                "address_type": "CONTACT",
                                "street_suite": "3 Third Street\n",
                                "city": "Treeton",
                                "country_subdivision": "TN",
                                "country": "US",
                                "postal_code": "333333",
                            }
                        ],
                        "tax_ids": [],
                    },
                    {
                        "id": "STOCKHOLDER.4",
                        "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}"],
                        "object_type": "STAKEHOLDER",
                        "name": {"legal_name": "Fourth Guy"},
                        "stakeholder_type": "INDIVIDUAL",
                        "issuer_assigned_id": "STOCKHOLDER.4",
                        "current_relationship": "FOUNDER",
                        "primary_contact": {
                            "name": {"legal_name": "Fourth Guy"},
                            "emails": [
                                {
                                    "email_type": "PERSONAL",
                                    "email_address": "p4@four.come",
                                }
                            ],
                            "phone_numbers": [
                                {
                                    "phone_type": "HOME",
                                    "phone_number": "+1 444 444 4444",
                                }
                            ],
                        },
                        "addresses": [
                            {
                                "address_type": "CONTACT",
                                "street_suite": "Fourth Place",
                                "city": "Fourth City",
                                "country_subdivision": "FL",
                                "country": "US",
                                "postal_code": "44444",
                            }
                        ],
                        "tax_ids": [],
                    },
                    {
                        "id": "STOCKHOLDER.5",
                        "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}"],
                        "object_type": "STAKEHOLDER",
                        "name": {"legal_name": "Fifth Person"},
                        "stakeholder_type": "INDIVIDUAL",
                        "issuer_assigned_id": "STOCKHOLDER.5",
                        "current_relationship": "FOUNDER",
                        "primary_contact": {
                            "name": {"legal_name": "Fifth Person"},
                            "emails": [
                                {
                                    "email_type": "PERSONAL",
                                    "email_address": "5@five.com",
                                }
                            ],
                            "phone_numbers": [
                                {
                                    "phone_type": "HOME",
                                    "phone_number": "+1 555 555 5555",
                                }
                            ],
                        },
                        "addresses": [
                            {
                                "address_type": "CONTACT",
                                "street_suite": "Fifth Place",
                                "city": "Fifton",
                                "country_subdivision": "FL",
                                "country": "US",
                                "postal_code": "55555",
                            }
                        ],
                        "tax_ids": [],
                    },
                ],
                stakeholders_ocf,
            )
            logger.debug("\tSUCCESS!")

    def test_fail_on_missing_values(self):
        """
        Depending on your needs, you may want the data mapper to fail when a value cannot be found. Test
        an export without a SOP with fail_on_missing_variable set to True and ensure custom exception VariableNotFound
        is thrown.
        """

        with self.assertRaises(VariableNotFoundError):
            with open(fixture_dir / "ce_datasheet_no_repetition.json") as ce_data:
                datasheet_items: list[ContractExpressVarObj] = json.loads(ce_data.read())
                stock_plan_datamap = StockPlanDataMap.parse_file(self.stock_plan_datamap)
                traverse_datamap(
                    stock_plan_datamap,
                    None,
                    datasheet_items,
                    value_overrides={"PARSER_VERSION": GD_PARSER_VERSION},
                    fail_on_missing_variable=True,
                )

    def test_parse_stock_plan(self):
        with open(fixture_dir / "ce_datasheet_five_stockholders.json") as ce_data:
            datasheet_items: list[ContractExpressVarObj] = json.loads(ce_data.read())
            stock_plan_ocf = parse_stock_plan_from_ce_jsons(
                datasheet_items,
                post_processors={"plan_name": lambda x, _: f"{year_from_iso_date(x)} Stock Plan"},
                value_overrides={"PARSER_VERSION": GD_PARSER_VERSION},
            )
            stock_plan_ocf.pop("id")

            self.assertEqual(
                {
                    "board_approval_date": datetime.now(timezone.utc).date().isoformat(),
                    "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}"],
                    "initial_shares_reserved": "9877",  # This isn't defined in loaded sample
                    "object_type": "STOCK_PLAN",
                    "plan_name": "2022 Stock Plan",
                    "stock_class_id": "COMMON_STOCK",
                    "stockholder_approval_date": datetime.now(timezone.utc).date().isoformat(),
                },
                stock_plan_ocf,
            )

    # TODO - recreate
    # def test_parse_no_stockholder_in_ce_to_ocf(self):
    #     with open(fixture_dir / "ce_datasheet_no_stockholders.json") as ce_data:
    #
    #         ce_json: list[ContractExpressVarObj] = json.loads(ce_data.read())
    #
    #         stakeholders_ocf = parse_stakeholder_ocf_from_ce(datasheet_items=ce_json)
    #
    #         self.assertEqual(stakeholders_ocf, {"file_type": "OCF_STAKEHOLDERS_FILE", "items": []})
    #
    #         logger.debug("SUCCESS")
    #

    def test_parse_fully_vested_issuances(self):
        with open(fixture_dir / "sample_ce_jsons" / "fully_vested_repeated.json") as ce_data:
            ce_json: list[ContractExpressVarObj] = json.loads(ce_data.read())

            RepeatableVestingStockIssuanceDataMap.register_handlers(
                {"repeated_variables": gunderson_repeat_var_processor}
            )
            common_issuance_data_map = RepeatableVestingStockIssuanceDataMap.parse_file(
                self.common_stock_issuance_datamap
            )

            issuance_ocf = traverse_datamap(
                common_issuance_data_map,
                None,
                ce_json,
                value_overrides={"PARSER_VERSION": GD_PARSER_VERSION},
                fail_on_missing_variable=False,
            )
            assert isinstance(issuance_ocf, list)

            # Clean the id off the items because these are transaction_items = transaction_ocf["items"]
            for issuance in issuance_ocf:
                assert isinstance(issuance, dict)
                issuance.pop("id")

            self.assertEqual(
                issuance_ocf,
                [
                    {
                        "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}"],
                        "object_type": "TX_STOCK_ISSUANCE",
                        "date": datetime.now(timezone.utc).date().isoformat(),
                        "security_id": "COMMON.ISSUANCE.1",
                        "custom_id": "CS-1",
                        "stakeholder_id": "STOCKHOLDER.1",
                        "board_approval_date": datetime.now(timezone.utc).date().isoformat(),
                        "consideration_text": "10.00000000 USD; Consideration: IP",
                        "security_law_exemptions": [],
                        "stock_class_id": "COMMON",
                        "share_price": {"amount": "0.0001", "currency": "USD"},
                        "quantity": "100000",
                        "cost_basis": {"amount": "10.00000000", "currency": "USD"},
                        "stock_legend_ids": ["COMMON.legend"],
                    },
                    {
                        "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}"],
                        "object_type": "TX_STOCK_ISSUANCE",
                        "date": datetime.now(timezone.utc).date().isoformat(),
                        "security_id": "COMMON.ISSUANCE.2",
                        "custom_id": "CS-2",
                        "stakeholder_id": "STOCKHOLDER.2",
                        "board_approval_date": datetime.now(timezone.utc).date().isoformat(),
                        "consideration_text": "1.000000000 USD; Consideration: IP",
                        "security_law_exemptions": [],
                        "stock_class_id": "COMMON",
                        "share_price": {"amount": "0.0001", "currency": "USD"},
                        "quantity": "10000",
                        "cost_basis": {"amount": "1.000000000", "currency": "USD"},
                        "stock_legend_ids": ["COMMON.legend"],
                    },
                    {
                        "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}"],
                        "object_type": "TX_STOCK_ISSUANCE",
                        "date": datetime.now(timezone.utc).date().isoformat(),
                        "security_id": "COMMON.ISSUANCE.3",
                        "custom_id": "CS-3",
                        "stakeholder_id": "STOCKHOLDER.3",
                        "board_approval_date": datetime.now(timezone.utc).date().isoformat(),
                        "consideration_text": "0.3333000000 USD; Consideration: IP",
                        "security_law_exemptions": [],
                        "stock_class_id": "COMMON",
                        "share_price": {"amount": "0.0001", "currency": "USD"},
                        "quantity": "3333",
                        "cost_basis": {
                            "amount": "0.3333000000",
                            "currency": "USD",
                        },
                        "stock_legend_ids": ["COMMON.legend"],
                    },
                    {
                        "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}"],
                        "object_type": "TX_STOCK_ISSUANCE",
                        "date": datetime.now(timezone.utc).date().isoformat(),
                        "security_id": "COMMON.ISSUANCE.4",
                        "custom_id": "CS-4",
                        "stakeholder_id": "STOCKHOLDER.4",
                        "board_approval_date": datetime.now(timezone.utc).date().isoformat(),
                        "consideration_text": "0.4444000000 USD; Consideration: IP",
                        "security_law_exemptions": [],
                        "stock_class_id": "COMMON",
                        "share_price": {"amount": "0.0001", "currency": "USD"},
                        "quantity": "4444",
                        "cost_basis": {"amount": "0.4444000000", "currency": "USD"},
                        "stock_legend_ids": ["COMMON.legend"],
                    },
                    {
                        "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}"],
                        "object_type": "TX_STOCK_ISSUANCE",
                        "date": datetime.now(timezone.utc).date().isoformat(),
                        "security_id": "COMMON.ISSUANCE.5",
                        "custom_id": "CS-5",
                        "stakeholder_id": "STOCKHOLDER.5",
                        "board_approval_date": datetime.now(timezone.utc).date().isoformat(),
                        "consideration_text": "0.5555000000 USD; Consideration: IP",
                        "security_law_exemptions": [],
                        "stock_class_id": "COMMON",
                        "share_price": {"amount": "0.0001", "currency": "USD"},
                        "quantity": "5555",
                        "cost_basis": {"amount": "0.5555000000", "currency": "USD"},
                        "stock_legend_ids": ["COMMON.legend"],
                    },
                ],
            )

            # We need to switch our registered post-processor to generate FFPreferred ids
            preferred_issuance_data_map = RepeatableFullyVestedStockIssuanceDataMap.parse_file(
                self.preferred_stock_issuance_datamap
            )

            issuance_ocf = traverse_datamap(
                preferred_issuance_data_map,
                None,
                ce_json,
                value_overrides={"PARSER_VERSION": GD_PARSER_VERSION},
                fail_on_missing_variable=False,
            )
            assert isinstance(issuance_ocf, list)

            # These are random uuids... need to drop them as we can't precalc them
            for issuance in issuance_ocf:
                assert isinstance(issuance, dict)
                issuance.pop("id")

            self.assertEqual(
                issuance_ocf,
                [
                    {
                        "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}"],
                        "object_type": "TX_STOCK_ISSUANCE",
                        "date": datetime.now(timezone.utc).date().isoformat(),
                        "security_id": "FFPREFERRED.ISSUANCE.1",
                        "custom_id": "FF-1",
                        "stakeholder_id": "STOCKHOLDER.1",
                        "board_approval_date": datetime.now(timezone.utc).date().isoformat(),
                        "consideration_text": "200.0000000 USD; Consideration: IP",
                        "security_law_exemptions": [],
                        "stock_class_id": "FFPREFERRED",
                        "share_price": {"amount": "0.0002", "currency": "USD"},
                        "quantity": "1000000",
                        "cost_basis": {"amount": "200.0000000", "currency": "USD"},
                        "stock_legend_ids": ["FFPREFERRED.legend"],
                    },
                    {
                        "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}"],
                        "object_type": "TX_STOCK_ISSUANCE",
                        "date": datetime.now(timezone.utc).date().isoformat(),
                        "security_id": "FFPREFERRED.ISSUANCE.2",
                        "custom_id": "FF-2",
                        "stakeholder_id": "STOCKHOLDER.2",
                        "board_approval_date": datetime.now(timezone.utc).date().isoformat(),
                        "consideration_text": "200.0000000 USD; Consideration: IP",
                        "security_law_exemptions": [],
                        "stock_class_id": "FFPREFERRED",
                        "share_price": {"amount": "0.0002", "currency": "USD"},
                        "quantity": "1000000",
                        "cost_basis": {"amount": "200.0000000", "currency": "USD"},
                        "stock_legend_ids": ["FFPREFERRED.legend"],
                    },
                    {
                        "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}"],
                        "object_type": "TX_STOCK_ISSUANCE",
                        "date": datetime.now(timezone.utc).date().isoformat(),
                        "security_id": "FFPREFERRED.ISSUANCE.3",
                        "custom_id": "FF-3",
                        "stakeholder_id": "STOCKHOLDER.3",
                        "board_approval_date": datetime.now(timezone.utc).date().isoformat(),
                        "consideration_text": "200.0000000 USD; Consideration: IP",
                        "security_law_exemptions": [],
                        "stock_class_id": "FFPREFERRED",
                        "share_price": {"amount": "0.0002", "currency": "USD"},
                        "quantity": "1000000",
                        "cost_basis": {"amount": "200.0000000", "currency": "USD"},
                        "stock_legend_ids": ["FFPREFERRED.legend"],
                    },
                    {
                        "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}"],
                        "object_type": "TX_STOCK_ISSUANCE",
                        "date": datetime.now(timezone.utc).date().isoformat(),
                        "security_id": "FFPREFERRED.ISSUANCE.4",
                        "custom_id": "FF-4",
                        "stakeholder_id": "STOCKHOLDER.4",
                        "board_approval_date": datetime.now(timezone.utc).date().isoformat(),
                        "consideration_text": "200.0000000 USD; Consideration: IP",
                        "security_law_exemptions": [],
                        "stock_class_id": "FFPREFERRED",
                        "share_price": {"amount": "0.0002", "currency": "USD"},
                        "quantity": "1000000",
                        "cost_basis": {"amount": "200.0000000", "currency": "USD"},
                        "stock_legend_ids": ["FFPREFERRED.legend"],
                    },
                    {
                        "comments": [f"Auto-generated by CE2OCF Contract Express Parser v{GD_PARSER_VERSION}"],
                        "object_type": "TX_STOCK_ISSUANCE",
                        "date": datetime.now(timezone.utc).date().isoformat(),
                        "security_id": "FFPREFERRED.ISSUANCE.5",
                        "custom_id": "FF-5",
                        "stakeholder_id": "STOCKHOLDER.5",
                        "board_approval_date": datetime.now(timezone.utc).date().isoformat(),
                        "consideration_text": "200.0000000 USD; Consideration: IP",
                        "security_law_exemptions": [],
                        "stock_class_id": "FFPREFERRED",
                        "share_price": {"amount": "0.0002", "currency": "USD"},
                        "quantity": "1000000",
                        "cost_basis": {"amount": "200.0000000", "currency": "USD"},
                        "stock_legend_ids": ["FFPREFERRED.legend"],
                    },
                ],
            )

    def test_parse_vesting_drivers(self):
        """
        Vesting is really, really hard to create a datamap for. Certainly, in most questionnaires, you have a couple
        enum values that will have to drive the creation of complex OCF vesting objects. The approach we're testing
        here (and what we recommend for enum-driven questionnaires) is to use a generic RepeatableDataMap and set
        repeated_pattern to a dict with a single field `vesting_events`. Its value should be a dictionary containing
        all the drivers that will be used to generate your OCF. We recommend you post-process `vesting_events`
        and convert the enum to ocf. We'll show you how to do that with our defaults and enum values, but you'll need to
        either adapt your template to meet our enums or modify the datamap to suit your chosen template enums.

        This test is just going to test that we're extracting the expected enums. We'll have a separate test showing
        the conversion from enum to proper ocf.
        """

        with open(fixture_dir / "ce_datasheet_five_stockholders.json") as ce_data:
            datasheet_items: list[ContractExpressVarObj] = json.loads(ce_data.read())

            ce_to_vesting_enums_datamap = load_vesting_schedule_driving_enums_datamap()

            # Want to clear any post processors from relevant datamaps
            RepeatableVestingScheduleDriversDataMap.clear_handlers()
            VestingScheduleInputsDataMap.clear_handlers()

            # We want raw vesting schedule values, so no changes there, but we do want to
            # properly map the repeated_variables, so register a post processor
            RepeatableVestingScheduleDriversDataMap.register_handlers(
                {"repeated_variables": gunderson_repeat_var_processor}
            )

            vesting_ocf = traverse_datamap(
                ce_to_vesting_enums_datamap,
                None,
                datasheet_items,
                value_overrides={"PARSER_VERSION": GD_PARSER_VERSION},
                fail_on_missing_variable=False,
                drop_null_leaves=True,
            )
            logger.debug(f"Vesting ocf:\n{json.dumps(vesting_ocf, indent=2)}")

            self.assertEqual(
                vesting_ocf,
                [
                    {
                        "vesting_schedule": {
                            "consideration": "IP",
                            "double_trigger": "100% of unvested; Involuntary Termination within 12 months after CiC",
                            "shares_issued": "100000",
                            "single_trigger": "100%; all times after CiC",
                            "vesting_commencement_date": "2021-09-23",
                            "vesting_schedule": "4yr with 1yr Cliff",
                            "stockholder_id": 1,
                        }
                    },
                    {
                        "vesting_schedule": {
                            "consideration": "IP",
                            "double_trigger": "100% of unvested; Involuntary Termination within 12 months after CiC",
                            "shares_issued": "10000",
                            "single_trigger": "100%; all times after CiC",
                            "vesting_commencement_date": "2021-09-23",
                            "vesting_schedule": "4yr with no Cliff",
                            "stockholder_id": 2,
                        }
                    },
                    {
                        "vesting_schedule": {
                            "consideration": "IP",
                            "double_trigger": "100% of unvested; Involuntary Termination within 12 months after CiC",
                            "shares_issued": "3333",
                            "single_trigger": "100%; all times after CiC",
                            "vesting_commencement_date": "2021-09-23",
                            "vesting_schedule": "Fully Vested",
                            "stockholder_id": 3,
                        }
                    },
                    {
                        "vesting_schedule": {
                            "consideration": "IP",
                            "double_trigger": "100% of unvested; Involuntary Termination within 12 months after CiC",
                            "shares_issued": "100000",
                            "single_trigger": "100%; all times after CiC",
                            "vesting_commencement_date": "2021-09-23",
                            "vesting_schedule": "Fully Vested",
                            "stockholder_id": 4,
                        }
                    },
                    {
                        "vesting_schedule": {
                            "consideration": "IP",
                            "double_trigger": "100% of unvested; Involuntary Termination within 12 months after CiC",
                            "shares_issued": "100000",
                            "single_trigger": "100%; all times after CiC",
                            "vesting_commencement_date": "2021-09-23",
                            "vesting_schedule": "4yr with 1yr Cliff",
                            "stockholder_id": 5,
                        }
                    },
                ],
            )

    def test_vesting_enums_to_ocf_schedule(self):
        with open(fixture_dir / "ce_datasheet_five_stockholders.json") as ce_data:
            datasheet_items: list[ContractExpressVarObj] = json.loads(ce_data.read())

            ce_to_vesting_enums_datamap = load_vesting_schedule_driving_enums_datamap()

            # Want to clear any post processors from relevant datamaps
            RepeatableVestingScheduleDriversDataMap.clear_handlers()
            VestingScheduleInputsDataMap.clear_handlers()

            # Then we want to register a post processor for vesting_schedule to map to ocf and another for our
            # usual Gunderson repeat variables
            RepeatableVestingScheduleDriversDataMap.register_handlers(
                {"repeated_variables": gunderson_repeat_var_processor}
            )
            VestingScheduleInputsDataMap.register_handlers(
                {"vesting_schedule": generate_ocf_vesting_schedule_from_vesting_drivers}
            )

            vesting_schedule_ocf = traverse_datamap(
                ce_to_vesting_enums_datamap,
                None,
                datasheet_items,
                value_overrides={"PARSER_VERSION": GD_PARSER_VERSION},
                fail_on_missing_variable=False,
                drop_null_leaves=True,
            )
            logger.debug(f"Vesting ocf:\n{json.dumps(vesting_schedule_ocf, indent=2)}")
