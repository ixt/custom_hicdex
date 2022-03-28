import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction

from hicdex.types.objktbid_marketplace.parameter.fulfill_bid import FulfillBidParameter
from hicdex.types.objktbid_marketplace.storage import ObjktbidMarketplaceStorage


async def on_fulfill_bid(
    ctx: HandlerContext,
    fulfill_bid: Transaction[FulfillBidParameter, ObjktbidMarketplaceStorage],
) -> None:

    try:
        bid = await models.Bid.filter(id=fulfill_bid.parameter.__root__, platform='bid').get()
        seller, _ = await models.Holder.get_or_create(address=fulfill_bid.data.sender_address)

        bid.seller = seller
        bid.status = models.AuctionStatus.CONCLUDED

        bid.update_level = fulfill_bid.data.level  # type: ignore
        bid.update_timestamp = fulfill_bid.data.timestamp  # type: ignore

        await bid.save()
    except:
        pass
