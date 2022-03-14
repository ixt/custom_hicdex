import hicdex.models as models
from dipdup.models import Transaction
from hicdex.types.objktbid_dutch2.storage import ObjktbidDutch2Storage
from dipdup.context import HandlerContext
from hicdex.types.objktbid_dutch2.parameter.cancel_auction import CancelAuctionParameter


async def on_cancel_dutch_v2(
    ctx: HandlerContext,
    cancel_auction: Transaction[CancelAuctionParameter, ObjktbidDutch2Storage],
) -> None:

    auction_model = await models.DutchAuction.filter(id=int(cancel_auction.parameter.__root__), contract_version=2).get()
    auction_model.status = models.AuctionStatus.CANCELLED

    auction_model.update_level = cancel_auction.data.level  # type: ignore
    auction_model.update_timestamp = cancel_auction.data.timestamp  # type: ignore

    await auction_model.save()
