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


class NasaCachedListResponse(BaseModel):
    source: str
    nocache: bool = False
    cached: bool
    cache_date: str
    data: list[dict[str, Any]] = Field(default_factory=list)


class NasaCachedObjectResponse(BaseModel):
    source: str
    nocache: bool = False
    cached: bool
    cache_date: str
    data: dict[str, Any] = Field(default_factory=dict)
