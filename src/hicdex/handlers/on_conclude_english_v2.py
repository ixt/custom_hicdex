import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction

from hicdex.types.objktbid_english2.parameter.settle_auction import SettleAuctionParameter
from hicdex.types.objktbid_english2.storage import ObjktbidEnglish2Storage

from hicdex.metadata_utils import dump


async def on_conclude_english_v2(
    ctx: HandlerContext,
    settle_auction: Transaction[SettleAuctionParameter, ObjktbidEnglish2Storage],
) -> None:

    data = settle_auction.data.diffs[0]
    auction = data.get('content').get('value')

    auction_model = await models.EnglishAuction.filter(id=int(settle_auction.parameter.__root__), platform='bid2').get()
    buyer, _ = await models.Holder.get_or_create(address=auction.get('highest_bidder'))

    auction_model.update_level = settle_auction.data.level  # type: ignore
    auction_model.update_timestamp = settle_auction.data.timestamp  # type: ignore
    auction_model.status = models.AuctionStatus.CONCLUDED
    if auction.get('highest_bidder') == auction_model.creator_id:
        auction_model.status = models.AuctionStatus.CANCELLED

    auction_model.highest_bidder = buyer
    auction_model.highest_bid = auction.get('current_price')

    await auction_model.save()
