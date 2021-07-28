from dataclasses import make_dataclass, field, asdict
import json

from pydantic import create_model, ValidationError
from pydantic.dataclasses import dataclass


def dataclass_to_model(dc):
    return dataclass(dc)


def serialize(i):
    return json.loads(
        i.__pydantic_model__(**asdict(i)).json()
    )


def extract_schema(name, entity, include=None):
    fields = entity.fields(include, aslist=True)
    cls = type(
        name, (),
        dict((f[0], f[2]) for f in fields)
    )
    cls.__annotations__ = dict(
        (f[0], f[1]) for f in fields
    )
    return dataclass(cls)
