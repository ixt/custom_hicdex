from datetime import datetime
from enum import Enum, IntEnum

from tortoise import Model, fields


class SwapStatus(IntEnum):
    ACTIVE = 0
    FINISHED = 1
    CANCELED = 2


class ShareholderStatus(str, Enum):
    unspecified = 'unspecified'
    core_participant = 'core_participant'
    benefactor = 'benefactor'


class Holder(Model):
    address = fields.CharField(36, pk=True)
    name = fields.TextField(default='')
    fxname = fields.TextField(null=True)
    fxflag = fields.SmallIntField(null=True)
    twitter = fields.TextField(null=True)
    description = fields.TextField(default='')
    metadata_file = fields.TextField(default='')
    metadata = fields.JSONField(default={})
    hdao_balance = fields.BigIntField(default=0)
    is_split = fields.BooleanField(default=False)
    last_refresh = fields.DatetimeField(null=True, index=True)
    last_mint = fields.DatetimeField(null=True, index=True)
    last_buy = fields.DatetimeField(null=True, index=True)


class SplitContract(Model):
    contract = fields.ForeignKeyField('models.Holder', 'shares', index=True)
    administrator = fields.CharField(36, null=True)
    total_shares = fields.BigIntField(null=True)


class Shareholder(Model):
    split_contract = fields.ForeignKeyField(
        'models.SplitContract', 'shareholders', index=True)
    holder = fields.ForeignKeyField(
        'models.Holder', 'shareholders', index=True)
    shares = fields.BigIntField()
    holder_type = fields.CharEnumField(
        ShareholderStatus, default=ShareholderStatus.unspecified)


class MarketplaceStats(Model):
    id = fields.BigIntField(pk=True)
    platform = fields.CharField(20, index=True)
    primary_swap = fields.BooleanField(default=False)
    buy_on = fields.DateField(index=True)
    sales_count = fields.BigIntField(default=0)
    sales_total = fields.BigIntField(default=0)

    class Meta:
        unique_together = (("platform", "primary_swap", "buy_on"), )


class Token(Model):
    pk_id = fields.BigIntField(pk=True)
    id = fields.CharField(100, index=True)
    fa2 = fields.ForeignKeyField('models.Fa2', 'tokens', index=True)
    uuid = fields.CharField(140, null=True, index=True)
    creator = fields.ForeignKeyField(
        'models.Holder', 'tokens', index=True, null=True)
    title = fields.TextField(default='')
    description = fields.TextField(default='')
    artifact_uri = fields.TextField(default='')
    display_uri = fields.TextField(default='')
    thumbnail_uri = fields.TextField(default='')
    metadata = fields.TextField(default='')
    extra = fields.JSONField(default={})
    mime = fields.TextField(default='')
    royalties = fields.SmallIntField(default=0)
    supply = fields.IntField(default=0)
    balance = fields.SmallIntField(null=True)
    price = fields.BigIntField(null=True)
    is_signed = fields.BooleanField(default=False)
    enabled = fields.BooleanField(null=True)
    moderated = fields.SmallIntField(null=True)
    locked_seconds = fields.IntField(null=True)
    max_per_address = fields.SmallIntField(null=True)
    req_verified = fields.BooleanField(null=True)
    fixed = fields.BooleanField(default=False, index=True)
    level = fields.BigIntField(default=0)
    timestamp = fields.DatetimeField(default=datetime.utcnow())
    primary_total = fields.BigIntField(default=0, null=False, index=True)
    primary_count = fields.IntField(default=0, null=False)
    primary_price = fields.BigIntField(default=0, null=False)

    class Meta:
        unique_together = (("fa2_id", "id"), )


class Tag(Model):
    id = fields.BigIntField(pk=True)
    name = fields.CharField(255)


class TokenTag(Model):
    token = fields.ForeignKeyField(
        'models.Token', 'token_tags', null=False, index=True)
    tag = fields.ForeignKeyField(
        'models.Tag', 'tag_tokens', null=False, index=True)

    class Meta:
        table = 'token_tag'


class TokenHolder(Model):
    holder = fields.ForeignKeyField(
        'models.Holder', 'holders_token', null=False, index=True)
    token = fields.ForeignKeyField(
        'models.Token', 'token_holders', null=False, index=True)
    quantity = fields.BigIntField(default=0)

    class Meta:
        table = 'token_holder'


