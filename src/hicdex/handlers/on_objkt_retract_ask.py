
import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction

from hicdex.types.objktbid_marketplace2.storage import ObjktbidMarketplace2Storage
from hicdex.types.objktbid_marketplace2.parameter.retract_ask import RetractAskParameter


async def on_objkt_retract_ask(
    ctx: HandlerContext,
    retract_ask: Transaction[RetractAskParameter, ObjktbidMarketplace2Storage],
) -> None:

    try:
        ask = await models.Ask.filter(id=int(retract_ask.parameter.__root__), platform='bid2').get_or_none()
    except Exception as e:
        ctx.logger.info('Error on retract ask v2 `%s` - %s',
                        retract_ask.parameter.__root__, str(e))
        raise e

    if ask is not None:
        ask.status = models.AuctionStatus.CANCELLED
        ask.update_level = retract_ask.data.level  # type: ignore
        ask.update_timestamp = retract_ask.data.timestamp  # type: ignore

        await ask.save()
    else:
        ctx.logger.info('ask v2 `%s` NOT FOUND',
                        retract_ask.parameter.__root__)
