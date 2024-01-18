import uuid
from datetime import datetime, timezone
from typing import Optional, Union

from pydantic import BaseModel, Field

from CE2OCF.datamap import (
    FieldPostProcessorModel,
    OverridableBoolField,
    OverridableStringField,
    RepeatableDataMap,
)


class CurrencyDatamap(BaseModel):
    amount: Union[str, OverridableStringField]
    currency: Union[str, OverridableStringField]


class RatioDatamap(BaseModel):
    numerator: Union[str, OverridableStringField]
    denominator: Union[str, OverridableStringField]


class AddressDataMap(FieldPostProcessorModel):
    address_type: Union[str, OverridableStringField] = Field(
        default_factory=lambda: {"static": "CONTACT"}
    )  # Default that works for a lot of situations (not all, obv)
    street_suite: Union[str, OverridableStringField]
    city: Union[str, OverridableStringField]
    country_subdivision: Union[str, OverridableStringField]
    country: Union[str, OverridableStringField] = Field(
        default_factory=lambda: {"static": "US"}
    )  # Default that works for a lot of situations (not all, obv)
    postal_code: Union[str, OverridableStringField]


class PhoneDataMap(FieldPostProcessorModel):
    phone_type: Union[str, OverridableStringField]
    phone_number: Union[str, OverridableStringField]


class IssuerDataMap(FieldPostProcessorModel):
    id: Union[str, OverridableStringField] = Field(default_factory=lambda: {"static": uuid.uuid4().__str__()})
    legal_name: Union[str, OverridableStringField]
    dba: Union[str, OverridableStringField]
    country_of_formation: Union[str, OverridableStringField]
    country_subdivision_of_formation: Union[str, OverridableStringField]
    formation_date: Union[str, OverridableStringField] = Field(
        default_factory=lambda: {"static": datetime.now(timezone.utc).date().isoformat()}
    )
    object_type: OverridableStringField = Field(default_factory=lambda: {"static": "ISSUER"})
    tax_ids: Optional[list[Union[str, OverridableStringField]]]
    address: AddressDataMap
    phone: Optional[PhoneDataMap]
    comments: list[Union[str, OverridableStringField]]


class StockholderInfoDataMap(BaseModel):
    legal_name: Union[str, OverridableStringField]


class StockholderAddrDataMap(BaseModel):
    city: str
    country_subdivision: str
    street_suite: str
    postal_code: str


class VestingDrivingEnumsDataMap(BaseModel):
    single_trigger: str
    double_trigger: str
    shares_issued: str
    consideration: str
    vesting_schedule: str
    vesting_commencement_date: str
    stockholder_id: str


class StockholderPreferredIssuancesDataMap(BaseModel):
    shares_issued: str


class StockholderEmailDataMap(BaseModel):
    email_type: Union[str, OverridableStringField] = Field(default_factory=lambda: {"static": "PERSONAL"})
    email_address: Union[str, OverridableStringField]


class StockholderPrimaryContact(BaseModel):
    name: StockholderInfoDataMap
    emails: list[StockholderEmailDataMap]
    phone_numbers: list[PhoneDataMap]


class StockholderDataMap(FieldPostProcessorModel):
    id: Union[str, OverridableStringField] = Field(default_factory=lambda: {"static": uuid.uuid4().__str__()})
    object_type: OverridableStringField = Field(default_factory=lambda: {"static": "STAKEHOLDER"})
    name: StockholderInfoDataMap
    stakeholder_type: OverridableStringField = Field(default_factory=lambda: {"static": "INDIVIDUAL"})
    issuer_assigned_id: Union[str, OverridableStringField]
    current_relationship: Union[str, OverridableStringField] = Field(default_factory=lambda: {"static": "FOUNDER"})
    primary_contact: StockholderPrimaryContact
    addresses: list[AddressDataMap]
    tax_ids: list = []
    comments: list[Union[str, OverridableStringField]]


class StockLegendDataMap(FieldPostProcessorModel):
    id: Union[str, OverridableStringField] = Field(default_factory=lambda: {"static": uuid.uuid4().__str__()})
    object_type: Union[str, OverridableStringField] = Field(default_factory=lambda: {"static": "STOCK_LEGEND_TEMPLATE"})
    comments: list[Union[str, OverridableStringField]]
    name: Union[str, OverridableStringField]
    text: Union[str, OverridableStringField]


class ConversionMechanismDataMap(BaseModel):
    type: Union[str, OverridableStringField]
    conversion_price: CurrencyDatamap
    rounding_type: Union[str, OverridableStringField]
    ratio: RatioDatamap


class ConversionRightsDataMap(BaseModel):
    converts_to_future_round: Union[str, OverridableBoolField]
    conversion_mechanism: ConversionMechanismDataMap


class StockClassDataMap(FieldPostProcessorModel):
    id: Union[str, OverridableStringField] = Field(default_factory=lambda: {"static": uuid.uuid4().__str__()})
    name: Union[str, OverridableStringField]
    object_type: OverridableStringField = Field(default_factory=lambda: {"static": "STOCK_CLASS"})
    class_type: OverridableStringField
    default_id_prefix: Union[str, OverridableStringField]
    initial_shares_authorized: Union[str, OverridableStringField]
    board_approval_date: Union[str, OverridableStringField] = Field(
        default_factory=lambda: {"static": datetime.now(timezone.utc).date().isoformat()}
    )
    votes_per_share: Union[str, OverridableStringField]
    par_value: CurrencyDatamap
    price_per_share: CurrencyDatamap
    seniority: Union[str, OverridableStringField]
    conversion_rights: list[ConversionRightsDataMap]
    liquidation_preference_multiple: Union[str, OverridableStringField]
    participation_cap_multiple: Union[str, OverridableStringField]
    comments: list[Union[str, OverridableStringField]]


