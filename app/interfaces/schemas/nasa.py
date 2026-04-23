from typing import Any

from pydantic import BaseModel, Field


class NasaListResponse(BaseModel):
    source: str
    nocache: bool = True
    data: list[dict[str, Any]] = Field(default_factory=list)


class NasaObjectResponse(BaseModel):
    source: str
    nocache: bool = True
    data: dict[str, Any] = Field(default_factory=dict)
