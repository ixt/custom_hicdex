import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from hicdex.types.hen_swap_v2.parameter.cancel_swap import CancelSwapParameter
from hicdex.types.hen_swap_v2.storage import HenSwapV2Storage


async def on_cancel_swap_v2(
    ctx: HandlerContext,
    cancel_swap: Transaction[CancelSwapParameter, HenSwapV2Storage],
) -> None:
    swap = await models.Ask.filter(id=int(cancel_swap.parameter.__root__), platform='hen2').get()
    swap.status = models.AuctionStatus.CANCELLED
    swap.update_level = cancel_swap.data.level  # type: ignore
    swap.update_timestamp = cancel_swap.data.timestamp  # type: ignore
    await swap.save()