class StockClassesDataMap(BaseModel):
    common_data_map: StockClassDataMap
    founder_preferred_data_map: Optional[StockClassDataMap] = None


class StockPlanDataMap(FieldPostProcessorModel):
    id: Union[str, OverridableStringField] = Field(default_factory=lambda: {"static": uuid.uuid4().__str__()})
    object_type: Union[str, OverridableStringField] = Field(default_factory=lambda: {"static": "STOCK_PLAN"})
    plan_name: Union[
        str, OverridableStringField
    ]  # We actually don't get plan name but year, so we need a post-processor
    stock_class_id: Union[str, OverridableStringField]
    board_approval_date: Union[str, OverridableStringField] = Field(
        default_factory=lambda: {"static": datetime.now(timezone.utc).date().isoformat()}
    )
    stockholder_approval_date: Union[str, OverridableStringField] = Field(
        default_factory=lambda: {"static": datetime.now(timezone.utc).date().isoformat()}
    )
    initial_shares_reserved: Union[str, OverridableStringField]
    comments: list[Union[str, OverridableStringField]]


class SecurityLawExemptionMap(FieldPostProcessorModel):
    jurisdiction: Union[str, OverridableStringField]
    description: Union[str, OverridableStringField]


class VestingStockIssuanceDataMap(FieldPostProcessorModel):
    id: Union[str, OverridableStringField] = Field(default_factory=lambda: {"static": uuid.uuid4().__str__()})
    date: Union[str, OverridableStringField] = Field(
        default_factory=lambda: {"static": datetime.now(timezone.utc).date().isoformat()}
    )
    object_type: Union[str, OverridableStringField] = Field(default_factory=lambda: {"static": "TX_STOCK_ISSUANCE"})
    security_id: Union[str, OverridableStringField] = Field(default_factory=lambda: {"static": uuid.uuid4().__str__()})
    custom_id: Union[str, OverridableStringField]
    comments: list[Union[str, OverridableStringField]]
    stakeholder_id: Union[str, OverridableStringField]
    board_approval_date: Union[str, OverridableStringField] = Field(
        default_factory=lambda: {"static": datetime.now(timezone.utc).date().isoformat()}
    )
    consideration_text: Union[str, OverridableStringField]
    security_law_exemptions: list[SecurityLawExemptionMap] = []
    stock_class_id: Union[str, OverridableStringField]
    share_price: CurrencyDatamap
    quantity: Union[str, OverridableStringField]
    cost_basis: CurrencyDatamap
    stock_legend_ids: list[Union[str, OverridableStringField]]
    vesting_terms_id: Optional[Union[str, OverridableStringField]]


class FullyVestedStockIssuanceDataMap(FieldPostProcessorModel):
    id: Union[str, OverridableStringField] = Field(default_factory=lambda: {"static": uuid.uuid4().__str__()})
    date: Union[str, OverridableStringField] = Field(
        default_factory=lambda: {"static": datetime.now(timezone.utc).date().isoformat()}
    )
    object_type: Union[str, OverridableStringField] = Field(default_factory=lambda: {"static": "TX_STOCK_ISSUANCE"})
    security_id: Union[str, OverridableStringField] = Field(default_factory=lambda: {"static": uuid.uuid4().__str__()})
    custom_id: Union[str, OverridableStringField]
    comments: list[Union[str, OverridableStringField]]
    stakeholder_id: Union[str, OverridableStringField]
    board_approval_date: Union[str, OverridableStringField] = Field(
        default_factory=lambda: {"static": datetime.now(timezone.utc).date().isoformat()}
    )
    consideration_text: Union[str, OverridableStringField]
    security_law_exemptions: list[SecurityLawExemptionMap] = []
    stock_class_id: Union[str, OverridableStringField]
    share_price: CurrencyDatamap
    quantity: Union[str, OverridableStringField]
    cost_basis: CurrencyDatamap
    stock_legend_ids: list[Union[str, OverridableStringField]]


class VestingEventsInputsDataMap(FieldPostProcessorModel):
    """
    This is the same as VestingScheduleInputsDataMap BUT the different class definitions let us register
    different post-processors have fewer worries that someone forgets to register and/or de-register post-processors
    """

    vesting_schedule: VestingDrivingEnumsDataMap


class VestingScheduleInputsDataMap(FieldPostProcessorModel):
    """
    This is the same as VestingEventsInputsDataMap BUT the different class definitions let us register
    different post-processors have fewer worries that someone forgets to register and/or de-register post-processors
    """

    vesting_schedule: VestingDrivingEnumsDataMap


class RepeatableVestingEventDriversDataMap(RepeatableDataMap):
    repeated_pattern = VestingEventsInputsDataMap


class RepeatableVestingScheduleDriversDataMap(RepeatableDataMap):
    repeated_pattern: VestingScheduleInputsDataMap


class RepeatableStockholderDataMap(RepeatableDataMap):
    repeated_pattern: StockholderDataMap


class RepeatableFullyVestedStockIssuanceDataMap(RepeatableDataMap):
    repeated_pattern: FullyVestedStockIssuanceDataMap


class RepeatableVestingStockIssuanceDataMap(RepeatableDataMap):
    repeated_pattern: VestingStockIssuanceDataMap
