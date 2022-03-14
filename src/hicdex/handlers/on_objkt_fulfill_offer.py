
import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction

from hicdex.types.objktbid_marketplace2.storage import ObjktbidMarketplace2Storage
from hicdex.types.objktbid_marketplace2.parameter.fulfill_offer import FulfillOfferParameter


async def on_objkt_fulfill_offer(
    ctx: HandlerContext,
    fulfill_offer: Transaction[FulfillOfferParameter, ObjktbidMarketplace2Storage],
) -> None:

    bid = await models.Bid.filter(id=fulfill_offer.parameter.offer_id, platform='bid2').get()
    seller, _ = await models.Holder.get_or_create(address=fulfill_offer.data.sender_address)

    bid.seller = seller
    bid.status = models.AuctionStatus.CONCLUDED

    bid.update_level = fulfill_offer.data.level  # type: ignore
    bid.update_timestamp = fulfill_offer.data.timestamp  # type: ignore

    await bid.save()
