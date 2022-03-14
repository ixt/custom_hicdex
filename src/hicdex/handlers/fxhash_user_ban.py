import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction

from hicdex.types.fxhash_user_moderation.storage import FxhashUserModerationStorage
from hicdex.types.fxhash_user_moderation.parameter.ban import BanParameter


async def fxhash_user_ban(
    ctx: HandlerContext,
    ban: Transaction[BanParameter, FxhashUserModerationStorage],
) -> None:

    addr = ban.parameter.__root__
    holder, _ = await models.Holder.get_or_create(address=addr)
    if holder:
        holder.fxflag = 3
        ctx.logger.info('Address `%s` banned', addr)
        await holder.save()
