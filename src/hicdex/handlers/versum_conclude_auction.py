
import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from hicdex.metadata_utils import dump

from hicdex.types.versum_market.parameter.withdraw import WithdrawParameter
from hicdex.types.versum_market.storage import VersumMarketStorage


async def versum_conclude_auction(
    ctx: HandlerContext,
    withdraw: Transaction[WithdrawParameter, VersumMarketStorage],
) -> None:

    data = withdraw.data.diffs[0]
    auction = data.get('content').get('value')

    if auction.get('bidder') == '':
        raise RuntimeError(
            f'conclude versum auction bidder not found - `{withdraw.parameter.__root__}`')

    buyer, _ = await models.Holder.get_or_create(address=auction.get('bidder'))

    auction_model = await models.EnglishAuction.filter(id=int(withdraw.parameter.__root__), platform='versum').get_or_none()
    if auction_model is not None:
        auction_model.update_level = withdraw.data.level  # type: ignore
        auction_model.update_timestamp = withdraw.data.timestamp  # type: ignore
        auction_model.status = models.AuctionStatus.CONCLUDED
        auction_model.highest_bidder = buyer

        if auction.get('bidder') == auction.get('seller'):
            auction_model.status = models.AuctionStatus.CANCELLED
            auction_model.highest_bid = 0
        else:
            auction_model.highest_bid = auction.get('bid_amount')

        await auction_model.save()
    else:
        ctx.logger.info('versum auction `%s` NOT FOUND',
                        withdraw.parameter.__root__)
