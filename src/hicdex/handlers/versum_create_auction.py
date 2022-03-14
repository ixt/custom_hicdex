
from hashids import Hashids

import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from hicdex.metadata_utils import proper_integer

from hicdex.types.versum_market.parameter.create_auction import CreateAuctionParameter
from hicdex.types.versum_market.storage import VersumMarketStorage

from datetime import datetime

hashids = Hashids(salt='versum.auction#', min_length=8)


async def versum_create_auction(
    ctx: HandlerContext,
    create_auction: Transaction[CreateAuctionParameter, VersumMarketStorage],
) -> None:

    auction_id = int(create_auction.storage.auction_counter) - 1
    fa2, _ = await models.Fa2.get_or_create(contract=create_auction.parameter.token.address)
    creator, _ = await models.Holder.get_or_create(address=create_auction.data.sender_address)
    token = await models.Token.filter(id=create_auction.parameter.token.nat, fa2_id=create_auction.parameter.token.address).first()

    auction_model = models.EnglishAuction(
        id=auction_id,  # type: ignore
        platform='versum',
        hash=hashids.encode(auction_id),
        fa2=fa2,
        status=models.AuctionStatus.ACTIVE,
        objkt_id=str(create_auction.parameter.token.nat),
        token=token,
        creator=creator,
        start_time=datetime.now(),
        end_time=create_auction.parameter.end_timestamp,
        price_increment=0,
        extension_time=0,
        reserve=create_auction.parameter.bid_amount,
        contract_version=1,
        timestamp=create_auction.data.timestamp,
        level=create_auction.data.level,
    )

    if token is not None:
        auction_model.artist_id = token.creator_id
        auction_model.royalties = proper_integer(token.royalties)
    else:
        holder, _ = await models.Holder.get_or_create(address='')
        auction_model.artist_id = ''
        auction_model.royalties = 0

    await auction_model.save()
