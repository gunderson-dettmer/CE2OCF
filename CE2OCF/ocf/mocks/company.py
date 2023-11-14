import random

from faker import Faker

from CE2OCF.types.enums import CommonCityEnum, RegisteredAgentsEnum
from CE2OCF.types.models import Company, Director

fake = Faker()


def fake_phone_number() -> str:
    """
    Generates a valid US phone number with the international calling code.

    The format is +1 (XXX) XXX-XXXX, with the following rules for the area code:
    1. The first digit cannot be 0 or 1.
    2. The second digit cannot be 9.
    3. The second and third digits cannot both be 0.

    Returns:
        str: A valid US phone number with international calling code.
    """
    # Define the range for the first digit of area code (2-9)
    first_digit = random.randint(2, 9)

    # Define the range for the second and third digits of area code
    # The second digit cannot be 9, and the (second, third) cannot be (0, 0)
    while True:
        second_digit = random.randint(0, 8)
        third_digit = random.randint(0, 9)
        if not (second_digit == 0 and third_digit == 0):
            break

    # Generate the seven digits following the area code
    # The first digit of these seven digits cannot be 0 or 1 either.
    second_set_first_digit = random.randint(2, 9)
    remaining_six_digits = random.randint(0, 999999)

    # Combine all parts to create the phone number
    phone_number = f"+1 ({first_digit}{second_digit}{third_digit}) {second_set_first_digit}{remaining_six_digits:06d}"
    return phone_number


def mock_company() -> Company:
    return Company(
        CompanyName=fake.company(),
        CompanyShortName=fake.company_suffix(),
        PricePerShare=round(random.uniform(0.10, 3.00), 2),
        DateBlank=fake.date(),
        ClientMatterNumber=fake.random_int(min=1, max=999),
        CompanyPhoneNumber=fake_phone_number(),
        CompanyCity=fake.city(),
        CompanyCounty=fake.state_abbr(include_territories=False, include_freely_associated_states=False),
        CompanyZip=fake.zipcode(),
        CompanyFaxNumber=fake_phone_number(),
        CFOTreasurer=fake.name(),
        CEO=fake.name(),
        FFPreferred=fake.boolean(),
        FFPreferredPricePerShare=round(random.uniform(0.10, 3.00), 2),
        FFPreferredSharesAuthorized=fake.random_int(min=1000, max=9999),
        FirstDateWagesPaid=fake.date(),
        Form941Or944=fake.boolean(),
        GDIncorporator=fake.boolean(),
        GDOffice=random.choice(list(CommonCityEnum)),
        GoverningLaw=fake.state_abbr(include_territories=False, include_freely_associated_states=False),
        IPFormsOffice=random.choice(list(CommonCityEnum)),
        NumberAnticipatedEmployees=fake.random_int(min=10, max=100),
        NumberDirectors=fake.random_int(min=1, max=10),
        NumberStockholders=fake.random_int(min=1, max=10),
        OperationState=fake.state_abbr(include_territories=False, include_freely_associated_states=False),
        ParValue=float(fake.random_number(digits=3)) / 100000,
        President=fake.name(),
        PrincipalBusinessActivity=fake.sentence(),
        ResponsibleParty=fake.name(),
        ResponsiblePartySSN=fake.ssn(),
        ResponsiblePartyTitle=fake.job(),
        RASelect=random.choice(list(RegisteredAgentsEnum)),
        Secretary=fake.name(),
        SharesAuthorized=fake.random_int(min=1000, max=9999),
        SharesReservedStockPlan=fake.random_int(min=1000, max=9999),
        SoleIncorporator=fake.name(),
        SOPYear=fake.year(),
        StockPlan=fake.boolean(),
        DescriptionServicesProvided=fake.sentence(),
        CompanyState=fake.state_abbr(include_territories=False, include_freely_associated_states=False),
        CompanyStreet=fake.street_address(),
        EDGAR=fake.random_int(),
        EIN=fake.ssn(),
    )


def mock_director() -> Director:
    return Director(DirectorName=fake.name())
