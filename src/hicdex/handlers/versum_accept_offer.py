import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from hicdex.metadata_utils import dump

from hicdex.types.versum_market.storage import VersumMarketStorage
from hicdex.types.versum_market.parameter.accept_offer import AcceptOfferParameter


async def versum_accept_offer(
    ctx: HandlerContext,
    accept_offer: Transaction[AcceptOfferParameter, VersumMarketStorage],
) -> None:

    bid = await models.Bid.filter(id=accept_offer.parameter.__root__, platform='versum').get()
    seller, _ = await models.Holder.get_or_create(address=accept_offer.data.sender_address)

    bid.seller = seller
    bid.status = models.AuctionStatus.CONCLUDED

    bid.update_level = accept_offer.data.level  # type: ignore
    bid.update_timestamp = accept_offer.data.timestamp  # type: ignore

    await bid.save()
