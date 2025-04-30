import humps
from pydantic import BaseModel, ConfigDict


def to_camel(string: str) -> str:
    return humps.camelize(string)


class BaseSchemaModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
