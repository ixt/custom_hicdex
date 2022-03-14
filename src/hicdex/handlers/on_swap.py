import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from hicdex.types.hen_minter.parameter.swap import SwapParameter
from hicdex.types.hen_minter.storage import HenMinterStorage
from hicdex.metadata_utils import fix_token_metadata


async def on_swap(
    ctx: HandlerContext,
    swap: Transaction[SwapParameter, HenMinterStorage],
) -> None:
    holder, _ = await models.Holder.get_or_create(address=swap.data.sender_address)
    token = await models.Token.filter(id=swap.parameter.objkt_id, fa2_id='KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton').get()
    swap_model = models.Ask(
        id=int(swap.storage.swap_id) - 1,  # type: ignore
        objkt_id=token.id,
        fa2_id=token.fa2_id,
        creator=holder,
        artist_id=token.creator_id,
        token=token,
        price=swap.parameter.xtz_per_objkt,
        amount=swap.parameter.objkt_amount,
        amount_left=swap.parameter.objkt_amount,
        status=models.AuctionStatus.ACTIVE,
        ophash=swap.data.hash,
        level=swap.data.level,
        timestamp=swap.data.timestamp,
        royalties=token.royalties,
        platform='hen1',
        is_valid=True,
    )
    await swap_model.save()

    if not token.artifact_uri and not token.title:
        await fix_token_metadata(token)
