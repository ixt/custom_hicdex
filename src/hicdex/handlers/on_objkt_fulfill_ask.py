
import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction

from hicdex.types.objktbid_marketplace2.storage import ObjktbidMarketplace2Storage
from hicdex.types.objktbid_marketplace2.parameter.fulfill_ask import FulfillAskParameter


async def on_objkt_fulfill_ask(
    ctx: HandlerContext,
    fulfill_ask: Transaction[FulfillAskParameter, ObjktbidMarketplace2Storage],
) -> None:

    # type: ignore
    ask = await models.Ask.filter(id=fulfill_ask.parameter.ask_id, platform='bid2').get().prefetch_related('creator', 'token')
    buyer, _ = await models.Holder.get_or_create(address=fulfill_ask.data.sender_address)

    fulfilled_ask = models.FulfilledAsk(
        platform='bid2',
        ask=ask,
        seller=ask.creator,
        buyer=buyer,
        fa2_id=ask.fa2_id,
        objkt_id=str(ask.objkt_id),
        token=ask.token,
        amount=1,
        price=ask.price,
        level=fulfill_ask.data.level,
        timestamp=fulfill_ask.data.timestamp,
    )
    await fulfilled_ask.save()

    ask.amount_left -= 1  # type: ignore
    if ask.amount_left == 0:
        ask.status = models.AuctionStatus.CONCLUDED
        ask.update_level = fulfill_ask.data.level  # type: ignore
        ask.update_timestamp = fulfill_ask.data.timestamp  # type: ignore
    await ask.save()
