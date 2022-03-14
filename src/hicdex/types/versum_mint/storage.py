# generated by datamodel-codegen:
#   filename:  storage.json

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Extra


class Key(BaseModel):
    class Config:
        extra = Extra.forbid

    address: str
    nat: str


class LedgerItem(BaseModel):
    class Config:
        extra = Extra.forbid

    key: Key
    value: str


class Key1(BaseModel):
    class Config:
        extra = Extra.forbid

    operator: str
    owner: str
    token_id: str


class Operator(BaseModel):
    class Config:
        extra = Extra.forbid

    key: Key1
    value: Dict[str, Any]


class Key2(BaseModel):
    class Config:
        extra = Extra.forbid

    cocreator: str
    token_id: str


class SignedCoCreatorshipItem(BaseModel):
    class Config:
        extra = Extra.forbid

    key: Key2
    value: Dict[str, Any]


class TokenIdAmount(BaseModel):
    class Config:
        extra = Extra.forbid

    amount: str
    token_id: str


class Infusion(BaseModel):
    class Config:
        extra = Extra.forbid

    token_address: str
    token_id_amounts: List[TokenIdAmount]


class Split(BaseModel):
    class Config:
        extra = Extra.forbid

    address: str
    pct: str


class TokenExtraData(BaseModel):
    class Config:
        extra = Extra.forbid

    contracts_may_hold_token: bool
    extra_fields: Dict[str, str]
    infusions: List[Infusion]
    max_per_address: str
    minter: str
    no_transfers_until: Optional[str]
    req_verified_to_own: bool
    royalty: str
    splits: List[Split]


class TokenMetadata(BaseModel):
    class Config:
        extra = Extra.forbid

    token_id: str
    token_info: Dict[str, str]


class VersumMintStorage(BaseModel):
    class Config:
        extra = Extra.forbid

    admin_check_lambda: str
    administrator: str
    all_tokens: List[str]
    big_map: Dict[str, str]
    contract_registry: str
    contracts_may_hold_tokens_global: bool
    extra_db: Dict[str, str]
    genesis_minters: List[str]
    genesis_timeout: str
    identity: str
    ledger: List[LedgerItem]
    market: str
    materia_address: str
    metadata: Dict[str, str]
    mint_materia_cost: str
    mint_slots: Dict[str, str]
    minting_paused: bool
    operators: List[Operator]
    paused: bool
    require_verified_to_mint: bool
    signed_co_creatorship: List[SignedCoCreatorshipItem]
    token_counter: str
    token_extra_data: Dict[str, TokenExtraData]
    token_metadata: Dict[str, TokenMetadata]
    total_supply: Dict[str, str]