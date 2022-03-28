import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from hicdex.types.objktbid_dutch.parameter.buy import BuyParameter
from hicdex.types.objktbid_dutch.storage import ObjktbidDutchStorage


async def on_buy_dutch(
    ctx: HandlerContext,
    buy: Transaction[BuyParameter, ObjktbidDutchStorage],
) -> None:
    try:
        auction_model = await models.DutchAuction.filter(id=int(buy.parameter.__root__)).get()
        buyer, _ = await models.Holder.get_or_create(address=buy.data.sender_address)

        auction_model.buyer = buyer
        auction_model.buy_price = buy.data.amount  # type: ignore

        auction_model.status = models.AuctionStatus.CONCLUDED

        auction_model.update_level = buy.data.level  # type: ignore
        auction_model.update_timestamp = buy.data.timestamp  # type: ignore

        await auction_model.save()
    except:
        pass
