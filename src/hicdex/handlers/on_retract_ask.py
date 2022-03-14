import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction

from hicdex.types.objktbid_marketplace.parameter.retract_ask import RetractAskParameter
from hicdex.types.objktbid_marketplace.storage import ObjktbidMarketplaceStorage


async def on_retract_ask(
    ctx: HandlerContext,
    retract_ask: Transaction[RetractAskParameter, ObjktbidMarketplaceStorage],
) -> None:

    try:
        ask = await models.Ask.filter(id=int(retract_ask.parameter.__root__), platform='bid').get_or_none()
    except Exception as e:
        ctx.logger.info('Error on retract ask `%s` - %s',
                        retract_ask.parameter.__root__, str(e))
        raise e

    if ask is not None:
        ask.status = models.AuctionStatus.CANCELLED
        ask.update_level = retract_ask.data.level  # type: ignore
        ask.update_timestamp = retract_ask.data.timestamp  # type: ignore

        await ask.save()
    else:
        ctx.logger.info('ask `%s` NOT FOUND', retract_ask.parameter.__root__)
