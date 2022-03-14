
from hicdex.types.versum_mint.storage import VersumMintStorage
from hicdex.types.versum_mint.parameter.mint import MintParameter
from hicdex.metadata_utils import dump, proper_integer, get_fa2_metadata
from hicdex.utils import fromhex
import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction

import logging
_logger = logging.getLogger(__name__)


async def versum_mint(
    ctx: HandlerContext,
    mint: Transaction[MintParameter, VersumMintStorage],
) -> None:

    # token_id = list(mint.storage.token_metadata.keys())[0]
    token_id = int(mint.storage.token_counter) - 1

    fa2, _ = await models.Fa2.get_or_create(contract=mint.data.target_address)
    if await models.Token.exists(id=str(token_id), fa2_id=fa2.contract):
        return

    metadata = ''
    if mint.parameter.metadata and mint.parameter.metadata.get(''):
        metadata = fromhex(mint.parameter.metadata.get(''))

    holder, _ = await models.Holder.get_or_create(address=mint.data.sender_address)
    creator = holder
    creator.last_mint = mint.data.timestamp
    await creator.save()

    token = models.Token(
        id=str(token_id),
        fa2=fa2,
        uuid='{}_{}'.format(fa2.contract, token_id),
        royalties=proper_integer(mint.parameter.royalty),
        title='',
        description='',
        artifact_uri='',
        display_uri='',
        thumbnail_uri='',
        metadata=metadata,
        max_per_address=mint.parameter.max_per_address,
        req_verified=mint.parameter.req_verified_to_own,
        mime='',
        creator=creator,
        supply=mint.parameter.amount,
        level=mint.data.level,
        timestamp=mint.data.timestamp,
    )
    if metadata == '':
        token.fixed = True

    await token.save()

    seller_holding, _ = await models.TokenHolder.get_or_create(token=token, holder=holder, quantity=int(mint.parameter.amount))
    await seller_holding.save()

    await get_fa2_metadata(token)
