import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from hicdex.metadata_utils import dump

from hicdex.types.versum_market.storage import VersumMarketStorage
from hicdex.types.versum_market.parameter.cancel_swap import CancelSwapParameter


async def versum_cancel_swap(
    ctx: HandlerContext,
    cancel_swap: Transaction[CancelSwapParameter, VersumMarketStorage],
) -> None:

    ask = await models.Ask.filter(id=int(cancel_swap.parameter.__root__), platform='versum').get()
    ask.status = models.AuctionStatus.CANCELLED
    ask.update_level = cancel_swap.data.level  # type: ignore
    ask.update_timestamp = cancel_swap.data.timestamp  # type: ignore
    await ask.save()