class Signatures(Model):
    token = fields.ForeignKeyField(
        'models.Token', 'token_signatures', null=False, index=True)
    holder = fields.ForeignKeyField(
        'models.Holder', 'holder_signatures', null=False, index=True)

    class Meta:
        table = 'split_signatures'
        unique_together = (("token", "holder"),)


# class Swap(Model):
#     id = fields.BigIntField(pk=True)
#     creator = fields.ForeignKeyField('models.Holder', 'swaps', index=True)
#     token = fields.ForeignKeyField('models.Token', 'swaps', index=True)
#     price = fields.BigIntField()
#     amount = fields.SmallIntField()
#     amount_left = fields.SmallIntField()
#     status = fields.IntEnumField(SwapStatus)
#     royalties = fields.SmallIntField()
#     contract_version = fields.SmallIntField()
#     is_valid = fields.BooleanField(default=True)

#     ophash = fields.CharField(51)
#     level = fields.BigIntField()
#     timestamp = fields.DatetimeField()


# class Trade(Model):
#     id = fields.BigIntField(pk=True)
#     token = fields.ForeignKeyField('models.Token', 'trades', index=True)
#     swap = fields.ForeignKeyField('models.Swap', 'trades', index=True)
#     seller = fields.ForeignKeyField('models.Holder', 'sales', index=True)
#     buyer = fields.ForeignKeyField('models.Holder', 'purchases', index=True)
#     amount = fields.BigIntField()

#     ophash = fields.CharField(51)
#     level = fields.BigIntField()
#     timestamp = fields.DatetimeField()

####################
# OBJKT.BID Models #
####################

class Block(Model):
    hash = fields.CharField(51, pk=True)
    predecessor = fields.CharField(51, null=False)
    level = fields.IntField(null=False)
    timestamp = fields.DatetimeField(null=False)


class AuctionStatus(str, Enum):
    ACTIVE = 'active'
    CANCELLED = 'cancelled'
    CONCLUDED = 'concluded'


class Fa2(Model):
    contract = fields.CharField(36, pk=True)
    name = fields.CharField(255, null=True)
    description = fields.TextField(null=True)
    creator = fields.ForeignKeyField(
        'models.Holder', 'collections', index=True, null=True)
    collection_id = fields.BigIntField(null=True)
    indexing = fields.BooleanField(default=False, null=False)
    timestamp = fields.DatetimeField(null=True)
    metadata = fields.TextField(null=True)


class EnglishAuction(Model):
    pk_id = fields.BigIntField(pk=True)
    id = fields.BigIntField(index=True)
    platform = fields.CharField(20, index=True)
    hash = fields.CharField(55, index=True)
    fa2 = fields.ForeignKeyField('models.Fa2', 'english_auctions', index=True)
    status = fields.CharEnumField(AuctionStatus)
    objkt_id = fields.CharField(100, index=True)
    token = fields.ForeignKeyField(
        'models.Token', 'english_auctions', null=True, index=True)
    creator = fields.ForeignKeyField(
        'models.Holder', 'created_english_auctions', index=True)
    artist = fields.ForeignKeyField(
        'models.Holder', 'starring_english_auctions', index=True)
    royalties = fields.BigIntField()
    start_time = fields.DatetimeField()
    end_time = fields.DatetimeField()
    extension_time = fields.BigIntField()
    price_increment = fields.BigIntField()
    reserve = fields.BigIntField()
    contract_version = fields.SmallIntField()

    level = fields.BigIntField()
    timestamp = fields.DatetimeField()

    update_level = fields.BigIntField(null=True)
    update_timestamp = fields.DatetimeField(null=True)
    highest_bid = fields.BigIntField(null=True)
    highest_bidder = fields.ForeignKeyField(
        'models.Holder', 'highest_english_bids', null=True, index=True)

    class Meta:
        table = 'english_auction'
        unique_together = (("platform", "id"), )


# class EnglishBid(Model):
#     id = fields.BigIntField(pk=True)
#     bidder = fields.ForeignKeyField(
#         'models.Holder', 'english_bids', index=True)
#     amount = fields.BigIntField()
#     auction = fields.ForeignKeyField(
#         'models.EnglishAuction', 'bids', index=True)

#     level = fields.BigIntField()
#     timestamp = fields.DatetimeField()

#     class Meta:
#         table = 'english_bid'


