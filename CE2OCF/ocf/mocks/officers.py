from faker import Faker

from CE2OCF.types.models import Director

fake = Faker()


def mock_director() -> Director:
    return Director(DirectorName=fake.name())
