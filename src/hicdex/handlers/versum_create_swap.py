import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from hicdex.metadata_utils import dump, proper_integer

from hicdex.types.versum_market.parameter.create_swap import CreateSwapParameter
from hicdex.types.versum_market.storage import VersumMarketStorage

import logging
_logger = logging.getLogger(__name__)


async def versum_create_swap(
    ctx: HandlerContext,
    create_swap: Transaction[CreateSwapParameter, VersumMarketStorage],
) -> None:

    swap_id = int(create_swap.storage.swap_counter) - 1

    fa2, _ = await models.Fa2.get_or_create(contract=create_swap.parameter.token.address)
    creator, _ = await models.Holder.get_or_create(address=create_swap.data.sender_address)

    token = await models.Token.filter(id=proper_integer(create_swap.parameter.token.nat), fa2_id=create_swap.parameter.token.address).first()

    try:
        ask_model = models.Ask(
            id=swap_id,  # type: ignore
            platform='versum',
            creator=creator,
            objkt_id=str(create_swap.parameter.token.nat),
            fa2=fa2,
            token=token,
            status=models.AuctionStatus.ACTIVE,
            require_verified=create_swap.parameter.require_verified,
            max_per_tx=proper_integer(
                create_swap.parameter.collect_max_per_tx),
            price=proper_integer(create_swap.parameter.starting_price_in_nat),
            end_price=proper_integer(
                create_swap.parameter.ending_price_in_nat),
            amount=proper_integer(create_swap.parameter.token_amount),
            amount_left=create_swap.parameter.token_amount,
            level=create_swap.data.level,
            timestamp=create_swap.data.timestamp,
        )

        if token is not None:
            ask_model.artist_id = token.creator_id
            ask_model.royalties = proper_integer(token.royalties)
        else:
            holder, _ = await models.Holder.get_or_create(address='')
            ask_model.artist_id = ''
            ask_model.royalties = 0

        await ask_model.save()
    except Exception as e:
        ctx.logger.info('Error on versum swap %s - Hash: %s',
                        swap_id, create_swap.data.hash)
        raise e