class DutchAuction(Model):
    id = fields.BigIntField(pk=True)
    hash = fields.CharField(55, index=True)
    fa2 = fields.ForeignKeyField('models.Fa2', 'dutch_auctions', index=True)
    status = fields.CharEnumField(AuctionStatus)
    objkt_id = fields.CharField(100, index=True)
    token = fields.ForeignKeyField(
        'models.Token', 'dutch_auctions', null=True, index=True)
    creator = fields.ForeignKeyField(
        'models.Holder', 'created_dutch_auctions', index=True)
    artist = fields.ForeignKeyField(
        'models.Holder', 'starring_dutch_auctions', index=True)
    royalties = fields.BigIntField()
    start_time = fields.DatetimeField()
    end_time = fields.DatetimeField()
    start_price = fields.BigIntField()
    end_price = fields.BigIntField(null=True)
    buyer = fields.ForeignKeyField(
        'models.Holder', 'won_dutch_auctions', index=True, null=True)
    buy_price = fields.BigIntField(null=True)
    contract_version = fields.SmallIntField()

    level = fields.BigIntField()
    timestamp = fields.DatetimeField()

    update_level = fields.BigIntField(null=True)
    update_timestamp = fields.DatetimeField(null=True)

    class Meta:
        table = 'dutch_auction'


class Bid(Model):
    pk_id = fields.BigIntField(pk=True)
    id = fields.BigIntField(index=True)
    platform = fields.CharField(20, index=True)
    creator = fields.ForeignKeyField('models.Holder', 'bids', index=True)
    artist = fields.ForeignKeyField(
        'models.Holder', 'starring_bids', index=True)
    objkt_id = fields.CharField(100, index=True)
    token = fields.ForeignKeyField(
        'models.Token', 'bids', null=True, index=True)
    fa2 = fields.ForeignKeyField('models.Fa2', 'bids', index=True)
    price = fields.BigIntField()
    royalties = fields.BigIntField()
    status = fields.CharEnumField(AuctionStatus)
    seller = fields.ForeignKeyField(
        'models.Holder', 'sold_bids', index=True, null=True)

    level = fields.BigIntField()
    timestamp = fields.DatetimeField()

    update_level = fields.BigIntField(null=True)
    update_timestamp = fields.DatetimeField(null=True)

    class Meta:
        unique_together = (("platform", "id"), )


class Ask(Model):
    pk_id = fields.BigIntField(pk=True)
    id = fields.BigIntField(index=True)
    platform = fields.CharField(20, index=True)
    creator = fields.ForeignKeyField('models.Holder', 'asks', index=True)
    artist = fields.ForeignKeyField(
        'models.Holder', 'starring_asks', index=True)
    objkt_id = fields.CharField(100, index=True)
    token = fields.ForeignKeyField(
        'models.Token', 'asks', null=True, index=True)
    fa2 = fields.ForeignKeyField('models.Fa2', 'asks', index=True)
    price = fields.BigIntField()
    royalties = fields.BigIntField()
    amount = fields.BigIntField()
    amount_left = fields.BigIntField()
    status = fields.CharEnumField(AuctionStatus)
    end_price = fields.BigIntField(null=True)
    require_verified = fields.BooleanField(default=False)
    max_per_tx = fields.BigIntField(null=True)
    is_valid = fields.BooleanField(default=True)

    level = fields.BigIntField()
    timestamp = fields.DatetimeField()

    update_level = fields.BigIntField(null=True)
    update_timestamp = fields.DatetimeField(null=True)

    class Meta:
        unique_together = (("platform", "id"), )


class FulfilledAsk(Model):
    id = fields.BigIntField(pk=True)
    platform = fields.CharField(20, index=True)
    objkt_id = fields.CharField(100, index=True)
    fa2 = fields.ForeignKeyField(
        'models.Fa2', 'fulfilled_asks', null=True, index=True)
    token = fields.ForeignKeyField(
        'models.Token', 'fulfilled_asks', null=True, index=True)
    ask = fields.ForeignKeyField('models.Ask', 'fulfilled', index=True)
    seller = fields.ForeignKeyField('models.Holder', 'sales', index=True)
    buyer = fields.ForeignKeyField('models.Holder', 'purchases', index=True)
    amount = fields.BigIntField()
    price = fields.BigIntField(null=True)

    level = fields.BigIntField()
    timestamp = fields.DatetimeField()

    class Meta:
        table = 'fulfilled_ask'
