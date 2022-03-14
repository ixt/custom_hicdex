import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from hicdex.metadata_utils import dump

from hicdex.types.versum_market.storage import VersumMarketStorage
from hicdex.types.versum_market.parameter.cancel_offer import CancelOfferParameter


async def versum_cancel_offer(
    ctx: HandlerContext,
    cancel_offer: Transaction[CancelOfferParameter, VersumMarketStorage],
) -> None:

    bid = await models.Bid.filter(id=int(cancel_offer.parameter.__root__), platform='versum').get_or_none()
    if bid is not None:
        bid.status = models.AuctionStatus.CANCELLED

        bid.update_level = cancel_offer.data.level  # type: ignore
        bid.update_timestamp = cancel_offer.data.timestamp  # type: ignore

        await bid.save()
