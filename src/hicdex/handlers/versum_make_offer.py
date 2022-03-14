import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from hicdex.metadata_utils import dump, proper_integer

from hicdex.types.versum_market.storage import VersumMarketStorage
from hicdex.types.versum_market.parameter.make_offer import MakeOfferParameter


async def versum_make_offer(
    ctx: HandlerContext,
    make_offer: Transaction[MakeOfferParameter, VersumMarketStorage],
) -> None:
    fa2, _ = await models.Fa2.get_or_create(contract=make_offer.parameter.token.address)
    creator, _ = await models.Holder.get_or_create(address=make_offer.data.sender_address)
    token = await models.Token.filter(id=proper_integer(make_offer.parameter.token.nat), fa2_id=make_offer.parameter.token.address).first()

    bid_model = models.Bid(
        id=int(make_offer.storage.offer_counter) - 1,  # type: ignore
        platform='versum',
        creator=creator,
        objkt_id=str(make_offer.parameter.token.nat),
        token=token,
        fa2=fa2,
        price=proper_integer(make_offer.data.amount),
        status=models.AuctionStatus.ACTIVE,
        level=make_offer.data.level,
        timestamp=make_offer.data.timestamp,
    )

    if token is not None:
        bid_model.artist_id = token.creator_id
        bid_model.royalties = proper_integer(token.royalties)
    else:
        holder, _ = await models.Holder.get_or_create(address='')
        bid_model.artist_id = ''
        bid_model.royalties = 0

    await bid_model.save()
