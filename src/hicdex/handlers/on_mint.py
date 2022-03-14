import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from hicdex.types.hen_minter.parameter.mint_objkt import MintOBJKTParameter
from hicdex.types.hen_minter.storage import HenMinterStorage
from hicdex.types.hen_objkts.parameter.mint import MintParameter
from hicdex.types.hen_objkts.storage import HenObjktsStorage
from hicdex.utils import fromhex
from hicdex.metadata_utils import proper_integer, fix_token_metadata


async def on_mint(
    ctx: HandlerContext,
    mint_objkt: Transaction[MintOBJKTParameter, HenMinterStorage],
    mint: Transaction[MintParameter, HenObjktsStorage],
) -> None:

    if await models.Token.exists(id=str(mint.parameter.token_id), fa2_id='KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton'):
        return

    holder, _ = await models.Holder.get_or_create(address=mint.parameter.address)
    creator = holder
    if mint.parameter.address != mint_objkt.data.sender_address:
        creator, _ = await models.Holder.get_or_create(address=mint_objkt.data.sender_address)

    fa2, _ = await models.Fa2.get_or_create(contract='KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton')

    creator.last_mint = mint.data.timestamp
    await creator.save()

    metadata = ''
    if mint_objkt.parameter.metadata:
        metadata = fromhex(mint_objkt.parameter.metadata)

    token = models.Token(
        id=mint.parameter.token_id,
        fa2=fa2,
        uuid='{}_{}'.format(fa2.contract, mint.parameter.token_id),
        royalties=proper_integer(mint_objkt.parameter.royalties),
        title='',
        description='',
        artifact_uri='',
        display_uri='',
        thumbnail_uri='',
        metadata=metadata,
        mime='',
        creator=creator,
        supply=proper_integer(mint.parameter.amount),
        level=mint.data.level,
        timestamp=mint.data.timestamp,
    )
    await token.save()

    seller_holding, _ = await models.TokenHolder.get_or_create(token=token, holder=holder, quantity=int(mint.parameter.amount))
    await seller_holding.save()

    await fix_token_metadata(token)
