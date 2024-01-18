import logging
import unittest

from CE2OCF.datamap.loaders import (
    load_cic_event_definition,
    load_double_trigger_definitions,
    load_single_trigger_definitions,
)

logger = logging.getLogger(__name__)


class TestConfigLoaders(unittest.TestCase):
    def test_load_cic_definition(self):
        default_def = load_cic_event_definition()
        self.assertEqual(
            default_def,
            {
                "description": "Triggered on change in control. Meaning (i) the consummation of a merger or "
                "consolidation of the Company with or into another entity, (ii) the sale of all or "
                "substantially all of the assets of the Company, either in one transaction or a series "
                "of related transactions, or (iii) the dissolution, liquidation, or winding up of "
                "the Company. See the Stock Purchase Agreement for precise language and related terms.",
                "remainder": False,
                "portion_numerator": 0,
                "portion_denominator": 1,
            },
        )

    def test_load_single_trigger_definitions(self):
        default_def = load_single_trigger_definitions()
        self.assertEqual(
            default_def,
            {
                "N/A": None,
                "100%; all times after CiC": {
                    "description": "If the Company is subject to a Change in Control before the Purchaser's Service "
                    "terminates, then the Right of Repurchase shall lapse with respect to all "
                    "Restricted Shares.",
                    "remainder": True,
                    "portion_numerator": 1,
                    "portion_denominator": 1,
                },
                "100%; Involuntary Termination": {
                    "description": "If the Purchaser is subject to an Involuntary Termination at any time, then the "
                    "Right of Repurchase shall lapse with respect to all Restricted Shares.",
                    "remainder": True,
                    "portion_numerator": 1,
                    "portion_denominator": 1,
                },
                "6 months; all times after CiC": {
                    "description": "If the Company is subject to a Change in Control before the Purchaser's Service "
                    "terminates, at all times after the Change in Control, the vested portion of the "
                    "Restricted Shares shall be determined by adding 6 months to the Purchaser's "
                    "actual Service.",
                    "remainder": False,
                    "portion_numerator": 6,
                    "portion_denominator": 48,
                },
                "12 months; all times after CiC": {
                    "description": "If the Company is subject to a Change in Control before the Purchaser's "
                    "Service terminates, at all times after the Change in Control, the vested "
                    "portion of the Restricted Shares shall be determined by adding 12 months to the "
                    "Purchaser's actual Service.",
                    "remainder": False,
                    "portion_numerator": 12,
                    "portion_denominator": 48,
                },
                "24 months; all times after CiC": {
                    "description": "If the Company is subject to a Change in Control before the Purchaser's "
                    "Service terminates, at all times after the Change in Control, the vested portion "
                    "of the Restricted Shares shall be determined by adding 24 months to the "
                    "Purchaser's actual Service.",
                    "remainder": False,
                    "portion_numerator": 24,
                    "portion_denominator": 48,
                },
                "6 months; Involuntary Termination": {
                    "description": "If the Purchaser is subject to an Involuntary Termination at any time, "
                    "the vested portion of the Restricted Shares shall be determined by adding 6 "
                    "months to the Purchaser's actual Service",
                    "remainder": False,
                    "portion_numerator": 6,
                    "portion_denominator": 48,
                },
                "12 months; Involuntary Termination": {
                    "description": "If the Purchaser is subject to an Involuntary Termination at any time, "
                    "the vested portion of the Restricted Shares shall be determined by adding 12 "
                    "months to the Purchaser's actual Service",
                    "remainder": False,
                    "portion_numerator": 12,
                    "portion_denominator": 48,
                },
                "24 months; Involuntary Termination": {
                    "description": "If the Purchaser is subject to an Involuntary Termination at any time, the vested "
                    "portion of the Restricted Shares shall be determined by adding 24 months to the Purchaser's actual"
                    " Service",
                    "remainder": False,
                    "portion_numerator": 24,
                    "portion_denominator": 48,
                },
                "Custom": None,
            },
        )

    def test_load_double_trigger_definitions(self):
        default_def = load_double_trigger_definitions()
        self.assertEqual(
            default_def,
            {
                "N/A": None,
                "25% of unvested; Involuntary Termination within 12 months after CiC": {
                    "time_based_expiration_details": {
                        "time_units": "MONTHS",
                        "time_unit_quantity": 12,
                        "time_period_repetition": 1,
                        "remainder": True,
                        "portion_numerator": 0,
                        "portion_denominator": 1,
                    },
                    "termination_event_details": {
                        "description": "If the Purchaser is subject to an Involuntary Termination within 12 months "
                        "after the Change in Control, then the Right of Repurchase shall lapse with "
                        "respect to 25% of any remaining Restricted Shares.",
                        "remainder": True,
                        "portion_numerator": 1,
                        "portion_denominator": 4,
                    },
                },
                "50% of unvested; Involuntary Termination within 12 months after CiC": {
                    "time_based_expiration_details": {
                        "time_units": "MONTHS",
                        "time_unit_quantity": 12,
                        "time_period_repetition": 1,
                        "remainder": True,
                        "portion_numerator": 0,
                        "portion_denominator": 1,
                    },
                    "termination_event_details": {
                        "description": "If the Purchaser is subject to an Involuntary Termination within 12 months "
                        "after the Change in Control, then the Right of Repurchase shall lapse with "
                        "respect to 50% of any remaining Restricted Shares. ",
                        "remainder": True,
                        "portion_numerator": 1,
                        "portion_denominator": 2,
                    },
                },
                "100% of unvested; Involuntary Termination within 12 months after CiC": {
                    "time_based_expiration_details": {
                        "time_units": "MONTHS",
                        "time_unit_quantity": 12,
                        "time_period_repetition": 1,
                        "remainder": True,
                        "portion_numerator": 0,
                        "portion_denominator": 1,
                    },
                    "termination_event_details": {
                        "description": "If the Purchaser is subject to an Involuntary Termination within 12 months "
                        "after the Change in Control, then the Right of Repurchase shall lapse with "
                        "respect to 100% of any remaining Restricted Shares.",
                        "remainder": True,
                        "portion_numerator": 1,
                        "portion_denominator": 1,
                    },
                },
                "25% of unvested; Involuntary Termination any time after CiC": {
                    "time_based_expiration_details": None,
                    "termination_event_details": {
                        "description": "If the Purchaser is subject to an Involuntary Termination any time after the "
                        "Change in Control, then the Right of Repurchase shall lapse with respect to "
                        "25% of any remaining Restricted Shares.",
                        "remainder": True,
                        "portion_numerator": 1,
                        "portion_denominator": 4,
                    },
                },
                "50% of unvested; Involuntary Termination any time after CiC": {
                    "time_based_expiration_details": None,
                    "termination_event_details": {
                        "description": "If the Purchaser is subject to an Involuntary Termination any time after the "
                        "Change in Control, then the Right of Repurchase shall lapse with respect to "
                        "50% of any remaining Restricted Shares.",
                        "remainder": True,
                        "portion_numerator": 1,
                        "portion_denominator": 2,
                    },
                },
                "100% of unvested; Involuntary Termination any time after CiC": {
                    "time_based_expiration_details": None,
                    "termination_event_details": {
                        "description": "If the Purchaser is subject to an Involuntary Termination any time after the "
                        "Change in Control, then the Right of Repurchase shall lapse with respect to "
                        "100% of any remaining Restricted Shares.",
                        "remainder": True,
                        "portion_numerator": 1,
                        "portion_denominator": 1,
                    },
                },
            },
        )
