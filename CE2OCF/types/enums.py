import enum


class OcfVestingDayOfMonthEnum(str, enum.Enum):
    ONE = "01"
    TWO = "02"
    THREE = "03"
    FOUR = "04"
    FIVE = "05"
    SIX = "06"
    SEVEN = "07"
    EIGHT = "08"
    NINE = "09"
    TEN = "10"
    ELEVEN = "11"
    TWELVE = "12"
    THIRTEEN = "13"
    FOURTEEN = "14"
    FIFTEEN = "15"
    SIXTEEN = "16"
    SEVENTEEN = "17"
    EIGHTEEN = "18"
    NINETEEN = "19"
    TWENTY = "20"
    TWENTY_ONE = "21"
    TWENTY_TWO = "22"
    TWENTY_THREE = "23"
    TWENTY_FOUR = "24"
    TWENTY_FIVE = "25"
    TWENTY_SIX = "26"
    TWENTY_SEVEN = "27"
    TWENTY_EIGHT = "28"
    TWENTY_NINE_OR_LAST_DAY_OF_MONTH = "29_OR_LAST_DAY_OF_MONTH"
    THIRTY_OR_LAST_DAY_OF_MONTH = "30_OR_LAST_DAY_OF_MONTH"
    THIRTY_ONE_OR_LAST_DATA_OF_MONTH = "31_OR_LAST_DAY_OF_MONTH"
    VESTING_START_DAY_OR_LAST_DAY_OF_MONTH = "VESTING_START_DAY_OR_LAST_DAY_OF_MONTH"


class OcfPeriodTypeEnum(str, enum.Enum):
    DAYS = "DAYS"
    MONTHS = "MONTHS"
    YEARS = "YEARS"


class SingleTriggerTypesEnum(str, enum.Enum):
    NA = "N/A"
    SIX_MONTHS_ALL_TIMES = "6 months; all times after CiC"
    TWELVE_MONTHS_ALL_TIMES = "12 months; all times after CiC"
    TWENTY_FOUR_MONTHS_ALL_TIMES = "24 months; all times after CiC"
    ONE_HUNDRED_PERCENT_ALL_TIMES = "100%; all times after CiC"
    SIX_MONTHS_INVOLUNTARY_TERMINATION = "6 months; Involuntary Termination"
    TWELVE_MONTHS_INVOLUNTARY_TERMINATION = "12 months; Involuntary Termination"
    TWENTY_FOUR_MONTHS_INVOLUNTARY_TERMINATION = "24 months; Involuntary Termination"
    ONE_HUNDRED_PERCENT_INVOLUNTARY_TERMINATION = "100%; Involuntary Termination"
    CUSTOM = "Custom"


class DoubleTriggerTypesEnum(str, enum.Enum):
    NA = "N/A"
    TWENTY_FIVE_PERCENT_12_MONTHS = "25% of unvested; Involuntary Termination within 12 months after CiC"
    FIFTY_PERCENT_12_MONTHS = "50% of unvested; Involuntary Termination within 12 months after CiC"
    ONE_HUNDRED_PERCENT_12_MONTHS = "100% of unvested; Involuntary Termination within 12 months after CiC"
    TWENTY_FIVE_PERCENT_ANY_TIME = "25% of unvested; Involuntary Termination any time after CiC"
    FIFTY_PERCENT_ANY_TIME = "50% of unvested; Involuntary Termination any time after CiC"
    ONE_HUNDRED_PERCENT_ANY_TIME = "100% of unvested; Involuntary Termination any time after CiC"
    CUSTOM = "Custom"


class VestingTypesEnum(str, enum.Enum):
    FOUR_YR_1_YR_CLIFF = "4yr with 1yr Cliff"
    FOUR_YR_NO_CLIFF = "4yr with no Cliff"
    FULLY_VESTED = "Fully Vested"
    CUSTOM = "Custom"  # We're not going to support this via OCF


class PaidWithOptionsEnum(str, enum.Enum):
    IP = "IP"
    CASH = "Cash"


class RegisteredAgentsEnum(str, enum.Enum):
    CSC = "Corporation Service Company"
    IS = "Incorporating Services, Ltd"
    CTC = "The Corporation Trust Company"
    COGENCY = "Cogency Global Inc."
    SINGLE_FILE = "SingleFile"
    OTHER = "Other"


class RepeatableFields(enum.Enum):
    """
    Some stockholder fields can be set on the first stockholder and then repeated for all four.
    This is an enum that covers all such fields.
    """

    PAID_WITH = "PaidWith"
    VESTING_SCHEDULE = "Vesting"
    VCD = "VCD"
    SINGLE_TRIGGER_ACCEL = "SingleTrigger"
    DOUBLE_TRIGGER = "DoubleTrigger"
    COMPANY_DESCRIPTION = "BroadDescriptionAssignedTechnology"  # Not sure why each shareholder has a broad and
    # narrow description, honestly.
    ASSIGNED_TECHNOLOGY = "DescriptionAssignedTechnology"
    # ALL = "All"  # If this is selected, all values of this enum are assigned as <Value> child tags to applicable
    # variable... so it's not actually a value


# Lets us map from the enum values in the template to specify which repeatable fields to repeat.
# TODO - GD-specific values. Remove
map_repeat_variable_names_to_template_choices = {
    "PaidWith": "Paid With",
    "Vesting": "Vesting Schedule",
    "VCD": "Vesting Commencement Date",
    "SingleTrigger": "Single Trigger Acceleration Provision",
    "DoubleTrigger": "Double Trigger Acceleration Provision",
    "BroadDescriptionAssignedTechnology": "Genus-level Description of Company Project",
    "All": "All",
    "DescriptionAssignedTechnology": "Specific Description of Assigned Technology",
}


class CommonCityEnum(str, enum.Enum):
    ANN_ARBOR = "Ann Arbor"
    AUSTIN = "Austin"
    BEIJING = "Beijing"
    BOSTON = "Boston"
    LOS_ANGELES = "Los Angeles"
    NEW_YORK = "New York"
    SAN_DIEGO = "San Diego"
    SAN_FRANCISCO = "San Francisco"
    SAO_PAULO = "São Paulo"
    SILICON_VALLEY = "Silicon Valley"
    SINGAPORE = "Singapore"


class TransferRestrictionEnum(str, enum.Enum):
    ALL_STOCK = "All Stock"
    COMMON_STOCK = (
        "Common Stock (will exclude Common stock issued upon conversion of Preferred Stock, "
        "and if applicable, Founder Preferred Stock) "
    )
