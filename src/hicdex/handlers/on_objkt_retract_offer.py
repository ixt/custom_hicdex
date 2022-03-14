import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction

from hicdex.types.objktbid_marketplace2.storage import ObjktbidMarketplace2Storage
from hicdex.types.objktbid_marketplace2.parameter.retract_offer import RetractOfferParameter


async def on_objkt_retract_offer(
    ctx: HandlerContext,
    retract_offer: Transaction[RetractOfferParameter, ObjktbidMarketplace2Storage],
) -> None:

    bid = await models.Bid.filter(id=int(retract_offer.parameter.__root__), platform='bid2').get_or_none()
    if bid is not None:
        bid.status = models.AuctionStatus.CANCELLED
        bid.update_level = retract_offer.data.level  # type: ignore
        bid.update_timestamp = retract_offer.data.timestamp  # type: ignore
        await bid.save()
    else:
        ctx.logger.info('offer v2 `%s` NOT FOUND',
                        retract_offer.parameter.__root__)
