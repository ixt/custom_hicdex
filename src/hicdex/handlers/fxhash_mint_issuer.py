import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction

from hicdex.types.fxhash_minter.parameter.mint_issuer import MintIssuerParameter
from hicdex.types.fxhash_minter.storage import FxhashMinterStorage

from hicdex.utils import fromhex

from hicdex.metadata_utils import get_fa2_metadata
from hicdex.metadata_utils import dump


async def fxhash_mint_issuer(
    ctx: HandlerContext,
    mint_issuer: Transaction[MintIssuerParameter, FxhashMinterStorage],
) -> None:

    data = mint_issuer.storage.ledger
    ledger = list(data.values())[0]
    token_id = list(data.keys())[0]
    fa2_id = mint_issuer.data.target_address

    metadata = ''
    if ledger.metadata:
        metadata = fromhex(ledger.metadata)

    token = await models.Token.filter(id=str(token_id), fa2_id=fa2_id).get_or_none()
    if token is not None:
        # we are going back in time so let's update data if level match
        if token.level == mint_issuer.data.level:
            token.supply = int(ledger.supply)
            token.balance = int(ledger.balance)
            token.price = int(ledger.price)
            token.enabled = ledger.enabled
            token.royalties = ledger.royalties
            token.locked_seconds = ledger.locked_seconds
            await token.save()

        return

    creator, _ = await models.Holder.get_or_create(address=ledger.author)
    creator.last_mint = mint_issuer.data.timestamp
    await creator.save()

    fa2, _ = await models.Fa2.get_or_create(contract=fa2_id)

    token = models.Token(
        id=token_id,
        fa2=fa2,
        uuid='{}_{}'.format(fa2.contract, token_id),
        royalties=int(ledger.royalties),
        title='',
        description='',
        artifact_uri='',
        display_uri='',
        thumbnail_uri='',
        metadata=metadata,
        mime='',
        creator=creator,
        supply=int(ledger.supply),
        balance=int(ledger.balance),
        price=int(ledger.price),
        level=mint_issuer.data.level,
        timestamp=mint_issuer.data.timestamp,
        enabled=ledger.enabled,
        locked_seconds=ledger.locked_seconds
    )

    await token.save()
    await get_fa2_metadata(token)
