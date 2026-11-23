from pydantic import BaseModel, ConfigDict, Field


class CreateItem___feature__(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=120)


class Item___feature__(CreateItem___feature__):
    id: str


# Keep feature-local imports stable while OpenAPI uses the qualified class names.
CreateItem = CreateItem___feature__
Item = Item___feature__
