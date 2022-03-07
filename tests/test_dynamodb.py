from dataclasses import dataclass, asdict
from moto import mock_dynamodb2 as mock_dynamodb

from api_machine.storage.dynamodb import DynamoTable, DynamoRepository


@mock_dynamodb
def test_list_over_limit():
    t = DynamoTable(
        name="test", pk="pk", sk="sk", dk="dk",
        schema={'pk': 'pk', 'sk': 'sk', 'dk': 'dk'},
        components=[]
    )
    repo = DynamoRepository(config=DynamoRepository.Config(source=t))

    repo.create_table()

    for i in range(100):
        repo.insert({'pk': "1", 'sk': str(i)})

    r = repo.list("pk=:pk", params={'pk': "1"}, limit=10)
    assert len(r.items) == 10
    assert r.next_cursor is not None

    r = repo.list("pk=:pk", params={'pk': "1"}, limit=10, cursor=r.next_cursor)

    assert len(r.items) == 10
    assert r.next_cursor is not None
