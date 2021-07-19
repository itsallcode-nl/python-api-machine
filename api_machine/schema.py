from dataclasses import make_dataclass

from pydantic import create_model, ValidationError
from pydantic.dataclasses import dataclass


def dataclass_to_model(dc):
    return dataclass(dc)


def extract_schema(name, entity, include=None):
    return dataclass(
        make_dataclass(
            name,
            entity.fields(include, aslist=True)
        )
    )
