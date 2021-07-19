from dataclasses import dataclass, field, fields, make_dataclass

from .schema import dataclass_to_model
from .lifecycle import StateMachine


class InputMessageSchema:
    pass


@dataclass
class InputMessage:
    ref: str
    payload: object


class MessageSchema:
    pass


@dataclass
class Message:
    ref: str
    payload: object


class EntitySchema:
    pass


@dataclass
class Entity:
    name: str
    schema: object
    lifecycle: StateMachine
    mutable: set
    private: set

    key: list = field(default_factory=lambda: {'id'})
    indices: list = None

    def __post_init__(self):
        if isinstance(self.lifecycle, list):
            self.lifecycle = StateMachine(self.lifecycle)
        self.schema = dataclass_to_model(self.schema)

    def create(self, values: dict):
        return self.Schema(**values)

    def update(self, obj, values: dict):
        return obj.copy(update=values)

    def delete(self, obj):
        return obj

    def set_status(self, obj, action):
        if hasattr(obj, "status"):
            self.obj.status = self.lifecycle.do(
                self.obj.status, action
            ).target

    def fields(self, include=None, aslist=False):
        result = fields(self.schema)
        if include:
            result = [f for f in result if f.name in include]
        if aslist:
            return list(
                (f.name, f.type, f) for f in result
            )
        return set(
            f.name for f in result
        )
