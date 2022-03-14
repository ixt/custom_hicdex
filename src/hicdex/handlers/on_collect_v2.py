import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from hicdex.types.hen_swap_v2.parameter.collect import CollectParameter
from hicdex.types.hen_swap_v2.storage import HenSwapV2Storage


async def on_collect_v2(
    ctx: HandlerContext,
    collect: Transaction[CollectParameter, HenSwapV2Storage],
) -> None:
    try:
        swap = await models.Ask.filter(id=int(collect.parameter.__root__), platform='hen2').get()
    except Exception as e:
        ctx.logger.info('Error on swap `%s` - not found',
                        collect.parameter.__root__)
        raise e

    seller = await swap.creator
    buyer, _ = await models.Holder.get_or_create(address=collect.data.sender_address)
    token = await swap.token.get()  # type: ignore

    trade = models.FulfilledAsk(
        objkt_id=token.id,
        fa2_id=token.fa2_id,
        ask=swap,
        seller=seller,
        buyer=buyer,
        token=token,
        amount=1,
        price=swap.price,
        level=collect.data.level,
        timestamp=collect.data.timestamp,
        platform=swap.platform,
    )
    await trade.save()

    swap.amount_left -= 1  # type: ignore
    if swap.amount_left == 0:
        swap.status = models.AuctionStatus.CONCLUDED
    await swap.save()
