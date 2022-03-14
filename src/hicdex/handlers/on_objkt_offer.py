
import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from hicdex.metadata_utils import proper_integer

from hicdex.types.objktbid_marketplace2.storage import ObjktbidMarketplace2Storage
from hicdex.types.objktbid_marketplace2.parameter.offer import OfferParameter


async def on_objkt_offer(
    ctx: HandlerContext,
    offer: Transaction[OfferParameter, ObjktbidMarketplace2Storage],
) -> None:

    fa2, _ = await models.Fa2.get_or_create(contract=offer.parameter.token.address)
    creator, _ = await models.Holder.get_or_create(address=offer.data.sender_address)
    token = await models.Token.filter(id=offer.parameter.token.token_id, fa2_id=offer.parameter.token.address).first().prefetch_related('creator')

    if len(offer.parameter.shares) > 0:
        share = offer.parameter.shares[0]
    else:
        share = None

    if token is None:
        artist = creator
        if share is not None and offer.data.sender_address != share.recipient:
            artist, _ = await models.Holder.get_or_create(address=share.recipient)
    else:
        artist = token.creator

    if share is None:
        royalties = 0
    else:
        royalties = proper_integer(share.amount) / 10

    bid_model = models.Bid(
        id=int(offer.storage.next_offer_id) - 1,  # type: ignore
        platform='bid2',
        creator=creator,
        objkt_id=str(offer.parameter.token.token_id),
        token=token,
        artist=artist,
        royalties=royalties,
        fa2=fa2,
        price=proper_integer(offer.parameter.amount),
        status=models.AuctionStatus.ACTIVE,
        level=offer.data.level,
        timestamp=offer.data.timestamp,
    )
    await bid_model.save()
