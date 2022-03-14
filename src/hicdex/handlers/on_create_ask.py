import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from hicdex.metadata_utils import proper_integer

from hicdex.types.objktbid_marketplace.parameter.ask import AskParameter
from hicdex.types.objktbid_marketplace.storage import ObjktbidMarketplaceStorage


async def on_create_ask(
    ctx: HandlerContext,
    ask: Transaction[AskParameter, ObjktbidMarketplaceStorage],
) -> None:

    fa2, _ = await models.Fa2.get_or_create(contract=ask.parameter.fa2)
    creator, _ = await models.Holder.get_or_create(address=ask.data.sender_address)

    artist = creator
    if ask.data.sender_address != ask.parameter.artist:
        artist, _ = await models.Holder.get_or_create(address=ask.parameter.artist)

    token = await models.Token.filter(id=ask.parameter.objkt_id, fa2_id=ask.parameter.fa2).first()

    ask_model = models.Ask(
        id=int(ask.storage.ask_id) - 1,  # type: ignore
        platform='bid',
        creator=creator,
        objkt_id=str(ask.parameter.objkt_id),
        fa2=fa2,
        token=token,
        price=proper_integer(ask.parameter.price),
        status=models.AuctionStatus.ACTIVE,
        level=ask.data.level,
        timestamp=ask.data.timestamp,
        artist=artist,
        royalties=proper_integer(ask.parameter.royalties),
        amount=proper_integer(ask.parameter.amount),
        amount_left=proper_integer(ask.parameter.amount),
    )
    await ask_model.save()
