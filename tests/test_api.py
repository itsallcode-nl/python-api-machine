from unittest.mock import MagicMock

from api_machine.service import Service, InputMessage
from api_machine.entity import Entity
from api_machine.lifecycle import CrudLifeCycle
from api_machine.schema import dataclass, field


@dataclass
class ArticleSchema:
    id: str
    subject: str
    content: str = field(default="some content")

repo = MagicMock()
repo.insert = lambda p: p

article_entity = Entity(
    name="Article",
    schema=ArticleSchema,
    lifecycle=CrudLifeCycle,
    mutable={'content', 'subject'},
    private={'created_at'}
)


def test_api():
    service = Service("TestApp")
    service.mount_entity(article_entity, repo)

    result = service(InputMessage(
        ref='TestApp:Article:command:create',
        payload={
            'id': 'articleid1',
            'subject': 'test subject'
        }
    ))
    created_instance = result.payload
    assert created_instance == {
        'id': 'articleid1',
        'subject': 'test subject',
        'content': 'some content',
        '__version__': 0
    }
