import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from hicdex.types.objktbid_english.parameter.conclude_auction import ConcludeAuctionParameter
from hicdex.types.objktbid_english.storage import ObjktbidEnglishStorage

from hicdex.metadata_utils import dump


async def on_conclude_english(
    ctx: HandlerContext,
    conclude_auction: Transaction[ConcludeAuctionParameter, ObjktbidEnglishStorage],
) -> None:

    data = conclude_auction.storage.auctions
    auction = list(data.values())[0]

    buyer, _ = await models.Holder.get_or_create(address=auction.highest_bidder)

    auction_model = await models.EnglishAuction.filter(id=int(conclude_auction.parameter.__root__), platform='bid').get()
    auction_model.update_level = conclude_auction.data.level  # type: ignore
    auction_model.update_timestamp = conclude_auction.data.timestamp  # type: ignore
    auction_model.status = models.AuctionStatus.CONCLUDED
    if auction.highest_bidder == auction_model.creator_id:
        auction_model.status = models.AuctionStatus.CANCELLED

    auction_model.highest_bidder = buyer
    auction_model.highest_bid = auction.current_price

    await auction_model.save()
