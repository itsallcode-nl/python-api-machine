from dataclasses import dataclass, asdict
import typing

from . import exc
from .lifecycle import Transition
from .entity import Entity, InputMessage, Message
from .schema import (
    extract_schema, dataclass_to_model, ValidationError
)


@dataclass
class OperationContext:
    service: object
    repository: object
    entity: Entity

    def create(self, values):
        instance = self.entity.create(values)
        return self.repository.create(
            instance.dict()
        )

    def get(self, key):
        return self.entity.create(
            self.repository.get(key)
        )

    def update(self, key, instance, values):
        new_instance = self.entity.update(instance, values)
        return self.repository.update(
            key, new_instance.dict()
        )

    def list(self, payload):
        list_params = asdict(payload)
        return self.repository.list(
            list_params.pop('expr'),
            **list_params['params']
        ).serialize()


@dataclass
class Operation:
    action: str
    entity: Entity
    input_model: object
    private_model: object = None
    output_model: object = None
    __action_type__ = None

    @property
    def ref(self):
        return ":".join([
            self.entity.name, self.__action_type__,
            self.action
        ])

    def create_context(self, service):
        repo = service.repos[self.entity.name]
        return OperationContext(
            service,
            repo, self.entity
        )

    @staticmethod
    def name(action, entity):
        return "".join(c.capitalize() for c in [
            action, entity.name
        ])

    @classmethod
    def create(cls, action, entity):
        fields = cls.get_fields(
            entity
        )
        input_fields = fields - entity.private
        name = cls.name(action, entity)
        return cls(
            action, entity,
            input_model=extract_schema(name, entity, input_fields),
            private_model=extract_schema(name, entity, fields),
            output_model=entity.schema
        )

    @classmethod
    def get_fields(cls, entity):
        return entity.fields()

    def deserialize(self, payload):
        try:
            obj = self.input_model(**payload)
        except ValidationError:
            raise exc.ValidationError

        if self.private_model:
            return self.private_model(**asdict(obj))
        return obj

    def get_primary_key(self, payload):
        return [
            getattr(payload, k) for k in self.entity.key
        ]

    def __call__(self, context: OperationContext, msg: InputMessage):
        msg = Message(
            ref=self.ref,
            payload=self.deserialize(msg.payload),
        )
        return self.execute(context, msg)


class Mutation(Operation):
    __action_type__ = "command"


class Query(Operation):
    __action_type__ = "query"


class CreateOperation(Mutation):
    __action_type__ = "command"

    def execute(self, msg):
        self.entity.lifecycle.do(
            None, self.action
        )
        return self.context.create(msg.payload.dict())


class GetOperation(Query):
    @classmethod
    def get_fields(cls, entity):
        return entity.key

    def execute(self, context: OperationContext, msg):
        key = self.get_primary_key(msg.payload)
        return context.get(key)


class UpdateOperation(Mutation):
    @classmethod
    def get_fields(cls, entity):
        fields = super().get_fields(entity)
        return fields & entity.mutable

    def execute(self, context: OperationContext, msg):
        key = self.get_primary_key(msg.payload)
        instance = context.get(key)
        context.entity.set_status(instance, self.action)
        return context.update(key, instance, msg.payload.dict())


class ListOperation(Query):
    @classmethod
    def create(cls, action, entity):
        @dataclass
        class ListModel:
            expr: str = None
            params: dict = None

        @dataclass
        class EntityList:
            items: typing.List[entity.schema]

        model = dataclass_to_model(ListModel)
        output_model = dataclass_to_model(EntityList)

        return cls(
            action, entity,
            input_model=model, private_model=model,
            output_model=output_model
        )

    def execute(self, context: OperationContext, msg):
        return context.list(msg.payload)


def action_to_operation(action: str):
    return {
        'create': CreateOperation,
        'update': UpdateOperation,
    }.get(action, UpdateOperation)


class OperationRegistry(dict):
    def append(self, operation: Operation):
        self[operation.ref] = operation


class Service:
    operations = None

    def __init__(self):
        self.operations = OperationRegistry()
        self.repos = {}

    def mount_entity(self, entity, repository):
        for transition in entity.lifecycle.transitions:
            operation_cls = action_to_operation(
                transition.action
            )
            operation = operation_cls.create(
                transition.action, entity
            )
            self.mount_operation(operation)

        self.mount_operation(
            GetOperation.create("get", entity)
        )
        self.mount_operation(
            ListOperation.create("list", entity)
        )
        self.repos[entity.name] = repository

    def mount_operation(self, operation: Operation):
        self.operations.append(operation)

    def __call__(self, msg: InputMessage):
        scoped_ref = ":".join(msg.ref.split(":")[1:])
        try:
            operation = self.operations[scoped_ref]
            context = operation.create_context(
                self
            )
            return operation(
                context,
                msg
            )
        except KeyError:
            raise exc.OperationDoesNotExist()
