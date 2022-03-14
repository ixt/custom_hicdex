import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from hicdex.metadata_utils import dump, proper_integer, fix_token_metadata
from hicdex.types.hen_swap_v2.parameter.swap import SwapParameter
from hicdex.types.hen_swap_v2.storage import HenSwapV2Storage
from tortoise.exceptions import DoesNotExist


async def on_swap_v2(
    ctx: HandlerContext,
    swap: Transaction[SwapParameter, HenSwapV2Storage],
) -> None:

    try:
        token, _ = await models.Token.get_or_create(id=swap.parameter.objkt_id, fa2_id='KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton')
    except Exception as e:
        ctx.logger.info('Error on swap v2 - token `%s` not found',
                        swap.parameter.objkt_id)
        raise e

    holder, _ = await models.Holder.get_or_create(address=swap.data.sender_address)
    swap_id = int(swap.storage.counter) - 1

    is_valid = swap.parameter.creator == token.creator_id and int(
        swap.parameter.royalties) == int(token.royalties)  # type: ignore

    swap_model = models.Ask(
        id=swap_id,  # type: ignore
        objkt_id=token.id,
        fa2_id=token.fa2_id,
        creator=holder,
        artist_id=token.creator_id,
        platform='hen2',
        token=token,
        price=proper_integer(swap.parameter.xtz_per_objkt),
        amount=proper_integer(swap.parameter.objkt_amount),
        amount_left=proper_integer(swap.parameter.objkt_amount),
        status=models.AuctionStatus.ACTIVE,
        ophash=swap.data.hash,
        level=swap.data.level,
        timestamp=swap.data.timestamp,
        royalties=proper_integer(swap.parameter.royalties),
        is_valid=is_valid,
    )
    await swap_model.save()

    if not token.artifact_uri and not token.title:
        await fix_token_metadata(token)
