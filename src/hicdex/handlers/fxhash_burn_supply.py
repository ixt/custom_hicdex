import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction

from hicdex.types.fxhash_minter.parameter.burn_supply import BurnSupplyParameter
from hicdex.types.fxhash_minter.storage import FxhashMinterStorage

from hicdex.metadata_utils import dump

import logging
_logger = logging.getLogger(__name__)


async def fxhash_burn_supply(
    ctx: HandlerContext,
    burn_supply: Transaction[BurnSupplyParameter, FxhashMinterStorage],
) -> None:

    ledger = list(burn_supply.storage.ledger.values())[0]
    fa2_id = burn_supply.data.target_address
    token_id = burn_supply.parameter.issuer_id
    amount = int(burn_supply.parameter.amount)

    token = await models.Token.filter(id=int(token_id), fa2_id=fa2_id).get_or_none()
    if token is not None:
        token.supply = ledger.supply
        token.balance = ledger.balance
        token.enabled = ledger.enabled
        token.price = ledger.price
        token.royalties = ledger.royalties
        token.locked_seconds = ledger.locked_seconds
        await token.save()
        _logger.info('Burned `%s` editions of token `%s`', amount, token_id)
