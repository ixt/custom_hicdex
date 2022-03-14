import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction

from hicdex.types.fxhash_minter.storage import FxhashMinterStorage
from hicdex.types.fxhash_minter.parameter.update_issuer import UpdateIssuerParameter

from hicdex.metadata_utils import dump


async def fxhash_update_issuer(
    ctx: HandlerContext,
    update_issuer: Transaction[UpdateIssuerParameter, FxhashMinterStorage],
) -> None:

    infos = update_issuer.parameter
    fa2_id = update_issuer.data.target_address
    token_id = infos.issuer_id

    token = await models.Token.filter(id=str(token_id), fa2_id=fa2_id).get_or_none()
    if token is not None:
        token.royalties = int(infos.royalties)
        token.price = int(infos.price)
        token.enabled = int(infos.enabled)
        await token.save()
