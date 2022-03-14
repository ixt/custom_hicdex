import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from hicdex.metadata_utils import proper_integer

from hicdex.types.objktbid_marketplace.parameter.bid import BidParameter
from hicdex.types.objktbid_marketplace.storage import ObjktbidMarketplaceStorage


async def on_create_bid(
    ctx: HandlerContext,
    bid: Transaction[BidParameter, ObjktbidMarketplaceStorage],
) -> None:

    fa2, _ = await models.Fa2.get_or_create(contract=bid.parameter.fa2)
    creator, _ = await models.Holder.get_or_create(address=bid.data.sender_address)
    token = await models.Token.filter(id=bid.parameter.objkt_id, fa2_id=bid.parameter.fa2).first()

    artist = creator
    if bid.parameter.artist != bid.data.sender_address:
        artist, _ = await models.Holder.get_or_create(address=bid.parameter.artist)

    bid_model = models.Bid(
        id=int(bid.storage.bid_id) - 1,  # type: ignore
        platform='bid',
        creator=creator,
        objkt_id=str(bid.parameter.objkt_id),
        token=token,
        fa2=fa2,
        price=proper_integer(bid.data.amount),
        status=models.AuctionStatus.ACTIVE,
        level=bid.data.level,
        timestamp=bid.data.timestamp,
        artist=artist,
        royalties=proper_integer(bid.parameter.royalties),
    )
    await bid_model.save()
