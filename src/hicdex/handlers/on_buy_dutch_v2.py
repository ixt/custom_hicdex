
import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction

from hicdex.types.objktbid_dutch2.parameter.buy import BuyParameter
from hicdex.types.objktbid_dutch2.storage import ObjktbidDutch2Storage


async def on_buy_dutch_v2(
    ctx: HandlerContext,
    buy: Transaction[BuyParameter, ObjktbidDutch2Storage],
) -> None:

    auction_model = await models.DutchAuction.filter(id=int(buy.parameter.auction_id), contract_version=2).get()
    buyer, _ = await models.Holder.get_or_create(address=buy.data.sender_address)

    auction_model.buyer = buyer
    auction_model.buy_price = buy.parameter.amount  # type: ignore

    auction_model.status = models.AuctionStatus.CONCLUDED

    auction_model.update_level = buy.data.level  # type: ignore
    auction_model.update_timestamp = buy.data.timestamp  # type: ignore

    await auction_model.save()
