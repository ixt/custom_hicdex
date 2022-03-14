import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from hicdex.metadata_utils import dump

from hicdex.types.versum_market.storage import VersumMarketStorage
from hicdex.types.versum_market.parameter.collect_swap import CollectSwapParameter

import logging
_logger = logging.getLogger(__name__)


async def versum_collect_swap(
    ctx: HandlerContext,
    collect_swap: Transaction[CollectSwapParameter, VersumMarketStorage],
) -> None:

    try:
        swap_id = int(collect_swap.parameter.swap_id)
        ask = await models.Ask.filter(id=swap_id, platform='versum').get().prefetch_related('creator', 'token')
        buyer, _ = await models.Holder.get_or_create(address=collect_swap.data.sender_address)

        fulfilled_ask = models.FulfilledAsk(
            platform='versum',
            ask=ask,
            seller=ask.creator,
            buyer=buyer,
            fa2_id=ask.fa2_id,
            objkt_id=str(ask.objkt_id),
            token=ask.token,
            amount=int(collect_swap.parameter.amount),
            price=ask.price,
            level=collect_swap.data.level,
            timestamp=collect_swap.data.timestamp,
        )
        await fulfilled_ask.save()

        ask.amount_left -= int(collect_swap.parameter.amount)  # type: ignore
        if ask.amount_left == 0:
            ask.status = models.AuctionStatus.CONCLUDED
            ask.update_level = collect_swap.data.level  # type: ignore
            ask.update_timestamp = collect_swap.data.timestamp  # type: ignore

        await ask.save()
    except Exception as e:
        ctx.logger.info('Error on collect versum swap %s - Hash: %s',
                        swap_id, collect_swap.data.hash)
        raise e
