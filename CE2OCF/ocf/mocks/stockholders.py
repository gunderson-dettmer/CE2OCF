import random
import uuid

from faker import Faker

from CE2OCF.ocf.mocks.company import fake_phone_number
from CE2OCF.types.enums import (
    DoubleTriggerTypesEnum,
    PaidWithOptionsEnum,
    SingleTriggerTypesEnum,
    VestingTypesEnum,
)
from CE2OCF.types.models import Stockholder

fake = Faker()


def sum_shares(stockholder_list: list[Stockholder]) -> tuple[int, int]:
    total_FFPreferredShares = 0
    total_Shares = 0

    for stockholder in stockholder_list:
        if stockholder.FFPreferredShares is not None:
            total_FFPreferredShares += stockholder.FFPreferredShares
        if stockholder.Shares is not None:
            total_Shares += stockholder.Shares  # if Shares are floats, replace with `float(stockholder.Shares)`

    return total_FFPreferredShares, total_Shares


def mock_stockholder() -> Stockholder:
    return Stockholder(
        id=uuid.uuid4().__str__(),
        DoubleTrigger=random.choice(list(DoubleTriggerTypesEnum)),
        DescriptionAssignedTechnology=fake.sentence(),
        BroadDescriptionAssignedTechnology=fake.sentence(),
        EmailAddress=fake.email(),
        FFPreferredShares=fake.random_int(min=0, max=1000),
        PaidWith=random.choice(list(PaidWithOptionsEnum)),
        PhoneNumber=fake_phone_number(),
        SingleTrigger=random.choice(list(SingleTriggerTypesEnum)),
        Shares=fake.random_int(min=0, max=1000),
        SSN=fake.ssn(),
        Stockholder=fake.name(),
        StockholderCity=fake.city(),
        StockholderState=fake.state_abbr(include_territories=False, include_freely_associated_states=False),
        StockholderStreet=fake.street_address(),
        StockholderZip=fake.zipcode(),
        VCD=fake.word(),
        Vesting=random.choice(list(VestingTypesEnum)),
    )
