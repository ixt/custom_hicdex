import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction

from hicdex.types.fxhash_user_moderation.storage import FxhashUserModerationStorage
from hicdex.types.fxhash_user_moderation.parameter.verify import VerifyParameter


async def fxhash_user_verified(
    ctx: HandlerContext,
    verify: Transaction[VerifyParameter, FxhashUserModerationStorage],
) -> None:

    addr = verify.parameter.__root__
    holder, _ = await models.Holder.get_or_create(address=addr)
    if holder:
        holder.fxflag = 10
        ctx.logger.info('Address `%s` verified', addr)
        await holder.save()
