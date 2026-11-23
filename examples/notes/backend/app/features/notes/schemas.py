from pydantic import BaseModel, ConfigDict, Field


class CreateItem(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=120)
    priority: int = Field(default=3, ge=1, le=5, strict=True)


class Item(CreateItem):
    id: str
