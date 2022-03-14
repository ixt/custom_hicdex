from hashids import Hashids

import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from hicdex.metadata_utils import proper_integer

from hicdex.types.objktbid_dutch2.parameter.create_auction import CreateAuctionParameter
from hicdex.types.objktbid_dutch2.storage import ObjktbidDutch2Storage

hashids = Hashids(salt='objkt.bid2!', min_length=8)


async def on_create_dutch_v2(
    ctx: HandlerContext,
    create_auction: Transaction[CreateAuctionParameter, ObjktbidDutch2Storage],
) -> None:

    auction_id = int(create_auction.storage.next_auction_id) - 1
    fa2, _ = await models.Fa2.get_or_create(contract=create_auction.parameter.token.address)
    creator, _ = await models.Holder.get_or_create(address=create_auction.data.sender_address)
    token = await models.Token.filter(id=str(create_auction.parameter.token.token_id), fa2_id=create_auction.parameter.token.address).first().prefetch_related('creator')

    if len(create_auction.parameter.shares) > 0:
        share = create_auction.parameter.shares[0]
    else:
        share = None

    if token is None:
        artist = creator
        if share is not None and create_auction.data.sender_address != share.recipient:
            artist, _ = await models.Holder.get_or_create(address=share.recipient)
    else:
        artist = token.creator

    if share is None:
        royalties = 0
    else:
        royalties = proper_integer(share.amount) / 10

    auction_model = models.DutchAuction(
        id=auction_id,  # type: ignore
        hash=hashids.encode(auction_id),
        fa2=fa2,
        status=models.AuctionStatus.ACTIVE,
        objkt_id=str(create_auction.parameter.token.token_id),
        token=token,
        creator=creator,
        artist=artist,
        royalties=royalties,
        start_time=create_auction.parameter.start_time,
        end_time=create_auction.parameter.end_time,
        start_price=create_auction.parameter.start_price,
        end_price=create_auction.parameter.end_price,
        contract_version=2,
        timestamp=create_auction.data.timestamp,
        level=create_auction.data.level,
    )
    await auction_model.save()
