"""
Pydantic Models Representing the Fields in a GD Incorporation Questionnaire, grouped by object. In use in tests and
mock data generator primarily.

Some notes
----------------------------------------------------------------------------------------------------------------------
1. Appears that, if you had previously answered a question for a given stockholder - e.g. Paid With for stockholders
   2 - 4, and THEN you make that a repeated value... the old values remain BUT a property "relevant" with value
   "false" is added.
2. If you suddenly remove the StockholderInfoSame value for a given field - like PaidWith - and there is
   no value for applicable stockholders for that field, you see the property Known="false" and there is no <Value/>
   child
"""
import uuid
from typing import Optional

from pydantic import BaseModel, Field

from CE2OCF.types.enums import (
    DoubleTriggerTypesEnum,
    PaidWithOptionsEnum,
    RegisteredAgentsEnum,
    SingleTriggerTypesEnum,
    VestingTypesEnum,
)


class Stockholder(BaseModel):
    id: str
    DoubleTrigger: DoubleTriggerTypesEnum
    # our answer will appear below the general description entered above. If no additional language is necessary,
    # skip this field
    DescriptionAssignedTechnology: Optional[str]
    # The description should provide clarity regarding exactly what property is being transferred while being neither
    # too narrow nor too broad.
    BroadDescriptionAssignedTechnology: str
    EmailAddress: str
    FFPreferredShares: Optional[
        int
    ] = None  # If founder preferred is authorized for company AND we want to give this stockholder some,
    # how many shares do they get?
    PaidWith: PaidWithOptionsEnum
    PhoneNumber: str
    SingleTrigger: SingleTriggerTypesEnum
    Shares: int
    SSN: str
    Stockholder: str = Field(
        default_factory=lambda: uuid.uuid4().__str__()
    )  # Name of stockholder goes here BUT we're using uuid to be able filter objs by name and have guaranteed
    # uniques. Required for tests.
    StockholderCity: str
    StockholderState: str
    StockholderStreet: str
    StockholderZip: str
    VCD: str
    Vesting: VestingTypesEnum


class Company(BaseModel):
    CompanyName: str
    CompanyShortName: str
    PricePerShare: float = Field(..., ge=0.10, le=3.00, decimals=2)
    DateBlank: str
    ClientMatterNumber: int
    CompanyPhoneNumber: str
    CompanyCity: str
    CompanyCounty: str
    CompanyZip: str
    CompanyFaxNumber: str
    CFOTreasurer: str
    CEO: str
    FFPreferred: bool  # Should we create and authorize Founder Preferred stock?
    FFPreferredPricePerShare: Optional[float] = None  # IF FFPreferred is true, what's price per share
    FFPreferredSharesAuthorized: Optional[int] = None  # IF FFPreferred is true, what's total # of shares
    FirstDateWagesPaid: str  # Format YYYY-MM-DD
    Form941Or944: bool
    GDIncorporator: bool  # Who was the GD incorporator (name)
    GDOffice: str  # Which office was this client from
    GoverningLaw: str  # Which U.S. State's law governs
    IPFormsOffice: str
    NumberAnticipatedEmployees: int
    NumberDirectors: int  # How many directors are there? We'll need to generate a director object for each
    NumberStockholders: int  # How many stockholders should we generate - generate objets for as many as is specified
    OperationState: str  # What state does the company operate in primarily?
    ParValue: float  # What is the Par Value for the Stock? Typically this is $0.0001 or $0.001
    President: str  # Who is the president of the company?
    PrincipalBusinessActivity: str  # What does the company do?
    ResponsibleParty: str  # What is the name of the person responsible for the companyt
    ResponsiblePartySSN: str  # What is the SSN of the person responsible for company
    ResponsiblePartyTitle: str  # Which officer is responsible for the company incorporation
    RASelect: RegisteredAgentsEnum
    Secretary: str  # Who is the company secretary?
    SharesAuthorized: int  # This must be greater than the options, common stock and founder preferred.
    SharesReservedStockPlan: int  # IF StockPlan is true, how many share are reserved?
    SoleIncorporator: str
    SOPYear: str  # If StockPlan is true, what is the year YYYY-MM-DD
    StockPlan: bool
    DescriptionServicesProvided: str
    CompanyState: str
    CompanyStreet: str
    EDGAR: str  # EDGAR ID #
    EIN: str  # Company EIN for EDGAR filings


class Designee(BaseModel):
    Designee: str
    DesigneeFaxNumber: str
    DesigneePhoneNumber: str
    DesigneeTitle: str


class BylawVars(BaseModel):
    RoFR: bool  # Include a standard Right of First Refusal in the bylaws?
    QuasiCA: bool  # any possibility that the Company is or could become a Quasi-California company?
    TransferRestrictions: bool  # Include Transfer Restrictions in the Bylaws?
    TransferRestrictionsLanguage: bool  # Include lang ref these transfer restrictions in the Founder SPA?
    TransferRestrictionDate: bool  # Include exact date to impose transfer restrictions on Shares?
    TransferRestrictionStock: str
    TransferDate: Optional[str]  # This is only included if TransferRestrictionDate is True and is format YYYY-MM-DD
    DirectListingTransfer: bool  # Do the stock transfer restrictions terminate upon a direct listing?
    #  Do the transfer restrictions apply to common stock or all stock?


class FormVars(BaseModel):
    StockholderInfoSame: list[
        str
    ]  # This is a weird field... if this is present, has a comma separated lits of var names to automatically use
    # the _S1 value.
    UsingTopTemplateFlag: bool
    UsingTopTemplateFlagFO_IAL: str  # Not sure what this is
    UsingTopTemplateFlag_IA: str  # Not sure what this is
    Waiver220: bool  # Include waiver of statutory information rights under DGCL Section 220?
    IndemnificationAgrIncluded: bool  # include an indemnification agreement?
    EmployeeNoncompete: bool


class Director(BaseModel):
    DirectorName: str
