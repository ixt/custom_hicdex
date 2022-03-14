
import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from hicdex.metadata_utils import proper_integer

from hicdex.types.objktbid_marketplace2.storage import ObjktbidMarketplace2Storage
from hicdex.types.objktbid_marketplace2.parameter.ask import AskParameter


async def on_objkt_ask(
    ctx: HandlerContext,
    ask: Transaction[AskParameter, ObjktbidMarketplace2Storage],
) -> None:

    fa2, _ = await models.Fa2.get_or_create(contract=ask.parameter.token.address)
    creator, _ = await models.Holder.get_or_create(address=ask.data.sender_address)
    token = await models.Token.filter(id=str(ask.parameter.token.token_id), fa2_id=ask.parameter.token.address).first().prefetch_related('creator')

    if len(ask.parameter.shares) > 0:
        share = ask.parameter.shares[0]
    else:
        share = None

    if token is None:
        artist = creator
        if share is not None and ask.data.sender_address != share.recipient:
            artist, _ = await models.Holder.get_or_create(address=share.recipient)
    else:
        artist = token.creator

    if share is None:
        royalties = 0
    else:
        royalties = proper_integer(share.amount) / 10

    ask_model = models.Ask(
        id=int(ask.storage.next_ask_id) - 1,  # type: ignore
        platform='bid2',
        creator=creator,
        objkt_id=str(ask.parameter.token.token_id),
        fa2=fa2,
        token=token,
        artist=artist,
        royalties=royalties,
        price=proper_integer(ask.parameter.amount),
        amount=proper_integer(ask.parameter.editions),
        amount_left=proper_integer(ask.parameter.editions),
        status=models.AuctionStatus.ACTIVE,
        level=ask.data.level,
        timestamp=ask.data.timestamp,
    )
    await ask_model.save()
