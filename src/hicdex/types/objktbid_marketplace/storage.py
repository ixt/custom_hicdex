# generated by datamodel-codegen:
#   filename:  storage.json

from __future__ import annotations

from typing import Dict

from pydantic import BaseModel, Extra


class Asks(BaseModel):
    class Config:
        extra = Extra.forbid

    amount: str
    artist: str
    fa2: str
    issuer: str
    objkt_id: str
    royalties: str
    xtz_per_objkt: str


class Bids(BaseModel):
    class Config:
        extra = Extra.forbid

    artist: str
    fa2: str
    issuer: str
    objkt_id: str
    royalties: str
    xtz_per_objkt: str


class ObjktbidMarketplaceStorage(BaseModel):
    class Config:
        extra = Extra.forbid

    admin: str
    ask_id: str
    asks: Dict[str, Asks]
    bid_id: str
    bids: Dict[str, Bids]
    management_fee: str
    metadata: Dict[str, str]