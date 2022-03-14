import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction

from hicdex.types.fxhash_minter.storage import FxhashMinterStorage
from hicdex.types.fxhash_minter.parameter.burn import BurnParameter

import logging
_logger = logging.getLogger(__name__)


async def fxhash_burn_token(
    ctx: HandlerContext,
    burn: Transaction[BurnParameter, FxhashMinterStorage],
) -> None:

    fa2_id = burn.data.target_address
    token_id = burn.parameter.__root__
    token = await models.Token.filter(id=int(token_id), fa2_id=fa2_id).get_or_none()
    if token is not None:
        await token.delete()
        _logger.info('Burned FxHash mint `%s`', token_id)
