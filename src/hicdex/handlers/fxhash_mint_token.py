import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction

from hicdex.types.fxhash_minter.storage import FxhashMinterStorage
from hicdex.types.fxhash_minter.parameter.mint import MintParameter


async def fxhash_mint_token(
    ctx: HandlerContext,
    mint: Transaction[MintParameter, FxhashMinterStorage],
) -> None:

    fa2_id = mint.data.target_address
    ledger = list(mint.storage.ledger.values())[0]

    token = await models.Token.filter(id=str(mint.parameter.__root__), fa2_id=fa2_id).get_or_none()
    if token is not None:
        token.supply = ledger.supply
        token.balance = ledger.balance
        token.enabled = ledger.enabled
        await token.save()
