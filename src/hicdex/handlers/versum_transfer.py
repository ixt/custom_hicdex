
import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction

from hicdex.types.versum_mint.parameter.transfer import TransferParameter
from hicdex.types.versum_mint.storage import VersumMintStorage
from hicdex.metadata_utils import dump


async def versum_transfer(
    ctx: HandlerContext,
    transfer: Transaction[TransferParameter, VersumMintStorage],
) -> None:
    for t in transfer.parameter.__root__:
        sender, _ = await models.Holder.get_or_create(address=t.from_)
        for tx in t.txs:
            receiver, _ = await models.Holder.get_or_create(address=tx.to_)
            if tx.to_ != 'tz1burnburnburnburnburnburnburjAYjjX':
                receiver.last_buy = transfer.data.timestamp
                await receiver.save()

            token = await models.Token.filter(id=str(tx.token_id), fa2_id='KT1LjmAdYQCLBjwv4S2oFkEzyHVkomAf5MrW').get()

            sender_holding, _ = await models.TokenHolder.get_or_create(token=token, holder=sender)
            sender_holding.quantity -= int(tx.amount)  # type: ignore
            if sender_holding.quantity == 0:
                await sender_holding.delete()
            else:
                await sender_holding.save()

            receiver_holding, _ = await models.TokenHolder.get_or_create(token=token, holder=receiver)
            receiver_holding.quantity += int(tx.amount)  # type: ignore
            await receiver_holding.save()

            if tx.to_ == 'tz1burnburnburnburnburnburnburjAYjjX':
                token.supply -= int(tx.amount)  # type: ignore
                await token.save()
