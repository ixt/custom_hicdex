# generated by datamodel-codegen:
#   filename:  storage.json

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Extra


class Key(BaseModel):
    class Config:
        extra = Extra.forbid

    address: str
    id: str


class Report(BaseModel):
    class Config:
        extra = Extra.forbid

    key: Key
    value: bool


class FxhashModerationStorage(BaseModel):
    class Config:
        extra = Extra.forbid

    admin: str
    metadata: Dict[str, str]
    moderated: Dict[str, str]
    moderators: Dict[str, bool]
    reports: List[Report]