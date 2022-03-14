
import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction

from hicdex.types.objktbid_english2.storage import ObjktbidEnglish2Storage
from hicdex.types.objktbid_english2.parameter.cancel_auction import CancelAuctionParameter


async def on_cancel_english_v2(
    ctx: HandlerContext,
    cancel_auction: Transaction[CancelAuctionParameter, ObjktbidEnglish2Storage],
) -> None:

    auction_model = await models.EnglishAuction.filter(id=int(cancel_auction.parameter.__root__), platform='bid2').get()
    auction_model.status = models.AuctionStatus.CANCELLED

    auction_model.update_level = cancel_auction.data.level  # type: ignore
    auction_model.update_timestamp = cancel_auction.data.timestamp  # type: ignore

    await auction_model.save()
